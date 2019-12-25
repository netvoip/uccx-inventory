#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib3
import requests
import xmltodict
import argparse
import configparser
import os

urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'ECDHE_RSA_AES_128_CBC_SHA1'
Noparams = Errored = 0
# Limit max app count for testing purposes
Applimit = 0

def ApiRequest(url):
    # Returns API request result
    Response = requests.get((url),
        auth=(apiuser, apipassword), verify=False)
    Response.encoding = 'utf-8'
    Out = Response.text
    return Out

def GetApp(url):
    # Returns dict of application attributes
    global Errored
    Response = ApiRequest(url)
    Item = xmltodict.parse(Response)
    if 'application' in Item: Item = Item['application']
    Dict = {}
    Dictparams = {}
    try:
        Dict = {'name': Item['applicationName'], 'state': Item['enabled'],
                'script': Item['ScriptApplication']['script'], 'maxsession': Item['maxsession']}
        if 'scriptParams' in Item['ScriptApplication']:
            ItemParams = Item['ScriptApplication']['scriptParams']
            if type(ItemParams) is list:
                for element in ItemParams:
                    Dictparams[element['name']] = element['value']
            else:
                Dictparams[ItemParams['name']] = ItemParams['value']
        Dict['parameters'] = Dictparams
    except:
        print('Something went wrong with {}\n'.format(Item['applicationName']))
        Errored += 1
    return Dict

def GetApplications(url):
    global Errored
    Out = []
    # Make list of links to every application
    Appdict = []
    Appdict = xmltodict.parse(ApiRequest(url))
    Appdict = Appdict['applications']['application']
    Appurls = []
    for i in Appdict:
        Appurls.append(i['self'].replace ('+', ' '))
    # Make list of dicts for applications
    for i in Appurls:
        Out.append(GetApp(i))
        if len(Out) == Applimit:
            break
    return Out

def GetContent(url, Type, Out):
    # Writes prompts/scripts attributes to Out list
    Level1 = xmltodict.parse(ApiRequest(url))
    if len(Level1) > 1:
        Level1 = Level1['Files'][Type]
    else:
        Level1 = Level1['Files']

    if 'File' in Level1:
        for i in Level1['File']:
            Dict = {}
            Dict = {'fullpath': i['path'] + i['FileName'], 'name': i['FileName'], 'path': i['path'],
                    'size': i['Details']['size'], 'dateModified': i['Details']['dateModified'],
                    'modifiedBy': i['Details']['modifiedBy']}
            Out.append(Dict)

    if 'Folder' in Level1:
        if not(type(Level1['Folder']) is list):
            if Level1['Folder']['Details']['size'] != '0 KB':
                Urlpath = url + '{}/'.format(Level1['Folder']['FolderName'])
                GetContent(Urlpath, Type, Out)
            return

        for i in Level1['Folder']:
            if ('FolderName' in i):
                if i['Details']['size']!= '0 KB':
                    Urlpath = url + '{}/'.format(i['FolderName'])
                    GetContent(Urlpath, Type, Out)
    return Out

def GetTriggers(url):
    Response = ApiRequest(url)
    Items = xmltodict.parse(Response)
    Items = Items['triggers']['trigger']
    Out = []
    if len(Items) > 0:
        for i in Items:
            Dict = {}
            Dict = {'dn': i['directoryNumber'], 'enabled': i['triggerEnabled'], 'locale': i['locale'],
                    'application': i['application']['@name'], 'deviceName': i['deviceName'],
                    'description': i['description'], 'sessions': i['maxNumOfSessions'],
                    'idleTimeout': i['idleTimeout'], 'alertingNameAscii': i['alertingNameAscii'],
                    'dpool': i['devicePool'], 'location': i['location'], 'partition': i['partition'],
                    'css': i['callingSearchSpace'], 'cssredirect': i['callingSearchSpaceForRedirect'],
                    'presenceGroup': i['presenceGroup'], 'forwardBusy': i['forwardBusy']['forwardBusyDestination'],
                    'displayname': i['display'], 'phonemask': i['externalPhoneMaskNumber']
                    }
            Out.append(Dict)
        Out = sorted(Out, key=lambda k: k['dn'])
    return Out

# Retrieve connection variables
path = os.path.dirname(os.path.abspath( __file__ ))
with open(os.path.join(path, 'uccx_vars.conf')) as config:
    vars = configparser.ConfigParser()
    vars.read_file(config)
host = vars['uccx']['host']
apiuser = vars['uccx']['apiuser']
apipassword = vars['uccx']['apipassword']
# Parsing arguments
parser = argparse.ArgumentParser(description='''Prints UCCX explicitly defined parameters
of all applications, reports unused prompt and script files. \n'-allprompts' and '-allscripts'
will show all files in the system. '-noprompts' '-noscripts' and '-noapps' will remove unwanted data.
''')
parser.add_argument('-allprompts', action="store_true", dest="allprompts")
parser.add_argument('-allscripts', action="store_true", dest="allscripts")
parser.add_argument('-alltriggers', action="store_true", dest="alltriggers")
parser.add_argument('-noprompts', action="store_true", dest="noprompts")
parser.add_argument('-noscripts', action="store_true", dest="noscripts")
parser.add_argument('-notriggers', action="store_true", dest="notriggers")
parser.add_argument('-noapps', action="store_true", dest="noapps")
args = parser.parse_args()
Usecase = {'applications': not(args.noapps), 'prompts': not(args.noprompts), 'allprompts': args.allprompts,
           'scripts': not(args.noscripts), 'allscripts': args.allscripts,
           'triggers': not(args.notriggers), 'alltriggers': args.alltriggers}

if Usecase['triggers']:
    Triggers = GetTriggers('https://{}/adminapi/trigger/'.format(host))
    Texttr = '\nAll triggers:\n\n'
    for i in Triggers:
        Texttr += 'DN: {}'.format(i['dn'])
        if i['enabled'] == 'false': Texttr += ' (disabled)'
        if i['forwardBusy']: Texttr += '. Forward Busy to: {}'.format(i['forwardBusy'])
        Texttr += '\nApplication: {}\n'.format(i['application'])
        Texttr += 'Description: {}\n--\n'.format(i['description'])
        Texttr += 'Device name: {}, Sessions: {}\n'.format(i['deviceName'], i['sessions'])
        Texttr += 'Language: {}\n'.format(i['locale'])
        Texttr += 'Partition: {}, CSS: {}\n'.format(i['partition'], i['css'])
        Texttr += 'CSS for Redirect: {}\n'.format(i['cssredirect'])
        Texttr += 'Device Pool: {}, Location: {}\n'.format(i['dpool'], i['location'])
        Texttr += 'Display name: {},   ASCII name: {}\n'.format(i['displayname'], i['alertingNameAscii'])
        if i['phonemask']: Texttr += 'External phone number mask: {}\n'.format(i['phonemask'])
        Texttr += '\n'

if Usecase['applications']:
    Apps = GetApplications('https://{}/adminapi/application/'.format(host))
    Textapp = '\nTotal applications: {}, with no parameters: {}, errors to retrieve info: {}.\n'.format(
            len(Apps), Noparams, Errored)
    for i in Apps:
        Textapp += '\nName: {}'.format(i['name'])
        if i['state'] == 'false': Textapp += ' (disabled)'
        Textapp += '\nScript: {}'.format(i['script'])
        if Usecase['triggers']:
            for trigger in Triggers:
                if trigger['application'] == i['name']:
                    Textapp += '\nTrigger: {}'.format(trigger['dn'])
        Textapp += '\nMax sessions: {}\n'.format(i['maxsession'])
        if len(i['parameters']) == 0:
            Textapp += '  -No parameters-\n'
            Noparams += 1
        else:
            for key, value in i['parameters'].items():
                Textapp += '  {:20} {}\n'.format(key, value)
    print(Textapp)

if Usecase['alltriggers']:
    print(Texttr)

if Usecase['prompts']:
    Prompts = []
    Prompts_used = []
    Prompts_unused = []
    Textpr = '\nAll prompts:\n\n'
    Textpr_unused = ''
    GetContent('https://{}/adminapi/prompt/'.format(host), 'Prompt', Prompts)
    Prompts = sorted(Prompts, key=lambda k: k['fullpath'])
    if len(Prompts) > 0:
        for i in Prompts:
            Textpr += "{} in {}, {}, uploaded '{}' by {}\n".format(
                    i['name'], i['path'], i['size'], i['dateModified'], i['modifiedBy'])
        if Usecase['applications']:
            for i in Prompts:
                Used = 0
                for app in Apps:
                    for key, param in app['parameters'].items():
                        if i['fullpath'].split('/', 2)[-1] == param:
                            Prompts_used.append(i)
                            Used = 1
                            break
                    if Used == 1: break
                if Used == 0:
                    Prompts_unused.append(i)
        if len(Prompts_unused) > 0:
            Textpr_unused += '\nThe following {} prompts of total {} seem to be unused:\n\n'.format(
                    len(Prompts_unused), len(Prompts))
            for i in Prompts_unused:
                Textpr_unused += "{} in {}, {}, uploaded '{}' by {}\n".format(
                        i['name'], i['path'], i['size'], i['dateModified'], i['modifiedBy'])
        if Usecase['allprompts']:
            print(Textpr)
        print(Textpr_unused)
    else:
        print('No scripts were found')

if Usecase['scripts']:
    Scripts = []
    Scripts_used = []
    Scripts_unused = []
    Textsc = '\nAll scripts:\n\n'
    Textsc_unused = ''
    GetContent('https://{}/adminapi/script/'.format(host), 'Script', Scripts)
    Scripts = sorted(Scripts, key=lambda k: k['fullpath'])
    if len(Scripts) > 0:
        for i in Scripts:
            Textsc += "{} in {}, {}, last modified '{}' by {}\n".format(
                    i['name'], i['path'], i['size'], i['dateModified'], i['modifiedBy'])
        if Usecase['applications']:
            for i in Scripts:
                Used = 0
                for j in Apps:
                    if 'SCRIPT[{}]'.format(i['name']) == j['script']:
                        Scripts_used.append(i)
                        Used = 1
                        break
                if Used == 0:
                    Scripts_unused.append(i)
        if len(Scripts_unused) > 0:
            Textsc_unused += '\nThe following {} scripts of total {} seem to be unused:\n\n'.format(
                    len(Scripts_unused), len(Scripts))
            for i in Scripts_unused:
                Textsc_unused += "{} in {}, {}, uploaded '{}' by {}\n".format(
                        i['name'], i['path'], i['size'], i['dateModified'], i['modifiedBy'])
        if Usecase['allscripts']:
            print(Textsc)
        print(Textsc_unused)
    else:
        print('No scripts were found')
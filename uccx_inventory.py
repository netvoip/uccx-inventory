#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib3
import requests
import xmltodict
import argparse
import configparser
urllib3.disable_warnings()
Timestart = datetime.now()
Noparams = Errored = 0
# Limit max app count for testing purposes
Applimit = 0

def ApiRequest(url):
    # Returns API request result
    Response = requests.get((url),
        auth=(apiuser, apipassword), verify=False)
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
    Level1 = Level1['Files'][Type]

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


# Retrieve connection variables
vars = configparser.ConfigParser()
vars.read('uccx_vars.conf')
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
parser.add_argument('-noprompts', action="store_true", dest="noprompts")
parser.add_argument('-noscripts', action="store_true", dest="noscripts")
parser.add_argument('-noapps', action="store_true", dest="noapps")
args = parser.parse_args()
Usecase = {'applications': not(args.noapps), 'prompts': not(args.noprompts), 'scripts': not(args.noscripts),
           'allprompts': args.allprompts, 'allscripts': args.allscripts}

if Usecase['applications']:
    Apps = GetApplications('https://{}/adminapi/application/'.format(host))
    Text = '\nTotal applications: {}, with no parameters: {}, errors to retrieve info: {}.\n'.format(
            len(Apps), Noparams, Errored)
    for i in Apps:
        Text += '\nName: {}'.format(i['name'])
        if i['state'] == 'false': Text += ' (disabled)'
        Text += '\nScript: {}'.format(i['script'])
        Text += '\nMax sessions: {}\n'.format(i['maxsession'])
        if len(i['parameters']) == 0:
            Text += '  -No parameters-\n'
            Noparams += 1
        else:
            for key, value in i['parameters'].items():
                Text += '  {:20} {}\n'.format(key, value)
    print(Text)

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
                        if i['name'] in param:
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
                    if i['name'] in j['script']:
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
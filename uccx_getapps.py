#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib3
import requests
import xmltodict
import configparser
urllib3.disable_warnings()
Appurls = []
Appdict = []
Text = ''
Nopars = Errored = counter = 0
limit = 0

def ApiRequest(url):
    Response = requests.get((url),
        auth=(apiuser, apipassword), verify=False)
    Text = Response.text
    return Text

# Retrieve connection variables
vars = configparser.ConfigParser()
vars.read('uccx_vars.conf')
host = vars['uccx']['host']
apiuser = vars['uccx']['apiuser']
apipassword = vars['uccx']['apipassword']

# Get all applications list
Response = ApiRequest('https://{}/adminapi/application/'.format(host))
# Make list of links to every application
Appdict = xmltodict.parse(Response)
Appdict = Appdict['applications']['application']
for i in Appdict:
    Appurls.append(i['self'].replace ('+', ' '))

# Connect to every application and compile text from output
for i in Appurls:
    Item = []
    Response = ApiRequest(i)
    Item = xmltodict.parse(Response)
    if 'application' in Item: Item = Item['application']
    try:
        Text += '\nName: {}'.format(Item['applicationName'])
        if Item['enabled'] == 'false': Text += ' (disabled)'
        Text += '\nScript: {}'.format(Item['ScriptApplication']['script'])
        Text += '\nMax sessions: {}\n'.format(Item['maxsession'])
        if 'scriptParams' in Item['ScriptApplication']:
            ItemParams = Item['ScriptApplication']['scriptParams']
            if type(ItemParams) is list:
                for element in ItemParams:
                    Text += '  {:20} {}\n'.format(element['name'], element['value'])
            else:
                Text += '  {}: {}\n'.format(ItemParams['name'], ItemParams['value'])
        else:
            Text += '-No parameters-\n'
            Nopars += 1
    except:
        Text += '\nSomething went wrong\n'
        Errored += 1
    counter += 1
    if counter == limit:
        break

Text += '\n\nTotal applications: {}, no parameters: {}, errors to retrieve: {}.'.format(
        counter, Nopars, Errored)
print(Text)
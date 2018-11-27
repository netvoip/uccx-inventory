### Introduction
When you have a lot of applications in your Cisco UCCX and want to make some changes or cleanup your server from obsolete data, it might be a pain to run around all applications to be sure your actions will be safe for active services.  

This script shows you all prompt and script files that are not used by any application anymore. Also it inventories all applications parameters to plain text so you can quickly check configuration manually. Also this script can be run periodically to archive config and track changes.

_Notice!_ The parameters are displayed only if they are explicitly defined and not default values. Either set all your parameters or check which default values are used in your scripts.

### Requirements
- Python 3 with modules: urllib3, requests, xmltodict, agrparse, configparser (install it by `pip install modulename` command).

### Usage
Define your uccx hostname, api user name and password. Currently Cisco supports only admin users with full rights.  
Run script by Python interpreter.

### Sample output
```
Name: Regions
Script: SCRIPT[Filials.aef]
Max sessions: 50
  P_Hello              Filials/hello_filials.wav
  Timezone             TZ[Europe/Etc-3]
  Num_hunt             "11133"

The following 1 prompts of total 93 seem to be unused:
test_prompt.wav in /en_US/ContactCenter/, 449.58 KB, uploaded '11/28/2017 03:05:19 PM' by admin

The following 1 scripts of total 17 seem to be unused:
test_script.aef in /, 42.56 KB, uploaded '06/08/2018 03:37:14 PM' by admin
```

### P.S.
Wishes, bugreports and practical recommendations are accepted at conftdowr@gmail.com.
### Introduction
When you have a lot of applications in your Cisco UCCX and you want to make some changes of cleanup your server from obsolete data, it might be a pain to run around all applications to be sure your actions will be safe for your current infrastructure.  

This simple script inventories applications parameters into plain text so you can quickly find all used or unused data.  

_Notice!_ The parameters are displayed only if they are explicitly defined and not default values. Either set all your parameters or check which default values are used in your scripts.

### Requirements
- Python 3 with modules: urllib3, requests, xmltodict, configparser (install it by `pip install modulename` command).

### Usage
Define your uccx hostname, api user name and password. Currently Cisco supports only admin users with full rights.  
Run script by Python interpreter.


###This import needed to parse templates
from flask import render_template

###Add support for POST calls
from flask import request
from flask import Flask, redirect, url_for, request

###Base import
from flask import Flask

##import the DNAC calls
import DNAC_API

###Import for the files updates needed
import os
from datetime import date

###Helpfull needed imports
import logging
import yaml
import re
import socket
import requests
from requests.auth import HTTPBasicAuth
import json
import socket


###Allow us to reload modules
import importlib

###To convert strings to dicts.
import ast

###Sets the app up
app = Flask(__name__, template_folder='templates', static_folder='StaticFiles')


#####Use logging andremvoe print statements.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

"""

1. Have the initial homepage of the server ask for the password and cache it for that session in a variable.
1a. If you hardcore a password in yml that will be preferd

"""

#Need to set the execute in the same folder for relative paths to use
os.chdir((os.path.dirname(os.path.abspath(__file__))))



####Two needed DNAC functions

def get_dnac(node):
   ip_regex = "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
   if node == 'sandbox':
      with open('Dnac_data.yml', 'r') as file:
         node = yaml.safe_load(file)['server']['sandbox']
   elif node == 'lab':
      with open('Dnac_data.yml', 'r') as file:
         node = yaml.safe_load(file)['server']['lab']
   else:
      raise NameError(f'No server found, valid is "sandbox" or "lab"')
   #
   if not re.match(ip_regex, node['IP']):
      try:
         node['IP'] = socket.getaddrinfo(node['Host'], 443)[0][4][0]
      except:
         print('No IP and unresolvable hostname')
         raise NameError(f'No IP and unresolvable hostname')
   #
   #DNAC_DATA = [node['IP'], node['Port'], node['Username'], node['Password'], node['Host']]
   logging.info(f'DNAC Dict data {node}')
   return(node)
   #return(DNAC_DATA)


def get_token(dnac_system):
    """[summary]
    Here we call up the API to get a token
    """
    logging.info(f'Token get for {dnac_system["IP"]}:{dnac_system["Port"]}')
    url = (f'https://{dnac_system["IP"]}:{dnac_system["Port"]}/api/system/v1/auth/token')
    headers = {'content-type': 'application/json'}
    resp = requests.post(url, auth=HTTPBasicAuth(username=dnac_system['Username'], password=dnac_system['Password']), headers=headers,verify=False)
    ####Add in error to catch bad password 
    token = resp.json()['Token']
    logging.info(f'DNAC token got {token}')
    return token





####The web/flask functions
@app.route('/',methods = ['POST', 'GET'])
def index():
   logging.info('Homepage opened')
   size = 0
   datestamp = 'Missing'
   if request.method == 'GET':
      cache_owner = ['N/A']
      if len(os.listdir('cache')) != 0:
         size = sum([os.path.getsize(x) for x in os.scandir('cache')])//1024
         datestamp = str(date.fromtimestamp(os.path.getmtime('cache')))
         with open('./cache/server_name.txt', 'r') as f:
            cache_owner = f.readlines()
      return render_template('dnac_sys_data.html', data=DNAC_data, size=size, cache_timestamp=datestamp, owner=cache_owner)


@app.route('/sandbox_mode',methods = ['GET'])
def sandbox():
   logging.info('sandbox mode')
   if request.method == 'GET':
      global DNAC_data
      DNAC_data = get_dnac('sandbox')
      return redirect(url_for('index'))

@app.route('/lab_mode',methods = ['GET'])
def lab_mode():
   logging.info('lab mode')
   if request.method == 'GET':
      global DNAC_data
      DNAC_data = get_dnac('lab')
      return redirect(url_for('index'))




@app.route('/update',methods = ['POST', 'GET'])
def update_system():
   if request.method == 'POST':
      IP = request.form.get("IPAddress")
      PORT = int(request.form.get("port"))
      USER = request.form.get("Username")
      HOST = request.form.get("Hostname")
      ####Need to add a check to see if the four above varaibles have an ', if they do error messsage
      ####And re-do
      #
      with open('Dnac_data.yml', 'r') as file:
         dict_obj = yaml.safe_load(file)
      logging.info(f'DNAC Dict update from: {dict_obj}')
      dict_obj['server']['lab']['IP'] = IP
      dict_obj['server']['lab']['Host'] = HOST
      dict_obj['server']['lab']['Port'] = PORT
      dict_obj['server']['lab']['Username'] = USER
      logging.info(f'DNAC Dict update to: {dict_obj}')
      with open('Dnac_data.yml', 'w') as file:
         yaml.dump(dict_obj, file)
      return redirect(url_for('index'))
      #return index()
   if request.method == 'GET':
      DNAC_data = get_dnac('lab')
      return render_template('dnac_update.html', data=DNAC_data)


@app.route('/flush',methods = ['POST', 'GET'])
def flush_system():
   if request.method == 'POST':
      return 'This is an unuset toilet flush_system, post'
   if request.method == 'GET':
      os.chdir('cache')
      #return os.listdir()
      for file in os.listdir():
         os.remove(file)
      os.chdir("..")
      return redirect(url_for('index'))
      #return os.listdir()


@app.route('/cache',methods = ['POST', 'GET'])
def update_cache():
   if request.method == 'POST':
      ##Need a bunch of APIs to download the local needed cache
      Password = request.form.get("Password")
      DNAC_data['Password'] = (Password)
      token = get_token(DNAC_data)
      ##Get ALL devices in DNAC
      devices = DNAC_API.get_devices(DNAC_data, token, 'ALL')
      with open('./cache/get_devices.txt', 'w+') as f:
            f.write(str(devices))
      ##Get ALL interfaces as the search string is empty/any
      find_port = DNAC_API.find_port(DNAC_data, token, devices, "")
      with open('./cache/find_port.txt', 'w+') as f:
            f.write(str(find_port))
      ##GET all the SFP info on ALL nodes
      get_sfp = DNAC_API.get_sfp(DNAC_data, token, devices)
      with open('./cache/get_sfp.txt', 'w+') as f:
         for line in get_sfp:
            f.write(str(line))
      with open('./cache/server_name.txt', 'w+') as f:
         f.write(str(DNAC_data['Host']))
      return redirect(url_for('index'))
   if request.method == 'GET':
      return render_template('cache.html')


##Here we get the dnac login info to get a authC token and then search port descriptions fro strings
@app.route('/description',methods = ['POST', 'GET'])
def dnac_go_interface():
   ###Need to wirtie code for the local cahce to run...
   if request.method == 'POST':
      if len(os.listdir('cache')) != 0:
         if os.path.getsize('cache/find_port.txt') != 0:
            with open('./cache/find_port.txt','rt') as f:
                  searched_data = f.readlines()
                  searched_data = ast.literal_eval(searched_data[0])
            search = request.form.get("Search")
            return render_template('rendered_search.html', search_str=search, found_devices=searched_data)
      else:
         Password = request.form.get("Password")
         search = request.form.get("Search")
         dev_type = request.form.get("Type")
         DNAC_data['Password'] = Password
         token = get_token(DNAC_data)
         logging.info(f'Device type {dev_type}')
         devices = DNAC_API.get_devices(DNAC_data, token, dev_type)
         logging.info(f'Device results {devices}')
         searched_data = DNAC_API.find_port(DNAC_data, token, devices, search)
         return render_template('rendered_search.html', search_str=search, found_devices=searched_data)
   if request.method == 'GET':
      return render_template('description.html')



##Here we get the dnac login info to get a authC token and then get all the SFP data
@app.route('/sfp',methods = ['POST', 'GET'])
def dnac_get_sfp():
   if request.method == 'POST':
      Password = request.form.get("Password")
      logging.info(f'Password fro form {Password}')
      DNAC_data['Password'] = Password
      logging.info(f'DNAC Password set {DNAC_data["Password"]}')
      token = get_token(DNAC_data)
      devices = DNAC_API.get_devices(DNAC_data, token)
      searched_data = DNAC_API.get_sfp(DNAC_data, token, devices)
      return render_template('rendered_sfp.html', sfps=searched_data)
   if request.method == 'GET':
      ##Check to see if there is cached data and a data in the file.
      if len(os.listdir('cache')) != 0:
         if os.path.getsize('cache/get_sfp.txt') != 0:
            searched_data = []
            with open('./cache/get_sfp.txt', 'r') as f:
               for line in f:
                  searched_data.append(line)
            return render_template('rendered_sfp.html', sfps=searched_data)
         else:
            return render_template('dnac_sfp.html')
      else:
         return render_template('dnac_sfp.html')


###This function updates DNAC User Deifned Fields with SNMP location/contact data
@app.route('/udf',methods = ['POST', 'GET'])
def dnac_get_udf():
   if request.method == 'POST':
      Password = request.form.get("Password")
      dev_type = request.form.get("Type")
      DNAC_data['Password'] = Password
      token = get_token(DNAC_data)
      devices = DNAC_API.get_devices(DNAC_data, token, dev_type)
      DNAC_API.get_snmp(DNAC_data, token, devices)
      logging.info(f'DNAC Password set {DNAC_data["Password"]}')
      return redirect(url_for('index'))
   if request.method == 'GET':
      return render_template('dnac_udf.html')


###Sets up the flask server if this code is called directly
if __name__ == '__main__':
   DNAC_data = get_dnac('lab')
   app.run(host='0.0.0.0', port=81)


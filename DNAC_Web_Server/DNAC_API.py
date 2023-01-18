"""This Uses the API to get the follwing data from functions
Devices SNMP server location and contact info
SPFs within each box
finds devices based on a confiured port description
The script is Cisco Confidential information and you should keep it securely
You are granted limited license to modify and enhance the provided Source Code [script] solely for your internal use and only to the extent we expressly permit
The script comes with no warranty of any kind, which means that if there are faults/errors in the script Cisco has no obligation to provide any help to resolve them
"""

__author__ = 'sabibby'
#!/usr/bin/env python3.10

###Get the stuff we need to use
import sys
import requests
import getpass
from requests.auth import HTTPBasicAuth
import json
import logging

requests.urllib3.disable_warnings()
user_inputs = sys.argv

def get_role():
    """_summary_
    Gets the deice subset from the user to search, used ofr interface description searching
    """
    roles = {0 : 'ACCESS', 1 : 'CORE', 2 : 'DISTRIBUTION', 3 : 'BORDER ROUTER', 4 : 'ALL'}
    print("What device roles do you want to search")
    for key,role in roles.items():
        print(f"{key} : {role}")
    selection = int(input('0-4: '))
    return roles[selection]

def get_devices(dnac_system, token, role=0):
    """[summary]
    Gets the required devices
    """
    headers = {'content-type': 'application/json'}
    headers['x-auth-token'] = token
    BASE_URL = f'https://{dnac_system["IP"]}:{dnac_system["Port"]}'
    ###Get all devices
    DEVICE_URL = '/dna/intent/api/v1/network-device'
    device_data = requests.get(BASE_URL+DEVICE_URL, headers=headers, verify=False)
    device_data = device_data.json()
    if role == 0:
        devices = [i['instanceUuid'] for i in device_data['response']]
    elif role == 'ALL':
        devices = [i['instanceUuid'] for i in device_data['response']]
    else:
        devices = [i['instanceUuid'] for i in device_data['response'] if i['role'] == role]
    return devices




###This function updates DNAC User Deifned Fields with SNMP location/contact data
def get_snmp(dnac_system, token, devices):
    """[summary]
    this will glean the SNMP contact/location from each deivce, then update the UDF fields
    in DNAC with this same data.
    """
    headers = {'content-type': 'application/json'}
    headers['x-auth-token'] = token
    BASE_URL = f'https://{dnac_system["IP"]}:{dnac_system["Port"]}'
    ##Get SNMP info
    DEVICE_URL = '/dna/intent/api/v1/network-device/'
    UDF_TAG = '/user-defined-field'
    for DEVICE in devices:
        platform_data = requests.get(BASE_URL+DEVICE_URL+DEVICE, headers=headers, verify=False)
        platform_data = platform_data.json()
        logging.info(f"hostname = {platform_data['response']['hostname']}")
        logging.info(f"platformId = {platform_data['response']['platformId']}")
        logging.info(f"serialNumber = {platform_data['response']['serialNumber']}")
        logging.info(f"snmpContact = {platform_data['response']['snmpContact']}")
        logging.info(f"snmpLocation = {platform_data['response']['snmpLocation']}")
        if platform_data['response']['snmpContact'] and platform_data['response']['snmpLocation']:
            payload = [{"name":"SNMP Contact","value":platform_data['response']['snmpContact']},
                    {"name":"SNMP Location","value":platform_data['response']['snmpLocation']}]
                    #
        elif platform_data['response']['snmpContact']:
            payload = [{"name":"SNMP Contact","value":platform_data['response']['snmpContact']}]
            #
        elif platform_data['response']['snmpLocation']:
            payload = [{"name":"SNMP Location","value":platform_data['response']['snmpLocation']}]
            #
        else:
            continue
        requests.put(BASE_URL+DEVICE_URL+DEVICE+UDF_TAG,data=json.dumps(payload), headers=headers, verify=False)


def get_sfp(dnac_system, token, devices):
    """[summary]
    Gets all SFPs in use and creates a text file with swithc and SFP details
    """
    headers = {'content-type': 'application/json'}
    headers['x-auth-token'] = token
    BASE_URL = f'https://{dnac_system["IP"]}:{dnac_system["Port"]}'
    ##Get SFP info
    DEVICE_URL = '/dna/intent/api/v1/network-device/'
    URL_SUFFIX = '/equipment?type=SFP'
    SFP_data = []
    #devices = ['357afa81-a518-4866-96f2-ff82e00b1142']
    for DEVICE in devices:
        platform_data = requests.get(BASE_URL+DEVICE_URL+DEVICE, headers=headers, verify=False)
        platform_data = platform_data.json()
        sfp_data = requests.get(BASE_URL+DEVICE_URL+DEVICE+URL_SUFFIX, headers=headers, verify=False)
        sfp_data = sfp_data.json()
        if len(sfp_data['response']) > 0:
            SFP_data.append(":::::::::::::::::\n")
            SFP_data.append(f"hostname = {platform_data['response']['hostname']}\n")
            SFP_data.append(":::::::::::::::::\n")
            for sfp in sfp_data['response']:
                SFP_data.append(f"{sfp['description']}\n")
                SFP_data.append(f"{sfp['serialNumber']}\n")
                SFP_data.append("\n")
    return SFP_data

def find_port(dnac_system, token, devices, FINDME='ZZZZZZZZ'):
    """[summary]
    finds a device and interface based on port description
    """
    headers = {'content-type': 'application/json'}
    headers['x-auth-token'] = token
    BASE_URL = f'https://{dnac_system["IP"]}:{dnac_system["Port"]}'
    INTERFACE_URL = '/dna/intent/api/v1/interface/network-device/' 
    DEVICE_URL = '/dna/intent/api/v1/network-device/'
    results = {}
    index = 0
    ###deivces is a list of deivce UUIDS
    for DEVICE in devices:
        ###Get ALL the interface details as an itterable for the current device that is passed
        platform_data = requests.get(BASE_URL+INTERFACE_URL+DEVICE, headers=headers, verify=False)
        platform_data = platform_data.json()
        ###Now we itterate over eace interface to look for a match on the interface description
        for i in platform_data['response']:
            if FINDME.upper() in i['description'].upper():
                index += 1
                ###use the device UUID to pull the deivce info to report back into the results
                platform_data = requests.get(BASE_URL+DEVICE_URL+i['deviceId'], headers=headers, verify=False)
                platform_data = platform_data.json()
                current_result = {}
                current_result['hostname'] = platform_data['response']['hostname']
                current_result['managementIpAddress'] = platform_data['response']['managementIpAddress']
                current_result['PortName'] = i['portName']
                current_result['description'] = i['description']
                results[index] = current_result
    return results




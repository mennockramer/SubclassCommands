import json
import os
import platform
import requests

#This script is just to remove SubclassCommands from SS Engine. Necessary if existing events are to be modified. 
steelSeriesAddress=""
if platform.system() == "Windows":
    steelSeriesAddress = json.load(open(os.environ['PROGRAMDATA']+"/SteelSeries/SteelSeries Engine 3/coreProps.json", "r"))['address']
    requests.post("http://"+steelSeriesAddress+"/remove_game", data=json.dumps({"game": "SUBCLASSCOMMANDS"}), headers={'Content-type': 'application/json'})
if platform.system() == "Darwin":
    steelSeriesAddress = json.load(open("/Library/Application Support/SteelSeries Engine 3/coreProps.json", "r"))['address']
    requests.post("http://"+steelSeriesAddress+"/remove_game", data=json.dumps({"game": "SUBCLASSCOMMANDS"}), headers={'Content-type': 'application/json'})
if platform.system() == "Linux":
    print("SteelSeries Engine is not available for Linux, skipping.")
#!/usr/bin/env python3 
from pickle import TRUE
import sys
import requests
import webview
import time
import threading
import datetime
import json
import os
import subprocess
from subprocess import PIPE
import re
import platform


__license__ = "GPL-3.0"

__author__ = "Menno Kramer"
__email__ = "mennockramer@gmail.com"
# if you're forking this, please add yourself here (with a note about which fork), so I don't get questions that make me say "What the fork is this?"


#don't be a jerk and abuse the fact that these needed to be included.
#if you're going to make your own variant, for example based on rarity of equipped weapons, I ask that you register your own Application with Bungie, and use your own values here.
#https://www.bungie.net/en/Application <-- here's where you do that, it's surprisingly simple!
apiKey ='173e93eb88604e8a96a2e4f85d4548ed'
clientID = "37211"
clientSecret = "P1KPzCPrNatEekBHvBImxPhnkVCv-lqoCVA7VRCqNGc"
#if I used the less secure authentication option, pretty sure every API call would need user-inputted authentication. Noone wants that.

accessToken = ""
refreshToken = ""
bungieMembershipID = ""
destinyMembershipID = ""
destinyMembershipType = ""

subclassDict = {
    
    2932390016:'striker',
    2550323932:'sunbreaker',
    2842471112:'sentinel',
    613647804:'behemoth',
    0000000000:'tyrant',

    2328211300:'arcstrider',
    2240888816:'gunslinger',
    2453351420:'nightstalker',
    873720784:'revenant',
    0000000000:'threadrunner',
    
    3168997075:'stormcaller',
    3941205951:'dawnblade',
    2849050827:'voidwalker',
    3291545503:'shadebinder',
    0000000000:'architect',

}

elementDict = {
   
    2932390016:'arc',
    2550323932:'solar',
    2842471112:'void',
    613647804:'stasis',
    0000000000:'strand',

    2328211300:'arc',
    2240888816:'solar',
    2453351420:'void',
    873720784:'stasis',
    0000000000:'strand',
    
    3168997075:'arc',
    3941205951:'solar',
    2849050827:'void',
    3291545503:'stasis',
    0000000000:'strand',
    
}

accessTokenExpiry = datetime.datetime.now() #inital value as a placeholder.

subclassCheckInterval = 10 #default value, overriden by config

tokenLock = threading.Lock() 
tokenUrl = "https://www.bungie.net/Platform/App/OAuth/Token/"

#grabs the authentication code from the authenication browser window
def auth_code_watcher(window):
    while True:
        authWindowURL = window.get_current_url()
        if "https://dummypage/?code=" in authWindowURL:
            global authCode
            authCode = authWindowURL.replace("https://dummypage/?code=","")
            
            break
        else:
            time.sleep(0.5)

    window.destroy()
     
def new_authentication():
   
    #creates and starts a browser window for user input for authentication
    authWindow = webview.create_window('Bungie Authentication', 'https://www.bungie.net/en/OAuth/Authorize?client_id='+clientID+'&response_type=code')
    webview.start(func=auth_code_watcher, args=authWindow)


    accessTokenData = {'grant_type': 'authorization_code', 'code': authCode}
    accessTokenResponseRaw = requests.post(tokenUrl, data=accessTokenData , auth=(clientID, clientSecret), headers = {"X-API-Key":apiKey})
    
    accessTokenResponse = accessTokenResponseRaw.json()
    
    global accessToken, refreshToken, bungieMembershipID, accessTokenExpiry
    accessToken = accessTokenResponse['access_token']
    refreshToken = accessTokenResponse['refresh_token']
    bungieMembershipID= accessTokenResponse['membership_id']

    accessTokenExpiry = datetime.datetime.now() + datetime.timedelta(accessTokenResponse['expires_in']) 

    tokenFile = open("SubclassCommandsTokens.txt", "w")
    tokenFile.write(accessToken+"\n"+refreshToken)
    tokenFile.close()

def renew_access_token():
    with tokenLock:
        global accessToken, refreshToken, bungieMembershipID, accessTokenExpiry
        refreshTokenData = {'grant_type': 'refresh_token', 'refresh_token': refreshToken}
        refreshTokenResponseRaw = requests.post(tokenUrl, data=refreshTokenData , auth=(clientID, clientSecret), headers = {"X-API-Key":apiKey})
        refreshTokenResponse = refreshTokenResponseRaw.json()
        
        try:
            accessToken = refreshTokenResponse['access_token']
            refreshToken = refreshTokenResponse['refresh_token']
            bungieMembershipID= refreshTokenResponse['membership_id']

            accessTokenExpiry = datetime.datetime.now() + datetime.timedelta(refreshTokenResponse['expires_in']) 

            tokenFile = open("SubclassCommandsTokens.txt", "w")
            tokenFile.write(accessToken+"\n"+refreshToken)
            tokenFile.close()
        except KeyError:
            new_authentication()

def subclass_checker():
    
    responseCharactersRaw = requests.get("https://www.bungie.net/Platform/Destiny2/"+destinyMembershipType+"/Profile/"+destinyMembershipID+"/?components=Characters", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    responseCharacters = responseCharactersRaw.json()
    
    # determine most recent character
    mostRecentCharacterDatetime = datetime.datetime.fromtimestamp(0)
    mostRecentCharacter =""
    for character in responseCharacters['Response']['characters']['data']:
        if datetime.datetime.strptime(responseCharacters['Response']['characters']['data'][character]['dateLastPlayed'],'%Y-%m-%dT%H:%M:%SZ') > mostRecentCharacterDatetime:
            mostRecentCharacterDatetime = datetime.datetime.strptime(responseCharacters['Response']['characters']['data'][character]['dateLastPlayed'],'%Y-%m-%dT%H:%M:%SZ')
            mostRecentCharacter = str(character)

    
    #get character's equipment
    responseCharacterEquipmentRaw = requests.get("https://www.bungie.net/Platform/Destiny2/"+destinyMembershipType+"/Profile/"+destinyMembershipID+"/Character/"+mostRecentCharacter+"?components=CharacterEquipment", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    responseCharacterEquipment = responseCharacterEquipmentRaw.json()
    #get lock state of user's ship
    shipItemInstanceId =""
    shipLockState=0
    for item in responseCharacterEquipment['Response']['equipment']['data']['items']:
        if item['bucketHash'] == 284967655:  # InventoryBucket Ship hash = 284967655
            shipItemInstanceId = item['itemInstanceId'] 
            shipLockState = item['state']

    #set lock state of user's ship to what was just retrieved above
    shipLockPost = requests.post("https://www.bungie.net/Platform/Destiny2/Actions/Items/SetLockState/", data="{'state': "+str(shipLockState)+", 'itemId': '"+shipItemInstanceId+"', 'characterId': "+mostRecentCharacter+", 'membershipType': "+destinyMembershipType+"}", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    
    #the two above actions "bust the cache" ensuring that the equipment and therefore subclass below are up to date (most of the time, it's still janky in orbit? broken entirely?)

    #Actual subclass check
    #get character's equipment
    responseCharacterEquipmentRaw = requests.get("https://www.bungie.net/Platform/Destiny2/"+destinyMembershipType+"/Profile/"+destinyMembershipID+"/Character/"+mostRecentCharacter+"?components=CharacterEquipment", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    responseCharacterEquipment = responseCharacterEquipmentRaw.json()
    
    #find subclass among inventory
    subclassHash ="error"
    for item in responseCharacterEquipment['Response']['equipment']['data']['items']:
        if item['bucketHash'] == 3284755031:  # InventoryBucket "Subclass" hash = 328755031
            subclassHash = item['itemHash'] 
    
    #change colours via enabled RGB programs
    if config['useRGBPrograms'] == True:
        # if config['RGBPrograms']['useAura'] == True:

        #     if subclassHash == 'error':   
        #         requests.post("http://localhost:27339/AuraSDK/AuraDevice", data= {"data" : {"range" : "all", "color" : HexRGBtoBGRInt(config['colourHexes']['error']) ,"apply": "true" },})    
                
        #     else:
        #         if config['perElementNotSubclass'] == True:
        #             requests.post("http://localhost:27339/AuraSDK/AuraDevice", data= {"data" : { "range" : "all", "color" : HexRGBtoBGRInt(config['colourHexes']['elements'][elementDict[subclassHash]]),"apply": "true",}})
        #         else:
        #             requests.post("http://localhost:27339/AuraSDK/AuraDevice", data= {"data" : { "range" : "all", "color" : HexRGBtoBGRInt(config['colourHexes']['subclasses'][subclassDict[subclassHash]]),"apply": "true",}})



        if config['RGBPrograms']['useOpenRGB'] == True:
            if OpenRGBPath != "":
                if subclassHash == 'error':   
                    os.system(OpenRGBPath+" -c "+config['colourHexes']['error'])
                    
                else:
                    if config['perElementNotSubclass'] == True:
                        os.system(OpenRGBPath+" -c "+config['colourHexes']['elements'][elementDict[subclassHash]])
                    else:
                        os.system(OpenRGBPath+" -c "+config['colourHexes']['subclasses'][subclassDict[subclassHash]])

        #if config['RGBPrograms']['useRazer'] == True:
            #print("Razer support NYI")
        
        if config['RGBPrograms']['useSteelSeries'] == True:
            if steelSeriesAddress != "":
                if subclassHash == 'error':   
                    requests.post("http://"+steelSeriesAddress+"/game_event", data =json.dumps({"game": "SUBCLASSCOMMANDS", "event": 'ERROR', "data": {"value": 1}}), headers={'Content-type': 'application/json'}, verify=False)
                    
                else:
                    if config['perElementNotSubclass'] == True:
                        testRaw = requests.post("http://"+steelSeriesAddress+"/game_event", data =json.dumps({"game": "SUBCLASSCOMMANDS", "event": elementDict[subclassHash].upper(), "data": {"value": 1}}), headers={'Content-type': 'application/json'}, verify=False)
                        test = testRaw.json()
                        print(test)    
                    else:
                        requests.post("http://"+steelSeriesAddress+"/game_event", data =json.dumps({"game": "SUBCLASSCOMMANDS", "event": subclassDict[subclassHash].upper(), "data": {"value": 1}}), headers={'Content-type': 'application/json'}, verify=False)
                        


    #run corresponding command
    if config['useCommands'] == True:
        
        if config['defaultBatAndSh'] == True:
            if subclassHash == 'error':   
                os.system("error.bat")
                os.system("error.sh")
            else:      
                if config['perElementNotSubclass'] == True:
                    os.system(elementDict[subclassHash]+".bat")
                    os.system(elementDict[subclassHash]+".sh")
                else:
                    os.system(subclassDict[subclassHash]+".bat")
                    os.system(subclassDict[subclassHash]+".sh")
        else:
            if subclassHash == 'error':   
                os.system(config['commands']['error'])
                
            else:
                if config['perElementNotSubclass'] == True:
                    os.system(config['commands']['elements'][elementDict[subclassHash]])
                else:
                    os.system(config['commands']['subclasses'][subclassDict[subclassHash]])
     
    
def HexRGBtoBGRInt(hex):
    #converts Hex RGB codes (eg FF00FF) to BGR ints 
    rgbHexList = re.findall('..', hex)
    r = int(rgbHexList[0],16)
    g = int(rgbHexList[1],16)
    b = int(rgbHexList[2],16)
    bgr = r + (256*g) + (65536*b)
    return bgr

def HexRGBToRGBDict(hex):
    rgbHexList = re.findall('..', hex)
    rgbDict = {"red": int(rgbHexList[0],16), "green":int(rgbHexList[1],16), "blue":int(rgbHexList[2],16)}
    #print(rgbDict)
    return rgbDict    


### End of methods ###



### main execution flow below ###

#try to load config (if fail, create default and load that)
try:
    configFile = open("SubclassCommandsConfig.json", "r")
    config = json.load(configFile)
   

except FileNotFoundError:
    print("Config file not found, copying from default on git.")
   
    defaultConfigFileResponse = requests.get("https://raw.githubusercontent.com/mennockramer/SubclassCommands/main/SubclassCommandsConfig-DEFAULT.json")
    

    configFile = open("SubclassCommandsConfig.json", "x")
    configFile.write(defaultConfigFileResponse.text)

    configFile = open("SubclassCommandsConfig.json", "r")
    config = json.load(configFile)
    
subclassCheckInterval = config['subclassCheckInterval']

#try to load tokens from file
try:
    tokenFile = open("SubclassCommandsTokens.txt", "r")
    tokenList = tokenFile.read().splitlines()
    accessToken = tokenList[0]
    refreshToken = tokenList[1]

    renew_access_token()

except FileNotFoundError:
    tokenFile = open("SubclassCommandsTokens.txt", "x")
    print("SubclassCommandsTokens.txt not found, creating a new one")
    new_authentication()



# get destinyMembershipID for the bungieMembershipID
responseLinkedProfilesRaw = requests.get("https://www.bungie.net/Platform/Destiny2/254/Profile/"+bungieMembershipID+"/LinkedProfiles", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
responseLinkedProfiles = responseLinkedProfilesRaw.json()


# determine most recent profile
mostRecentProfileDatetime = datetime.datetime.fromtimestamp(0)
mostRecentProfile =""
for profile in responseLinkedProfiles['Response']['profiles']:
    if datetime.datetime.strptime(profile['dateLastPlayed'],'%Y-%m-%dT%H:%M:%SZ') > mostRecentProfileDatetime:
        mostRecentProfileDatetime = datetime.datetime.strptime(profile['dateLastPlayed'],'%Y-%m-%dT%H:%M:%SZ')
        mostRecentProfile = profile


destinyMembershipID = str(mostRecentProfile['membershipId'])
destinyMembershipType = str(mostRecentProfile['membershipType'])


# setup for any RGB programs that require API initialisation or so
if config['useRGBPrograms'] == True:
        print("Using RGB Programs")

        if config["RGBPrograms"]["useAura"] == True:
            # responseAuraInitRaw = requests.post("http://localhost:27339/AuraSDK", data= {"category":"SDK"})
            # responseAuraInit= responseAuraInitRaw.json()
            # if responseAuraInit["result"] != 0:
            #     print("Asus Aura SDK Initialisation failed, will not be used, Aura SDK error code: "+responseAuraInit["result"], file= sys.stderr)
            print("Aura support NYI")
            

        if config["RGBPrograms"]["useOpenRGB"] == True:
            print("Using OpenRGB")
            OpenRGBPath =""

            if platform.system() == "Windows":
                OpenRGBPathFindProcess = subprocess.Popen('powershell "Get-Process OpenRGB | Format-List Path"', shell=True, stdout=PIPE, stderr=PIPE)
                stdout, stderr = OpenRGBPathFindProcess.communicate()
                stdout = stdout.decode().strip()
                stderr = stderr.decode().strip()

                #if error from command
                if stderr != "":
                    print("Path for OpenRGB not automatically found via running task, falling back to config file specified path")
                    if config['RGBPrograms']['OpenRGBPath'] != "":
                        OpenRGBPath = config['RGBPrograms']['OpenRGBPath']
                        print("OpenRGB path found: "+OpenRGBPath)
                    else:
                        print("No OpenRGB path found automatically or in config file. OpenRGB will not be used.")
                else:
                    OpenRGBPath = stdout.strip()[7:]
                    print("OpenRGB path found: "+OpenRGBPath)
                
                
            if platform.system() == "Linux":
                OpenRGBPathFindProcess = subprocess.Popen('pwdx "$(pgrep openrgb)"', shell=True, stdout=PIPE, stderr=PIPE)
                stdout, stderr = OpenRGBPathFindProcess.communicate()
                stdout = stdout.decode().strip()
                stderr = stderr.decode().strip()

                #if error from command
                if stderr != "":
                    print("Path for OpenRGB not automatically found via running task, falling back to config file specified path")
                    if config['RGBPrograms']['OpenRGBPath'] != "":
                        OpenRGBPath = config['RGBPrograms']['OpenRGBPath']
                        print("OpenRGB path found: "+OpenRGBPath)
                    else:
                        print("No OpenRGB path found automatically or in config file. OpenRGB will not be used.")
                else:
                    OpenRGBPath = stdout.split(":")[1].strip()
                    print("OpenRGB path found: "+OpenRGBPath)



            if platform.system() == "Darwin":
                print("WARNING: This code has not be tested on MacOS. Linux code reused, raise an issue on https://github.com/mennockramer/SubclassCommands if it doesn't work/you know a better way to get a program's path.")
                OpenRGBPathFindProcess = subprocess.Popen('pwdx "$(pgrep openrgb)"', shell=True, stdout=PIPE, stderr=PIPE)
                stdout, stderr = OpenRGBPathFindProcess.communicate()
                stdout = stdout.decode().strip()
                stderr = stderr.decode().strip()

                #if error from command
                if stderr != "":
                    print("Path for OpenRGB not automatically found via running task, falling back to config file specified path")
                    if config['RGBPrograms']['OpenRGBPath'] != "":
                        OpenRGBPath = config['RGBPrograms']['OpenRGBPath']
                        print("OpenRGB path found: "+OpenRGBPath)
                    else:
                        print("No OpenRGB path found automatically or in config file. OpenRGB will not be used.")
                else:
                    OpenRGBPath = stdout.split(":")[1].strip()
                    print("OpenRGB path found: "+OpenRGBPath)
            

        if config['RGBPrograms']['useRazer'] == True:
            #razer docs outdated, init packet mustve changed
            
            # #razer chroma sdk initialisation
            # responseRazerInitRaw = requests.post("http://localhost:54235/razer/chromasdk", data= {"title": "SubclassCommands", "description": "Changing RGB to match Destiny Subclass","author": {"name": "Menno Kramer","contact": "mennockramer@gmail.com"},"device_supported": ["keyboard","mouse","headset","mousepad", "keypad", "chromalink"], "category": "application" })
            # responseRazerInit = responseRazerInitRaw.json()
            # print("Razer Init: "+responseRazerInit)
            # if responseRazerInit["result"] == 0: #incorrect, need to catch if it exists
            #     print("Razer Chroma SDK Initialisation failed, will not be used, Razer error code: "+responseRazerInit["result"], file=sys.stderr)

            # #testing, comment out later
            # requests.put(responseRazerInit["uri"+"/headset"], {"effect": "CHROMA_STATIC", "param": { "color": 255 },})
            print("Razer support NYI")
            
        
        if config['RGBPrograms']['useSteelSeries'] == True:
            print("Using Steelseries Engine")
            
            steelSeriesAddress=""
            if platform.system() == "Windows":
                steelSeriesAddress = json.load(open(os.environ['PROGRAMDATA']+"/SteelSeries/SteelSeries Engine 3/coreProps.json", "r"))['address']
            if platform.system() == "Darwin":
                steelSeriesAddress = json.load(open("/Library/Application Support/SteelSeries Engine 3/coreProps.json", "r"))['address']
            if platform.system() == "Linux":
                print("SteelSeries Engine is not available for Linux, skipping.")

            if steelSeriesAddress != "":
                  
                print("Posting metadata to SteelSeries Engine for user-friendliness")
                requests.post("http://"+steelSeriesAddress+"/game_metadata", data=json.dumps({ "game":"SUBCLASSCOMMANDS", "game_display_name": "SubclassCommands for Destiny 2", "developer": "Menno Kramer", 'deinitialize_timer_length_ms': 60000}), headers={'Content-type': 'application/json'})
                
                print("Setting up Game Events with SteelSeries Engine")
                #feel free to customise the below event bindings with device zones and/or more advanced effects as per the GameSense API docs at https://github.com/SteelSeries/gamesense-sdk/blob/master/doc/api/json-handlers-color.md
                #note that changes to this will not update the events in SS Engine until the event/"game" has be removed and readded. Use SubclassCommandsSteelSeriesRemove.py to remove SC from SSE, and then run SubclassCommands as normal
                #this code does do the same devices+zones for all elements/subclasses, can be modified do to each separately (replacing the element/subclass variable with string literals eg 'arc'). 
                #note that this only sets default colours for events, which can be overridden in SSE
                
                #per element
                for element in elementDict.values():
                    requests.post("http://"+steelSeriesAddress+"/bind_game_event", data=json.dumps({"game": "SUBCLASSCOMMANDS","event": element.upper(), "max_value":1, "handlers":[
                        { "device-type": "rgb-1-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-2-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-3-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-5-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-8-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-12-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-17-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-24-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-103-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        { "device-type": "rgb-per-key-zones", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['elements'][element]),"mode": "color" },
                        ], "value_optional": True  }), headers={'Content-type': 'application/json'} , verify=False)
                    
                #per subclass
                for subclass in subclassDict.values():
                    requests.post("http://"+steelSeriesAddress+"/bind_game_event", data=json.dumps({"game": "SUBCLASSCOMMANDS","event": subclass.upper(), "max_value":1, "handlers":[
                        { "device-type": "rgb-1-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-2-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-3-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-5-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-8-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-12-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-17-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-24-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-103-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        { "device-type": "rgb-per-key-zones", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['subclasses'][subclass]),"mode": "color" },
                        ], "value_optional": True }), headers={'Content-type': 'application/json'} , verify=False)

                #error case
                requests.post("http://"+steelSeriesAddress+"/bind_game_event", data=json.dumps({"game": "SUBCLASSCOMMANDS","event": 'ERROR', "max_value":1, "handlers":[
                        { "device-type": "rgb-1-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-2-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-3-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-5-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-8-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-12-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-17-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-24-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-103-zone", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        { "device-type": "rgb-per-key-zones", "zone": "all","color": HexRGBToRGBDict(config['colourHexes']['error']),"mode": "color" },
                        ], "value_optional": True  }), headers={'Content-type': 'application/json'} , verify=False)
                    
                
## main loop ##
while True:
    if datetime.datetime.now() > accessTokenExpiry:
        renew_access_token()

    if config['onlyWhileDestinyRunning']:        
        if "destiny2.exe" in str(subprocess.check_output('tasklist', shell=True)):
            subclass_checker()  
        else:
            print("destiny2.exe not running.")
    else:
        subclass_checker()
    
    
    time.sleep(subclassCheckInterval)



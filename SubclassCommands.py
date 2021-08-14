import requests
import webview
import time
import threading
import datetime
import json
import os
import subprocess

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
    
    2958378809:'striker',
    3105935002:'sunbreaker',
    3382391785:'sentinel',
    613647804:'behemoth',

    1334959255:'arcstrider',
    3635991036:'gunslinger',
    3225959819:'nightstalker',
    873720784:'revenant',
    
    1751782730:'stormcaller',
    3481861797:'dawnblade',
    3887892656:'voidwalker',
    3291545503:'shadebinder',

}

elementDict = {
   
    2958378809:'arc',
    3105935002:'solar',
    3382391785:'void',
    613647804:'stasis',

    1334959255:'arc',
    3635991036:'solar',
    3225959819:'void',
    873720784:'stasis',
    
    1751782730:'arc',
    3481861797:'solar',
    3887892656:'void',
    3291545503:'stasis',
    
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
    
    #the two above actions "bust the cache" ensuring that the equipment and therefore subclass below are up to date

    #Actual subclass check
    #get character's equipment
    responseCharacterEquipmentRaw = requests.get("https://www.bungie.net/Platform/Destiny2/"+destinyMembershipType+"/Profile/"+destinyMembershipID+"/Character/"+mostRecentCharacter+"?components=CharacterEquipment", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    responseCharacterEquipment = responseCharacterEquipmentRaw.json()
    
    #find subclass among inventory
    subclassHash =""
    for item in responseCharacterEquipment['Response']['equipment']['data']['items']:
        if item['bucketHash'] == 3284755031:  # InventoryBucket "Subclass" hash = 328755031
            subclassHash = item['itemHash'] 
    
    
    #run corresponding command
    if config['defaultBatAndSh'] == True:
        if config['perElementNotSubclass'] == True:
            os.system(elementDict[subclassHash]+".bat")
            os.system(elementDict[subclassHash]+".sh")
        else:
            os.system(subclassDict[subclassHash]+".bat")
            os.system(subclassDict[subclassHash]+".sh")
    else:
        if config['perElementNotSubclass'] == True:
            os.system(config['commands']['elements'][elementDict[subclassHash]])
        else:
            os.system(config['commands']['subclasses'][subclassDict[subclassHash]])
    
    


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



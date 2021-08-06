import requests
import webview
import time
import threading
import concurrent.futures
import multiprocessing
import datetime

#Application API keys go here, remove for GitHub


accessToken = ""
refreshToken = ""
bungieMembershipID = ""
destinyMembershipID = ""
destinyMembershipType = ""

accessTokenExpiry = datetime.datetime.now()

subclassCheckInterval = 10

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
    
    responseCharacterEquipmentRaw = requests.get("https://www.bungie.net/Platform/Destiny2/"+destinyMembershipType+"/Profile/"+destinyMembershipID+"/?components=CharacterEquipment", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    responseCharacterEquipment = responseCharacterEquipmentRaw.json()
    #print(responseCharacterEquipment)

    responseCharactersRaw = requests.get("https://www.bungie.net/Platform/Destiny2/"+destinyMembershipType+"/Profile/"+destinyMembershipID+"/?components=Characters", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    responseCharacters = responseCharactersRaw.json()
    #print(responseCharacters['Response']['characters']['data'])

    # determine most recent character
    mostRecentCharacterDatetime = datetime.datetime.fromtimestamp(0)
    mostRecentCharacter =""
    for character in responseCharacters['Response']['characters']['data']:
        if datetime.datetime.strptime(responseCharacters['Response']['characters']['data'][character]['dateLastPlayed'],'%Y-%m-%dT%H:%M:%SZ') > mostRecentCharacterDatetime:
            mostRecentCharacterDatetime = datetime.datetime.strptime(responseCharacters['Response']['characters']['data'][character]['dateLastPlayed'],'%Y-%m-%dT%H:%M:%SZ')
            mostRecentCharacter = character

    print(mostRecentCharacter)


#try to load tokens from file
try:
    tokenFile = open("SubclassCommandsTokens.txt", "r")
    tokenList = tokenFile.read().splitlines()
    accessToken = tokenList[0]
    refreshToken = tokenList[1]

    #print("Stored Access Token: "+accessToken)
    #print("Stored Refresh Token: "+refreshToken)
    renew_access_token()
except FileNotFoundError:
    tokenFile = open("SubclassCommandsTokens.txt", "x")
    print("SubclassCommandsTokens.txt not found, creating a new one")
    new_authentication()

#print("Continuing with AT: "+accessToken)
#print("Continuing with RT: "+refreshToken)

# get destinyMembershipID for the bungieMembershipID
responseLinkedProfilesRaw = requests.get("https://www.bungie.net/Platform/Destiny2/3/Profile/"+bungieMembershipID+"/LinkedProfiles/?=getAllMemberships", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
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


# while true
# if AT expired, refresh
# check subclass
# sleep

while True:
    if datetime.datetime.now() > accessTokenExpiry:
        renew_access_token()

    subclass_checker()
    time.sleep(subclassCheckInterval)



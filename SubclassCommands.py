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
membershipID=""

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
    
    global accessToken, refreshToken, membershipID, accessTokenExpiry
    accessToken = accessTokenResponse['access_token']
    refreshToken = accessTokenResponse['refresh_token']
    membershipID= accessTokenResponse['membership_id']

    accessTokenExpiry = datetime.datetime.now() + datetime.timedelta(accessTokenResponse['expires_in']) 

    tokenFile = open("SubclassCommandsTokens.txt", "w")
    tokenFile.write(accessToken+"\n"+refreshToken)
    tokenFile.close()




def renew_access_token():
    with tokenLock:
        global accessToken, refreshToken, membershipID, accessTokenExpiry
        refreshTokenData = {'grant_type': 'refresh_token', 'refresh_token': refreshToken}
        refreshTokenResponseRaw = requests.post(tokenUrl, data=refreshTokenData , auth=(clientID, clientSecret), headers = {"X-API-Key":apiKey})
        refreshTokenResponse = refreshTokenResponseRaw.json()
        
        try:
            accessToken = refreshTokenResponse['access_token']
            refreshToken = refreshTokenResponse['refresh_token']
            membershipID= refreshTokenResponse['membership_id']

            accessTokenExpiry = datetime.datetime.now() + datetime.timedelta(refreshTokenResponse['expires_in']) 

            tokenFile = open("SubclassCommandsTokens.txt", "w")
            tokenFile.write(accessToken+"\n"+refreshToken)
            tokenFile.close()
        except KeyError:
            new_authentication()


def subclass_checker():
    #api call
    subclassResponseRaw = requests.get("https://www.bungie.net/Platform/Destiny2/3/Profile/###MEMBERSHIPID###/?components=CharacterEquipment", headers = {"X-API-Key":apiKey,"Authorization": "Bearer "+accessToken})
    subclassResponse = subclassResponseRaw.json()
    print(subclassResponse)




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


# while true
# if AT expired, refresh
# check subclass
# sleep

while True:
    if datetime.datetime.now() > accessTokenExpiry:
        renew_access_token()

    subclass_checker()
    time.sleep(subclassCheckInterval)



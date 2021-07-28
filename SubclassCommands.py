import requests
import webview
import time
import threading
import concurrent.futures

#Application API keys go here, remove for GitHub
apiKey ='173e93eb88604e8a96a2e4f85d4548ed'
clientID = "37211"
clientSecret = "P1KPzCPrNatEekBHvBImxPhnkVCv-lqoCVA7VRCqNGc"

accessToken = ""
refreshToken = ""
membershipID=""

HEADERS = {"X-API-Key":apiKey}

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
    accessTokenResponseRaw = requests.post(tokenUrl, data=accessTokenData , auth=(clientID, clientSecret))
    
    accessTokenResponse = accessTokenResponseRaw.json()
    
    global accessToken, refreshToken, membershipID
    accessToken = accessTokenResponse['access_token']
    refreshToken = accessTokenResponse['refresh_token']
    membershipID= accessTokenResponse['membership_id']

def access_token_timer():
    while True:
        time.sleep(3500)
        renew_access_token()


def renew_access_token():

    global accessToken, refreshToken, membershipID
    refreshTokenData = {'grant_type': 'refresh_token', 'refresh_token': refreshToken}
    refreshTokenResponseRaw = requests.post(tokenUrl, data=refreshTokenData , auth=(clientID, clientSecret))
    refreshTokenResponse = refreshTokenResponseRaw.json()
    
    accessToken = refreshTokenResponse['access_token']
    refreshToken = refreshTokenResponse['refresh_token']
    membershipID= refreshTokenResponse['membership_id']


#attempt to read tokens from file, if fail, new_authentication()

#if 
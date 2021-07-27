import requests
import webview
import time
import threading
import concurrent.futures

#Application API keys go here, remove for GitHub


HEADERS = {"X-API-Key":apiKey}
#authCode=""

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
   
    


#creates and starts a browser window for user input for authentication
authWindow = webview.create_window('Bungie Authentication', 'https://www.bungie.net/en/OAuth/Authorize?client_id='&clientID&'&response_type=code')
webview.start(func=auth_code_watcher, args=authWindow)

tokenUrl = "https://www.bungie.net/Platform/App/OAuth/Token/"
accessTokenData = {'grant_type': 'authorization_code', 'code': authCode}
accessTokenResponse = requests.post(tokenUrl, data=accessTokenData , auth=(clientID, clientSecret))
#Content-Type: application/x-www-form-urlencoded
print(accessTokenResponse.text)

refreshTokenData = {'grant_type': 'refresh_token', 'refresh_token': authCode}




#POST https://www.bungie.net/Platform/App/OAuth/Token/ HTTP/1.1
#Authorization: Basic {base64encoded(client-id:client-secret)}
#Content-Type: application/x-www-form-urlencoded

#grant_type=refresh_token&refresh_token={refresh-token}
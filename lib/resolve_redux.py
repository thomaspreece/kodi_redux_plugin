import requests
from datetime import timedelta, date
from dateutil import parser

import xbmcplugin
import xbmcgui
import xbmcaddon

from lib.xbmc_util import get_user_dir

import sys
import os

__profile__ = get_user_dir()

def resolve_episode_ref(redux_token, show_json, season_num, episode_num):
    episode_json = show_json["season"][season_num]["episode"][episode_num]
    broadcast_time = parser.parse(episode_json["start"])
    minute_dela = timedelta(minutes=1)

    searchParams = {'token': redux_token,
                    'q': show_json["title"],
                    'titleonly': 1,
                    'before': (broadcast_time + minute_dela).isoformat(),
                    'after': (broadcast_time - minute_dela).isoformat(),
                    'limit': 50}
    print(searchParams)
    searchApiUrl = "https://i.bbcredux.com/asset/search"
    searchResponse = requests.get(searchApiUrl, params=searchParams, stream=False)
    print(searchResponse.url)
    if searchResponse.status_code == 200:
        searchJson = searchResponse.json()
        if ("results" in searchJson and "assets" in searchJson["results"]):
            if len(searchJson['results']['assets']) > 0:
                print(searchJson['results']['assets'])
                for i in range(len(searchJson['results']['assets'])):
                    channel_name = searchJson['results']['assets'][i]["channel"]["name"]
                    if(channel_name == "bbcone" or channel_name == "bbctwo" or channel_name == "bbcthree" or channel_name == "bbcfour"):
                        return [0,searchJson['results']['assets'][i]["reference"]]
                return [1,searchJson['results']['assets'][0]["reference"]]
            else:
                print("assets empty")
                return [-1,None]
        else:
            print("results/assets not returned")
            print(searchJson)
            return [-3,None]
        # self.reduxAssets = [asset for asset in searchJson['results']['assets'] if asset['name'].lower() == self.masterTitle.lower()]
        # for asset in self.reduxAssets:
        #     startDate = dateParse(asset['timing']['start'])
        #     asset['timing']['startDatenum'] = startDate.toordinal()
    else:
        print('redux search failed')
        return [-2,None]

def resolve_episode_url(redux_token, disk_ref):
    getAssetKeyUrl = 'https://i.bbcredux.com/asset/details'
    getAssetKeyParams = {'reference': disk_ref,
                         'token': redux_token,
                         "transcode": [
                            "h264_mp4_hi_v1.0",
                            "h264_mp4_lo_v1.0",
                            "h264_mp4_hi_v1.1",
                            "h264_mp4_lo_v1.1"
                         ]}

    assetKeyResponse = requests.get(getAssetKeyUrl,
                                    params=getAssetKeyParams)
    # if OK response
    if (assetKeyResponse.status_code == 200):
        assetKeyResponseJson = assetKeyResponse.json()
        assetTranscodes = assetKeyResponseJson['transcodes']
        assetKey = assetKeyResponseJson['key']

        assetUrls = {}
        # if(assetTranscodes["h264_mp4_lo_v1.3"]["generated"] == 1):
        #     assetUrls["h264_mp4_lo"] = assetTranscodes["h264_mp4_lo_v1.3"]["uri"]
        # elif(assetTranscodes["h264_mp4_lo_v1.2"]["generated"] == 1):
        #     assetUrls["h264_mp4_lo"] = assetTranscodes["h264_mp4_lo_v1.2"]["uri"]
        if(assetTranscodes["h264_mp4_lo_v1.1"]["generated"] == 1):
            assetUrls["h264_mp4_lo"] = assetTranscodes["h264_mp4_lo_v1.1"]["uri"]
        elif(assetTranscodes["h264_mp4_lo_v1.0"]["generated"] == 1):
            assetUrls["h264_mp4_lo"] = assetTranscodes["h264_mp4_lo_v1.0"]["uri"]

        # if(assetTranscodes["h264_mp4_hi_v1.3"]["generated"] == 1):
        #     assetUrls["h264_mp4_hi"] = assetTranscodes["h264_mp4_hi_v1.3"]["uri"]
        # elif(assetTranscodes["h264_mp4_hi_v1.2"]["generated"] == 1):
        #     assetUrls["h264_mp4_hi"] = assetTranscodes["h264_mp4_hi_v1.2"]["uri"]
        if(assetTranscodes["h264_mp4_hi_v1.1"]["generated"] == 1):
            assetUrls["h264_mp4_hi"] = assetTranscodes["h264_mp4_hi_v1.1"]["uri"]
        elif(assetTranscodes["h264_mp4_hi_v1.0"]["generated"] == 1):
            assetUrls["h264_mp4_hi"] = assetTranscodes["h264_mp4_hi_v1.0"]["uri"]

        assetUrls["ts"] = 'https://i.bbcredux.com/asset/media'\
                        + '/' + str(disk_ref) \
                        + '/' + assetKey \
                        + '/ts/media.ts'

        return assetUrls
    else:
        print('No asset url found for disk ref: ' + disk_ref)
        return None


class ReduxAccount():
    def __init__(self, loginfile):
        self.username = xbmcaddon.Addon('plugin.video.redux').getSetting("username")
        self.password = xbmcaddon.Addon('plugin.video.redux').getSetting("password")
        self.token = ''
        self.loginfile = loginfile
        self.getReduxLogin()
        if(self.username == "" or self.password == ""):
            self.token = ""
            xbmcgui.Dialog().ok("Redux Credentials Invalid", "Please enter username and password", "in plugin settings")

    def getToken(self):
        return self.token

    def checkAndGetToken(self):
        if self.checkToken():
            return self.token
        else:
            self.getTokenFromDetails()
            return self.token

    def getReduxLogin(self):
        if(os.path.isfile(self.loginfile)):
            with open(self.loginfile, 'rt') as fID:
                self.token = fID.readline().split('\n')[0]
        else:
            self.token = ''

    def writeReduxLogin(self):
        with open(self.loginfile, 'wt') as fID:
            fID.write(self.token + '\n')

    def getTokenFromDetails(self):
        reduxLoginDetails = {'username': self.username, 'password': self.password}
        reduxLoginResponse = requests.get("https://i.bbcredux.com/user/login", params=reduxLoginDetails, stream=False)
        reduxDown = False
        wrongPassword = False
        loginSuccess = False

        # check redux status code
        if reduxLoginResponse.status_code == 403:
            wrongPassword = True
        elif reduxLoginResponse.status_code >= 500:
            reduxDown = True
        else:
            try:
                reduxLoginJson = reduxLoginResponse.json()
                self.token = reduxLoginJson['token']
                loginSuccess = True
                self.writeReduxLogin()
            except:
                pass

        if not loginSuccess:
            if wrongPassword:
                self.token = ""
                xbmcgui.Dialog().ok("Redux Credentials Invalid", "Please enter username and password", "in plugin settings")

            elif reduxDown:
                self.token = ""
                xbmcgui.Dialog().ok("Redux Down", "Please try again later")

            else:
                self.token = ""
                xbmcgui.Dialog().ok("Unknown Redux Error", "Unknown error occured")

    def checkToken(self):
        validLogin = False
        reduxTokenDetails = {'token': self.token}
        tokenCheckResponse = requests.get("https://i.bbcredux.com/user/details", params=reduxTokenDetails, stream=False)
        try:
            validReduxToken = (200 <= tokenCheckResponse.status_code < 300)
            validLogin = validReduxToken
        except:
            pass

        return validLogin

# end ReduxAccount

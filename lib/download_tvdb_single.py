import util
import requests
import math
from time import sleep

from pytvdbapi import api
import json

try:
    xbmc_libraries_loaded = True
    import xbmcaddon
except:
    xbmc_libraries_loaded = False

import datetime

CALLS = 60
CALLTIME = 30
# Change number of threads to match number of requests per second

def download_files(download_list):
    if(xbmc_libraries_loaded):
        api_key = xbmcaddon.Addon('plugin.video.redux').getSetting("tvdb_api_key")
    else:
        api_key = util.getManualSetting("tvdb_api_key")

    db = api.TVDB(api_key)
    start_time = util.get_millisecs()
    CallsMade=0
    for item in download_list:
        [search,output_file,complete_message] = item
        while(True):
            end_time = util.get_millisecs()
            CallsAllowed = (float(end_time - start_time)/(CALLTIME*1000))*CALLS
            if CallsMade > CallsAllowed:
                sleep(0.01)
                continue
            if CallsMade > 2*CALLS:
                CallsMade -= CALLS
                start_time -= (CALLTIME*1000)

            try:
                search_result = db.search(search, "en")

                show = None
                if(len(search_result) > 0):
                    for i in range(len(search_result)):
                        tvdb_show = search_result[i]

                        a = util.cleanString(util.checkStr(tvdb_show.SeriesName))
                        b = util.cleanString(util.checkStr(search))
                        if(a == b):
                            show = tvdb_show
                            break

                if (len(search_result) > 0) and show != None:
                    show.update()

                    show_json = {}
                    for key in dir(show):
                        key_value = getattr(show,key)
                        show_json[key] = key_value
                    show_json["api"] = None

                    for key in show_json:
                        if(type(show_json[key]) == datetime.datetime or type(show_json[key]) == datetime.date ):
                            show_json[key] = show_json[key].strftime("%y-%m-%d")

                    output_file_handle = open(output_file, 'w')
                    json.dump(show_json,output_file_handle)
                    output_file_handle.close()
                    print("Results Found & Saved")
                else:
                    show_json = {}
                    output_file_handle = open(output_file, 'w')
                    json.dump(show_json,output_file_handle)
                    output_file_handle.close()
                    print("Search Empty/ No Valid Results")
                CallsMade += 1
            except Exception as e:
                #Server Returned an Error Code
                print("Search Error, Skipping...")
                print(str(e))
                print(str(search))
                sleep(1)
                break
            break
        print("{0}".format(complete_message))

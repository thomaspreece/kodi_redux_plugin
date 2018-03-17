import util
import requests
import math
from time import sleep

from tmdb3 import set_key, set_locale, searchMovie
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
        api_key = xbmcaddon.Addon('plugin.video.redux').getSetting("moviedb_api_key")
    else:
        api_key = util.getManualSetting("moviedb_api_key")

    set_key(api_key)
    set_locale('en', 'gb')
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
                search_result = searchMovie(search, adult=True)

                show = None
                if(len(search_result) > 0):
                    for i in range(len(search_result)):
                        moviedb_show = search_result[i]

                        a = util.cleanString(util.checkStr(moviedb_show.title))
                        b = util.cleanString(util.checkStr(search))
                        if(a == b):
                            show = moviedb_show
                            break

                if (len(search_result) > 0) and show != None:

                    show_json = {}
                    show_json["id"] = show.id
                    show_json["title"] = show.title
                    if(show.backdrop):
                        show_json["backdrop"] = show.backdrop.geturl()
                    if(show.poster):
                        show_json["poster"] = show.poster.geturl()
                    show_json["cast"] = []
                    if(show.cast):
                        for i in range(len(show.cast)):
                            show_json["cast"].append(show.cast[i].name)

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

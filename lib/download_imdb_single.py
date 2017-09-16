import util
import requests
import math
from time import sleep

from imdbpie import Imdb
import json

import datetime

CALLS = 60
CALLTIME = 30
# Change number of threads to match number of requests per second

def download_files(download_list):
    imdb = Imdb()
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
                search_result = imdb.search_for_title(strip_non_ascii(search))

                show = None
                if(len(search_result) > 0):
                    for i in range(len(search_result)):
                        imdb_show = search_result[i]

                        a = util.cleanString(util.checkStr(imdb_show["title"]))
                        b = util.cleanString(util.checkStr(search))
                        if(a == b):
                            show = imdb.get_title_by_id(imdb_show["imdb_id"])
                            break

                if (len(search_result) > 0) and show != None:

                    show_json = convertToJson(show)

                    for i in range(len(show_json["writers_summary"])):
                        show_json["writers_summary"][i] = convertToJson(show_json["writers_summary"][i])
                    for i in range(len(show_json["directors_summary"])):
                        show_json["directors_summary"][i] = convertToJson(show_json["directors_summary"][i])
                    for i in range(len(show_json["cast_summary"])):
                        show_json["cast_summary"][i] = convertToJson(show_json["cast_summary"][i])
                    for i in range(len(show_json["credits"])):
                        show_json["credits"][i] = convertToJson(show_json["credits"][i])
                    for i in range(len(show_json["creators"])):
                        show_json["creators"][i] = convertToJson(show_json["creators"][i])

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
                print(util.checkStr(search))
                sleep(1)
                break
            break
        print("{0}".format(complete_message))

def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

def convertToJson(show):
    show_json = {}
    for key in dir(show):
        key_value = getattr(show,key)
        if key[0] != "_":
            show_json[key] = key_value
    return show_json

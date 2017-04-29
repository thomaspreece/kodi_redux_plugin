import util
import urllib2
from multiprocessing import Queue, Pool
import math
from time import sleep
from Queue import Empty
from pytvdbapi import api
import json
try:
   import cPickle as pickle
except:
   import pickle

from datetime import date, datetime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

CALLS = 60
CALLTIME = 60
# Change number of threads to match number of requests per second
THREADS = 2

tvdb_download_queue = Queue()

def get_tvdb_files_thread(data):
    db = api.TVDB("D7924BA9B9E92F65")
    thread_number = data[0]
    print("Starting: {0}".format(thread_number))
    try:
        start_time = util.get_millisecs()

        CallsMade=0
        while(True):
            try:
                [search,output_file,complete_message] = tvdb_download_queue.get(True,5)
            except:
                print("Thread {0}: Cound Not Find Any More Output. Exiting...".format(thread_number))
                return

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
                            if(type(show_json[key]) == datetime or type(show_json[key]) == date ):
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
                    print("Search Error, Sleeping...")
                    print(str(e))
                    print(str(search))
                    sleep(3)
                    continue
                break
            print("{0}: {1}".format(thread_number,complete_message))
    except KeyboardInterrupt:
        print("{0}: Closing Process".format(thread_number))

def download_tvdb_files(download_list):
    for item in download_list:
        tvdb_download_queue.put(item)
    if(tvdb_download_queue.qsize() != 0):
        download_pool = Pool(THREADS)
        zero_counter = 0
        minimum_requests = math.floor((CALLS/CALLTIME)*THREADS)
        try:
            download_pool.map_async(get_tvdb_files_thread, [(x, ) for x in range(1,THREADS+1)])
            while(True):
                old_size = tvdb_download_queue.qsize()
                sleep(1)
                new_size = tvdb_download_queue.qsize()

                # A curious bug of the urllib library hanging after a while results
                # in the requests per second dropping to zero.
                # This below code resets all the threads if the requests drop below
                # the average request rate for 5 consecutive seconds
                if(old_size-new_size < minimum_requests and new_size != 0):
                    zero_counter += 1
                else:
                    zero_counter = 0

                if(zero_counter > 5):
                    print("Request amount dropped, threads must be hung, restarting threads.")
                    download_pool.terminate()
                    download_pool = Pool(THREADS)
                    download_pool.map_async(get_tvdb_files_thread, [(x, ) for x in range(1,THREADS+1)])
                if(new_size == 0):
                    sleep(3)
                    download_pool.terminate()
                    download_pool.join()
                    break
                print(bcolors.WARNING+ "{0} requests per second ({1} left)".format(old_size-new_size,new_size)+ bcolors.ENDC)
        except KeyboardInterrupt:
            # **** THIS PART NEVER EXECUTES. ****
            download_pool.close()
            download_pool.terminate()
            download_pool.join()
            print("You cancelled the program!")
        else:
            download_pool.close()
            download_pool.join()

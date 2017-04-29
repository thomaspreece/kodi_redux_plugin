import util
import requests
import math
from time import sleep

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
CALLTIME = 30
# Change number of threads to match number of requests per second

def download_files(download_list):
    start_time = util.get_millisecs()
    CallsMade=0
    for item in download_list:
        [url,output_file,complete_message] = item
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
                response = requests.get(url, timeout=3)
                #response = urllib2.urlopen(url,None,5)
                #json = response.read()
                json = response.content
                #response.close()

                output_file_handle = open(output_file, 'w')
                output_file_handle.write(json)
                output_file_handle.close()

                CallsMade += 1
            except:
                #Server Returned an Error Code
                print("Connection Timeout Error, Sleeping...")
                sleep(3)
                continue
            break
        print("{0}".format(complete_message))

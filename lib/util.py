import os
import time
import errno
from datetime import timedelta
import re

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def get_millisecs():
    return int(round(time.time() * 1000))

def cleanString(s):
    s = s.lower()
    s = s.replace("&","and")
    s = re.sub("[^a-zA-Z0-9 ]","",s)
    return re.sub("  "," ",s)

def checkStr(s):
    if(s == None):
        return None
    else:
        return unicode(s)

def emptyStr(s):
    if(s == None):
        return True
    elif(unicode(s) == ""):
        return True
    elif(unicode(s) == " "):
        return True
    else:
        return False

def convert_format(vidformat):
    if(vidformat == "Original stream"):
        return "ts"
    elif(vidformat == "H264 large"):
        return "h264_mp4_hi"
    elif(vidformat == "H264 small"):
        return "h264_mp4_lo"
    else:
        print("Invalid Format!")
        xbmcgui.Dialog().ok('Converting Format Setting', "The Setting {0} is invalid".format(vidformat))
        return ""

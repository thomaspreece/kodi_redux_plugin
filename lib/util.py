import os
import time
import errno
from datetime import timedelta
import json
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

def validBBCPid(str):
    # n3ct712k
    if len(str) == 8 and str[0].isalpha():
        return True
    return False

def cleanString(s):
    s = s.lower()
    s = s.replace("&","and")
    s = re.sub("[^a-zA-Z0-9 ]","",s)
    return re.sub("  "," ",s)

def removeInvalidFilesystemChars(s):
    retS = s
    retS = re.sub("[^a-zA-Z0-9 -'&]","",retS)
    retS = re.sub("  "," ",retS)
    return retS

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

def getManualSetting(settingName):
    filename = 'Settings-NonKodi.json'
    try:
        with open(filename) as data_file:
            data = json.load(data_file)
            return data[settingName]
    except Exception as e:
        print(e)
        raise ValueError("Could not open or find {0} or {1} key within it".format(filename,settingName))

def get_manual_db_data():
    db_format = getManualSetting("db_format")
    db_data = {
        "db_format": db_format,
        "data": {}
    }

    if(db_format == "mysql"):
        db_data["data"]["host"] = getManualSetting("mysql_hostname")
        db_data["data"]["port"] = getManualSetting("mysql_port")
        db_data["data"]["username"] = getManualSetting("mysql_username")
        db_data["data"]["password"] = getManualSetting("mysql_password")
        db_data["data"]["db"] = getManualSetting("mysql_db")
    elif(db_format == "sqlite"):
        use_custom_db_path = getManualSetting("sqlite_use_db_folder")
        if(use_custom_db_path == "true"):
            database_folder = getManualSetting("sqlite_db_folder")
            if(database_folder.endswith("\\") or database_folder.endswith("/")):
                pass
            else:
                database_folder = database_folder+"/"
            database_path = "{0}shows.db".format(database_folder)
        else:
            raise ValueError("use_custom_db_path=False not supported")

        db_data["data"]["path"] = database_path
    else:
        raise ValueError("Invalid database provider (show)")

    user_db_format = getManualSetting("user_db_format")
    user_db_data = {
        "db_format": db_format,
        "data": {}
    }
    use_same_db = getManualSetting("user_use_same_db")
    if(use_same_db == "true"):
        user_db_data = db_data
        user_db_format = db_format
    else:
        if(user_db_format == "mysql"):
            user_db_data["data"]["host"] = getManualSetting("user_mysql_hostname")
            user_db_data["data"]["port"] = getManualSetting("user_mysql_port")
            user_db_data["data"]["username"] = getManualSetting("user_mysql_username")
            user_db_data["data"]["password"] = getManualSetting("user_mysql_password")
            user_db_data["data"]["db"] = getManualSetting("user_mysql_db")
        elif(user_db_format == "sqlite"):
            user_database_folder = getManualSetting("user_sqlite_db_folder")
            if(user_database_folder.endswith("\\") or user_database_folder.endswith("/")):
                pass
            else:
                user_database_folder = user_database_folder+"/"
            user_database_path = "{0}shows.db".format(user_database_folder)
            user_db_data["data"]["path"] = user_database_path
        else:
            raise ValueError("Invalid database provider (user)")

    return [db_data, user_db_data]

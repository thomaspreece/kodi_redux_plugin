import xbmc
import xbmcgui
import xbmcaddon

__profile__ = get_user_dir()

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

def get_user_dir():
    addon = xbmcaddon.Addon()
    return xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")


def get_db_data():
    db_format = xbmcaddon.Addon('plugin.video.redux').getSetting("db_format")
    db_data = {
        "db_format": db_format,
        "data": {}
    }

    if(db_format == "mysql"):
        db_data["data"]["host"] = xbmcaddon.Addon('plugin.video.redux').getSetting("mysql_hostname")
        db_data["data"]["port"] = xbmcaddon.Addon('plugin.video.redux').getSetting("mysql_port")
        db_data["data"]["username"] = xbmcaddon.Addon('plugin.video.redux').getSetting("mysql_username")
        db_data["data"]["password"] = xbmcaddon.Addon('plugin.video.redux').getSetting("mysql_password")
        db_data["data"]["db"] = xbmcaddon.Addon('plugin.video.redux').getSetting("mysql_db")
    elif(db_format == "sqlite"):
        use_custom_db_path = xbmcaddon.Addon('plugin.video.redux').getSetting("sqlite_use_db_folder")
        if(use_custom_db_path == "true"):
            database_folder = xbmcaddon.Addon('plugin.video.redux').getSetting("sqlite_db_folder")
            if(database_folder.endswith("\\") or database_folder.endswith("/")):
                pass
            else:
                database_folder = database_folder+"/"
            database_folder = xbmc.translatePath(database_folder)
            print(database_folder)
            database_path = "{0}shows.db".format(database_folder)
        else:
            database_path = "{0}shows.db".format(__profile__)

        db_data["data"]["path"] = database_path
    else:
        raise ValueError("Invalid database provider (show)")

    user_db_format = xbmcaddon.Addon('plugin.video.redux').getSetting("user_db_format")
    user_db_data = {
        "db_format": db_format,
        "data": {}
    }
    use_same_db = xbmcaddon.Addon('plugin.video.redux').getSetting("user_use_same_db")
    if(use_same_db == "true"):
        user_db_data = db_data
        user_db_format = db_format
    else:
        if(user_db_format == "mysql"):
            user_db_data["data"]["host"] = xbmcaddon.Addon('plugin.video.redux').getSetting("user_mysql_hostname")
            user_db_data["data"]["port"] = xbmcaddon.Addon('plugin.video.redux').getSetting("user_mysql_port")
            user_db_data["data"]["username"] = xbmcaddon.Addon('plugin.video.redux').getSetting("user_mysql_username")
            user_db_data["data"]["password"] = xbmcaddon.Addon('plugin.video.redux').getSetting("user_mysql_password")
            user_db_data["data"]["db"] = xbmcaddon.Addon('plugin.video.redux').getSetting("user_mysql_db")
        elif(user_db_format == "sqlite"):
            user_database_folder = xbmcaddon.Addon('plugin.video.redux').getSetting("user_sqlite_db_folder")
            if(user_database_folder.endswith("\\") or user_database_folder.endswith("/")):
                pass
            else:
                user_database_folder = user_database_folder+"/"
            user_database_folder = xbmc.translatePath(user_database_folder)
            user_database_path = "{0}shows.db".format(user_database_folder)
            user_db_data["data"]["path"] = user_database_path
        else:
            raise ValueError("Invalid database provider (user)")

    return [db_data, user_db_data]

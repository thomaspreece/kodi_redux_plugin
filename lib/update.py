import os

from datetime import date

import sys
import signal

import shutil
import code

import util
import download_single
import download_tvdb_single
import download_moviedb_single
import download_imdb_single
import download_lists
import parseSchedule
try:
    xbmc_libraries_loaded = True
    import xbmcgui
    import xbmc
except:
    xbmc_libraries_loaded = False

def update(script_dir = ".", xbmc = True, return_to_interpreter = False):
    if(xbmc_libraries_loaded == False and xbmc == True):
        raise ValueError("Could not load XBMC Libraries")

    if(xbmc):
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Updating Shows', 'Loading Shows...')
    else:
        print("")
        print("Loading Shows")

    shows = {"shows": {}, "parsed": None, "failed_files": [], "genres": {}, "recent": []}

    if os.path.isfile("{0}/shows.pickle".format(script_dir)):
        shows = parseSchedule.load_shows("{0}/shows.pickle".format(script_dir))
        print("Parsing: {0}".format(shows["parsed"]))
    if(xbmc):
        pDialog.update(5,"Loading Shows... Done","Creating Schedule Download List...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Creating Schedule Download List")

    # ========= Download Schedules Overview from BBC =========
    download_list = download_lists.get_bbc_programmes_schedule_download_list(False, shows["parsed"], script_dir+"/")

    if(xbmc):
        pDialog.update(10, "Creating Schedule Download List...Done","Downloading Schedules...","("+str(len(download_list))+")")
        if (pDialog.iscanceled()): return
        # [TODO]: Should take failed files and deal with them
    else:
        print("")
        print("Downloading Schedules")

    if (len(download_list) != 0):
        download_single.download_files(download_list)

    # ========= Parse Schedule Overview =========
    if(xbmc):
        pDialog.update(15, "Downloading Schedules...Done", "Parsing Schedules For Further Download Links...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Parsing Schedules For Further Download Links")

    # Extracts list of episode programme PIDS from daily html schedules
    download_list = download_lists.get_schedule_items(shows["parsed"], script_dir+"/")

    # ========= Download Detailed Schedule Items from BBC =========
    if(xbmc):
        pDialog.update(20, "Parsing Schedules For Further Download Links...Done", "Downloading Extra Schedule Detail...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Downloading Extra Schedule Detail")

    if (len(download_list) != 0):
        download_single.download_files(download_list)

    # ========= Convert Detailed Schedule Items To JSON Schedules =========
    if(xbmc):
        pDialog.update(25, "Downloading Extra Schedule Detail...Done", "Updating Schedules...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Updating Schedules")

    parseSchedule.convert_html_schedules()

    # ========== Parse JSON Schedules =======
    if(xbmc):
        pDialog.update(30, "Updating Schedules...Done", "Parsing Schedules...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Parsing Schedules")

    # Take download schedules and update shows object
    shows = parseSchedule.get_shows(shows, script_dir+"/")

    if(xbmc):
        pDialog.update(35, "Parsing Schedules...Done","Creating Shows Download List...")
        if (pDialog.iscanceled()): return

    # ========= Download Shows Data from BBC & Merge =========
    download_list_2 = download_lists.get_bbc_programmes_show_download_list(shows["shows"], False, script_dir+"/")

    if(xbmc):
        pDialog.update(40,"Creating Shows Download List...Done","Downloading Shows...","("+str(len(download_list_2))+")")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Downloading Shows")

    if (len(download_list_2) != 0):
        download_single.download_files(download_list_2)

    if(xbmc):
        pDialog.update(45,"Downloading Shows...Done","Parsing Shows...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Parsing Shows")

    shows["shows"] = parseSchedule.merge_shows_files(shows, script_dir+"/")

    if(xbmc):
        pDialog.update(50,"Parsing Shows...Done","Creating TVDB Download List...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Creating TVDB Download List")

    # ========= Download Shows Data from TVDB & Merge =========
    download_list_3 = download_lists.get_tvdb_show_download_list(shows["shows"], False, script_dir+"/")

    if(xbmc):
        pDialog.update(55,"Creating TVDB Download List...Done","Downloading TVDB...","("+str(len(download_list_3))+")")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Downloading TVDB")

    if (len(download_list_3) != 0):
        download_tvdb_single.download_files(download_list_3)

    if(xbmc):
        pDialog.update(60,"Downloading TVDB...Done","Parsing TVDB...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Parsing TVDB")

    shows["shows"] = parseSchedule.merge_tvdb_files(shows["shows"], script_dir+"/")

    if(xbmc):
        pDialog.update(65,"Parsing TVDB...Done","Creating MovieDB Download List...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Creating MovieDB Download List")

    # ========= Download Shows Data from themovieDB & Merge =========
    download_list_4 = download_lists.get_moviedb_show_download_list(shows["shows"])

    if(xbmc):
        pDialog.update(70,"Creating MovieDB Download List...Done","Downloading MovieDB...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Downloading MovieDB")

    if (len(download_list_4) != 0):
        download_moviedb_single.download_files(download_list_4)

    if(xbmc):
        pDialog.update(75,"Downloading MovieDB...Done","Parsing MovieDB...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Parsing MovieDB")

    shows["shows"] = parseSchedule.merge_moviedb_files(shows["shows"])

    if(xbmc):
        pDialog.update(80,"Parsing MovieDB...Done","Creating IMDB Download List...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Creating IMDB Download List")

    # ========= Download Shows Data from IMDB & Merge =========
    download_list_5 = download_lists.get_imdb_show_download_list(shows["shows"])

    if(xbmc):
        pDialog.update(85,"Creating IMDB Download List...Done","Downloading IMDB...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Downloading IMDB")

    if (len(download_list_5) != 0):
        download_imdb_single.download_files(download_list_5)

    if(xbmc):
        pDialog.update(90,"Downloading IMDB...Done","Parsing IMDB...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Parsing IMDB")

    shows["shows"] = parseSchedule.merge_imdb_files(shows["shows"])

    if(xbmc):
        pDialog.update(95,"Parsing IMDB...Done","Saving Updated Shows...")
        if (pDialog.iscanceled()): return
    else:
        print("")
        print("Saving Updated Shows")

    # ========= Save Shows =========
    parseSchedule.save_shows(shows,"{0}/shows.pickle".format(script_dir))

    if(xbmc):
        pDialog.update(100,"Saving Updated Shows...Done")
        if os.path.isdir("{0}/show-scrape-tvdb/".format(script_dir)):
            shutil.rmtree("{0}/show-scrape-tvdb/".format(script_dir))
        if os.path.isdir("{0}/schedule-scrape-bbc/".format(script_dir)):
            shutil.rmtree("{0}/schedule-scrape-bbc/".format(script_dir))
        if os.path.isdir("{0}/show-scrape-bbc/".format(script_dir)):
            shutil.rmtree("{0}/show-scrape-bbc/".format(script_dir))
        pDialog.close()

    if(return_to_interpreter):
        code.interact(local=locals())

if __name__ == "__main__":
    update(False)

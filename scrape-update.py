import os

from datetime import date

import sys
import signal

import shutil

from lib import util
from lib import download_single
from lib import download_tvdb_single
from lib import download_moviedb_single
from lib import download_imdb_single
from lib import download_lists
from lib import parseSchedule

import xbmcgui
import xbmc

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

def update():
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Updating Shows', 'Loading Shows...')

    shows = {"shows": {}, "parsed": None, "failed_files": []}

    if os.path.isfile("{0}/shows.pickle".format(SCRIPT_DIR)):
        shows = parseSchedule.load_shows("{0}/shows.pickle".format(SCRIPT_DIR))

    pDialog.update(5,"Loading Shows... Done","Creating Schedule Download List...")
    if (pDialog.iscanceled()): return

    # ========= Download Schedules Data from BBC =========
    download_list = download_lists.get_bbc_programmes_schedule_download_list(False, shows["parsed"], SCRIPT_DIR+"/")

    pDialog.update(10, "Creating Schedule Download List...Done","Downloading Schedules...","("+str(len(download_list))+")")
    if (pDialog.iscanceled()): return
    # [TODO]: Should take failed files and deal with them

    if (len(download_list) != 0):
        download_single.download_files(download_list)

    pDialog.update(15, "Downloading Schedules...Done", "Parsing Schedules...")
    if (pDialog.iscanceled()): return

    # Take download schedules and update shows object
    shows = parseSchedule.get_shows(shows, SCRIPT_DIR+"/")

    pDialog.update(20, "Parsing Schedules...Done","Creating Shows Download List...")
    if (pDialog.iscanceled()): return

    # ========= Download Shows Data from BBC & Merge =========
    download_list_2 = download_lists.get_bbc_programmes_show_download_list(shows["shows"], False, SCRIPT_DIR+"/")

    pDialog.update(25,"Creating Shows Download List...Done","Downloading Shows...","("+str(len(download_list_2))+")")
    if (pDialog.iscanceled()): return

    if (len(download_list_2) != 0):
        download_single.download_files(download_list_2)

    pDialog.update(30,"Downloading Shows...Done","Parsing Shows...")
    if (pDialog.iscanceled()): return

    shows["shows"] = parseSchedule.merge_shows_files(shows["shows"], SCRIPT_DIR+"/")

    pDialog.update(35,"Parsing Shows...Done","Creating TVDB Download List...")
    if (pDialog.iscanceled()): return

    # ========= Download Shows Data from TVDB & Merge =========
    download_list_3 = download_lists.get_tvdb_show_download_list(shows["shows"], False, SCRIPT_DIR+"/")

    pDialog.update(40,"Creating TVDB Download List...Done","Downloading TVDB...","("+str(len(download_list_3))+")")
    if (pDialog.iscanceled()): return

    if (len(download_list_3) != 0):
        download_tvdb_single.download_files(download_list_3)

    pDialog.update(45,"Downloading TVDB...Done","Parsing TVDB...")
    if (pDialog.iscanceled()): return

    shows["shows"] = parseSchedule.merge_tvdb_files(shows["shows"], SCRIPT_DIR+"/")

    pDialog.update(50,"Parsing TVDB...Done","Creating MovieDB Download List...")
    if (pDialog.iscanceled()): return


    # ========= Download Shows Data from themovieDB & Merge =========
    download_list_4 = download_lists.get_moviedb_show_download_list(shows["shows"])

    pDialog.update(55,"Creating MovieDB Download List...Done","Downloading MovieDB...")
    if (pDialog.iscanceled()): return

    if (len(download_list_4) != 0):
        download_moviedb_single.download_files(download_list_4)

    pDialog.update(60,"Downloading MovieDB...Done","Parsing MovieDB...")
    if (pDialog.iscanceled()): return

    shows["shows"] = parseSchedule.merge_moviedb_files(shows["shows"])

    pDialog.update(65,"Parsing MovieDB...Done","Creating IMDB Download List...")
    if (pDialog.iscanceled()): return

    # ========= Download Shows Data from IMDB & Merge =========
    download_list_5 = download_lists.get_imdb_show_download_list(shows["shows"])

    pDialog.update(70,"Creating IMDB Download List...Done","Downloading IMDB...")
    if (pDialog.iscanceled()): return

    if (len(download_list_5) != 0):
        download_imdb_single.download_files(download_list_5)

    pDialog.update(75,"Downloading IMDB...Done","Parsing IMDB...")
    if (pDialog.iscanceled()): return

    shows["shows"] = parseSchedule.merge_imdb_files(shows["shows"])

    pDialog.update(80,"Parsing IMDB...Done","Saving Updated Shows...")
    if (pDialog.iscanceled()): return

    # ========= Save Shows =========
    parseSchedule.save_shows(shows,"{0}/shows.pickle".format(SCRIPT_DIR))

    pDialog.update(100,"Saving Updated Shows...Done")

    if os.path.isdir("{0}/show-scrape-tvdb/".format(SCRIPT_DIR)):
        shutil.rmtree("{0}/show-scrape-tvdb/".format(SCRIPT_DIR))
    if os.path.isdir("{0}/schedule-scrape-bbc/".format(SCRIPT_DIR)):
        shutil.rmtree("{0}/schedule-scrape-bbc/".format(SCRIPT_DIR))
    if os.path.isdir("{0}/show-scrape-bbc/".format(SCRIPT_DIR)):
        shutil.rmtree("{0}/show-scrape-bbc/".format(SCRIPT_DIR))

    pDialog.close()

if __name__ == "__main__":
    update()

import os

from datetime import date

import sys
import signal

import shutil

from lib import util
from lib import download_single
from lib import download_tvdb_single
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

    pDialog.update(10,"Loading Shows... Done","Creating Schedule Download List...")
    if (pDialog.iscanceled()): return

    # ========= Download Schedules Data from BBC =========
    download_list = download_lists.get_bbc_programmes_schedule_download_list(False, shows["parsed"], SCRIPT_DIR+"/")

    pDialog.update(20, "Creating Schedule Download List...Done","Downloading Schedules...","("+str(len(download_list))+")")
    if (pDialog.iscanceled()): return
    # [TODO]: Should take failed files and deal with them

    if (len(download_list) != 0):
        download_single.download_files(download_list)

    pDialog.update(30, "Downloading Schedules...Done", "Parsing Schedules...")
    if (pDialog.iscanceled()): return

    # Take download schedules and update shows object
    shows = parseSchedule.get_shows(shows, SCRIPT_DIR+"/")

    pDialog.update(40, "Parsing Schedules...Done","Creating Shows Download List...")
    if (pDialog.iscanceled()): return

    # ========= Download Shows Data from BBC & Merge =========
    download_list_2 = download_lists.get_bbc_programmes_show_download_list(shows["shows"], False, SCRIPT_DIR+"/")

    pDialog.update(50,"Creating Shows Download List...Done","Downloading Shows...","("+str(len(download_list_2))+")")
    if (pDialog.iscanceled()): return

    if (len(download_list_2) != 0):
        download_single.download_files(download_list_2)

    pDialog.update(60,"Downloading Shows...Done","Parsing Shows...")
    if (pDialog.iscanceled()): return

    shows["shows"] = parseSchedule.merge_shows_files(shows["shows"], SCRIPT_DIR+"/")

    pDialog.update(70,"Parsing Shows...Done","Creating TVDB Download List...")
    if (pDialog.iscanceled()): return

    # ========= Download Shows Data from TVDB & Merge =========
    download_list_3 = download_lists.get_tvdb_show_download_list(shows["shows"], False, SCRIPT_DIR+"/")

    pDialog.update(80,"Creating TVDB Download List...Done","Downloading TVDB...","("+str(len(download_list_3))+")")
    if (pDialog.iscanceled()): return

    if (len(download_list_3) != 0):
        download_tvdb_single.download_files(download_list_3)

    pDialog.update(90,"Downloading TVDB...Done","Parsing TVDB...")
    if (pDialog.iscanceled()): return

    shows["shows"] = parseSchedule.merge_tvdb_files(shows["shows"], SCRIPT_DIR+"/")

    pDialog.update(99,"Parsing TVDB...Done","Saving Updated Shows...")
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

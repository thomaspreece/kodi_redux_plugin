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

from lib import update
from lib import xbmc_util

import traceback

import xbmcgui
import xbmc

__profile__ = xbmc_util.get_user_dir()

if __name__ == "__main__":
    try:
        update.update("{0}/shows.pickle".format(__profile__), __profile__, True)
    except Exception, e:
        print(str(e))
        traceback.print_exc()
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('Updating Data', 'Something went wrong and an exception was thrown:', str(e), 'See kodi.log for more details')

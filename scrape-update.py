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

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    update.update(SCRIPT_DIR, True)

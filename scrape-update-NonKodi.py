import os
from lib import update
import argparse
#from lib import resolve_redux

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROFILE_DIR = "{0}/../../userdata/addon_data/plugin.video.redux".format(SCRIPT_DIR)

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--pickle_dir", help="Location of shows.pickle", default=PROFILE_DIR)
parser.add_argument("-w", "--working_dir", help="Location to use for saving JSON files etc", default=PROFILE_DIR)
parser.add_argument("-i", "--interp_return", help="Run interpreter after script finishes", action="store_true")
args = parser.parse_args()

if __name__ == "__main__":
    update.update("{0}/shows.pickle".format(args.pickle_dir), args.working_dir, False, args.interp_return)

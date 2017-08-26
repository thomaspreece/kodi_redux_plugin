import os
from lib import update

#from lib import resolve_redux

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    update.update(SCRIPT_DIR, False, True)

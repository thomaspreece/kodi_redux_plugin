import os

from lib import database_functions
from lib import database_schema
try:
   import cPickle as pickle
except:
   import pickle

def load_shows_json(location = None):
    print("Loading Shows")
    script_dir = os.path.dirname(os.path.realpath(__file__))
    if location == None:
        location = "{0}/shows.pickle".format(script_dir)
    if os.path.isfile(location):
        f = open( location, "rb" )
        shows = pickle.load( f )
        shows = shows["shows"]
        f.close()
        print("Finished Loading Shows (Success)")
        return shows
    else:
        print("Finished Loading Shows (Fail)")
        return None

if __name__ == "__main__":
    db = database_schema.BaseModel._meta.database
    db.init("shows.db")
    print("Database Initialised")
    database_functions.create_database()
    print("Database Created. Populating...")
    shows = load_shows_json()
    database_functions.populate_database(shows)

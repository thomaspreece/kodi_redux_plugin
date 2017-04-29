import os
import re

try:
   import cPickle as pickle
except:
   import pickle

import xbmcgui
import xbmc
import xbmcaddon

from lib import util
from lib import resolve_redux

def load_shows(location = "shows.pickle"):
    if os.path.isfile(location):
        shows = pickle.load( open( location, "rb" ) )
        return shows
    else:
        raise ValueError("Could not find {0}".format(location))

pDialog = xbmcgui.DialogProgress()
pDialog.create('Generating Download List', 'Loading Shows...')

script_dir = os.path.dirname(os.path.realpath(__file__))
location = "{0}/shows.pickle".format(script_dir)
shows = load_shows(location)

home_folder = os.path.expanduser("~")
desktop_folder = os.path.join(home_folder,"desktop")

_handle = int(sys.argv[1])
show_title = sys.argv[2]
if (len(sys.argv) > 4):
    show_episode = sys.argv[4]
    show_season = sys.argv[3]
    title = re.sub('[^a-zA-Z0-9]', '', show_title) + " - Season " + re.sub('[^a-zA-Z0-9]', '', show_season) + " - Episode" + re.sub('[^a-zA-Z0-9]', '', show_episode)
elif (len(sys.argv) > 3):
    show_season = sys.argv[3]
    show_episode = None
    title = re.sub('[^a-zA-Z0-9]', '', show_title) + " - Season " + re.sub('[^a-zA-Z0-9]', '', show_season)
else:
    show_season = None
    show_episode = None
    title = re.sub('[^a-zA-Z0-9]', '', show_title)

save_file = os.path.join(desktop_folder,  title) + ".txt"

# Get Number of Episodes to make list for
show = shows["shows"][show_title]
show_seasons = show["season"]
total_episodes = 0
current_episode = 0
for season in sorted(show_seasons):
    if(show_season != None and season != show_season):
        continue
    show_episodes = show_seasons[season]["episode"]
    for episode in sorted(show_episodes):
        if(show_episode != None and episode != show_episode):
            continue
        total_episodes += 1

pDialog.update(1,"Resolving Redux Urls...")

loginfile = '{0}/reduxLogin.txt'.format(script_dir)
redux_account = resolve_redux.ReduxAccount(loginfile)
redux_token = redux_account.checkAndGetToken()

requested_format_setting = xbmcaddon.Addon('plugin.video.redux').getSetting("format")
requested_format = util.convert_format(requested_format_setting)

if(redux_token == ""):
    pass
    # Raise Error Here!
else:
    failed_downloads = []

    if(not os.path.isfile(save_file)):
        f = open(save_file, 'w')
        f.write('# Download for '+show_title+'\n')  # python will convert \n to os.linesep

        show = shows["shows"][show_title]
        show_seasons = show["season"]

        for season in sorted(show_seasons):
            if(show_season != None and season != show_season):
                continue
            show_episodes = show_seasons[season]["episode"]
            for episode in sorted(show_episodes):
                if(show_episode != None and episode != show_episode):
                    continue
                pDialog.update( int((100*current_episode)/total_episodes) ,"Resolving Redux Urls...","Resolved {0}/{1}".format(current_episode,total_episodes),"Resolving Disk Reference")
                [error,ref] = resolve_redux.resolve_episode_ref(redux_token, show, season, episode)
                url = None
                defaultedTo = None
                if (error > -1):
                    pDialog.update( int((100*current_episode)/total_episodes) ,"Resolving Redux Urls...","Resolved {0}/{1}".format(current_episode,total_episodes),"Resolving URL")
                    urls = resolve_redux.resolve_episode_url(redux_token, ref)
                    if urls == None:
                        failed_downloads.append("S{0}E{1}".format(season,episode))
                    else:
                        if (requested_format in urls):
                            url = urls[requested_format]
                        elif (len(urls) > 1):
                            for key in urls:
                                if (key != "ts"):
                                    url = urls[key]
                                    defaultedTo = key
                                    break
                        else:
                            url = urls["ts"]
                            defaultedTo = "ts"
                else:
                    failed_downloads.append("S{0}E{1}".format(season,episode))

                if url != None:
                    if(defaultedTo != None):
                        f.write("# Download S{0}E{1} (Defaulted to {2} Format)".format(season,episode,defaultedTo)+"\n")
                    else:
                        f.write("# Download S{0}E{1}".format(season,episode)+"\n")

                    url = url.replace("media.","{2}_S{0}E{1}.".format(season,episode,re.sub("[^a-zA-Z0-9]","",show_title)))

                    f.write("{0}\n".format(url))
                else:
                    f.write("# Download S{0}E{1}".format(season,episode)+"\n")
                    f.write("# Unavailable\n".format(url))

                current_episode += 1
                pDialog.update( int((100*current_episode)/total_episodes) ,"Resolving Redux Urls...","Resolved {0}/{1}".format(current_episode,total_episodes),"")
        f.close()
        pDialog.update(100,"Resolving Redux Urls... Done","","")
        pDialog.close()
        xbmcgui.Dialog().ok("Generating Download List", "Download List Saved To: ",save_file)
    else:
        pDialog.close()
        xbmcgui.Dialog().ok("Generating Download List", "File Already Exists: ",save_file)

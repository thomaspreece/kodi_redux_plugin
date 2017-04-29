import os
import json
import sys
try:
   import cPickle as pickle
except:
   import pickle

from pytvdbapi import api

from datetime import timedelta, date
from dateutil import parser
import time

import util

import glob

def load_shows(location = "shows.pickle"):
    if os.path.isfile(location):
        shows = pickle.load( open( location, "rb" ) )
        return shows
    else:
        raise ValueError("Could not find {0}".format(location))

def save_shows(shows, location = "shows.pickle"):
    if(shows):
        if os.path.isfile(location):
            os.remove(location)
        pickle.dump( shows, open( location, "wb" ) )
    else:
        raise ValueError("No Shows Provided")

def get_shows(shows = {"shows": {}, "parsed": None, "failed_files": []}, script_prefix=""):
    SCRAPE_FOLDER = "{0}schedule-scrape-bbc".format(script_prefix)
    BASE_FANART_URL = "https://ichef.bbci.co.uk/images/ic/640x360/"
    if shows["parsed"] != None:
        latest_parse = parser.parse(shows["parsed"])
    else:
        latest_parse = None
    failed_files = shows["failed_files"]
    shows = shows["shows"]
    print("")
    print("Parsing {0}/*".format(SCRAPE_FOLDER))

    k = 0
    for schedule_folder in sorted(glob.glob("{0}/*".format(SCRAPE_FOLDER))):
        for json_file in sorted(glob.glob(schedule_folder+"/*.json")):
            k = k + 1
            if(k > 50):
                k = 0
                sys.stdout.write('.')
                sys.stdout.flush()
            if os.path.isfile(json_file):
                try:
                    json_content = json.load(open(json_file))
                except:
                    print("")
                    print("Failed to parse {0}".format(json_file))
                    failed_files.append(json_file)
                    continue
                service_title = json_content["schedule"]["service"]["title"]
                #if(not (service_title in shows)):
                #    shows[service_title] = {}

                json_file_date = parser.parse(json_content["schedule"]["day"]["date"])
                if latest_parse == None or json_file_date > latest_parse:
                    latest_parse = json_file_date

                for i in range(len(json_content["schedule"]["day"]["broadcasts"])):
                    json_broadcast = json_content["schedule"]["day"]["broadcasts"][i]

                    episode_duration = json_broadcast["duration"]
                    episode_repeat = json_broadcast["is_repeat"]
                    episode_start = util.checkStr(json_broadcast["start"])#parser.parse(json_broadcast["start"])
                    episode_end = util.checkStr(json_broadcast["end"])#parser.parse(json_broadcast["end"])
                    json_episode = json_broadcast["programme"]
                    if(json_episode["type"] != "episode"):
                        print(json.dumps(json_broadcast))
                        raise ValueError("Invalid Type")

                    if("image" in json_episode):
                        episode_image = BASE_FANART_URL+util.checkStr(json_episode["image"]["pid"])
                    else:
                        episode_image = None
                    # if(episode_repeat):
                    #     episode_first_broadcast = parser.parse(json_broadcast["end"])#episode_start
                    # else:
                    #     episode_first_broadcast = parser.parse(json_episode["first_broadcast_date"])

                    episode_first_broadcast = util.checkStr(json_episode["first_broadcast_date"])#parser.parse(json_episode["first_broadcast_date"])
                    episode_pid = util.checkStr(json_episode["pid"])
                    episode_number = util.checkStr(json_episode["position"])
                    episode_title = util.checkStr(json_episode["title"])
                    episode_synopsis = util.checkStr(json_episode["short_synopsis"])

                    show_title = None
                    season_number = None
                    season_title = None

                    if(not ("programme" in json_episode)):
                        # Episode is a one off (likely a film)
                        show_title = util.checkStr(episode_title)
                        show_pid = None
                        show_image = None
                        season_number = '0'
                        season_title = None
                        season_pid = None
                        season_image = None

                    two_pronged_episode_number = False
                    two_pronged_episode_number_unknown = False
                    json_programme = json_episode
                    while(True):
                        if("programme" in json_programme):
                            json_programme = json_programme["programme"]
                        else:
                            break

                        if(json_programme["type"] == "brand"):
                            json_brand = json_programme
                            show_title = util.checkStr(json_brand["title"])
                            show_pid = util.checkStr(json_brand["pid"])
                            if("image" in json_brand):
                                show_image = BASE_FANART_URL+util.checkStr(json_brand["image"]["pid"])
                            else:
                                show_image = None
                        elif(json_programme["type"] == "series"):
                            json_season = json_programme
                            if(season_number != None):
                                two_pronged_episode_number = True
                                if(episode_number != None):
                                    episode_number = str(season_number)+"."+str(episode_number)
                                else:
                                    two_pronged_episode_number_unknown = True
                                    episode_number = str(season_number)+".U"
                            if(season_title != None):
                                episode_title = str(season_title) + ": " + str(episode_title)
                            season_number = util.checkStr(json_season["position"])
                            season_title = util.checkStr(json_season["title"])
                            season_pid = util.checkStr(json_season["pid"])
                            if("image" in json_season):
                                season_image = BASE_FANART_URL+util.checkStr(json_season["image"]["pid"])
                            else:
                                season_image = None
                            if(season_number == None):
                                season_number = '0'
                            else:
                                season_number = season_number
                        else:
                            print(json.dumps(json_broadcast))
                            raise ValueError("Invalid Programme Type")

                    if(show_title == None):
                        show_title = util.checkStr(season_title)
                        show_pid = None
                        show_image = None
                    if(season_number == None):
                        season_number = '0'
                        season_pid = None
                        season_image = None

                    if(not (show_title in shows)):
                        shows[show_title] = {
                            "title": show_title,
                            "pid": show_pid,
                            "image": show_image,
                            "season": {},
                            "show_merged": False,
                            "tvdb_merged": False
                        }

                    if(not (season_number in shows[show_title]["season"])):
                        shows[show_title]["season"][season_number] = {
                            "number": season_number,
                            "title": season_title,
                            "pid": season_pid,
                            "image": season_image,
                            "episode": {}
                        }

                    if(episode_number != None and (two_pronged_episode_number or not two_pronged_episode_number_unknown)):
                        if(not (episode_number in shows[show_title]["season"][season_number]["episode"])):
                            shows[show_title]["season"][season_number]["episode"][episode_number] = {
                                "number": episode_number,
                                "pid": episode_pid,
                                "title": episode_title,
                                "synopsis": episode_synopsis,
                                "image": episode_image,
                                "start": None,
                                "end": None,
                                "duration": episode_duration,
                                "first_broadcast": None,
                                "service": None,
                                "repeats": []
                            }
                        if(not ("repeats" in shows[show_title]["season"][season_number]["episode"][episode_number])):
                            shows[show_title]["season"][season_number]["episode"][episode_number]["repeats"] = []
                        # if(not episode_repeat):
                        #     if(shows[show_title]["season"][season_number]["episode"][episode_number]["start"]):
                        #         print("INVALID!")
                        #     shows[show_title]["season"][season_number]["episode"][episode_number]["start"] = episode_start
                        #     shows[show_title]["season"][season_number]["episode"][episode_number]["end"] = episode_end
                        #     shows[show_title]["season"][season_number]["episode"][episode_number]["first_broadcast"] = episode_first_broadcast
                        # else:
                        shows[show_title]["season"][season_number]["episode"][episode_number]["repeats"].append({
                            "start": episode_start,
                            "end": episode_end,
                            "first_broadcast": episode_first_broadcast,
                            "service": service_title
                        })
                    else:
                        if(not ("unknown" in shows[show_title]["season"][season_number]["episode"])):
                            shows[show_title]["season"][season_number]["episode"]["unknown"] = []
                        shows[show_title]["season"][season_number]["episode"]["unknown"].append({
                            "number": episode_number,
                            "pid": episode_pid,
                            "title": episode_title,
                            "synopsis": episode_synopsis,
                            "image": episode_image,
                            "start": episode_start,
                            "end": episode_end,
                            "duration": episode_duration,
                            "first_broadcast": episode_first_broadcast,
                            "service": service_title
                        })
    print("")
    if(len(failed_files) != 0):
        print("------------------------------------")
        print("FAILED FILES: ")
        for f in failed_files:
            print(f)
        print("------------------------------------")
        while(True):
            delete_files = raw_input("Delete Failed Files? (y/n): ")
            if(delete_files == "y"):
                for f in failed_files:
                    os.remove(f)
                break
            elif(delete_files == "n"):
                break
            else:
                continue
    shows = resolve_repeats(shows)
    return {"shows": shows, "parsed": latest_parse.strftime('%Y-%m-%d'), "failed_files": failed_files}

def resolve_repeats(shows):
    k=0
    for show_name in shows:
        k = k + 1
        if(k > 50):
            k = 0
            sys.stdout.write('.')
            sys.stdout.flush()
        for season in shows[show_name]["season"]:
            for episode in shows[show_name]["season"][season]["episode"]:
                if(episode != "unknown"):
                    episode_dict = shows[show_name]["season"][season]["episode"][episode]
                    if not ("repeats" in episode_dict):
                        continue
                    repeats = episode_dict["repeats"]
                    for i in range(len(repeats)):
                        if episode_dict["start"] == None:
                            episode_dict["start"] = repeats[i]["start"]
                            episode_dict["end"] = repeats[i]["end"]
                            episode_dict["first_broadcast"] = repeats[i]["first_broadcast"]
                            episode_dict["service"] = repeats[i]["service"]
                        else:
                            if parser.parse(episode_dict["start"]) > parser.parse(repeats[i]["start"]):
                                episode_dict["start"] = repeats[i]["start"]
                                episode_dict["end"] = repeats[i]["end"]
                                episode_dict["first_broadcast"] = repeats[i]["first_broadcast"]
                                episode_dict["service"] = repeats[i]["service"]
                            if episode_dict["first_broadcast"] == episode_dict["start"]:
                                break
                    del episode_dict["repeats"]

    for show_name in shows:
        for season in shows[show_name]["season"]:
            sorted_episodes = []
            for episode in shows[show_name]["season"][season]["episode"]:
                if(episode != "unknown"):
                    sorted_episodes.append(dict(shows[show_name]["season"][season]["episode"][episode]))
                else:
                    sorted_episodes.extend(list(shows[show_name]["season"][season]["episode"][episode]))
            # Sort Unknown Episodes by first_broadcast datetime
            sorted_episodes = sorted(sorted_episodes, key=lambda k: parser.parse(k['first_broadcast']))
            # Remove Repeats
            sorted_episodes = [sorted_episodes[i] for i in range(len(sorted_episodes)) if (i == len(sorted_episodes)-1 or (sorted_episodes[i]["first_broadcast"] != sorted_episodes[i+1]["first_broadcast"]))]
            # Split Episodes into Unknown and X episode numbers and X.X episode numbers
            sorted_episodes_full = [k for k in sorted_episodes if (k["number"] == None or len(str(k["number"]).split(".")) != 2)]
            sorted_episodes_parts = [k for k in sorted_episodes if (k["number"] != None and  len(str(k["number"]).split(".")) == 2)]

            # Fill in missing episode numbers for Unknown episodes
            last_episode_number = 0
            for i in range(len(sorted_episodes_full)):
                ep = sorted_episodes_full[i]
                if(ep["number"] == None):
                    ep["old_number"] = None
                    ep["number"] = str(last_episode_number + 1)
                last_episode_number = int(ep["number"])

            # Fill in missing episode numbers for X.U episodes
            last_major_number = 0
            last_minor_number = 0
            for i in range(len(sorted_episodes_parts)):
                ep = sorted_episodes_parts[i]
                major_number = ep["number"].split(".")[0]
                minor_number = ep["number"].split(".")[1]
                if(minor_number == "U"):
                    ep["old_number"] = str(major_number)+"."+str(minor_number)
                    if(last_major_number == int(major_number)):
                        minor_number = int(last_minor_number) + 1
                    else:
                        minor_number = 1
                ep["number"] = str(major_number)+"."+str(minor_number)
                last_minor_number = int(minor_number)
                last_major_number = int(major_number)

            del shows[show_name]["season"][season]["episode"]
            shows[show_name]["season"][season]["episode"] = {}
            for episode in sorted_episodes_full:
                shows[show_name]["season"][season]["episode"][episode["number"]] = episode
            for episode in sorted_episodes_parts:
                shows[show_name]["season"][season]["episode"][episode["number"]] = episode

    return shows

def merge_shows_files(shows, script_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-bbc".format(script_prefix)
    print("")
    print("Parsing {0}/*".format(SCRAPE_FOLDER))

    k = 0
    for show_key in shows:
        k = k + 1
        if(k > 50):
            k = 0
            sys.stdout.write('.')
            sys.stdout.flush()
        show = shows[show_key]
        if show["show_merged"] == True:
            continue
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        if(pid):
            json_file = "{0}/{1}.json".format(SCRAPE_FOLDER,pid)
            if os.path.isfile(json_file):
                try:
                    json_content = json.load(open(json_file))
                except:
                    print("")
                    print("Failed to parse {0}".format(json_file))
                    failed_files.append(json_file)
                    continue
                show["show_merged"] = True
                show["type"] = None
                show["summary_long"] = util.checkStr(json_content["programme"]["long_synopsis"])
                show["summary_medium"] = util.checkStr(json_content["programme"]["medium_synopsis"])
                show["summary_short"] = util.checkStr(json_content["programme"]["short_synopsis"])

                if(show["summary_long"]):
                    show["summary"] = show["summary_long"]
                elif(show["summary_medium"]):
                    show["summary"] = show["summary_medium"]
                elif(show["summary_short"]):
                    show["summary"] = show["summary_short"]
                else:
                    show["summary"] = ""

                show["premier"] = util.checkStr(json_content["programme"]["first_broadcast_date"])
                if(show["premier"]):
                    show["year"] = util.checkStr(parser.parse(show["premier"]).year)
                else:
                    show["year"] = None
                #show["premier"] = show["premier"].strftime("%y-%m-%d")
                show["sub-genres"] = []
                show["genres"] = []
                show["actors"] = []
                categories = json_content["programme"]["categories"]
                for i in range(len(categories)):
                    if(categories[i]["type"] == "genre"):
                        if(not categories[i]["title"] in show["sub-genres"]):
                            show["sub-genres"].append(util.checkStr(categories[i]["title"]))
                        genre = util.checkStr(categories[i]["title"])
                        cat = categories[i]["broader"]
                        while(True):
                            if("category" in cat):
                                if(not cat["category"]["title"] in show["sub-genres"]):
                                    show["sub-genres"].append(util.checkStr(cat["category"]["title"]))
                                genre = util.checkStr(cat["category"]["title"])
                                cat = cat["category"]["broader"]
                                continue
                            break
                        if(not genre in show["genres"]):
                            show["genres"].append(genre)
                        if(genre in show["sub-genres"]):
                            show["sub-genres"].remove(genre)
                    elif(categories[i]["type"] == "format"):
                        show["type"] = util.checkStr(categories[i]["title"])
                    elif(categories[i]["type"] == "subject" or categories[i]["type"] == "place" or categories[i]["type"] == "organisation"):
                        pass
                    elif(categories[i]["type"] == "person"):
                        show["actors"].append(util.checkStr(categories[i]["title"]))
                    else:
                        print(categories[i])
                        print(pid)
                        raise ValueError("Unknown Type")
            else:
                show["summary"] = ""
                show["summary_short"] = None
                show["summary_medium"] = None
                show["summary_long"] = None
                show["type"] = None
                show["premier"] = None
                show["year"] = None
                show["genres"] = []
                show["sub-genres"] = []
                show["actors"] = []
                print("")
                print("Missing pid file {0}".format(json_file))
    return shows

def merge_tvdb_files(shows, script_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-tvdb".format(script_prefix)
    BASE_FANART_URL = "http://thetvdb.com/banners/"
    print("")
    print("Parsing {0}/*".format(SCRAPE_FOLDER))

    k = 0
    for show_key in shows:
        k = k + 1
        if(k > 50):
            k = 0
            sys.stdout.write('.')
            sys.stdout.flush()
        show = shows[show_key]
        if show["tvdb_merged"] == True:
            continue
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        output_file = "{1}/{0}.json".format(pid,SCRAPE_FOLDER)
        if(pid and os.path.isfile(output_file)):
            try:
                input_file_handle = open(output_file, 'rb')
                tvdb_show = json.load(input_file_handle)
                input_file_handle.close()
                show["tvdb_merged"] = True
            except Exception as e:
                print("")
                print("JSON Load Failed: {0}".format(str(e)))
                tvdb_show = {}


            if("SeriesName" in tvdb_show):
                a = util.cleanString(util.checkStr(tvdb_show["SeriesName"]))
                b = util.cleanString(util.checkStr(show["title"]))
                if(a != b):
                    tvdb_show = {}

            if("Actors" in tvdb_show):
                show["actors"].extend(tvdb_show["Actors"])

            if("Rating" in tvdb_show):
                show["rating"] = tvdb_show["Rating"]
                show["rating_count"] = tvdb_show["RatingCount"]
            else:
                show["rating"] = None
                show["rating_count"] = None

            if("id" in tvdb_show):
                show["tvdb_id"] = util.checkStr(tvdb_show["id"])
            else:
                show["tvdb_id"] = None

            if("IMDB_ID" in tvdb_show):
                show["imdb_id"] = util.checkStr(tvdb_show["IMDB_ID"])
            else:
                show["imdb_id"] = None

            if("banner" in tvdb_show):
                show["banner"] = BASE_FANART_URL+util.checkStr(tvdb_show["banner"])
            else:
                show["banner"] = None

            if("fanart" in tvdb_show):
                show["fanart"] = BASE_FANART_URL+util.checkStr(tvdb_show["fanart"])
            else:
                show["fanart"] = None

            if("poster" in tvdb_show):
                show["poster"] = BASE_FANART_URL+util.checkStr(tvdb_show["poster"])
            else:
                show["poster"] = None
        else:
            show["rating"] = None
            show["rating_count"] = None
            show["tvdb_id"] = None
            show["imdb_id"] = None
            show["poster"] = None
            show["fanart"] = None
            show["banner"] = None
            print("")
            print("Missing pid file {0}".format(output_file))
    return shows

# def split_films(shows):
#     print("")
#     print("Splitting Up Films")
#     k = 0
#     new_shows = {"Films": {}}
#     for channel_key in shows:
#         if(not channel_key in new_shows):
#             new_shows[channel_key] = {}
#         channel = shows[channel_key]
#         for show_key in channel:
#             k = k + 1
#             if(k > 50):
#                 k = 0
#                 sys.stdout.write('.')
#                 sys.stdout.flush()
#             show = channel[show_key]
#             if(show["type"] == "Films"):
#                 new_shows["Films"][show_key] = show
#             else:
#                 new_shows[channel_key][show_key] = show
#     return new_shows

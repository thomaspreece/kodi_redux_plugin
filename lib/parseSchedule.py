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
from bs4 import BeautifulSoup

import code

import glob

def load_shows(location):
    if os.path.isfile(location):
        shows = pickle.load( open( location, "rb" ) )
        return shows
    else:
        raise ValueError("Could not find {0}".format(location))

def save_shows(shows, location):
    if(shows):
        if os.path.isfile(location):
            os.remove(location)
        pickle.dump( shows, open( location, "wb" ) )
    else:
        raise ValueError("No Shows Provided")

def fill_out_schedule(service,date,schedule_list, script_prefix =""):
    EPISODE_FOLDER = "{0}episode-scrape-bbc".format(script_prefix)
    schedule = {}
    schedule["service"] = {}
    schedule["service"]["type"] = "tv"
    schedule["service"]["key"] = service
    if(service == "bbcfour"):
        schedule["service"]["title"] = "BBC Four"
    if(service == "bbctwo"):
        schedule["service"]["title"] = "BBC Two"
        schedule["service"]["outlet"] = {
            "key": "england",
            "title": "England"
        }
    if(service == "bbcone"):
        schedule["service"]["title"] = "BBC One"
        schedule["service"]["outlet"] = {
            "key": "london",
            "title": "London"
        }
    schedule["day"] = {}
    schedule["day"]["date"] = date
    schedule["day"]["has_next"] = 1
    schedule["day"]["has_previous"] = 1
    schedule["day"]["broadcasts"] = []
    broadcasts = schedule["day"]["broadcasts"]

    for schedule_item in schedule_list:
        if(not os.path.isfile("{0}/{1}.json".format(EPISODE_FOLDER, schedule_item["pid"]))):
            print("Could not find episode info: {0}".format(schedule_item["pid"]))
            return -1
        try:
            json_content = json.load(open("{0}/{1}.json".format(EPISODE_FOLDER, schedule_item["pid"])))
        except:
            print("")
            print(schedule_list)
            print("Failed to parse {0}".format(schedule_item["pid"]))
            return -1
        broadcast = {}
        if("first_broadcast_date" in json_content["programme"] and json_content["programme"]["first_broadcast_date"] == schedule_item["datetime"]):
            broadcast["is_repeat"] = False
        else:
            broadcast["is_repeat"] = True
        broadcast["is_blanked"] = False
        broadcast["start"] = schedule_item["datetime"]
        broadcast["end"] = schedule_item["end_datetime"]
        duration = abs((parser.parse(schedule_item["end_datetime"]) - parser.parse(schedule_item["datetime"])).seconds)

        broadcast["duration"] = duration
        broadcast["programme"] = {k: json_content["programme"][k] for k in json_content["programme"] if k not in (
            'parent', 'peers', 'versions', 'links', 'supporting_content_items', 'categories')}
        if("parent" in json_content["programme"]):
            broadcast["programme"]["programme"] = json_content["programme"]["parent"]["programme"]
            if("parent" in json_content["programme"]["parent"]["programme"]):
                broadcast["programme"]["programme"]["programme"] = json_content["programme"]["parent"]["programme"]["parent"]["programme"]

        broadcasts.append(broadcast)
    return {"schedule": schedule}

def convert_html_schedules(script_prefix=""):
    SCHEDULE_FOLDER = "{0}schedule-scrape-bbc".format(script_prefix)
    renameFiles = []
    print("")
    print("Converting HTML: {0}/*".format(SCHEDULE_FOLDER))
    # for schedule_folder in sorted(glob.glob("{0}/*".format(SCHEDULE_FOLDER))):
    #     for html_file in sorted(glob.glob(schedule_folder+"/*.old_html")):
    #          html_file_datetime = parser.parse(html_file.rsplit('/')[-1][0:10])
    #          html_file_date = parser.parse(html_file.rsplit('/')[-1][0:10]).strftime("%Y-%m-%d")
    #          html_file_service = html_file.rsplit('/')[-1][11:-9]
    #          html_file_path = html_file.rsplit('/', 1)[0]
    #
    #          new_json_file = html_file_path+"/"+html_file_date+"-"+html_file_service+".json"
    #          os.remove(new_json_file)
    #          os.rename(html_file,html_file_path+"/"+html_file_date+"-"+html_file_service+".html")

    for schedule_folder in sorted(glob.glob("{0}/*".format(SCHEDULE_FOLDER))):
        for html_file in sorted(glob.glob(schedule_folder+"/*.html")):
            schedule_item_list = []
            html_file_datetime = parser.parse(html_file.rsplit('/')[-1][0:10])
            html_file_date = parser.parse(html_file.rsplit('/')[-1][0:10]).strftime("%Y-%m-%d")
            html_file_service = html_file.rsplit('/')[-1][11:-5]
            html_file_path = html_file.rsplit('/', 1)[0]

            new_json_file = html_file_path+"/"+html_file_date+"-"+html_file_service+".json"
            if(not os.path.isfile(new_json_file)):

                print(html_file_date+"-"+html_file_service)

                previous_html_file_date = (html_file_datetime - timedelta(days=1)).strftime("%Y-%m-%d")
                previous_html_file = html_file_path+"/"+previous_html_file_date+"-"+html_file_service+".html"

                next_html_file_date = (html_file_datetime + timedelta(days=1)).strftime("%Y-%m-%d")
                next_html_file = html_file_path+"/"+next_html_file_date+"-"+html_file_service+".html"
                # if(not os.path.isfile(previous_html_file)):
                #     previous_html_file = previous_html_file[0:-5]+".old_html"
                if(os.path.isfile(previous_html_file) and os.path.isfile(next_html_file)):
                    bs_current = BeautifulSoup(open(html_file), "lxml")
                    bs_previous = BeautifulSoup(open(previous_html_file), "lxml")
                    current_schedule_items = bs_current.find_all("div", class_="broadcast")
                    previous_schedule_items = bs_previous.find_all("div", class_="broadcast")
                    next_schedule_first_item_time = None

                    bs_next = BeautifulSoup(open(next_html_file), "lxml")
                    next_schedule_items = bs_next.find_all("div", class_="broadcast")
                    for schedule_item in next_schedule_items:
                        schedule_item_time_html = schedule_item.find("h3", class_="broadcast__time")
                        schedule_item_offair_html = schedule_item.find("div", class_="broadcast__live")
                        if(schedule_item_offair_html == None or schedule_item_offair_html.get_text() != "Off air"):
                            next_schedule_first_item_time = schedule_item_time_html.get("content")
                            break
                    for schedule_item in previous_schedule_items:
                        schedule_item_time_html = schedule_item.find("h3", class_="broadcast__time")
                        schedule_item_offair_html = schedule_item.find("div", class_="broadcast__live")
                        if(schedule_item_offair_html == None or schedule_item_offair_html.get_text() != "Off air"):
                            schedule_item_time = schedule_item_time_html.get("content")
                            if(schedule_item_time[0:10] == html_file_date):
                                schedule_item_links = schedule_item.findAll("a")
                                if len(schedule_item_links) == 0:
                                    raise ValueError("Invalid Link")
                                pid_found = False
                                for link_ind in range(len(schedule_item_links)):
                                    schedule_item_pid = schedule_item_links[link_ind].get("href").rsplit('/')[-1]
                                    schedule_item_pid = schedule_item_pid.rsplit("#")[0]
                                    if((schedule_item_pid[0] == "b" or schedule_item_pid[0] == "p") and len(schedule_item_pid) == 8):
                                        schedule_item_list.append({
                                            "datetime": schedule_item_time,
                                            "pid": schedule_item_pid,
                                        })
                                        pid_found = True
                                        break
                                if(pid_found == False):
                                    print(schedule_item)
                                    for link_ind in range(len(schedule_item_links)):
                                        schedule_item_pid = schedule_item_links[link_ind].get("href").rsplit('/')[-1]
                                        schedule_item_pid = schedule_item_pid.rsplit("#")[0]
                                        print(schedule_item_pid)
                                    raise ValueError("Invalid PID!")
                    for schedule_item in current_schedule_items:
                        schedule_item_time_html = schedule_item.find("h3", class_="broadcast__time")
                        schedule_item_offair_html = schedule_item.find("div", class_="broadcast__live")
                        if(schedule_item_offair_html == None or schedule_item_offair_html.get_text() != "Off air"):
                            schedule_item_time = schedule_item_time_html.get("content")
                            schedule_item_links = schedule_item.findAll("a")
                            if len(schedule_item_links) == 0:
                                raise ValueError("Invalid Link")
                            pid_found = False
                            for link_ind in range(len(schedule_item_links)):
                                schedule_item_pid = schedule_item_links[link_ind].get("href").rsplit('/')[-1]
                                schedule_item_pid = schedule_item_pid.rsplit("#")[0]
                                if((schedule_item_pid[0] == "b" or schedule_item_pid[0] == "p") and len(schedule_item_pid) == 8):
                                    schedule_item_list.append({
                                        "datetime": schedule_item_time,
                                        "pid": schedule_item_pid,
                                    })
                                    pid_found = True
                                    break
                            if(pid_found == False):
                                print(schedule_item)
                                for link_ind in range(len(schedule_item_links)):
                                    schedule_item_pid = schedule_item_links[link_ind].get("href").rsplit('/')[-1]
                                    schedule_item_pid = schedule_item_pid.rsplit("#")[0]
                                    print(schedule_item_pid)
                                raise ValueError("Invalid PID!")

                    for i in range(len(schedule_item_list)-1):
                        schedule_item_list[i]["end_datetime"] = schedule_item_list[i+1]["datetime"]
                    for i in range(len(schedule_item_list)-1,-1,-1):
                        if(schedule_item_list[i]["datetime"][0:10] != html_file_date):
                            del schedule_item_list[i]
                    for i in range(len(schedule_item_list)):
                        if(not "end_datetime" in schedule_item_list[i]):
                            if(i == len(schedule_item_list)-1 and next_schedule_first_item_time != None):
                                schedule_item_list[i]["end_datetime"] = next_schedule_first_item_time
                            else:
                                print(schedule_item_list)
                                print(next_schedule_first_item_time)
                                raise ValueError("Invalid Schedule Item")
                    complete_schedule = fill_out_schedule(html_file_service, html_file_date, schedule_item_list, script_prefix)

                    new_json_file = html_file_path+"/"+html_file_date+"-"+html_file_service+".json"
                    if(complete_schedule == -1):
                        print("Error getting schedule info")
                    else:
                        with open(new_json_file, 'w') as outfile:
                            json.dump(complete_schedule, outfile)
                        renameFiles.append(html_file)
                else:
                    print("No previous and/or next file")

    # for rfile in renameFiles:
    #     os.rename(rfile, rfile[0:-5]+".old_html")
    #         for schedule_item in schedule_items:
    #             schedule_item_time_html = schedule_item.find("h3", class_="broadcast__time")
    #             schedule_item_offair_html = schedule_item.find("div", class_="broadcast__live")
    #             if(schedule_item_offair_html == None or schedule_item_offair_html.get_text() != "Off air"):
    #                 schedule_item_time = schedule_item_time_html.get("content")
    #                 schedule_item_link = schedule_item.find("a")
    #                 if schedule_item_link == None:
    #                     raise ValueError("Invalid Link")
    #                 schedule_item_pid = schedule_item_link.get("href").rsplit('/')[-1]
    #                 if(schedule_item_pid[0] != "b" and len(schedule_item_pid) != 8):
    #                     raise ValueError("Invalid PID!")
    #                 # schedule_item_pid_list.append(schedule_item_pid)
    #                 schedule_item_pid_list.append([SCRAPE_URL+"programmes/{0}.json".format(schedule_item_pid), "{0}/{1}.json".format(SAVE_FOLDER,schedule_item_pid), "Saved: {0}".format(schedule_item_pid)])
    #
    # return schedule_item_pid_list

def add_show_to_resents(recents, show_title, recent_type, max_recents = 50):
    recents[:] = [d for d in recents if d.get('name') != show_title]
    recents.append({
        "name": show_title,
        "type": recent_type
    })
    if(len(recents) > max_recents):
        difference = max_recents - len(recents)
        recents = recents[difference:(len(recents)-1)]
    return recents

def get_shows(shows_obj, script_prefix=""):
    SCRAPE_FOLDER = "{0}schedule-scrape-bbc".format(script_prefix)
    BASE_FANART_URL = "https://ichef.bbci.co.uk/images/ic/640x360/"
    if shows_obj["parsed"] != None:
        latest_parse = parser.parse(shows_obj["parsed"])
    else:
        latest_parse = None
    failed_files = shows_obj["failed_files"]
    shows = shows_obj["shows"]
    print("")
    print("Parsing {0}/*".format(SCRAPE_FOLDER))
    initial_latest_parse = latest_parse

    k = 0
    for schedule_folder in sorted(glob.glob("{0}/*".format(SCRAPE_FOLDER))):
        for json_file in sorted(glob.glob(schedule_folder+"/*.json")):
            json_file_date = parser.parse(json_file.rsplit('/')[-1][0:10])
            if(initial_latest_parse != None and json_file_date <= initial_latest_parse):
                continue
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

                    show_added_to_recents = False
                    if(not (show_title in shows)):
                        shows[show_title] = {
                            "title": show_title,
                            "pid": show_pid,
                            "image": show_image,
                            "season": {},
                            "show_merged": False,
                            "tvdb_merged": False,
                            "imdb_merged": False,
                            "moviedb_merged": False,
                            "fanart": [],
                            "poster": [],
                            "banner": [],
                            "rating": None,
                            "rating_count": None
                        }
                        shows_obj["recent"] = add_show_to_resents(shows_obj["recent"], show_title, "new_show")
                        show_added_to_recents = True
                    if(not (season_number in shows[show_title]["season"])):
                        shows[show_title]["season"][season_number] = {
                            "number": season_number,
                            "title": season_title,
                            "pid": season_pid,
                            "image": season_image,
                            "episode": {}
                        }
                        if(show_added_to_recents != True):
                            shows_obj["recent"] = add_show_to_resents(shows_obj["recent"], show_title, "new_season")

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
    if(k != 0):
        shows = resolve_repeats(shows)
    shows_obj["shows"] = shows
    shows_obj["parsed"] = latest_parse.strftime('%Y-%m-%d')
    shows_obj["failed_files"] = failed_files
    return shows_obj

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

def merge_shows_files(showsObj, script_prefix=""):
    shows = showsObj["shows"]
    SCRAPE_FOLDER = "{0}show-scrape-bbc".format(script_prefix)
    print("")
    print("Parsing {0}/*".format(SCRAPE_FOLDER))

    k = 0
    for show_key in shows:
        show = shows[show_key]
        if show["show_merged"] == True:
            continue
        k = k + 1
        if(k > 50):
            k = 0
            sys.stdout.write('.')
            sys.stdout.flush()
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
                for genre in show["genres"]:
                    if(not genre in showsObj["genres"]):
                        showsObj["genres"][genre] = []
                    for subgenre in show["sub-genres"]:
                        if(not subgenre in showsObj["genres"][genre]):
                            showsObj["genres"][genre].append(subgenre)
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
        show = shows[show_key]
        if show["tvdb_merged"] == True or show["type"] == "Films":
            continue
        k = k + 1
        if(k > 50):
            k = 0
            sys.stdout.write('.')
            sys.stdout.flush()
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

            if("banner" in tvdb_show and not util.emptyStr(tvdb_show["banner"])):
                show["banner"].append(BASE_FANART_URL+util.checkStr(tvdb_show["banner"]))

            if("fanart" in tvdb_show and not util.emptyStr(tvdb_show["fanart"])):
                show["fanart"].append(BASE_FANART_URL+util.checkStr(tvdb_show["fanart"]))

            if("poster" in tvdb_show and not util.emptyStr(tvdb_show["poster"])):
                show["poster"].append(BASE_FANART_URL+util.checkStr(tvdb_show["poster"]))

        else:
            show["rating"] = None
            show["rating_count"] = None
            show["tvdb_id"] = None
            print("")
            print("Missing pid file {0}".format(output_file))
    return shows

def merge_moviedb_files(shows, script_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-moviedb".format(script_prefix)
    print("")
    print("Parsing {0}/*".format(SCRAPE_FOLDER))

    k = 0
    for show_key in shows:
        show = shows[show_key]
        if show["moviedb_merged"] == True or show["type"] != "Films":
            continue
        k = k + 1
        if(k > 50):
            k = 0
            sys.stdout.write('.')
            sys.stdout.flush()
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        output_file = "{1}/{0}.json".format(pid,SCRAPE_FOLDER)
        if(pid and os.path.isfile(output_file)):
            try:
                input_file_handle = open(output_file, 'rb')
                moviedb_show = json.load(input_file_handle)
                input_file_handle.close()
                show["moviedb_merged"] = True
            except Exception as e:
                print("")
                print("JSON Load Failed: {0}".format(str(e)))
                moviedb_show = {}

            if("cast" in moviedb_show):
                show["actors"].extend(moviedb_show["cast"])

            if("id" in moviedb_show):
                show["moviedb_id"] = util.checkStr(moviedb_show["id"])
            else:
                show["moviedb_id"] = None

            if("backdrop" in moviedb_show and moviedb_show["backdrop"] != None):
                show["fanart"].append(util.checkStr(moviedb_show["backdrop"]))

            if("poster" in moviedb_show and moviedb_show["poster"] != None):
                show["poster"].append(util.checkStr(moviedb_show["poster"]))
        else:
            show["moviedb_id"] = None
            print("")
            print("Missing pid file {0}".format(output_file))
    return shows

def merge_imdb_files(shows, script_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-imdb".format(script_prefix)
    print("")
    print("Parsing {0}/*".format(SCRAPE_FOLDER))

    k = 0
    for show_key in shows:
        show = shows[show_key]
        if show["imdb_merged"] == True:
            continue
        if len(show["poster"]) > 0:
            continue
        k = k + 1
        if(k > 50):
            k = 0
            sys.stdout.write('.')
            sys.stdout.flush()
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        output_file = "{1}/{0}.json".format(pid,SCRAPE_FOLDER)
        if(pid and os.path.isfile(output_file)):
            try:
                input_file_handle = open(output_file, 'rb')
                imdb_show = json.load(input_file_handle)
                input_file_handle.close()
                show["imdb_merged"] = True
            except Exception as e:
                print("")
                print("JSON Load Failed: {0}".format(str(e)))
                imdb_show = {}

            if("id" in imdb_show):
                show["imdb_id"] = util.checkStr(imdb_show["imdb_id"])
            else:
                show["imdb_id"] = None

            if("cover_url" in imdb_show and imdb_show["cover_url"] != None):
                show["poster"].append(util.checkStr(imdb_show["cover_url"]))

        else:
            show["imdb_id"] = None
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

import util
from datetime import date, timedelta
from dateutil import parser
import os
from sets import Set

import sys
import glob
from bs4 import BeautifulSoup

SCRAPE_URL = "http://www.bbc.co.uk/"
#SCRAPE_URL = "http://open.live.bbc.co.uk/aps/"

def get_moviedb_show_download_list(shows,redo=False,scrape_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-moviedb".format(scrape_prefix)
    util.mkdir_p(SCRAPE_FOLDER)

    download_list = []
    seen = Set([])
    skipped = 0
    for show_key in shows:
        show = shows[show_key]
        if show["moviedb_merged"] == True:
            continue
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        if(pid and show["type"] == "Films"):
            if os.path.isfile("{0}/{1}.json".format(SCRAPE_FOLDER,pid)) and not redo:
                skipped = skipped + 1
            else:
                if not pid in seen:
                    download_list.append([show["title"], "{1}/{0}.json".format(pid,SCRAPE_FOLDER), "Saved "+str(pid) ])
                    seen.add(pid)
    print("Skipped: {0}".format(skipped))
    return download_list

def get_bbc_programmes_show_download_list(shows,redo=False,scrape_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-bbc".format(scrape_prefix)
    util.mkdir_p(SCRAPE_FOLDER)

    download_list = []
    seen = Set([])

    skipped = 0
    for show_key in shows:
        show = shows[show_key]
        if show["show_merged"] == True:
            continue
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        if(pid):
            if os.path.isfile("{0}/{1}.json".format(SCRAPE_FOLDER,pid)) and not redo:
                skipped = skipped + 1
            else:
                if not pid in seen:
                    download_list.append([SCRAPE_URL + "programmes/{0}.json".format(pid), "{1}/{0}.json".format(pid,SCRAPE_FOLDER), "Saved "+str(pid) ])
                    seen.add(pid)

    print("Skipped: {0}".format(skipped))
    return download_list

def get_tvdb_show_download_list(shows,redo=False,scrape_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-tvdb".format(scrape_prefix)
    util.mkdir_p(SCRAPE_FOLDER)

    download_list = []
    seen = Set([])
    skipped = 0
    for show_key in shows:
        show = shows[show_key]
        if show["tvdb_merged"] == True:
            continue
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        if(pid and show["type"] != "Films"):
            if os.path.isfile("{0}/{1}.json".format(SCRAPE_FOLDER,pid)) and not redo:
                skipped = skipped + 1
            else:
                if not pid in seen:
                    download_list.append([show["title"], "{1}/{0}.json".format(pid,SCRAPE_FOLDER), "Saved "+str(pid) ])
                    seen.add(pid)
    print("Skipped: {0}".format(skipped))
    return download_list

def get_imdb_show_download_list(shows,redo=False):
    SCRAPE_FOLDER = "show-scrape-imdb"
    util.mkdir_p(SCRAPE_FOLDER)

    download_list = []
    seen = Set([])
    skipped = 0
    for show_key in shows:
        show = shows[show_key]
        if show["imdb_merged"] == True:
            continue
        if len(show["poster"]) > 0:
            continue
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        if(pid):
            if os.path.isfile("{0}/{1}.json".format(SCRAPE_FOLDER,pid)) and not redo:
                skipped = skipped + 1
            else:
                if not pid in seen:
                    download_list.append([show["title"], "{1}/{0}.json".format(pid,SCRAPE_FOLDER), "Saved "+str(pid) ])
                    seen.add(pid)

    print("Skipped: {0}".format(skipped))
    return download_list

def get_bbc_programmes_schedule_download_list(redo=False, start_date = None, scrape_prefix=""):
    SCRAPE_FOLDER = "{0}schedule-scrape-bbc".format(scrape_prefix)
    util.mkdir_p(SCRAPE_FOLDER)

    if start_date == None:
        start_date = date(2007, 6, 30)
    else:
        start_date = parser.parse(start_date).date()
    end_date = date.today()
    start_date = start_date + timedelta(days=1)

    download_list = []

    for single_date in util.daterange(start_date, end_date):
        single_date_prev = (single_date - timedelta(days=1))
        single_date_next = (single_date + timedelta(days=1))
        year=single_date.strftime("%Y")
        scrape_date = single_date.strftime("%Y-%m-%d")
        scrape_date_prev = single_date_prev.strftime("%Y-%m-%d")
        scrape_date_next = single_date_next.strftime("%Y-%m-%d")
        scrape_date_url_format = single_date.strftime("%Y/%m/%d")
        scrape_date_prev_url_format = single_date_prev.strftime("%Y/%m/%d")
        scrape_date_next_url_format = single_date_next.strftime("%Y/%m/%d")
        util.mkdir_p("{1}/{0}".format(year,SCRAPE_FOLDER))
        if os.path.isfile("{2}/{0}/{1}-bbcone.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCOne): %Y-%m-%d"))
        else:
            if os.path.isfile("{2}/{0}/{1}-bbcone.html".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
                print(single_date.strftime("Skipped (BBCOne): %Y-%m-%d"))
            else:
                download_list.append([SCRAPE_URL + "schedules/p00fzl6p/{0}".format(scrape_date_url_format), "{2}/{0}/{1}-bbcone.html".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCOne): %Y-%m-%d")])
            if os.path.isfile("{2}/{0}/{1}-bbcone.html".format(year,scrape_date_prev,SCRAPE_FOLDER)) and not redo:
                pass
            else:
                download_list.append([SCRAPE_URL + "schedules/p00fzl6p/{0}".format(scrape_date_prev_url_format), "{2}/{0}/{1}-bbcone.html".format(year,scrape_date_prev,SCRAPE_FOLDER), single_date_prev.strftime("Saved (BBCOne): %Y-%m-%d")])
            if os.path.isfile("{2}/{0}/{1}-bbcone.html".format(year,scrape_date_next,SCRAPE_FOLDER)) and not redo:
                pass
            else:
                download_list.append([SCRAPE_URL + "schedules/p00fzl6p/{0}".format(scrape_date_next_url_format), "{2}/{0}/{1}-bbcone.html".format(year,scrape_date_next,SCRAPE_FOLDER), single_date_next.strftime("Saved (BBCOne): %Y-%m-%d")])


        if os.path.isfile("{2}/{0}/{1}-bbctwo.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCTwo): %Y-%m-%d"))
        else:
            if os.path.isfile("{2}/{0}/{1}-bbctwo.html".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
                print(single_date.strftime("Skipped (BBCTwo): %Y-%m-%d"))
            else:
                download_list.append([SCRAPE_URL+"schedules/p00fzl97/{0}".format(scrape_date_url_format), "{2}/{0}/{1}-bbctwo.html".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCTwo): %Y-%m-%d")])
            if os.path.isfile("{2}/{0}/{1}-bbctwo.html".format(year,scrape_date_prev,SCRAPE_FOLDER)) and not redo:
                pass
            else:
                download_list.append([SCRAPE_URL + "schedules/p00fzl97/{0}".format(scrape_date_prev_url_format), "{2}/{0}/{1}-bbctwo.html".format(year,scrape_date_prev,SCRAPE_FOLDER), single_date_prev.strftime("Saved (BBCTwo): %Y-%m-%d")])
            if os.path.isfile("{2}/{0}/{1}-bbctwo.html".format(year,scrape_date_next,SCRAPE_FOLDER)) and not redo:
                pass
            else:
                download_list.append([SCRAPE_URL + "schedules/p00fzl97/{0}".format(scrape_date_next_url_format), "{2}/{0}/{1}-bbctwo.html".format(year,scrape_date_next,SCRAPE_FOLDER), single_date_next.strftime("Saved (BBCTwo): %Y-%m-%d")])

        if os.path.isfile("{2}/{0}/{1}-bbcthree.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCThree): %Y-%m-%d"))
        else:
            if single_date <  date(2016, 4, 1):
                download_list.append([SCRAPE_URL+"bbcthree/programmes/schedules/{0}".format(scrape_date_url_format), "{2}/{0}/{1}-bbcthree.html".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCThree): %Y-%m-%d")])

        if os.path.isfile("{2}/{0}/{1}-bbcfour.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCFour): %Y-%m-%d"))
        else:
            if os.path.isfile("{2}/{0}/{1}-bbcfour.html".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
                print(single_date.strftime("Skipped (BBCFour): %Y-%m-%d"))
            else:
                download_list.append([SCRAPE_URL+"schedules/p00fzl6b/{0}".format(scrape_date_url_format), "{2}/{0}/{1}-bbcfour.html".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCFour): %Y-%m-%d")])
            if os.path.isfile("{2}/{0}/{1}-bbcfour.html".format(year,scrape_date_prev,SCRAPE_FOLDER)) and not redo:
                pass
            else:
                download_list.append([SCRAPE_URL + "schedules/p00fzl6b/{0}".format(scrape_date_prev_url_format), "{2}/{0}/{1}-bbcfour.html".format(year,scrape_date_prev,SCRAPE_FOLDER), single_date_prev.strftime("Saved (BBCFour): %Y-%m-%d")])
            if os.path.isfile("{2}/{0}/{1}-bbcfour.html".format(year,scrape_date_next,SCRAPE_FOLDER)) and not redo:
                pass
            else:
                download_list.append([SCRAPE_URL + "schedules/p00fzl6b/{0}".format(scrape_date_next_url_format), "{2}/{0}/{1}-bbcfour.html".format(year,scrape_date_next,SCRAPE_FOLDER), single_date_next.strftime("Saved (BBCFour): %Y-%m-%d")])

    return download_list


def get_schedule_items(start_date = None, script_prefix=""):
    SCRAPE_FOLDER = "{0}schedule-scrape-bbc".format(script_prefix)
    SAVE_FOLDER = "{0}episode-scrape-bbc".format(script_prefix)
    util.mkdir_p(SAVE_FOLDER)
    # test = "<html><body><div class=\"test1 test2 test3\"></div></body></html>"
    # bs = BeautifulSoup(test)
    # print(len(bs.find_all("div", class_ = "test1" )))

    if start_date != None:
        latest_parse = parser.parse(start_date)
    else:
        latest_parse = None

    k = 0
    schedule_item_pid_list = []
    for schedule_folder in sorted(glob.glob("{0}/*".format(SCRAPE_FOLDER))):
        for html_file in sorted(glob.glob(schedule_folder+"/*.html")):
            k = k + 1
            if(k > 50):
                k = 0
                sys.stdout.write('.')
                sys.stdout.flush()
            html_file_date = parser.parse(html_file.rsplit('/')[-1][0:10])
            if(latest_parse != None and html_file_date <= latest_parse):
                continue
            if(os.path.isfile(html_file.replace("html","json"))):
                continue
            bs = BeautifulSoup(open(html_file), "lxml")
            schedule_items = bs.find_all("div", class_="broadcast")
            for schedule_item in schedule_items:
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
                        if((schedule_item_pid[0] == "b" or schedule_item_pid[0] == "p" or schedule_item_pid[0] == "m") and len(schedule_item_pid) == 8):
                            if(not os.path.isfile("{0}/{1}.json".format(SAVE_FOLDER,schedule_item_pid))):
                                schedule_item_pid_list.append([SCRAPE_URL+"programmes/{0}.json".format(schedule_item_pid), "{0}/{1}.json".format(SAVE_FOLDER,schedule_item_pid), "Saved: {0}".format(schedule_item_pid)])
                            pid_found = True
                            break
                    if(pid_found == False):
                        print(schedule_item)
                        raise ValueError("Invalid PID!")

    return schedule_item_pid_list

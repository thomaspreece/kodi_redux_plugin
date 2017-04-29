import util
from datetime import date, timedelta
from dateutil import parser
import os
from sets import Set

SCRAPE_URL = "http://www.bbc.co.uk/"
#SCRAPE_URL = "http://open.live.bbc.co.uk/aps/"

def get_bbc_programmes_show_download_list(shows,redo=False,scrape_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-bbc".format(scrape_prefix)
    util.mkdir_p(SCRAPE_FOLDER)

    download_list = []
    seen = Set([])

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
                print("Skipped: "+str(pid))
            else:
                if not pid in seen:
                    download_list.append([SCRAPE_URL + "programmes/{0}.json".format(pid), "{1}/{0}.json".format(pid,SCRAPE_FOLDER), "Saved "+str(pid) ])
                    seen.add(pid)

    return download_list

def get_tvdb_show_download_list(shows,redo=False,scrape_prefix=""):
    SCRAPE_FOLDER = "{0}show-scrape-tvdb".format(scrape_prefix)
    util.mkdir_p(SCRAPE_FOLDER)

    download_list = []
    seen = Set([])
    for show_key in shows:
        show = shows[show_key]
        if show["tvdb_merged"] == True:
            continue
        pid = show["pid"]
        if(not pid):
            pid = show["season"].values()[0]["pid"]
            if(not pid):
                pid = show["season"].values()[0]["episode"].values()[0]["pid"]

        if(pid and show["type"] != "FILM"):
            if os.path.isfile("{0}/{1}.json".format(SCRAPE_FOLDER,pid)) and not redo:
                print("Skipped: "+str(pid))
            else:
                if not pid in seen:
                    download_list.append([show["title"], "{1}/{0}.json".format(pid,SCRAPE_FOLDER), "Saved "+str(pid) ])
                    seen.add(pid)

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
        year=single_date.strftime("%Y")
        scrape_date = single_date.strftime("%Y-%m-%d")
        scrape_date_url_format = single_date.strftime("%Y/%m/%d")
        util.mkdir_p("{1}/{0}".format(year,SCRAPE_FOLDER))
        if os.path.isfile("{2}/{0}/{1}-bbcone.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCOne): %Y-%m-%d"))
        else:
            download_list.append([SCRAPE_URL + "bbcone/programmes/schedules/london/{0}.json".format(scrape_date_url_format), "{2}/{0}/{1}-bbcone.json".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCOne): %Y-%m-%d")])

        if os.path.isfile("{2}/{0}/{1}-bbctwo.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCTwo): %Y-%m-%d"))
        else:
            download_list.append([SCRAPE_URL+"bbctwo/programmes/schedules/england/{0}.json".format(scrape_date_url_format), "{2}/{0}/{1}-bbctwo.json".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCTwo): %Y-%m-%d")])
        if os.path.isfile("{2}/{0}/{1}-bbcthree.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCThree): %Y-%m-%d"))
        else:
            if single_date <  date(2016, 4, 1):
                download_list.append([SCRAPE_URL+"bbcthree/programmes/schedules/{0}.json".format(scrape_date_url_format), "{2}/{0}/{1}-bbcthree.json".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCThree): %Y-%m-%d")])

        if os.path.isfile("{2}/{0}/{1}-bbcfour.json".format(year,scrape_date,SCRAPE_FOLDER)) and not redo:
            print(single_date.strftime("Skipped (BBCFour): %Y-%m-%d"))
        else:
            download_list.append([SCRAPE_URL+"bbcfour/programmes/schedules/{0}.json".format(scrape_date_url_format), "{2}/{0}/{1}-bbcfour.json".format(year,scrape_date,SCRAPE_FOLDER), single_date.strftime("Saved (BBCFour): %Y-%m-%d")])

    return download_list

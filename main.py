# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcaddon
import xbmcgui
import xbmcplugin
import shutil
import datetime
import time

from lib.util import mkdir_p, removeInvalidFilesystemChars
from lib.database_schema import Show, Genre, RecentShows, ShowGenre, SubGenre, GenreToSubGenre, ShowSubGenre, Actor, ShowActor, Year, LastUpdate, DBVersion, BaseModel
from lib.user_database_schema import UserFavouriteShow, UserWatchedStatus, UserReduxResolve, UserReduxFile, UserLastUpdate, UserDBVersion, UserBaseModel
from lib.database_functions import convert_shows_to_json, convert_show_to_json, populate_database, populate_user_database, create_database, init_database, test_connection, get_userdb_version, get_showdb_version, update_show_watched_status

import json

import os
import re
try:
   import cPickle as pickle
except:
   import pickle

from lib import sort_shows
from lib import resolve_redux
from lib import util

import traceback

from lib import xbmc_util

import xbmc

__ShowDBVersion__ = get_showdb_version()
__UserDBVersion__ = get_userdb_version()

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

__profile__ = xbmc_util.get_user_dir()

DEFAULT_FANART = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/fanart.jpg')
DEFAULT_ICON = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/lists.png')
DEFAULT_ICON_SHOW = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/no_icon.png')
SEARCH_ICON = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/search.png')

DOWNLOAD_SCRIPT  = xbmc.translatePath('special://home/addons/plugin.video.redux/download.py')
UPDATE_SCRIPT  = xbmc.translatePath('special://home/addons/plugin.video.redux/scrape-update.py')

MAINMENU = [
    {'name':'In Progress' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Favourites' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Recently Added' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'View By Category' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Search', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Update Shows Database',
        'thumb': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/update.png'),
        'fanart': DEFAULT_FANART}
    ]

RECENTMENU = [
    {'name':'Show All' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Show New Shows Only' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Show New Seasons Only' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART}
]

SEARCHMENU = [
    {'name':'Search (By Name)', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Search (By Name, Desc, Actors)', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Advanced Search', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART}
]

CATEGORIES = [
    {'name':'All' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Channels' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Genres' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Sub-Genres' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Years' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Type' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART}
    ]

CHANNELS = [
    {'name':'BBC One', 'thumb': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_one.png'),
                        'fanart': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_one_ident.jpg')},
    {'name': 'BBC Two','thumb': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_two.png'),
                        'fanart': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_two_ident.jpg')},
    {'name': 'BBC Three','thumb': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_three.png'),
                        'fanart': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_three_ident.jpg')},
    {'name': 'BBC Four','thumb': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_four.png'),
                        'fanart': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_four_ident.jpg')},
    {'name': 'Films','thumb': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_films.png'),
                    'fanart': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/bbc_films_ident.jpg')}
    ]

class MyLogger(object):
    def debug(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

def get_url_query(**kwargs):
    return '?{0}'.format(urlencode(kwargs))

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def list_search():
    """
    Create the list of video categories in the Kodi interface.
    """

    # Iterate through categories
    for category in range(len(SEARCHMENU)):
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=SEARCHMENU[category]['name'])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': SEARCHMENU[category]['thumb'],
                          'icon': SEARCHMENU[category]['thumb'],
                          'fanart': SEARCHMENU[category]['fanart']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': SEARCHMENU[category]['name'], 'genre': SEARCHMENU[category]['name']})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='search', selection=SEARCHMENU[category]['name'])
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_parental_controls():
    parental_file = "{0}/parental.json".format(__profile__)
    if(os.path.isfile(parental_file)):
        list_item = xbmcgui.ListItem(label="Remove PIN")
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        list_item.setInfo('video', {'title': "Remove PIN", 'genre': "Parental Controls"})
        url = get_url(action='parental', selection="Remove PIN")
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        list_item = xbmcgui.ListItem(label="Change PIN")
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        list_item.setInfo('video', {'title': "Change PIN", 'genre': "Parental Controls"})
        url = get_url(action='parental', selection="Change PIN")
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    else:
        list_item = xbmcgui.ListItem(label="Add PIN")
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        list_item.setInfo('video', {'title': "Add PIN", 'genre': "Parental Controls"})
        url = get_url(action='parental', selection="Add PIN")
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(_handle)

def list_menu():
    """
    Create the list of video categories in the Kodi interface.
    """

    # Iterate through categories
    for category in range(len(MAINMENU)):
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=MAINMENU[category]['name'])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': MAINMENU[category]['thumb'],
                          'icon': MAINMENU[category]['thumb'],
                          'fanart': MAINMENU[category]['fanart']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': MAINMENU[category]['name'], 'genre': MAINMENU[category]['name']})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='menu', selection=MAINMENU[category]['name'])
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    show_parental_controls = xbmcaddon.Addon('plugin.video.redux').getSetting("show_parental_controls")
    if(show_parental_controls == "true"):
        list_item = xbmcgui.ListItem(label="Parental Controls")
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        list_item.setInfo('video', {'title': "Parental Controls", 'genre': "Parental Controls"})
        url = get_url(action='menu', selection="Parental Controls")
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_recently_added_shows_categories():
    for category in range(len(RECENTMENU)):
        list_item = xbmcgui.ListItem(label=RECENTMENU[category]['name'])

        list_item.setArt({'thumb': RECENTMENU[category]['thumb'],
                          'icon': RECENTMENU[category]['thumb'],
                          'fanart': RECENTMENU[category]['fanart']})

        list_item.setInfo('video', {'title': RECENTMENU[category]['name'], 'genre': RECENTMENU[category]['name']})

        url = get_url(action='show_listing', recent=RECENTMENU[category]['name'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """

    # Iterate through categories
    for category in range(len(CATEGORIES)):
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=CATEGORIES[category]['name'])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': CATEGORIES[category]['thumb'],
                          'icon': CATEGORIES[category]['thumb'],
                          'fanart': CATEGORIES[category]['fanart']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': CATEGORIES[category]['name'], 'genre': CATEGORIES[category]['name']})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=CATEGORIES[category]['name'])
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_years():
    all_year_shows = Year.select().order_by(Year.name)
    """
    Create the list of video categories in the Kodi interface.
    """
    i = 0
    # Iterate through categories
    for year_record in all_year_shows:
        year = year_record.name
        i += 1
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=year)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        #list_item.setArt({'thumb': CHANNELS[channel]['thumb'],
        #                  'icon': CHANNELS[channel]['thumb']})
        #                  'fanart': CHANNELS[channel]['thumb']})
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': year})
        list_item.setInfo('video', {'genre': year})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='show_listing', year=year)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_TITLE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_types():
    all_types = ["Normal", "Miniseries"]
    """
    Create the list of video categories in the Kodi interface.
    """
    i = 0
    # Iterate through categories
    for type_record in all_types:
        type = type_record
        i += 1
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=type)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        #list_item.setArt({'thumb': CHANNELS[channel]['thumb'],
        #                  'icon': CHANNELS[channel]['thumb']})
        #                  'fanart': CHANNELS[channel]['thumb']})
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': type})
        list_item.setInfo('video', {'genre': type})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='show_listing', type=type)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_TITLE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_subgenres():
    all_sub_genre_shows = SubGenre.select().order_by(SubGenre.name)

    """
    Create the list of video categories in the Kodi interface.
    """
    i = 0
    # Iterate through categories
    for genre_record in all_sub_genre_shows:
        genre = genre_record.name
        i += 1
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=genre)
        list_item.setInfo('video', {'title': genre})
        list_item.setInfo('video', {'genre': genre})
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        url = get_url(action='show_listing', subgenre=genre)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(_handle)



def list_genres():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    all_genre_shows = Genre.select().order_by(Genre.name)

    """
    Create the list of video categories in the Kodi interface.
    """
    i = 0
    # Iterate through categories
    for genre_record in all_genre_shows:
        genre = genre_record.name
        i += 1
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=genre)
        list_item.setInfo('video', {'title': genre})
        list_item.setInfo('video', {'genre': genre})
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        url = get_url(action='show_subgenre_of_genre_listing', genre=genre)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(_handle)

def list_subgenres_of_genre(genre):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    #subgenres = Genre.select(SubGenre).where(Genre.name == genre).join(GenreToSubGenre).join(SubGenre).order_by(SubGenre.name)
    subgenres = SubGenre.select().join(GenreToSubGenre).join(Genre).where(Genre.name == genre).order_by(SubGenre.name)

    """
    Create the list of video categories in the Kodi interface.
    """
    list_item = xbmcgui.ListItem(label="Show all from: {0}".format(genre))
    list_item.setInfo('video', {'title': genre})
    list_item.setInfo('video', {'genre': genre})
    list_item.setArt({'thumb': DEFAULT_ICON,
                      'icon': DEFAULT_ICON,
                      'fanart': DEFAULT_FANART})
    url = get_url(action='show_listing', genre=genre)
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    i = 0
    # Iterate through categories
    for subgenre_record in subgenres:
        subgenre = subgenre_record.name
        i += 1
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label="{0} ({1})".format(subgenre,genre))
        list_item.setInfo('video', {'title': subgenre})
        list_item.setInfo('video', {'genre': subgenre})
        list_item.setArt({'thumb': DEFAULT_ICON,
                          'icon': DEFAULT_ICON,
                          'fanart': DEFAULT_FANART})
        url = get_url(action='show_listing', genre=genre, subgenre=subgenre)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(_handle)


def list_channels():
    """
    Create the list of video categories in the Kodi interface.
    """
    i = 0
    # Iterate through categories
    for channel in range(len(CHANNELS)):
        i += 1
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=CHANNELS[channel]['name'])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': CHANNELS[channel]['thumb'],
                          'icon': CHANNELS[channel]['thumb'],
                          'fanart': CHANNELS[channel]['fanart']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': CHANNELS[channel]['name']})
        list_item.setInfo('video', {'genre': CHANNELS[channel]['name']})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='show_listing', channel=CHANNELS[channel]['name'])
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_shows_all():
    # script_dir = os.path.dirname(os.path.realpath(__file__))
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Retrieving Over 10,000 shows. ')
    pDialog.update(0,"Please be patient...")
    shows_records = Show.select().order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        if(shows[show]["year"]):
            list_item = xbmcgui.ListItem(label=show+" ("+shows[show]["year"]+")")
        else:
            list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_in_progress_shows():
    in_progress_shows_list = get_in_progress_shows_list()

    shows_records = Show.select().where(Show.title << in_progress_shows_list).order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False

        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_favourite_shows():
    favourite_shows_list = get_favourite_shows_list()

    shows_records = Show.select().where(Show.title << favourite_shows_list).order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        favourite = True
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_shows_by_year(year):
    shows_records = Show.select().where(Show.year == year).order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_shows_by_type(type):
    shows_records = Show.select().where(Show.show_type == type).order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_shows_by_genre(genre):
    shows_records = Show.select().join(ShowGenre).join(Genre).where(Genre.name == genre).order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()
    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_shows_by_subgenre(genre):
    shows_records = Show.select().join(ShowSubGenre).join(SubGenre).where(SubGenre.name == genre).order_by(Show.title)
    shows = convert_shows_to_json(shows_records)
    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_shows_by_genre_with_subgenre(genre, subgenre):
    shows_records = Show.select().join(ShowGenre).join(Genre).where(Genre.name == genre)
    shows_records = shows_records.switch(Show).join(ShowSubGenre).join(SubGenre).where(SubGenre.name == subgenre).order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_recently_added_shows(recenttype):
    if (recenttype == 'Show All'):
        shows_records = Show.select().join(RecentShows).order_by(Show.title)
    elif (recenttype == 'Show New Shows Only'):
        shows_records = Show.select().join(RecentShows).where(RecentShows.recenttype == 1).order_by(Show.title)
    elif (recenttype == 'Show New Seasons Only'):
        shows_records = Show.select().join(RecentShows).where(RecentShows.recenttype == 2).order_by(Show.title)
    else:
        raise ValueError("Invalid Recent Type")

    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        list_item = xbmcgui.ListItem(label=show)
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)
        #list_item.setInfo('video', {'title': '(New Season) {0}'.format(shows[show]["title"].encode("utf-8"))})

        url = get_url(action='season_listing', show=show.encode("utf-8"))
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_shows_by_channel(channel):
    if channel == "BBC One":
        shows_records = Show.select().where(Show.bbc1 == True).order_by(Show.title)
    elif channel == "BBC Two":
        shows_records = Show.select().where(Show.bbc2 == True).order_by(Show.title)
    elif channel == "BBC Three":
        shows_records = Show.select().where(Show.bbc3 == True).order_by(Show.title)
    elif channel == "BBC Four":
        shows_records = Show.select().where(Show.bbc4 == True).order_by(Show.title)
    elif channel == "Films":
        shows_records = Show.select().where(Show.film == True).order_by(Show.title)

    shows = convert_shows_to_json(shows_records)
    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        if(shows[show]["year"]):
            list_item = xbmcgui.ListItem(label=show+" ("+shows[show]["year"]+")")
        else:
            list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.

        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False
        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_seasons(show_name):
    show_record = Show.select().where(Show.title == show_name).get()
    show = convert_show_to_json(show_record)

    watchedseasons = UserWatchedStatus.select().where(
        (UserWatchedStatus.show == show_name) &
        (UserWatchedStatus.status_is_season == True)
    )

    listings = []

    if len(show['season']) == 1:
        list_episodes(show_name,next(iter(show['season'])))
        return
    for season in show['season']:
        watched = False
        for watchedseason in watchedseasons:
            if(watchedseason.season == season):
                watched = watchedseason.watched

        if(show['season'][season]["title"]):
            title = "{0} ({1})".format(show['season'][season]["title"].encode("utf-8"),season)
        else:
            title = "Untitled ({0})".format(season)
        list_item = xbmcgui.ListItem(label=title)

        set_season_metadata(show, season, list_item, watched)

        url = get_url(action='episode_listing', show=show_name, season=season)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        listings.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listings, len(listings))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

    shows = None

def list_episodes(show_name, season):
    show_record = Show.select().where(Show.title == show_name).get()
    show = convert_show_to_json(show_record)

    watchedepisodes = UserWatchedStatus.select().where(
        (UserWatchedStatus.show == show_name) &
        (UserWatchedStatus.season == season) &
        (UserWatchedStatus.status_is_episode == True)
    )

    listings = []
    for episode in show['season'][season]['episode']:
        watched = False
        for watchedepisode in watchedepisodes:
            if(watchedepisode.episode == episode):
                watched = watchedepisode.watched

        if(show['season'][season]['episode'][episode]["title"]):
            title = "E{0} {1}".format(episode,show['season'][season]['episode'][episode]["title"].encode("utf-8"))
        else:
            title = "E{0}".format(episode)
        list_item = xbmcgui.ListItem(label=title)
        list_item.setProperty('IsPlayable', 'true')

        list_item = set_episode_metadata(show,season,episode,list_item,watched)
        url = get_url(action='play_episode', show=show_name.encode("utf-8"), season=season, episode=episode)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = False

        listings.append((url, list_item, is_folder))
        # Add our item to the Kodi virtual folder listing.

    xbmcplugin.addDirectoryItems(_handle, listings, len(listings))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_episode(show, season, episode, format_override):
    loginfile = '{0}/reduxLogin.txt'.format(__profile__)

    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Playing Episode', 'Loading Shows...')

    show_record = Show.select().where(Show.title == show).get()
    show = convert_show_to_json(show_record)

    # TODO: Fix This Download
    #download = xbmcaddon.Addon('plugin.video.redux').getSetting("save_episode_stream")
    download = False

    download_folder = ""
    download_filename = ""
    if(download):
        # Pass URL to uGet
        download_path = ""
        if(show["film"]):
            download_path = xbmcaddon.Addon('plugin.video.redux').getSetting("movie_download_location")
        else:
            download_path = xbmcaddon.Addon('plugin.video.redux').getSetting("tvshow_download_location")

        if(len(download_path) == 0 or (not os.path.exists(download_path))):
            xbmcgui.Dialog().ok('Playing Episode', "Download path doesn't exist.", " Please setup tvshow_download_location and movie_download_location correctly in Plugin Settings")
            return

        download_folder = os.path.join(
            download_path,
            removeInvalidFilesystemChars(show["title"]),
            removeInvalidFilesystemChars(show['season'][season]["title"])
        )
        try:
            mkdir_p(download_folder)
        except:
            xbmcgui.Dialog().ok('Playing Episode', "Could not create path: {0}".format(download_folder))
            return

        download_filename = "S{0}E{1}-{2}.mp4".format(season,episode,show['season'][season]['episode'][episode]["title"])

    pDialog.update(25,"Contacting Redux...")

    redux_account = resolve_redux.ReduxAccount(loginfile)
    redux_token = redux_account.checkAndGetToken()
    print(redux_token)
    if(redux_token == ""):
        dialog = xbmcgui.Dialog()
        dialog.ok("No Redux Token")
        return

    redux_ref_rows = UserReduxResolve.select().where(
        (UserReduxResolve.show == show["title"]) &
        (UserReduxResolve.season == season) &
        (UserReduxResolve.episode == episode)
    )

    if(len(redux_ref_rows) > 0):
        ref = redux_ref_rows[0].diskref
        error = 0
    else:
        pDialog.update(50,"Contacting Redux... Done","Getting Disc Ref...")
        # Needs to Check that a h264 version is available and also check that a non regions version is available
        [error,ref] = resolve_redux.resolve_episode_ref(redux_token, show, season, episode)
        print([error,ref])
        if (error > -1):
            UserReduxResolve(
                show=show["title"],
                season=season,
                episode=episode,
                diskref=ref
            ).save()

    pDialog.update(75,"Contacting Redux... Done","Getting Disc Ref... Done","Resolving to URL...")

    if (error < 0):
        xbmcgui.Dialog().ok('Playing Episode', "Could not get disc reference from Redux")
        return

    urls = resolve_redux.resolve_episode_url(redux_token, ref)
    for key in urls.keys():
        UserReduxFile(
            show=show["title"],
            season=season,
            episode=episode,
            url=urls[key],
            encoding=key,
            time=datetime.datetime.now()
        ).save()

    print(urls)

    if urls == None:
        xbmcgui.Dialog().ok('Playing Episode', "Could not resolve disc reference from Redux")
        return
    else:
        print("URLs: {0}".format(urls))
        pDialog.update(90,"Contacting Redux... Done","Getting Disc Ref... Done","Resolving to URL... Done")

    if(format_override == True):
        play = xbmcgui.Dialog().select("Which format should I play?", urls.keys(), useDetails=True)
        if (play < 0 ):
            return
        else:
            url = urls[urls.keys()[play]]
    else:
        requested_format_setting = xbmcaddon.Addon('plugin.video.redux').getSetting("format")
        requested_format = xbmc_util.convert_format(requested_format_setting)
        if (requested_format in urls):
            url = urls[requested_format]
        else:
            if(len(urls.keys()) == 1):
                play_original = xbmcgui.Dialog().yesno("Playing Episode", "Cannot find a version of episode in {0}. Play 'Original stream' format instead?".format(requested_format_setting))
                if(play_original):
                    url = urls["ts"]
                else:
                    return
            else:
                play = xbmcgui.Dialog().select("Cannot find a version of episode in {0}. Play another format instead?".format(requested_format_setting), urls.keys(), useDetails=True)
                if (play < 0 ):
                    return
                else:
                    url = urls[urls.keys()[play]]


    if(download):
        command = 'uget "{0}"  --folder="{1}" --filename="{2}" --quiet'.format(
            url,
            removeInvalidFilesystemChars(download_folder),
            removeInvalidFilesystemChars(download_filename),
        )
        new_url = os.path.join(download_folder, download_filename)
        print(command)
        pDialog.update(91,"Starting download with uGet...")
        os.system(command)
        pDialog.update(92,"Starting download with uGet... Done", "Waiting for uGet to start download...")

        # Wait for uGet to start streaming file
        i = 1
        while True:
            if(os.path.isfile(new_url)):
                time.sleep(2)
                break
            time.sleep(1)
            pDialog.update(95,"Starting download with uGet... Done", "Waiting for uGet to start download... timeout in {0}".format(31-i))
            i += 1
            if(i > 30):
                xbmcgui.Dialog().ok('Playing Episode', "Timout - uGet has not created the expected file at {0}".format(new_url))
                return

        pDialog.close()
        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=new_url)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
        pass
    else:
        pDialog.close()
        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=url)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def set_season_metadata(show, season, list_item, watched = False):
    show_season = show["season"][season]
    if(show_season["title"]):
        title = "{0} ({1})".format(show_season["title"].encode("utf-8"),season)
    else:
        title = "Untitled (Series {0})".format(season)

    if len(show["poster"]) > 0:
        list_item.setArt({'thumb': show["poster"][0], 'icon': show["poster"][0]})
        list_item.setArt({'poster': show["poster"][0]})
    else:
        list_item.setArt({'thumb': DEFAULT_ICON_SHOW, 'icon': DEFAULT_ICON_SHOW})

    if len(show["fanart"]) > 0:
        list_item.setArt({'fanart': show["fanart"][0], 'landscape': show["fanart"][0]})
    else:
        list_item.setArt({'fanart': DEFAULT_FANART, 'landscape': DEFAULT_FANART})

    if len(show["banner"]) > 0:
        list_item.setArt({'banner': show["banner"][0]})

    contextMenuItems = [
        ("(Redux) Download via uGet",'XBMC.RunPlugin(%s?action=download&download_type=uget&show=%s&season=%s)' % (sys.argv[0], show["title"], season)),
        ("(Redux) Export Download List",'XBMC.RunPlugin(%s?action=download&download_type=list&show=%s&season=%s)' % (sys.argv[0], show["title"], season))
    ]

    if (watched):
        contextMenuItems.append(("(Redux) Mark Unwatched", 'XBMC.RunPlugin(%s?action=watched_mark&show=%s&watched=False&season=%s)' % (sys.argv[0], show["title"].encode("utf-8"), season)))
    else:
        contextMenuItems.append(("(Redux) Mark Watched", 'XBMC.RunPlugin(%s?action=watched_mark&show=%s&watched=True&season=%s)' % (sys.argv[0], show["title"].encode("utf-8"), season)))

    list_item.addContextMenuItems(contextMenuItems)

    list_item.setInfo('video', {'title': title})
    if(len(show["genres"]) > 0):
        genre_string = ""
        for gen in range(len(show["genres"])):
            genre_string += "/"+show["genres"][gen]
        genre_string = genre_string[1:]
        if(len(show["sub-genres"]) > 0):
            genre_string += " ("
            for gen in range(len(show["sub-genres"])):
                genre_string += show["sub-genres"][gen]+"/"
            genre_string = genre_string[:-1]
            genre_string += ")"

        list_item.setInfo('video', {'genre': genre_string.encode("utf-8")})
    list_item.setInfo('video', {'rating': show["rating"]})
    list_item.setInfo('video', {'plot': show["summary"].encode("utf-8")})
    list_item.setInfo('video', {'premiered': show["premier"]})
    list_item.setInfo('video', {'year': show["year"]})
    list_item.setInfo('video', {'cast': show["actors"]})
    if(watched):
        list_item.setInfo('video', {'playcount': 1})
        list_item.setInfo('video', {'overlay': 5}) # watched overlay
    else:
        list_item.setInfo('video', {'playcount': 0})
        list_item.setInfo('video', {'overlay': 4}) # unwatched overlay

    list_item.setInfo('video', {'season': season})
    list_item.setInfo('video', {'mediatype': "season"})
    list_item.setInfo('video', {'tvshowtitle': show["title"].encode("utf-8")})

    return list_item

def set_episode_metadata(show,season,episode,list_item, watched = False):
    show_episode = show["season"][season]["episode"][episode]
    if(show_episode["title"]):
        title = "E{0} - {1}".format(episode,show_episode["title"].encode("utf-8"))
    else:
        title = "E{0}".format(episode)

    if False:#show["season"][season]["episode"][episode]["image"] != None:
        image = show["season"][season]["episode"][episode]["image"]
        list_item.setArt({'thumb': image, 'icon': image})
    else:
        if len(show["poster"]) > 0:
            list_item.setArt({'thumb': show["poster"][0], 'icon': show["poster"][0]})
            list_item.setArt({'poster': show["poster"][0]})
        else:
            list_item.setArt({'thumb': DEFAULT_ICON_SHOW, 'icon': DEFAULT_ICON_SHOW})

    if len(show["fanart"]) > 0:
        list_item.setArt({'fanart': show["fanart"][0], 'landscape': show["fanart"][0]})
    else:
        list_item.setArt({'fanart': DEFAULT_FANART, 'landscape': DEFAULT_FANART})

    if len(show["banner"]) > 0:
        list_item.setArt({'banner': show["banner"][0]})

    contextMenuItems = [
        # TODO: Figure out why this doesn't work :(
        #("(Redux) Play - Choose Format",'XBMC.RunPlugin(%s?action=play_episode&show=%s&season=%s&episode=%s&format=True)' % (sys.argv[0], show["title"], season ,episode)),
        ("(Redux) Download via uGet",'XBMC.RunPlugin(%s?action=download&download_type=uget&show=%s&season=%s&episode=%s)' % (sys.argv[0], show["title"], season ,episode)),
        ("(Redux) Export Download List",'XBMC.RunPlugin(%s?action=download&download_type=list&show=%s&season=%s&episode=%s)' % (sys.argv[0], show["title"], season ,episode))
    ]

    if(watched):
        contextMenuItems.append(("(Redux) Mark Unwatched", 'XBMC.RunPlugin(%s?action=watched_mark&show=%s&watched=False&season=%s&episode=%s)' % (sys.argv[0], show["title"].encode("utf-8"), season, episode)))
    else:
        contextMenuItems.append(("(Redux) Mark Watched", 'XBMC.RunPlugin(%s?action=watched_mark&show=%s&watched=True&season=%s&episode=%s)' % (sys.argv[0], show["title"].encode("utf-8"), season, episode)))

    list_item.addContextMenuItems(contextMenuItems)

    list_item.setInfo('video', {'title': title})
    if(len(show["genres"]) > 0):
        genre_string = ""
        for gen in range(len(show["genres"])):
            genre_string += "/"+show["genres"][gen]
        genre_string = genre_string[1:]
        if(len(show["sub-genres"]) > 0):
            genre_string += " ("
            for gen in range(len(show["sub-genres"])):
                genre_string += show["sub-genres"][gen]+"/"
            genre_string = genre_string[:-1]
            genre_string += ")"

        list_item.setInfo('video', {'genre': genre_string.encode("utf-8")})
    list_item.setInfo('video', {'rating': show["rating"]})
    list_item.setInfo('video', {'plot': show_episode["synopsis"].encode("utf-8")})
    list_item.setInfo('video', {'premiered': show["premier"]})
    list_item.setInfo('video', {'year': show["year"]})
    list_item.setInfo('video', {'cast': show["actors"]})
    if(watched):
        list_item.setInfo('video', {'playcount': 1})
        list_item.setInfo('video', {'overlay': 5}) # watched overlay
    else:
        list_item.setInfo('video', {'playcount': 0})
        list_item.setInfo('video', {'overlay': 4}) # unwatched overlay

    list_item.setInfo('video', {'season': season})
    list_item.setInfo('video', {'episode': episode})

    list_item.setInfo('video', {'mediatype': "episode"})

    list_item.setInfo('video', {'tvshowtitle': show["title"].encode("utf-8")})
    list_item.setInfo('video', {'aired': show_episode["first_broadcast"].encode("utf-8")})
    list_item.setInfo('video', {'duration': show_episode["duration"]})

    return list_item


def set_show_metadata(show, list_item, favourite = False, watched = False):
    if len(show["poster"]) > 0:
        list_item.setArt({'thumb': show["poster"][0], 'icon': show["poster"][0]})
        list_item.setArt({'poster': show["poster"][0]})
    else:
        list_item.setArt({'thumb': DEFAULT_ICON_SHOW, 'icon': DEFAULT_ICON_SHOW})

    if len(show["fanart"]) > 0:
        list_item.setArt({'fanart': show["fanart"][0], 'landscape': show["fanart"][0]})
    else:
        list_item.setArt({'fanart': DEFAULT_FANART, 'landscape': DEFAULT_FANART})

    if len(show["banner"]) > 0:
        list_item.setArt({'banner': show["banner"][0]})

    contextMenuItems = []
    contextMenuItems.append(("(Redux) Download via uGet",'XBMC.RunPlugin(%s?action=download&download_type=uget&show=%s)' % (sys.argv[0], show["title"])))
    contextMenuItems.append(("(Redux) Export Download List",'XBMC.RunPlugin(%s?action=download&download_type=list&show=%s)' % (sys.argv[0], show["title"])))
    if(favourite):
        contextMenuItems.append(("(Redux) Unfavourite", 'XBMC.RunPlugin(%s?action=favourite_mark&show=%s&unfavourite=True)' % (sys.argv[0], show["title"].encode("utf-8"))))
    else:
        contextMenuItems.append(("(Redux) Add To Favourites", 'XBMC.RunPlugin(%s?action=favourite_mark&show=%s&unfavourite=False)' % (sys.argv[0], show["title"].encode("utf-8"))))

    if(watched):
        contextMenuItems.append(("(Redux) Mark Unwatched", 'XBMC.RunPlugin(%s?action=watched_mark&show=%s&watched=False)' % (sys.argv[0], show["title"].encode("utf-8"))))
    else:
        contextMenuItems.append(("(Redux) Mark Watched", 'XBMC.RunPlugin(%s?action=watched_mark&show=%s&watched=True)' % (sys.argv[0], show["title"].encode("utf-8"))))

    list_item.addContextMenuItems(contextMenuItems)


    list_item.setInfo('video', {'title': show["title"].encode("utf-8")})
    if(len(show["genres"]) > 0):
        genre_string = ""
        for gen in range(len(show["genres"])):
            genre_string += "/"+show["genres"][gen]
        genre_string = genre_string[1:]
        if(len(show["sub-genres"]) > 0):
            genre_string += " ("
            for gen in range(len(show["sub-genres"])):
                genre_string += show["sub-genres"][gen]+"/"
            genre_string = genre_string[:-1]
            genre_string += ")"

        list_item.setInfo('video', {'genre': genre_string.encode("utf-8")})
    list_item.setInfo('video', {'rating': show["rating"]})
    list_item.setInfo('video', {'plot': show["summary"].encode("utf-8")})
    list_item.setInfo('video', {'premiered': show["premier"]})
    list_item.setInfo('video', {'year': show["year"]})
    list_item.setInfo('video', {'cast': show["actors"]})
    if(watched):
        list_item.setInfo('video', {'playcount': 1})
        list_item.setInfo('video', {'overlay': 5}) # watched overlay
    else:
        list_item.setInfo('video', {'playcount': 0})
        list_item.setInfo('video', {'overlay': 4}) # unwatched overlay
    if(show["summary_short"]):
        list_item.setInfo('video', {'plotoutline': show["summary_short"].encode("utf-8")})
    elif(show["summary_medium"]):
        list_item.setInfo('video', {'plotoutline': show["summary_medium"].encode("utf-8")})

    #list_item.setInfo('video', {'season': })
    #list_item.setInfo('video', {'episode': })

    if(show["type"] == "Films"):
        list_item.setInfo('video', {'mediatype': "movie"})
        show_season = show["season"][show["season"].keys()[0]]
        show_episode = show_season["episode"][show_season["episode"].keys()[0]]
        list_item.setInfo('video', {'aired': show_episode["first_broadcast"].encode("utf-8")})
        list_item.setInfo('video', {'duration': show_episode["duration"]})
    else:
        list_item.setInfo('video', {'mediatype': "tvshow"})
        list_item.setInfo('video', {'tvshowtitle': show["title"].encode("utf-8")})

    #list_item.setInfo('video', {'mediatype': "season"})
    #list_item.setInfo('video', {'mediatype': "episode"})

    return list_item


def update_shows():
    xbmc.executescript(UPDATE_SCRIPT)

def advanced_search_for_shows():
    dialog = xbmcgui.Dialog()
    search_term = dialog.input('Enter search term', type=xbmcgui.INPUT_ALPHANUM)

    channel_list = ["All"]
    for channel in CHANNELS:
        channel_list.append(channel["name"])

    dialog = xbmcgui.Dialog()
    channel_selections = dialog.select("Choose Channel", channel_list)

    if(channel_selections == -1):
        return

    genre_record_list = Genre.select()
    sub_genre_record_list = SubGenre.select()
    genre_list = []
    for genre_record in genre_record_list:
        genre_list.append(genre_record.name)
    for subgenre_record in sub_genre_record_list:
        genre_list.append(subgenre_record.name)
    genre_list.sort()
    genre_list = ["All"] + genre_list

    dialog = xbmcgui.Dialog()
    genre_selections = dialog.select("Choose Genre", genre_list)

    if(genre_selections == -1):
        return

    year_record_list = Year.select().order_by(Year.name)
    year_list = ["All"]
    for year_record in year_record_list:
        year_list.append(year_record.name)

    dialog = xbmcgui.Dialog()
    year_selections = dialog.select("Choose Year", year_list)

    if(year_selections == -1):
        return

    advanced_search_for_shows_list(search_term, channel_selections, genre_selections, year_selections)

def advanced_search_for_shows_list(search_term, channel_selections, genre_selections, year_selections):
    channel_selections = int(channel_selections)
    genre_selections = int(genre_selections)
    year_selections = int(year_selections)

    query = True
    query_set = False

    if search_term != "":
        query_set = True
        regex = False
        if(search_term[0:3]=="-r "):
            regex = True

        if(regex == True):
            query = query & (Show.title.regexp(search_term[3:len(search_term)]))
        else:
            query = query & (Show.title.contains(search_term))

    if channel_selections > 0:
        query_set = True
        if channel_selections == 1:
            query = query & (Show.bbc1==True )
        elif channel_selections == 2:
            query = query & (Show.bbc2==True )
        elif channel_selections == 3:
            query = query & (Show.bbc3==True )
        elif channel_selections == 4:
            query = query & (Show.bbc4==True )
        elif channel_selections == 5:
            query = query & (Show.film==True )

    genre_record_list = Genre.select()
    sub_genre_record_list = SubGenre.select()
    genre_list = []
    for genre_record in genre_record_list:
        genre_list.append(genre_record.name)
    for genre_record in sub_genre_record_list:
        genre_list.append(genre_record.name)
    genre_list.sort()
    genre_list = ["All"] + genre_list

    if genre_selections > 0:
        query_set = True
        query = query & (
            Genre.name==genre_list[genre_selections] |
            SubGenre.name==genre_list[genre_selections]
         )

    year_record_list = Year.select().order_by(Year.name)
    year_list = ["All"]
    for year_record in year_record_list:
        year_list.append(year_record.name)

    if year_selections > 0:
        query_set = True
        query = query & (
            Show.year==year_list[year_selections]
         )

    shows_records = Show.select().join(ShowGenre).join(Genre).switch(Show).join(ShowSubGenre).join(SubGenre).where(query)
    shows = convert_shows_to_json(shows_records)

    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        if(shows[show]["year"]):
            list_item = xbmcgui.ListItem(label=show+" ("+shows[show]["year"]+")")
        else:
            list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False

        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def search_for_shows_vague():
    dialog = xbmcgui.Dialog()
    search_term = dialog.input('Enter search term', type=xbmcgui.INPUT_ALPHANUM)
    if search_term == '':
        return
    search_for_shows_vague_list(search_term)

def search_for_shows_vague_list(search_term):
    regex = False
    if(search_term[0:3]=="-r "):
        regex = True

    if(regex == True):
        shows_records = Show.select().join(ShowActor).join(Actor).where(
            (Show.title.regexp(search_term[3:len(search_term)])) |
            (Show.summary.regexp(search_term[3:len(search_term)])) |
            (Actor.name.regexp(search_term[3:len(search_term)]))
        )
    else:
        shows_records = Show.select().join(ShowActor).join(Actor).where(
            (Show.title.contains(search_term)) |
            (Show.summary.contains(search_term)) |
            (Actor.name.contains(search_term))
        )
    shows = convert_shows_to_json(shows_records)
    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        if(shows[show]["year"]):
            list_item = xbmcgui.ListItem(label=show+" ("+shows[show]["year"]+")")
        else:
            list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False

        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def search_for_shows():
    dialog = xbmcgui.Dialog()
    search_term = dialog.input('Enter search term', type=xbmcgui.INPUT_ALPHANUM)
    if search_term == '':
        return

    search_for_shows_list(search_term)

def search_for_shows_list(search_term):
    regex = False
    if(search_term[0:3]=="-r "):
        regex = True

    if(regex == True):
        shows_records = Show.select().where(Show.title.regexp(search_term[3:len(search_term)]))
    else:
        shows_records = Show.select().where(Show.title.contains(search_term))
    shows = convert_shows_to_json(shows_records)
    favourite_shows_list = get_favourite_shows_list()
    watched_shows_list = get_watched_shows_list()

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        if(shows[show]["year"]):
            list_item = xbmcgui.ListItem(label=show+" ("+shows[show]["year"]+")")
        else:
            list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        if(show in favourite_shows_list):
            favourite = True
        else:
            favourite = False
        if(show in watched_shows_list):
            watched = True
        else:
            watched = False

        list_item = set_show_metadata(shows[show], list_item, favourite, watched)

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='season_listing', show=show.encode("utf-8"))
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def get_favourite_shows_list():
    favourite_show_list = []
    favourite_show_results = UserFavouriteShow.select()
    for favourite_show_result in favourite_show_results:
        favourite_show_list.append(favourite_show_result.show)
    return favourite_show_list

def get_in_progress_shows_list():
    in_progress_show_list = []
    in_progress_show_results = UserWatchedStatus.select().where(UserWatchedStatus.status_is_show == True).where(UserWatchedStatus.in_progress == True)
    for in_progress_show_result in in_progress_show_results:
        in_progress_show_list.append(in_progress_show_result.show)
    return in_progress_show_list

def get_watched_shows_list():
    watched_show_list = []
    watched_show_results = UserWatchedStatus.select().where(UserWatchedStatus.status_is_show == True).where(UserWatchedStatus.watched == True)
    for watched_show_result in watched_show_results:
        watched_show_list.append(watched_show_result.show)
    return watched_show_list

def mark_watched(show_name, watched = False, season = None, episode = None):
    show_record = Show.select().where(Show.title == show_name).get()
    show = convert_show_to_json(show_record)

    print(show_name, watched, season, episode)

    if(episode != None):
        mark_watched_episode(show_name, watched, season, episode)
    elif(season != None):
        mark_watched_season(show_name, watched, season)
        for episode_key in show["season"][season]["episode"]:
            mark_watched_episode(show_name, watched, season , episode_key)
    else:
        mark_watched_show(show_name, watched)
        for season_key in show["season"]:
            mark_watched_season(show_name, watched, season_key)
            for episode_key in show["season"][season_key]["episode"]:
                mark_watched_episode(show_name, watched, season_key , episode_key)
                mark_watched_season(show_name, watched, season_key)
    update_show_watched_status(show_name)
    xbmc.executebuiltin("Container.Refresh")

def mark_watched_show(show_name, watched):
    showrow = UserWatchedStatus.select().where(
        (UserWatchedStatus.show == show_name) &
        (UserWatchedStatus.status_is_show == True)
    )
    if(len(showrow) == 0):
        UserWatchedStatus(
            show = show_name,
            status_is_show = True,
            in_progress = False,
            watched = watched
        ).save()
    else:
        UserWatchedStatus.update(watched = watched, in_progress = False).where(
            (UserWatchedStatus.show == show_name) &
            (UserWatchedStatus.status_is_show == True)
        ).execute()

def mark_watched_season(show_name, watched, season):
    seasonrow = UserWatchedStatus.select().where(
        (UserWatchedStatus.show == show_name) &
        (UserWatchedStatus.season == season) &
        (UserWatchedStatus.status_is_season == True)
    )
    if(len(seasonrow) == 0):
        UserWatchedStatus(
            show = show_name,
            season = season,
            status_is_season = True,
            in_progress = False,
            watched = watched
        ).save()
    else:
        UserWatchedStatus.update(watched = watched, in_progress = False).where(
            (UserWatchedStatus.show == show_name) &
            (UserWatchedStatus.season == season) &
            (UserWatchedStatus.status_is_season == True)
        ).execute()

def mark_watched_episode(show_name, watched, season , episode):
    episoderow = UserWatchedStatus.select().where(
        (UserWatchedStatus.show == show_name) &
        (UserWatchedStatus.season == season) &
        (UserWatchedStatus.episode == episode) &
        (UserWatchedStatus.status_is_episode == True)
    )
    if(len(episoderow) == 0):
        UserWatchedStatus(
            show = show_name,
            season = season,
            episode = episode,
            status_is_episode = True,
            in_progress = False,
            watched = watched
        ).save()
    else:
        UserWatchedStatus.update(watched = watched, in_progress = False).where(
            (UserWatchedStatus.show == show_name) &
            (UserWatchedStatus.season == season) &
            (UserWatchedStatus.episode == episode) &
            (UserWatchedStatus.status_is_episode == True)
        ).execute()

def mark_favourite(show_name, unfavourite = False):
    favourite_show_results = UserFavouriteShow.select().where(UserFavouriteShow.show == show_name)
    if(unfavourite == False):
        if(len(favourite_show_results) == 0):
            favourite_show = UserFavouriteShow(
                show = show_name
            ).save()
            dialog = xbmcgui.Dialog()
            dialog.ok('Added Favourite', '{0} successfully added to favourites'.format(show_name))
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Adding Favourite', '{0} already in favourites'.format(show_name))
    else:
        if(len(favourite_show_results) > 0):
            favourite_show = UserFavouriteShow.delete().where(
                UserFavouriteShow.show == show_name
            ).execute()
            dialog = xbmcgui.Dialog()
            dialog.ok('Removed Favourite', '{0} successfully removed from favourites'.format(show_name))
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Removing Favourite', '{0} is not in favourites'.format(show_name))
    xbmc.executebuiltin("Container.Refresh")

def check_parental_pin():
    parental_file = "{0}/parental.json".format(__profile__)
    if os.path.isfile(parental_file):
        entered_pin = xbmcgui.Dialog().numeric(0,'Enter existing PIN')
        pin_status = check_pin(parental_file, entered_pin)
        if(pin_status == -1):
            return
        elif(pin_status == False):
            xbmcgui.Dialog().ok("Error","PIN incorrect")
            return
    list_item = xbmcgui.ListItem(label="Click to Continue")
    list_item.setArt({'thumb': DEFAULT_ICON,
                      'icon': DEFAULT_ICON,
                      'fanart': DEFAULT_FANART})
    list_item.setInfo('video', {'title': "Click to Continue", 'genre': "Parental Controls"})
    url = get_url(action='list_menu')
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

    # print("------> Replacing Videos with xbmc.ReplaceWindow(Videos, {0})".format(url))
    # xbmc.executebuiltin("xbmc.ReplaceWindow(Videos, {0})".format(url))

def check_pin(parental_file, pin):
    try:
        with open(parental_file) as data_file:
            parental_data = json.load(data_file)
        if(parental_data["PIN"] == pin):
            return True
        else:
            return False
    except:
        xbmcgui.Dialog().ok("Error","PIN file corrupt. Removing.")
        os.remove(parental_file)
        return -1

def save_pin(parental_file, pin):
    if(os.path.isfile(parental_file)):
        xbmcgui.Dialog().ok("Error","PIN file already exists")
        return
    json_data = {"PIN": pin}
    with open(parental_file, 'w') as outfile:
        json.dump(json_data, outfile)

def pin_control(selection):
    parental_file = "{0}/parental.json".format(__profile__)
    if(params['selection'] == "Remove PIN" or params['selection'] == "Change PIN"):
        entered_pin = xbmcgui.Dialog().numeric(0,'Enter existing PIN')
        pin_status = check_pin(parental_file, entered_pin)
        if(pin_status == -1):
            return
        elif(pin_status == False):
            xbmcgui.Dialog().ok("Error","PIN incorrect")
            return
        os.remove(parental_file)

    if(params['selection'] == "Remove PIN"):
        xbmcgui.Dialog().ok("Success","PIN removed")
        return

    new_pin = xbmcgui.Dialog().numeric(0,'Enter new PIN')
    new_pin_confirm = xbmcgui.Dialog().numeric(0,'Confirm new PIN')
    if(new_pin != new_pin_confirm):
        xbmcgui.Dialog().ok("Error","PINs do not match")
    else:
        save_pin(parental_file, new_pin)

def download(download_type ,show_title, show_season, show_episode):
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Generating Download List', 'Loading Shows...')

    show_record = Show.select().where(Show.title == show_title).get()
    show = convert_show_to_json(show_record)

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

    loginfile = '{0}/reduxLogin.txt'.format(__profile__)
    redux_account = resolve_redux.ReduxAccount(loginfile)
    redux_token = redux_account.checkAndGetToken()

    requested_format_setting = xbmcaddon.Addon('plugin.video.redux').getSetting("format")
    requested_format = xbmc_util.convert_format(requested_format_setting)

    if(redux_token == ""):
        pDialog.close()
        xbmcgui.Dialog().ok("No Redux Token")
        return

    failed_downloads = []

    if(download_type == "list"):
        if (show_episode):
            title = re.sub('[^a-zA-Z0-9]', '', show_title) + " - Season " + re.sub('[^a-zA-Z0-9]', '', show_season) + " - Episode" + re.sub('[^a-zA-Z0-9]', '', show_episode)
        elif (show_season):
            title = re.sub('[^a-zA-Z0-9]', '', show_title) + " - Season " + re.sub('[^a-zA-Z0-9]', '', show_season)
        else:
            title = re.sub('[^a-zA-Z0-9]', '', show_title)

        home_folder = os.path.expanduser("~")
        desktop_folder = os.path.join(home_folder,"desktop")

        save_file = os.path.join(desktop_folder,  title) + ".txt"

        if(os.path.isfile(save_file)):
            pDialog.close()
            xbmcgui.Dialog().ok("Generating Download List", "File Already Exists: ",save_file)
            return

        f = open(save_file, 'w')
        f.write('# Download for '+show_title+'\n')  # python will convert \n to os.linesep
    elif(download_type == "uget"):
        if(show["film"]):
            download_path = xbmcaddon.Addon('plugin.video.redux').getSetting("movie_download_location")
        else:
            download_path = xbmcaddon.Addon('plugin.video.redux').getSetting("tvshow_download_location")

        if(len(download_path) == 0 or (not os.path.exists(download_path))):
            pDialog.close()
            xbmcgui.Dialog().ok('Generating Download List', "Download path doesn't exist.", " Please setup tvshow_download_location and movie_download_location correctly in Plugin Settings")
            return

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
                    failed_downloads.append("S{0}E{1} - no urls".format(season,episode))
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
                failed_downloads.append("S{0}E{1}  - error resolving".format(season,episode))

            if(download_type == "list"):
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
            elif(download_type == "uget"):
                if url != None:
                    download_folder = os.path.join(
                        download_path,
                        show["title"],
                        show['season'][season]["title"]
                    )
                    try:
                        mkdir_p(download_folder)
                    except:
                        xbmcgui.Dialog().ok('Generating Download List', "Could not create path: {0}".format(download_folder))
                        return

                    download_filename = "S{0}E{1}-{2}.mp4".format(season,episode,show['season'][season]['episode'][episode]["title"])
                    download_filepath = os.path.join(download_folder, download_filename)
                    if(os.path.isfile(download_filepath)):
                        failed_downloads.append("S{0}E{1}  - file exists".format(season,episode))
                    else:
                        command = 'uget "{0}"  --folder="{1}" --filename="{2}" --quiet'.format(
                            url,
                            download_folder,
                            download_filename,
                        )

                        os.system(command)

            current_episode += 1
            pDialog.update( int((100*current_episode)/total_episodes) ,"Resolving Redux Urls...","Resolved {0}/{1}".format(current_episode,total_episodes),"")


    pDialog.update(100,"Resolving Redux Urls... Done","","")
    pDialog.close()

    for failed in failed_downloads:
        print(failed)

    if(download_type == "list"):
        f.close()
        xbmcgui.Dialog().ok(
            "Generating Download List",
            "{0}/{1} Queued Successfully".format(total_episodes - len(failed_downloads), total_episodes),
            "Download List Saved To: ",
            save_file
        )
    elif(download_type == "uget"):
        xbmcgui.Dialog().ok(
            "Generating Download List",
            "{0}/{1} Queued Successfully".format(total_episodes - len(failed_downloads), total_episodes),
            "Downloads added to uGet"
        )
        if(len(failed_downloads) > 0):
            show_errors = xbmcgui.Dialog().yesno(
                "Generating Download List",
                "Would you like to see the errors which stopped {0} files from downloading?".format(len(failed_downloads))
            )
            if(show_errors):
                for failed in failed_downloads:
                    xbmcgui.Dialog().ok(
                        "Generating Download List",
                        "{0}".format(failed)
                    )

def router(params):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    # Check the parameters passed to the plugin


    if params:
        print(params)
        if params["action"] == "list_menu":
            list_menu()
        elif params['action'] == "parental":
            if(params['selection'] != "Add PIN" and params['selection'] != "Remove PIN" and params['selection'] != "Change PIN"):
                raise ValueError('Invalid paramstring: {0}!'.format(params))
            pin_control(params['selection'])
        elif params['action'] == 'watched_mark':
            if(params['watched'] == "True"):
                watched = True
            else:
                watched = False

            if "episode" in params:
                mark_watched(params['show'], watched, params["season"], params["episode"])
            elif "season" in params:
                mark_watched(params['show'], watched, params["season"], None)
            else:
                mark_watched(params['show'], watched, None, None)
        elif params['action'] == 'favourite_mark':
            if(params['unfavourite'] == "True"):
                mark_favourite(params['show'], True)
            else:
                mark_favourite(params['show'], False)
        elif params['action'] == 'menu':
            if params['selection'] == 'In Progress':
                list_in_progress_shows()
            elif params['selection'] == 'Favourites':
                list_favourite_shows()
            elif params['selection'] == 'Recently Added':
                list_recently_added_shows_categories()
            elif params['selection'] == 'View By Category':
                list_categories()
            elif params['selection'] == "Update Shows Database":
                # dialog = xbmcgui.Dialog()
                # dialog.ok('Update Shows Database', 'This feature has been disabled due to it being broken by shutdown of BBC /programmes schedules API. A workaround is in development.')
                # return
                update_shows()
            elif params['selection'] == "Search":
                list_search()
            elif params['selection'] == "Parental Controls":
                list_parental_controls()
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))

        elif params['action'] == 'search':
            if params['selection'] == 'Search (By Name)':
                search_for_shows()
            elif params['selection'] == 'Search (By Name, Desc, Actors)':
                search_for_shows_vague()
            elif params['selection'] == 'Advanced Search':
                advanced_search_for_shows()
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))
        elif params['action'] == 'search_list':
            if params['search_type'] == 'Search (By Name)':
                search_for_shows_list(params['search_term'])
            elif params['search_type'] == 'Search (By Name, Desc, Actors)':
                search_for_shows_vague_list(params['search_term'])
            elif params['search_type'] == 'Advanced Search':
                if('search_term' not in params):
                    params['search_term'] = ""
                advanced_search_for_shows_list(params['search_term'], params['channel_selections'], params['genre_selections'], params['year_selections'])
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))
        elif params['action'] == 'listing':
            # Display the list of videos in a provided category.
            if params['category'] == 'Channels':
                list_channels()
            elif params['category'] == 'All':
                list_shows_all()
            elif params['category'] == 'Genres':
                list_genres()
            elif params['category'] == 'Sub-Genres':
                list_subgenres()
            elif params['category'] == "Years":
                list_years()
            elif params['category'] == "Type":
                list_types()
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))
        elif params['action'] == "show_subgenre_of_genre_listing":
            list_subgenres_of_genre(params['genre'])
        elif params['action'] == 'show_listing':
            if 'recent' in params:
                list_recently_added_shows(params['recent'])
            elif 'channel' in params:
                list_shows_by_channel(params['channel'])
            elif 'genre' in params and 'subgenre' in params:
                list_shows_by_genre_with_subgenre(params['genre'], params['subgenre'])
            elif 'genre' in params:
                list_shows_by_genre(params['genre'])
            elif 'subgenre' in params:
                list_shows_by_subgenre(params['subgenre'])
            elif 'year' in params:
                list_shows_by_year(params['year'])
            elif 'type' in params:
                list_shows_by_type(params['type'])
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))
        elif params['action'] == 'season_listing':
            list_seasons(params['show'])
        elif params['action'] == 'episode_listing':
            list_episodes(params['show'],params['season'])
        elif params['action'] == 'play_episode':
            # Play a video by querying redux.
            if("format" in params):
                play_episode(params['show'],params['season'],params["episode"],True)
            else:
                play_episode(params['show'],params['season'],params["episode"],False)
        elif params['action'] == 'download':
            if("show" in params):
                show_title = params["show"]
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))

            if("download_type" in params):
                download_type = params["download_type"]
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))

            show_season = None
            show_episode = None

            if("season" in params):
                show_season = params["season"]
                if("episode" in params):
                    show_episode = params["episode"]

            if(download_type == "list"):
                download(download_type, show_title, show_season, show_episode)
            elif(download_type == "uget"):
                download(download_type, show_title, show_season, show_episode)
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(params))

        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(params))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        check_parental_pin()


SEARCHMENU = [
    {'name':'Search (By Name)', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Search (By Name, Desc, Actors)', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Advanced Search', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART}
]

def load_shows_json(location = None):
    print("Loading Shows")
    if location == None:
        location = "{0}/shows.pickle".format(__profile__)
    if os.path.isfile(location):
        f = open( location, "rb" )
        shows_obj = pickle.load( f )
        # shows = shows_obj["shows"]
        f.close()
        print("Finished Loading Shows (Success)")
        return shows_obj
    else:
        print("Finished Loading Shows (Fail)")
        return None


def check_for_database(db_data, user_db_data, pickle_path):
    show_connection = test_connection(db_data, "show")

    if(show_connection["connection_valid"] == False):
        dialog = xbmcgui.Dialog()
        dialog.ok('Connecting to Show DB Failed', show_connection["connection_error"], show_connection["connection_string"])
        xbmc.executebuiltin('Addon.OpenSettings(plugin.video.redux)')
        return False

    if(show_connection["preexisting_db"] == False):
        print("Creating Shows Tables")
        # Data not in Database
        if(os.path.isfile(pickle_path)):
            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Creating Database', 'Loading Shows...')
            shows_obj = load_shows_json()
            if(shows_obj == None):
                dialog = xbmcgui.Dialog()
                dialog.ok('Loading Data', 'Found pickled data but it is corrupted', "Failed File: {0}".format(pickle_path))
                return False

            pDialog.update(20,"Loading Shows... Done","Initialising Database...")
            db = BaseModel._meta.database
            init_database(db, db_data)
            create_database(True, False, __ShowDBVersion__, __UserDBVersion__)
            pDialog.update(40,"Initialising Database... Done", "Populating Database...")
            populate_database(shows_obj, pDialog)
            pDialog.update(100,"Populating Database... Done", "", "")
            pDialog.close()
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Loading Data', 'Could not find a pickled database of shows', "Expected: {0} to exist".format(pickle_path))
            return False
    elif(show_connection["update_db"] == True):
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Updating Database', 'Updating Tables...')
        db = BaseModel._meta.database
        init_database(db, db_data)
        create_database(True, False, __ShowDBVersion__, __UserDBVersion__)
        pDialog.update(100,"Updating Tables... Done", "", "")
        pDialog.close()
    user_connection = test_connection(user_db_data, "user")

    if(user_connection["connection_valid"] == False):
        dialog = xbmcgui.Dialog()
        dialog.ok('Connecting to User DB Failed', user_connection["connection_error"], user_connection["connection_string"])
        xbmc.executebuiltin('Addon.OpenSettings(plugin.video.redux)')
        return False

    if(user_connection["preexisting_db"] == False):
        # Data not in database
        print("Creating User Table")
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Creating User Database', 'Initialising Database...')
        user_db = UserBaseModel._meta.database
        init_database(user_db, user_db_data)
        create_database(False, True, __ShowDBVersion__, __UserDBVersion__)
        populate_user_database()
        pDialog.update(100, 'Initialising Database...Done')
        pDialog.close()
    elif(user_connection["update_db"] == True):
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Updating User Database', 'Updating Tables...')
        db = BaseModel._meta.database
        init_database(db, db_data)
        create_database(False, True, __ShowDBVersion__, __UserDBVersion__)
        pDialog.update(100,"Updating Tables... Done", "", "")
        pDialog.close()
    return True

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))

    packaged_pickle_file = "{0}/shows.pickle".format(script_dir)
    pickle_file = "{0}/shows.pickle".format(__profile__)

    if(not os.path.isfile(pickle_file)):
        if(os.path.isfile(packaged_pickle_file)):
            shutil.copyfile(packaged_pickle_file, pickle_file)

    [db_data, user_db_data] = xbmc_util.get_db_data()

    params = dict(parse_qsl(sys.argv[2][1:]))
    if 'action' in params and params['action'] == "test_connection":
        pdialog = xbmcgui.DialogProgress()
        pdialog.create("Testing DB Connection")

        if(params['connection'] == "show"):
            return_values = test_connection(db_data, "show")
        elif(params['connection'] == "user"):
            return_values = test_connection(user_db_data, "user")
        else:
            raise ValueError("Invalid connection parameter")

        connection_valid = return_values["connection_valid"]
        connection_error = return_values["connection_error"]
        connection_string = return_values["connection_string"]

        if(connection_valid):
            dialog = xbmcgui.Dialog()
            dialog.ok('Testing DB Connection', 'Successful!', '', connection_string)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Testing DB Connection', 'Failed:', connection_error, connection_string)

        xbmc.executebuiltin('Addon.OpenSettings(plugin.video.redux)')
    else:
        if(check_for_database(db_data, user_db_data, pickle_file)):
            # Connect to Database
            db = BaseModel._meta.database
            init_database(db, db_data)
            db.connect()

            db2 = UserBaseModel._meta.database
            init_database(db2, user_db_data)
            db2.connect()
            # Call the router function and pass the plugin call parameters to it.
            # We use string slicing to trim the leading '?' from the plugin call paramstring

            router(params)
            # Close Database
            db.close()
            db2.close()

# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin

from lib.database_schema import Show, Genre, ShowGenre, SubGenre, ShowSubGenre, Actor, ShowActor, Year, BaseModel
from lib.database_functions import convert_shows_to_json, convert_show_to_json, populate_database, create_database

import os
try:
   import cPickle as pickle
except:
   import pickle

from lib import sort_shows
from lib import resolve_redux
from lib import util

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

DEFAULT_FANART = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/fanart.jpg')
DEFAULT_ICON = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/lists.png')
DEFAULT_ICON_SHOW = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/no_icon.png')
SEARCH_ICON = xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/search.png')

DOWNLOAD_SCRIPT  = xbmc.translatePath('special://home/addons/plugin.video.redux/download.py')
UPDATE_SCRIPT  = xbmc.translatePath('special://home/addons/plugin.video.redux/scrape-update.py')

MAINMENU = [
    {'name':'View By Category' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Search', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Update Shows Database',
        'thumb': xbmc.translatePath('special://home/addons/plugin.video.redux/resources/media/update.png'),
        'fanart': DEFAULT_FANART}
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
    {'name':'Years' ,'thumb': DEFAULT_ICON, 'fanart': DEFAULT_FANART}
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
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
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
        url = get_url(action='show_listing', genre=genre)
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
    # shows = load_shows_json()
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Retrieving Over 10,000 shows. ')
    pDialog.update(0,"Please be patient...")
    shows_records = Show.select().order_by(Show.title)
    shows = convert_shows_to_json(shows_records)

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
        list_item = set_show_metadata(shows[show], list_item)

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

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item = set_show_metadata(shows[show], list_item)

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

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item = set_show_metadata(shows[show], list_item)

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

    # Iterate through shows
    for show in shows:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=show)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item = set_show_metadata(shows[show], list_item)

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
    # script_dir = os.path.dirname(os.path.realpath(__file__))
    # all_shows = load_shows_json()
    # all_channel_shows = sort_shows.sort_shows_by_channel(all_shows)
    # shows = all_channel_shows[channel]

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

        list_item = set_show_metadata(shows[show], list_item)

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

    listings = []

    if len(show['season']) == 1:
        list_episodes(show_name,next(iter(show['season'])))
        return
    for season in show['season']:
        if(show['season'][season]["title"]):
            title = "{0} ({1})".format(show['season'][season]["title"].encode("utf-8"),season)
        else:
            title = "Untitled ({0})".format(season)
        list_item = xbmcgui.ListItem(label=title)

        set_season_metadata(show,season,list_item)

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

    listings = []
    for episode in show['season'][season]['episode']:
        if(show['season'][season]['episode'][episode]["title"]):
            title = "E{0} {1}".format(episode,show['season'][season]['episode'][episode]["title"].encode("utf-8"))
        else:
            title = "E{0}".format(episode)
        list_item = xbmcgui.ListItem(label=title)

        list_item = set_episode_metadata(show,season,episode,list_item)

        list_item.setProperty('IsPlayable', 'true')
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

def play_episode(show, season, episode):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    loginfile = '{0}/reduxLogin.txt'.format(script_dir)

    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Playing Episode', 'Loading Shows...')

    shows = load_shows_json()

    pDialog.update(25,"Contacting Redux...")

    redux_account = resolve_redux.ReduxAccount(loginfile)
    redux_token = redux_account.checkAndGetToken()
    print(redux_token)
    if(redux_token == ""):
        return

    pDialog.update(50,"Contacting Redux... Done","Getting Disc Ref...")

    # Needs to Check that a h264 version is available and also check that a non regions version is available

    [error,ref] = resolve_redux.resolve_episode_ref(redux_token, shows[show], season, episode)
    print([error,ref])
    pDialog.update(75,"Contacting Redux... Done","Getting Disc Ref... Done","Resolving to URL...")
    if (error > -1):
        urls = resolve_redux.resolve_episode_url(redux_token, ref)
        print(urls)

        if urls == None:
            xbmcgui.Dialog().ok('Playing Episode', "Could not resolve disc reference from Redux")
            return
        else:
            print("URLs: {0}".format(urls))
            pDialog.update(100,"Contacting Redux... Done","Getting Disc Ref... Done","Resolving to URL... Done")
    else:
        xbmcgui.Dialog().ok('Playing Episode', "Could not get disc reference from Redux")
        return

    requested_format_setting = xbmcplugin.getSetting(_handle,"format")
    requested_format = util.convert_format(requested_format_setting)
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


    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def set_season_metadata(show,season,list_item):
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

    list_item.addContextMenuItems([("Download Season",'XBMC.RunScript('+DOWNLOAD_SCRIPT+', '+str(_handle)+", "+show["title"]+', '+season+')')])

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

    list_item.setInfo('video', {'season': season})
    list_item.setInfo('video', {'mediatype': "season"})
    list_item.setInfo('video', {'tvshowtitle': show["title"].encode("utf-8")})

    return list_item

def set_episode_metadata(show,season,episode,list_item):
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

    list_item.addContextMenuItems([("Download Episode",'XBMC.RunScript('+DOWNLOAD_SCRIPT+', '+str(_handle)+", "+show["title"]+', '+season+', '+episode+')')])

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

    list_item.setInfo('video', {'season': season})
    list_item.setInfo('video', {'episode': episode})

    list_item.setInfo('video', {'mediatype': "episode"})

    list_item.setInfo('video', {'tvshowtitle': show["title"].encode("utf-8")})
    list_item.setInfo('video', {'aired': show_episode["first_broadcast"].encode("utf-8")})
    list_item.setInfo('video', {'duration': show_episode["duration"]})

    return list_item


def set_show_metadata(show, list_item):
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

    list_item.addContextMenuItems([("Download Show",'XBMC.RunScript('+DOWNLOAD_SCRIPT+', '+str(_handle)+", "+show["title"]+')')])

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

    channel_list = ["All"]
    for channel in CHANNELS:
        channel_list.append(channel["name"])

    dialog = xbmcgui.Dialog()
    channel_selections = dialog.select("Choose Channel", channel_list)

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

    dialog = xbmcgui.Dialog()
    genre_selections = dialog.select("Choose Genre", genre_list)

    if genre_selections > 0:
        query_set = True
        query = query & (
            Genre.name==genre_list[genre_selections] |
            SubGenre.name==genre_list[genre_selections]
         )

    year_record_list = Year.select()
    year_list = ["All"]
    for year_record in year_record_list:
        year_list.append(year_record.name)

    dialog = xbmcgui.Dialog()
    year_selections = dialog.select("Choose Year", year_list)

    if year_selections > 0:
        query_set = True
        query = query & (
            Show.year==year_list[year_selections]
         )

    shows_records = Show.select().join(ShowGenre).join(Genre).switch(Show).join(ShowSubGenre).join(SubGenre).where(query)
    shows = convert_shows_to_json(shows_records)

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
        list_item = set_show_metadata(shows[show], list_item)

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
    # script_dir = os.path.dirname(os.path.realpath(__file__))
    # shows = load_shows_json()

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
        list_item = set_show_metadata(shows[show], list_item)

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
    # script_dir = os.path.dirname(os.path.realpath(__file__))
    # shows = load_shows_json()

    regex = False
    if(search_term[0:3]=="-r "):
        regex = True

    if(regex == True):
        shows_records = Show.select().where(Show.title.regexp(search_term[3:len(search_term)]))
    else:
        shows_records = Show.select().where(Show.title.contains(search_term))
    shows = convert_shows_to_json(shows_records)

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
        list_item = set_show_metadata(shows[show], list_item)

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

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'menu':
            if params['selection'] == 'View By Category':
                list_categories()
            elif params['selection'] == "Update Shows Database":
                dialog = xbmcgui.Dialog()
                dialog.ok('Update Shows Database', 'This feature has been disabled due to it being broken by shutdown of BBC /programmes schedules API. A workaround is in development.')
                return 
                update_shows()
            elif params['selection'] == "Search":
                list_search()
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(paramstring))

        elif params['action'] == 'search':
            if params['selection'] == 'Search (By Name)':
                search_for_shows()
            elif params['selection'] == 'Search (By Name, Desc, Actors)':
                search_for_shows_vague()
            elif params['selection'] == 'Advanced Search':
                advanced_search_for_shows()
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
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
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
        elif params['action'] == 'show_listing':
            if 'channel' in params:
                list_shows_by_channel(params['channel'])
            elif 'genre' in params:
                list_shows_by_genre(params['genre'])
            elif 'subgenre' in params:
                list_shows_by_subgenre(params['subgenre'])
            elif 'year' in params:
                list_shows_by_year(params['year'])
            else:
                raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
        elif params['action'] == 'season_listing':
            list_seasons(params['show'])
        elif params['action'] == 'episode_listing':
            list_episodes(params['show'],params['season'])
        elif params['action'] == 'play_episode':
            # Play a video by querying redux.
            play_episode(params['show'],params['season'],params["episode"])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_menu()


SEARCHMENU = [
    {'name':'Search (By Name)', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Search (By Name, Desc, Actors)', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART},
    {'name':'Advanced Search', 'thumb': SEARCH_ICON, 'fanart': DEFAULT_FANART}
]

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

def check_for_database(db_path,pickle_path):
    if( os.path.isfile(db_path)):
        return True
    if(os.path.isfile(pickle_path)):
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Creating Databasse', 'Loading Shows...')
        shows = load_shows_json()
        if(shows == None):
            dialog = xbmcgui.Dialog()
            dialog.ok('Loading Data', 'Found pickled data but it is corrupted', "Failed File: {0}".format(pickle_path))
            return False

        pDialog.update(20,"Loading Shows... Done","Initialising Database...")
        db = BaseModel._meta.database
        db.init(db_path)
        create_database()
        pDialog.update(40,"Initialising Database... Done", "Populating Database...")
        populate_database(shows, pDialog)
        pDialog.update(100,"Populating Database... Done", "", "")
        return True

    dialog = xbmcgui.Dialog()
    dialog.ok('Loading Data', 'Could not find a database of shows', "Expected: {0} to exist".format(pickle_path))
    return False

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))
    database_path = "{0}/shows.db".format(script_dir)
    pickle_path = "{0}/shows.pickle".format(script_dir)

    if(check_for_database(database_path,pickle_path)):
        # Connect to Database
        db = BaseModel._meta.database
        db.init(database_path)
        db.connect()
        # Call the router function and pass the plugin call parameters to it.
        # We use string slicing to trim the leading '?' from the plugin call paramstring
        router(sys.argv[2][1:])
        # Close Database
        db.close()

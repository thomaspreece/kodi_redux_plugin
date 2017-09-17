# models.py
from lib import peewee

from lib.database_schema import Show, Genre, RecentShows, ShowGenre, SubGenre, ShowSubGenre, GenreToSubGenre, LastUpdate, Actor, ShowActor, Year, BaseModel
from lib.user_database_schema import UserFavouriteShow, UserLastUpdate, UserBaseModel

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

try:
   import cPickle as pickle
except:
   import pickle

def init_database(db_proxy, db_data):
    if(db_data["db_format"] == "mysql"):
        # Remap blob to mediumblob as season can get larger then blob will allow in mySQL.
        database = peewee.MySQLDatabase(db_data["data"]["db"], host=db_data["data"]["host"], port=int(db_data["data"]["port"]), user=db_data["data"]["username"], password=db_data["data"]["password"], fields={'blob': 'mediumblob' })
        db_proxy.initialize(database)
    elif(db_data["db_format"] == "sqlite"):
        database = peewee.SqliteDatabase(db_data["data"]["path"])
        db_proxy.initialize(database)

def clear_database(clear_show_tables = False, clear_user_tables = False):
    if(clear_user_tables):
        db = UserBaseModel._meta.database
        db.connect()
        UserFavouriteShow.delete_instance()
        UserLastUpdate.delete_instance()
        db.close()

    if(clear_show_tables):
        db = BaseModel._meta.database
        db.connect()
        Show.delete_instance()
        Genre.delete_instance()
        RecentShows.delete_instance()
        ShowGenre.delete_instance()
        ShowGenre.delete_instance()
        ShowSubGenre.delete_instance()
        GenreToSubGenre.delete_instance()
        Actor.delete_instance()
        ShowActor.delete_instance()
        Year.delete_instance()
        LastUpdate.delete_instance()
        db.close()

def create_database(create_show_tables = True, create_user_tables = True):
    if(create_user_tables):
        db = UserBaseModel._meta.database
        db.connect()
        tables = [
            [UserFavouriteShow,"UserFavouriteShow"],
            [UserLastUpdate, "UserLastUpdate"]
        ]
        for table in tables:
            try:
                table[0].create_table()
            except peewee.InternalError, e:
                print(str(e))
                print("{0} table already exists!".format(table[1]))
            else:
                print("{0} table created".format(table[1]))
        db.close()

    if(create_show_tables):
        db = BaseModel._meta.database
        db.connect()
        tables = [
            [Show,"Show"],
            [Genre, "Genre"],
            [RecentShows, "RecentShows"],
            [ShowGenre, "ShowGenre"],
            [SubGenre, "SubGenre"],
            [ShowSubGenre, "ShowSubGenre"],
            [GenreToSubGenre, "GenreToSubGenre"],
            [Actor, "Actor"],
            [ShowActor, "ShowActor"],
            [Year, "Year"],
            [LastUpdate, "LastUpdate"]
        ]
        for table in tables:
            try:
                table[0].create_table()
            except peewee.InternalError, e:
                print(str(e))
                print("{0} table already exists!".format(table[1]))
            else:
                print("{0} table created".format(table[1]))
        db.close()

def populate_user_database():
    db = UserBaseModel._meta.database
    db.connect()
    UserLastUpdate(
        date = "0000-00-00"
    ).save()

def populate_database(shows_obj, pDialog= None):
    db = BaseModel._meta.database
    db.connect()

    if shows_obj == None:
        raise ValueError("No Shows!")

    shows = shows_obj["shows"]

    show_db_list = []
    recent_show_db_list = []

    show_link_db_list = []
    genre_link_db_list = []

    genre_db_dict = {}
    sub_genre_db_dict = {}
    actor_db_dict = {}
    year_db_dict = {}

    name_to_recent_index = {}
    for recent_ind in range(len(shows_obj["recent"])):
        name_to_recent_index[shows_obj["recent"][recent_ind]["name"]] = recent_ind

    for show_key in shows:
        show_json = shows[show_key]
        fanart = None
        if(len(show_json["fanart"]) > 0):
            fanart = show_json["fanart"][0]
        poster = None
        if(len(show_json["poster"]) > 0):
            poster = show_json["poster"][0]
        banner = None
        if(len(show_json["banner"]) > 0):
            banner = show_json["banner"][0]

        if show_json["year"] not in year_db_dict:
            year = Year(
                name = show_json["year"]
            )
            year_db_dict[show_json["year"]] = year

        for genre_name in show_json["genres"]:
            if genre_name not in genre_db_dict:
                genre = Genre(
                    name = genre_name
                )
                genre_db_dict[genre_name] = genre

        for sub_genre_name in show_json["sub-genres"]:
            if sub_genre_name not in sub_genre_db_dict:
                subgenre = SubGenre(
                    name = sub_genre_name
                )
                sub_genre_db_dict[sub_genre_name] = subgenre

        for actor_name in show_json["actors"]:
            if actor_name not in actor_db_dict:
                actor = Actor(
                    name = actor_name
                )
                actor_db_dict[actor_name] = actor

        film = False
        bbc1 = False
        bbc2 = False
        bbc3 = False
        bbc4 = False
        if show_json["type"] == "Films":
            film = True
        else:
            for season in show_json["season"]:
                for episode in show_json["season"][season]["episode"]:
                    service = show_json["season"][season]["episode"][episode]["service"]
                    if service == 'BBC One':
                        bbc1 = True
                    elif service == 'BBC Two':
                        bbc2 = True
                    elif service == 'BBC Three':
                        bbc3 = True
                    elif service == 'BBC Four':
                        bbc4 = True

        show = Show(
            title = show_json["title"],
            rating = show_json["rating"] if show_json["rating"] != '' else None,
            rating_count = show_json["rating_count"] if show_json["rating_count"] != '' else None,
            bbc1=bbc1,
            bbc2=bbc2,
            bbc3=bbc3,
            bbc4=bbc4,
            film=film,
            fanart = fanart,
            poster = poster,
            banner = banner,
            image = show_json["image"],
            summary = show_json["summary"],
            summary_long = show_json["summary_long"],
            summary_medium = show_json["summary_medium"],
            summary_short = show_json["summary_short"],
            show_type = show_json["show_type"] if ("show_type" in show_json) else None,
            genres_string = '/'.join(show_json["genres"]),
            sub_genres_string = '/'.join(show_json["sub-genres"]),
            actors_string = '/'.join(show_json["actors"]),
            year = show_json["year"],
            premier = show_json["premier"],
            season = pickle.dumps(show_json["season"], 2)
        )
        show_db_list.append(show)

        if show_json["title"] in name_to_recent_index:
            recent_ind = name_to_recent_index[show_json["title"]]
            recent_type_string = shows_obj["recent"][recent_ind]["type"]
            if(recent_type_string == "new_show"):
                recent_type = 1
            elif(recent_type_string == "new_season"):
                recent_type = 2
            else:
                raise ValueError(recent_type_string)
            recentshow = RecentShows(
                show = show,
                recenttype = recent_type
            )
            recent_show_db_list.append(recentshow)

        for genre_name in show_json["genres"]:
            showgenre = ShowGenre(
                show = show,
                genre = genre_db_dict[genre_name]
            )
            show_link_db_list.append(showgenre)

        for sub_genre_name in show_json["sub-genres"]:
            showsubgenre = ShowSubGenre(
                show = show,
                subgenre = sub_genre_db_dict[sub_genre_name]
            )
            show_link_db_list.append(showsubgenre)

        for actor_name in show_json["actors"]:
            showactor = ShowActor(
                show = show,
                actor = actor_db_dict[actor_name]
            )
            show_link_db_list.append(showactor)

    for genre_name in shows_obj["genres"]:
        for sub_genre_name in shows_obj["genres"][genre_name]:
            genretosubgenre = GenreToSubGenre(
                genre = genre_db_dict[genre_name],
                subgenre = sub_genre_db_dict[sub_genre_name]
            )
            genre_link_db_list.append(genretosubgenre)

    with db.atomic():
        if pDialog:
            pDialog.update(50,"Initialising Database... Done", "Populating Database...", "Populating Shows...")
        for show in show_db_list:
            show.save()
        print("Shows Saved")
        if pDialog:
            pDialog.update(52,"Initialising Database... Done", "Populating Database...", "Populating Genres...")
        for genre_key in genre_db_dict:
            genre_db_dict[genre_key].save()
        print("Genres Saved")
        if pDialog:
            pDialog.update(54,"Initialising Database... Done", "Populating Database...", "Populating Actors...")
        for actor_key in actor_db_dict:
            actor_db_dict[actor_key].save()
        print("Actors Saved")
        if pDialog:
            pDialog.update(56,"Initialising Database... Done", "Populating Database...", "Populating Sub-Genres...")
        for sub_genre_key in sub_genre_db_dict:
            sub_genre_db_dict[sub_genre_key].save()
        print("Sub Genres Saved")
        if pDialog:
            pDialog.update(58,"Initialising Database... Done", "Populating Database...", "Populating Years...")
        for year_key in year_db_dict:
            year_db_dict[year_key].save()
        print("Years Saved")
        if pDialog:
            pDialog.update(60,"Initialising Database... Done", "Populating Database...", "Populating Links...")
        for showlink in show_link_db_list:
            showlink.save()
        if pDialog:
            pDialog.update(70,"Initialising Database... Done", "Populating Database...", "Populating Genre Links...")
        for genrelink in genre_link_db_list:
            genrelink.save()
        if pDialog:
            pDialog.update(80,"Initialising Database... Done", "Populating Database...", "Populating Recent Shows...")
        for recentshow in recent_show_db_list:
            recentshow.save()

        LastUpdate(
            date = shows_obj["parsed"]
        ).save()
        print("Links Saved")
    db.close()

def convert_show_to_json(show_record):
    show = {
        "title": show_record.title,
        "rating": show_record.rating,
        "rating_count": show_record.rating_count,
        "fanart": [show_record.fanart] if show_record.fanart != None else [],
        "poster": [show_record.poster] if show_record.poster != None else [],
        "banner": [show_record.banner] if show_record.banner != None else [],
        "image": show_record.image,
        "summary": show_record.summary,
        "summary_long": show_record.summary_long,
        "summary_medium": show_record.summary_medium,
        "summary_short": show_record.summary_short,
        "type": show_record.show_type,
        "genres": show_record.genres_string.split("/"),
        "sub-genres": show_record.sub_genres_string.split("/"),
        "actors": show_record.actors_string.split("/"),
        "year": show_record.year,
        "premier": show_record.premier,
        "season": pickle.load(StringIO(show_record.season))
    }
    return show

def convert_shows_to_json(show_records):
    shows = {}
    for show_record in show_records:
        shows[show_record.title] = {
            "title": show_record.title,
            "rating": show_record.rating,
            "rating_count": show_record.rating_count,
            "fanart": [show_record.fanart] if show_record.fanart != None else [],
            "poster": [show_record.poster] if show_record.poster != None else [],
            "banner": [show_record.banner] if show_record.banner != None else [],
            "image": show_record.image,
            "summary": show_record.summary,
            "summary_long": show_record.summary_long,
            "summary_medium": show_record.summary_medium,
            "summary_short": show_record.summary_short,
            "type": show_record.show_type,
            "genres": show_record.genres_string.split("/"),
            "sub-genres": show_record.sub_genres_string.split("/"),
            "actors": show_record.actors_string.split("/"),
            "year": show_record.year,
            "premier": show_record.premier
        }
    return shows

if __name__ == "__main__":
    set_db_type("sqlite")
    db = BaseModel._meta.database
    db.init("Testing.db")
    create_database()

from lib import peewee

database_proxy = peewee.Proxy()

def init_database(db_proxy, db_data):
    if(db_data["db_format"] == "mysql"):
        database = peewee.MySQLDatabase(db_data["data"]["db"], host=db_data["data"]["host"], port=int(db_data["data"]["port"]), user=db_data["data"]["username"], password=db_data["data"]["password"])
        db_proxy.initialize(database)
    elif(db_data["db_format"] == "sqlite"):
        database = peewee.SqliteDatabase(db_data["data"]["path"])
        db_proxy.initialize(database)

########################################################################
class BaseModel(peewee.Model):
    class Meta:
        database = database_proxy

class Show(BaseModel):
    """
    ORM model of the Show table
    """
    title = peewee.TextField()

    rating = peewee.FloatField(null=True)
    rating_count = peewee.IntegerField(null=True)

    bbc1 = peewee.BooleanField(default=False)
    bbc2 = peewee.BooleanField(default=False)
    bbc3 = peewee.BooleanField(default=False)
    bbc4 = peewee.BooleanField(default=False)
    film = peewee.BooleanField(default=False)

    fanart = peewee.TextField(null=True)
    poster = peewee.TextField(null=True)
    banner = peewee.TextField(null=True)
    image = peewee.TextField(null=True)

    summary = peewee.TextField(null=True)
    summary_long = peewee.TextField(null=True)
    summary_medium = peewee.TextField(null=True)
    summary_short = peewee.TextField(null=True)

    show_type = peewee.TextField(null=True)

    genres_string = peewee.TextField(null=True)
    sub_genres_string = peewee.TextField(null=True)
    actors_string = peewee.TextField(null=True)

    year = peewee.CharField(max_length=4,index=True)
    premier = peewee.CharField(max_length=26)

    season = peewee.BlobField()

class Genre(BaseModel):
    """
    ORM model of the Genre table
    """
    name = peewee.TextField()

class Year(BaseModel):
    """
    ORM model of the Year table
    """
    name = peewee.TextField()

class RecentShows(BaseModel):
    """
    ORM model of the RecentShows table
    """
    show = peewee.ForeignKeyField(Show)
    recenttype = peewee.IntegerField(null=True)

class ShowGenre(BaseModel):
    """
    ORM model of the ShowGenre table
    """
    show = peewee.ForeignKeyField(Show)
    genre = peewee.ForeignKeyField(Genre)

class SubGenre(BaseModel):
    """
    ORM model of the SubGenre table
    """

    name = peewee.TextField()

class ShowSubGenre(BaseModel):
    """
    ORM model of the ShowSubGenre table
    """
    show = peewee.ForeignKeyField(Show)
    subgenre = peewee.ForeignKeyField(SubGenre)


class Actor(BaseModel):
    """
    ORM model of the Actor table
    """

    name = peewee.TextField()

class ShowActor(BaseModel):
    """
    ORM model of the ShowActor table
    """
    show = peewee.ForeignKeyField(Show)
    actor = peewee.ForeignKeyField(Actor)

class GenreToSubGenre(BaseModel):
    """
    ORM model connecting genre to subgenres
    """
    genre = peewee.ForeignKeyField(Genre)
    subgenre = peewee.ForeignKeyField(SubGenre)

class LastUpdate(BaseModel):
    """
    ORM model detailing the last update date
    """
    date = peewee.CharField(max_length=26)

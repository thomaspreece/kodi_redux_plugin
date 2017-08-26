from lib import peewee

database = peewee.SqliteDatabase(None)

########################################################################
class BaseModel(peewee.Model):
    class Meta:
        database = database

class Show(BaseModel):
    """
    ORM model of the Artist table
    """
    title = peewee.TextField(index=True)

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
    ORM model of the Artist table
    """
    name = peewee.TextField(unique = True)
    class Meta:
        database = database

class Year(BaseModel):
    """
    ORM model of the Artist table
    """
    name = peewee.TextField(unique = True)
    class Meta:
        database = database

class ShowGenre(BaseModel):
    """
    ORM model of the Artist table
    """
    show = peewee.ForeignKeyField(Show)
    genre = peewee.ForeignKeyField(Genre)

class SubGenre(BaseModel):
    """
    ORM model of the Artist table
    """

    name = peewee.TextField(unique = True)

class ShowSubGenre(BaseModel):
    """
    ORM model of the Artist table
    """
    show = peewee.ForeignKeyField(Show)
    subgenre = peewee.ForeignKeyField(SubGenre)


class Actor(BaseModel):
    """
    ORM model of the Artist table
    """

    name = peewee.TextField(unique = True)

class ShowActor(BaseModel):
    """
    ORM model of the Artist table
    """
    show = peewee.ForeignKeyField(Show)
    actor = peewee.ForeignKeyField(Actor)

from lib import peewee

database_proxy = peewee.Proxy()

########################################################################
class UserBaseModel(peewee.Model):
    class Meta:
        database = database_proxy

class UserFavouriteShow(UserBaseModel):
    show = peewee.TextField()

class UserWatchedStatus(UserBaseModel):
    show = peewee.TextField(null=True)
    season = peewee.TextField(null=True)
    episode = peewee.TextField(null=True)
    status_is_show = peewee.BooleanField(default=False)
    status_is_season = peewee.BooleanField(default=False)
    status_is_episode = peewee.BooleanField(default=False)
    in_progress = peewee.BooleanField(default=False)
    watched = peewee.BooleanField(default=False)

class UserReduxResolve(UserBaseModel):
    show = peewee.TextField()
    season = peewee.TextField()
    episode = peewee.TextField()
    diskref = peewee.TextField()

class UserReduxFile(UserBaseModel):
    show = peewee.TextField()
    season = peewee.TextField()
    episode = peewee.TextField()
    url = peewee.TextField()
    encoding = peewee.TextField()
    time = peewee.DateTimeField()

class UserLastUpdate(UserBaseModel):
    """
    ORM model detailing the last update date
    """
    date = peewee.CharField(max_length=26)

class UserDBVersion(UserBaseModel):
    version = peewee.IntegerField()

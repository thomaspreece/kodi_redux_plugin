from lib import peewee

database_proxy = peewee.Proxy()

########################################################################
class UserBaseModel(peewee.Model):
    class Meta:
        database = database_proxy

class UserFavouriteShow(UserBaseModel):
    show = peewee.TextField()

class UserLastUpdate(UserBaseModel):
    """
    ORM model detailing the last update date
    """
    date = peewee.CharField(max_length=26)

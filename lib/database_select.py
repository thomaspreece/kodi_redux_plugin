from lib import peewee

def load_database(db_type):
    if(db_type == "sqlite"):
        return peewee.SqliteDatabase(None)
    elif(db_type == "mysql"):
        return peewee.MySQLDatabase(None)
    else:
        raise ValueError("Invalid DB type")

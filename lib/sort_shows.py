def sort_shows_by_channel(shows):
    channels = {"Films": {}}
    for show in shows:
        if(shows[show]["type"] == "Films"):
            if(not show in channels["Films"]):
                channels["Films"][show] = shows[show]
        else:
            for season in shows[show]["season"]:
                for episode in shows[show]["season"][season]["episode"]:
                    service = shows[show]["season"][season]["episode"][episode]["service"]
                    if(not service in channels):
                        channels[service] = {}
                    if(not show in channels[service]):
                        channels[service][show] = shows[show]
    return channels

def sort_shows_by_year(shows):
    years = {'Unclassified':{} }
    for show in shows:
        if shows[show]['year'] != None:
            year = shows[show]['year']
            if not year in years:
                years[year] = {}
            years[year][show] = shows[show]
        else:
            years['Unclassified'][show] = shows[show]
    return years

def sort_shows_by_genre(shows):
    genres = {'Unclassified':{} }
    for show in shows:
        if shows[show]['genres'] != None and len(shows[show]['genres']) > 0:
            for j in range(len(shows[show]['genres'])):
                genre = shows[show]['genres'][j]
                if not genre in genres:
                    genres[genre] = {}
                genres[genre][show] = shows[show]
        else:
            genres['Unclassified'][show] = shows[show]
    return genres

def sort_shows_by_subgenre(shows):
    genres = {'Unclassified':{} }
    for show in shows:
        if shows[show]['sub-genres'] != None and len(shows[show]['sub-genres']) > 0:
            for j in range(len(shows[show]['sub-genres'])):
                genre = shows[show]['sub-genres'][j]
                if not genre in genres:
                    genres[genre] = {}
                genres[genre][show] = shows[show]
        else:
            genres['Unclassified'][show] = shows[show]
    return genres

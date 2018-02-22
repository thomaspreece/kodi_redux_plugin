import time
import xbmc

from lib import xbmc_util
from lib.database_functions import init_database, test_connection, update_show_watched_status
from lib.user_database_schema import UserWatchedStatus, UserReduxFile, UserBaseModel
from lib.database_schema import BaseModel

lookup = {}
currently_playing_details = {
    "filename": None
}

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(60):
            # Abort was requested while waiting. We should exit
            break

        if xbmc.Player().isPlaying():
            playing_file = xbmc.Player().getPlayingFile()
            if(currently_playing_details["filename"] != playing_file):
                currently_playing_details = {
                    "filename": playing_file
                }
            connection_tested = False
            if "bbcredux.com" in currently_playing_details["filename"]:
                if "show" not in currently_playing_details:
                    try:
                        [db_data, user_db_data] = xbmc_util.get_db_data()
                        user_connection = test_connection(user_db_data, "user")
                        show_connection = test_connection(db_data, "show")
                        if(
                            user_connection["connection_valid"] == False or
                            user_connection["preexisting_db"] == False or
                            user_connection["update_db"] == True or
                            show_connection["connection_valid"] == False or
                            show_connection["preexisting_db"] == False or
                            show_connection["update_db"] == True
                        ):
                            raise ValueError("Invalid Connection")
                        else:
                            db = UserBaseModel._meta.database
                            init_database(db, user_db_data)
                            db.connect()
                            db2 = BaseModel._meta.database
                            init_database(db2, db_data)
                            db2.connect()
                            connection_tested = True
                            reduxfiledetails = UserReduxFile.select().where(UserReduxFile.url == playing_file)
                            if(len(reduxfiledetails) > 0):
                                currently_playing_details["show"] = reduxfiledetails[0].show
                                currently_playing_details["season"] = reduxfiledetails[0].season
                                currently_playing_details["episode"] = reduxfiledetails[0].episode

                                watchedshowrows = UserWatchedStatus.select().where(
                                    UserWatchedStatus.show == currently_playing_details["show"]
                                )

                                watchedseasonrows = watchedshowrows.where(
                                    UserWatchedStatus.season == currently_playing_details["season"]
                                )

                                watchedepisoderows = watchedseasonrows.where(
                                    UserWatchedStatus.episode == currently_playing_details["episode"]
                                )

                                watchedrows =  watchedepisoderows.where(
                                    UserWatchedStatus.status_is_episode == True
                                )

                                if(len(watchedrows) == 0):
                                    UserWatchedStatus(
                                        show = currently_playing_details["show"],
                                        season = currently_playing_details["season"],
                                        episode = currently_playing_details["episode"],
                                        in_progress = False,
                                        watched = False,
                                        status_is_episode = True
                                    ).save()
                                    currently_playing_details["in_progress"] = False
                                    currently_playing_details["watched"] = False
                                else:
                                    currently_playing_details["in_progress"] = watchedrows[0].in_progress
                                    currently_playing_details["watched"] = watchedrows[0].watched


                                watchedrows =  watchedseasonrows.where(
                                    UserWatchedStatus.status_is_season == True
                                )

                                if(len(watchedrows) == 0):
                                    UserWatchedStatus(
                                        show = currently_playing_details["show"],
                                        season = currently_playing_details["season"],
                                        in_progress = False,
                                        watched = False,
                                        status_is_season = True
                                    ).save()

                                watchedrows =  watchedshowrows.where(
                                    UserWatchedStatus.status_is_show == True
                                )

                                if(len(watchedrows) == 0):
                                    UserWatchedStatus(
                                        show = currently_playing_details["show"],
                                        in_progress = False,
                                        watched = False,
                                        status_is_show = True
                                    ).save()
                            else:
                                raise ValueError("Cannot find file in db")
                            db.close()
                            db2.close()
                    except Exception,e:
                        print("Obtaining file properties show, season and episode failed")
                        print(str(e))
                        continue

                total_time = xbmc.Player().getTotalTime()
                current_time = xbmc.Player().getTime()

                started_watching = False
                finished_watching = False
                if current_time > ((total_time * 9)/10):
                    finished_watching = True
                else:
                    finished_watching = False

                if current_time > ((total_time * 1)/10):
                    started_watching = True
                else:
                    started_watching = False

                if(
                    (finished_watching == True and currently_playing_details["watched"] == False) or
                    (started_watching == True and finished_watching == False and currently_playing_details["in_progress"] == False) or
                    (started_watching == True and finished_watching == True and currently_playing_details["in_progress"] == True)
                ):
                    try:
                        [db_data, user_db_data] = xbmc_util.get_db_data()
                        if(connection_tested == False):
                            user_connection = test_connection(user_db_data, "user")
                            show_connection = test_connection(db_data, "show")
                            if(
                                user_connection["connection_valid"] == False or
                                user_connection["preexisting_db"] == False or
                                user_connection["update_db"] == True or
                                show_connection["connection_valid"] == False or
                                show_connection["preexisting_db"] == False or
                                show_connection["update_db"] == True
                            ):
                                raise ValueError("Invalid Connection")
                        db = UserBaseModel._meta.database
                        init_database(db, user_db_data)
                        db.connect()
                        db2 = BaseModel._meta.database
                        init_database(db2, db_data)
                        db2.connect()

                        if(finished_watching == True and currently_playing_details["watched"] == False):
                            UserWatchedStatus.update(watched = True).where(
                                UserWatchedStatus.show == currently_playing_details["show"] &
                                UserWatchedStatus.season == currently_playing_details["season"] &
                                UserWatchedStatus.episode == currently_playing_details["episode"] &
                                UserWatchedStatus.status_is_episode == True
                            ).execute()
                            currently_playing_details["watched"] = True

                        if(started_watching == True and finished_watching == False and currently_playing_details["in_progress"] == False):
                            UserWatchedStatus.update(in_progress = True).where(
                                UserWatchedStatus.show == currently_playing_details["show"] &
                                UserWatchedStatus.season == currently_playing_details["season"] &
                                UserWatchedStatus.episode == currently_playing_details["episode"] &
                                UserWatchedStatus.status_is_episode == True
                            ).execute()
                            currently_playing_details["in_progress"] = True

                        if(started_watching == True and finished_watching == True and currently_playing_details["in_progress"] == True):
                            UserWatchedStatus.update(in_progress = False).where(
                                UserWatchedStatus.show == currently_playing_details["show"] &
                                UserWatchedStatus.season == currently_playing_details["season"] &
                                UserWatchedStatus.episode == currently_playing_details["episode"] &
                                UserWatchedStatus.status_is_episode == True
                            ).execute()
                            currently_playing_details["in_progress"] = False

                        update_show_watched_status(currently_playing_details["show"])
                        db.close()
                        db2.close()
                    except Exception,e:
                        print("Updating show watched/in_progress status failed")
                        print(str(e))
                        continue

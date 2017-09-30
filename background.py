import time
import xbmc

if __name__ == '__main__':
    monitor = xbmc.Monitor()

    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(2):
            # Abort was requested while waiting. We should exit
            break
        if xbmc.Player().isPlaying():
            print(xbmc.Player().getPlayingFile())
            print("{0}/{1}".format(xbmc.Player().getTime(),xbmc.Player().getTotalTime()))
        

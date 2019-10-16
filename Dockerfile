FROM python:2.7.14-slim-stretch

RUN apt-get update && apt-get -y install cron procps
RUN pip install beautifulsoup4 httplib2 requests six python-dateutil cachecontrol lxml imdbpie PyMySQL pytvdbapi tmdb3

RUN mkdir -p /root/kodi-updater/
RUN mkdir -p /pickle/
RUN mkdir -p /scrapes/

WORKDIR /root/kodi-updater/

COPY lib/ lib/

COPY scrape-update-NonKodi.py scrape-update.py
COPY Settings-NonKodi.json Settings-NonKodi.json

COPY docker_resources/run_update.sh run_update.sh
RUN chmod +x run_update.sh

CMD /root/kodi-updater/run_update.sh

# Add crontab file in the cron directory
#ADD docker_resources/crontab /etc/cron.d/updatecron

# Give execution rights on the cron job
#RUN chmod 0644 /etc/cron.d/updatecron

# Create the log file to be able to run tail
#RUN touch /var/log/cron.log

# Run the command on container startup
#CMD cron && tail -f /var/log/cron.log

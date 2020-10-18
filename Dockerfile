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

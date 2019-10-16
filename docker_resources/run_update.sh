#!/bin/bash
cd /root/kodi-updater/

pgrep python
if [ $? -eq 0 ]; then
  kill $(pgrep python)
fi

pgrep python
if [ $? -eq 0 ]; then
  sleep 10
  kill -9 $(pgrep python)
fi

python -u scrape-update.py -p /pickle/ -w /scrapes/

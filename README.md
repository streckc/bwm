# Bandwidth Monitor
Started as a learning experiment and wanting to know what has been consuming the bandwidth in the household, and at what time.

![Screenshot](html/img/screenshot_1.png "Screenshot")

## Environment
Running on a linux host, that has an interface connected to a shark-tap.  Running the scripts in tmux for now.

  - bin/sniffer.py - Run as root to sniff interface and load databsae
  - bin/web_serv.py - Run native flask web server on port 8123

![Environment Diagram](html/img/environment.png "Environment Diagram")

## Requirements

General:
  - python3 (may work on 2.7+, but has not been tested)
  - sqlite3

Python Modules:
  - flask - http://flask.pocoo.org/

Javascript Additions:
  - Vis.js - http://visjs.org/ - place in html/js/vis
  - JQuery - http://jquery.com/ - place in html/js/jq
  - JQueryUI - http://jqueryui.com/ - place in html/js/jqui

## To do:
  - sniffer log to file
  - sniffer save updates to file (backup)
  - paramaterize utilities
  - configurize with configuration file
  - daemonize scripts
  - add archival of data in tables (table maintenance)
  - add override selection of data resolution in UI
  - choice of length vs count in UI

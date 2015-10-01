#!/usr/bin/env python

import sys
import os

path = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
os.chdir(path)
# Set up the path.
sys.path.insert(0, "lib")
sys.path.insert(0, "src")

import config
import cherrypy
import main

cherrypy_config = {
    "global": {
        "log.screen": None
    },
    "/": {
        "request.show_tracebacks": False,
        "request.show_mismatched_params": False,
        "log.error_file": config.ERROR_LOG
    }
}
cherrypy.quickstart(main.Main(), config=cherrypy_config)

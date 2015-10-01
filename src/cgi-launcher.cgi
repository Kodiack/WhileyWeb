#!/usr/bin/env python

import os
import cgi
import cgitb
import sys

path = os.path.dirname(os.path.realpath(__file__))
HOME_DIR = r + "\"" + path + "\""

os.chdir(HOME_DIR)

sys.path.insert(0, "lib")
sys.path.insert(0, "src")

import config

if config.DEBUG:
    cgitb.enable()

import cherrypy
import main

import wsgiref.handlers

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
def application(environ, start_response):
    app = cherrypy.tree.mount(main.Main(), config.ROOT_URL, config=cherrypy_config)
    return app(environ,start_response)

if __name__ == '__main__':
    wsgiref.handlers.CGIHandler().run(application)

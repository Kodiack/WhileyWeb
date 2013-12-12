# -*-python-*-

import os
from cherrypy.lib.static import serve_file
import subprocess
import json

# ============================================================
# Whiley Compiler Config
# ============================================================

WYJC_JAR="lib/wyjc-all-v0.3.21.jar"

# ============================================================
# Mako Config
# ============================================================

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['html'])

# ============================================================
# Application Entry
# ============================================================

class Main(object):
    def __init__(self,root_url,username):
        self.root_url = root_url
        self.username = username
    
    # gives access to images/
    def images(self, filename):
        abspath = os.path.abspath("images/" + filename)
        return serve_file(abspath, "image/png")
    images.exposed = True
    
    def js(self, filename):
        abspath = os.path.abspath("js/" + filename)
        return serve_file(abspath, "application/javascript")
    js.exposed = True

    def css(self, filename):
        abspath = os.path.abspath("css/" + filename)
        return serve_file(abspath, "text/css")
    css.exposed = True
    
    def compiler(self,code):
        return compile(code)
    compiler.exposed = True
    
    # application root
    def index(self):
        template = lookup.get_template("index.html")
        return template.render(ROOT_URL="")
    index.exposed = True
    # exposed

# ============================================================
# Compiler Interface
# ============================================================
    
# Load a given JSON file from the filesystem
def load(filename):
    f = open(filename,"r")
    data = json.load(f)
    f.close()
    return data

# Save a given file to the filesystem
def save(filename,data):
    f = open(filename,"w")
    f.write(data)
    f.close()
    return

# Compile a snippet of Whiley code.  This is done by saving the file
# to disk in a temporary location, compiling it using the Whiley2Java
# Compiler and then returning the compilation output.
def compile(code):
    # save the file
    save("tmp/tmp.whiley", code)
    # run the compiler
    proc = subprocess.Popen(["javac","-help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # return the output
    print "GOT OUTPUT: " + out
    return err
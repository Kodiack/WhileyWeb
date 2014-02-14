# -*-python-*-

import cgi
import os
import shutil
import tempfile
import subprocess
import json
import re

from cherrypy.lib.static import serve_file
from cherrypy.lib.cptools import allow
from cherrypy import HTTPRedirect

# ============================================================
# Whiley Compiler Config
# ============================================================

WYJC_JAR="lib/wyjc-all-v0.3.22.jar"
WYRT_JAR="lib/wyrt-v0.3.22.jar"

# ============================================================
# Java Config
# ============================================================

JAVA_CMD="/usr/bin/java"

# ============================================================
# Mako Config
# ============================================================

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['html'])

# ============================================================
# Application Config
# ============================================================
WORKING_DIR="data"

# ============================================================
# Application Entry
# ============================================================

class Main(object):
    def __init__(self,root_url):
        self.root_url = root_url

    # gives access to images/
    def images(self, filename, *args, **kwargs):
        allow(["HEAD", "GET"])
        abspath = os.path.abspath("images/" + filename)
        return serve_file(abspath, "image/png")
    images.exposed = True

    def js(self, filename, *args, **kwargs):
        allow(["HEAD", "GET"])
        abspath = os.path.abspath("js/" + filename)
        return serve_file(abspath, "application/javascript")
    js.exposed = True

    def css(self, filename, *args, **kwargs):
        allow(["HEAD", "GET"])
        abspath = os.path.abspath("css/" + filename)
        return serve_file(abspath, "text/css")
    css.exposed = True

    def compile(self, code, verify, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        dir = WORKING_DIR + "/" + dir
        # Second, compile the code
        result = compile(code,verify,dir)
        # Third, delete working directory
        shutil.rmtree(dir)
        # Fouth, return result as JSON
        if type(result) == str:
            response = {"result": "error", "error": str}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
        return json.dumps(response)
    compile.exposed = True

    def save(self, code, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        # Second, save the file
        save(WORKING_DIR + "/" + dir + "/tmp.whiley", code)
        # Fouth, return result as JSON
        return json.dumps({
            "id": dir
        })
    save.exposed = True

    def run(self, code, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        dir = WORKING_DIR + "/" + dir
        # Second, compile the code and then run it
        result = compile(code,"false",dir)
        if type(result) == str:
            response = {"result": "error", "error": str}
        elif len(result) != 0:
            response = {"result": "errors", "errors": result}
        else:
            response = {"result": "success"}
            # Run the code if the compilation succeeded.
            output = run(dir)
            response["output"] = output
        # Third, delete working directory
        shutil.rmtree(dir)
        # Fourth, return result as JSON
        return json.dumps(response)
    run.exposed = True

    # application root
    def index(self, id="HelloWorld", *args, **kwargs):
        allow(["HEAD", "GET"])
        error = ""
        redirect = "NO"
        try:
            # Sanitize the ID.
            safe_id = re.sub("[^a-zA-Z0-9-_]+", "", id)
            # Load the file
            code = load(WORKING_DIR + "/" + safe_id + "/tmp.whiley")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("index.html")
        return template.render(ROOT_URL=self.root_url,CODE=code,ERROR=error,REDIRECT=redirect)
    index.exposed = True
    # exposed

    # Everything else should redirect to the main page.
    def default(self, *args, **kwargs):
        raise HTTPRedirect("/")
    default.exposed = True

# ============================================================
# Compiler Interface
# ============================================================

# Load a given JSON file from the filesystem
def load(filename):
    f = open(filename,"r")
    data = f.read()
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
def compile(code,verify,dir):

    filename = dir + "/tmp.whiley"
    # set required arguments
    args = [
            JAVA_CMD,
            "-jar",
            WYJC_JAR,
            "-bootpath", WYRT_JAR, # set bootpath
            "-whileydir", dir,     # set location of Whiley source file(s)
            "-classdir", dir,      # set location to place class file(s)
            "-brief"              # enable brief compiler output (easier to parse)
        ]
    # Configure optional arguments
    if verify == "true":
        args.append("-verify")
    # save the file
    save(filename, code)
    args.append(filename)
    # run the compiler
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        (out, err) = proc.communicate()
        if err == None:
            return splitErrors(out)
        else:
            return splitErrors(err)
    except Exception as ex:
        # error, so return that
        return "Compile Error: " + str(ex)

def run(dir):
    try:
        # run the JVM
        proc = subprocess.Popen([
            JAVA_CMD,
            "-cp",WYJC_JAR + ":" + dir,
            "tmp"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        (out, err) = proc.communicate()
        return out
    except Exception as ex:
        # error, so return that
        return "Run Error: " + str(ex)

# Split errors output from WyC into a list of JSON records, each of
# which includes the filename, the line number, the column start and
# end, as well a the text of the error itself.
def splitErrors(errors):
    r = []
    for err in errors.split("\n"):
        if err != "":
            r.append(splitError(err))
    return r

def splitError(error):
    parts = error.split(":", 4)
    if len(parts) == 5:
        return {
            "filename": parts[0],
            "line": parts[1],
            "start": parts[2],
            "end": parts[3],
            "text": parts[4]
        }
    else:
        return {
            "filename": "",
            "line": "",
            "start": "",
            "end": "",
            "text": error
        }

# Get the working directory for this request.
def createWorkingDirectory():
    dir = tempfile.mkdtemp(prefix="",dir=WORKING_DIR)
    tail,head = os.path.split(dir)
    return head

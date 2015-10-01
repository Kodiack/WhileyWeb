# -*-python-*-

import cgi
import os
import shutil
import tempfile
import subprocess
import json
import re
import codecs
from threading import Timer

import config

from cherrypy.lib.static import serve_file
from cherrypy.lib.cptools import allow
from cherrypy import HTTPRedirect

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['html'])

# ============================================================
# Application Entry
# ============================================================

class Main(object):

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
        dir = config.DATA_DIR + "/" + dir
        # Second, compile the code
        result = compile(code,verify,dir)
        # Third, delete working directory
        shutil.rmtree(dir)
        # Fouth, return result as JSON
        if type(result) == str:
            response = {"result": "error", "error": result}
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
        save(config.DATA_DIR + "/" + dir + "/tmp.whiley", code, "utf-8")
        # Fouth, return result as JSON
        return json.dumps({
            "id": dir
        })
    save.exposed = True

    def run(self, code, *args, **kwargs):
        allow(["HEAD", "POST"])
        # First, create working directory
        dir = createWorkingDirectory()
        dir = config.DATA_DIR + "/" + dir
        # Second, compile the code and then run it
        result = compile(code,"false",dir)
        if type(result) == str:
            response = {"result": "error", "error": result}
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
            code = load(config.DATA_DIR + "/" + safe_id + "/tmp.whiley","utf-8")
            # Escape the code
            code = cgi.escape(code)
        except Exception:
            code = ""
            error = "Invalid ID: %s" % id
            redirect = "YES"
        template = lookup.get_template("index.html")
        return template.render(ROOT_URL=config.VIRTUAL_URL,CODE=code,ERROR=error,REDIRECT=redirect)
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
def load(filename,encoding):
    f = codecs.open(filename,"r",encoding)
    data = f.read()
    f.close()
    return data

# Save a given file to the filesystem
def save(filename,data,encoding):
    f = codecs.open(filename,"w",encoding)
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
            config.JAVA_CMD,
            "-jar",
            config.WYJC_JAR,            
            "-bootpath", config.WYRT_JAR, # set bootpath
            "-whileydir", dir,     # set location of Whiley source file(s)
            "-classdir", dir,      # set location to place class file(s)
            "-brief"              # enable brief compiler output (easier to parse)
        ]
    # Configure optional arguments
    if verify == "true":
        args.append("-verify")
    # save the file
    save(filename, code, "utf-8")
    args.append(filename)
    # run the compiler
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        # Configure Timeout
        kill_proc = lambda p: p.kill()
        timer = Timer(30, kill_proc, [proc])
        timer.start()
        # Run process        
        (out, err) = proc.communicate()
        timer.cancel()
        # Check what happened
        if proc.returncode < 0:
            return [{
                "filename": "",
                "line": "",
                "start": "",
                "end": "",
                "text": "Compiling / Verifying your program took too long!"
            }]
        # Continue
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
            config.JAVA_CMD,
            "-Djava.security.manager",
            "-Djava.security.policy=whiley.policy",
            "-cp",config.WYJC_JAR + ":" + dir,
            "tmp"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        # Configure Timeout
        kill_proc = lambda p: p.kill()
        timer = Timer(20, kill_proc, [proc])
        timer.start()
        # Run process        
        (out, err) = proc.communicate()
        timer.cancel()
        # Check what happened
        if proc.returncode >= 0:
            return out
        else:
            return "Timeout: Your program ran for too long!"
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
    if len(parts) >= 5:
        context = []
        if len(parts) == 6:
            context = splitContext(parts[5])
        
        return {
            "filename": parts[0],
            "line": int(parts[1]),
            "start": int(parts[2]),
            "end": int(parts[3]),
            "text": parts[4],
            "context": context
        }
    else:
        return {
            "filename": "",
            "line": "",
            "start": "",
            "end": "",
            "text": error
        }

def splitContext(context):
    r = []
    cs = context.split(",")
    for c in cs:
        parts = c.split(":", 3)
        r.append({
            "filename": parts[0],
            "line": int(parts[1]),
            "start": int(parts[2]),
            "end": int(parts[3])
        })
    return r

# Get the working directory for this request.
def createWorkingDirectory():
    dir = tempfile.mkdtemp(prefix="",dir=config.DATA_DIR)
    tail,head = os.path.split(dir)
    return head

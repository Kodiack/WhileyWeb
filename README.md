WhileyWeb
=========

A very simple web-interface for editing and compiling Whiley programs from a web-browser.  Requires a dedicated server which receives AJAX requests, runs the Whiley Compiler, and returns the results.

Dependencies
------------

WhileyWeb requires the following Python libraries to be installed and available:

* [CherryPy](http://www.cherrypy.org/)
* [Mako Templates](http://www.makotemplates.org/)

Setup
-----

WhileyWeb requires a configuration file called `config.py` to run. Included in the repository is an example config file called `example-config.py` which you can base your config file off.

All of the configuration options are mandatory as their are defaults built-in, but it is likely that you will need to change `ROOT_URL`, and possible `JAVA_CMD`. If you are running WhileyWeb as a CGI, then you will probably need to change `HOME_DIR` as well.

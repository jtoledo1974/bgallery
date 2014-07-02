import os
from os.path import join, dirname, basename
import logging
logging.basicConfig(level=logging.DEBUG)

from bottle import route, run, static_file

ROOT = "/home/toledo/2014"


@route('/hello')
def hello():
    return "Hello World!"


@route('/')
def root():
    logging.debug("root")
    return folder('')


@route('/<path:path>/')
def folder(path):
    logging.debug("path %s" % path)
    path = join(ROOT, path)
    return {'listdir': os.listdir(path)}


@route("/<path:path>")
def file(path):
    logging.debug("file %s" % path)
    filedir = join(ROOT, dirname(path))
    filename = basename(path)
    return static_file(filename, root=filedir)

run(host='localhost', port=8080, debug=True)

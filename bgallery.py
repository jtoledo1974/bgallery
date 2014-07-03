import os
from os.path import join, dirname, basename, isfile, isdir, splitext, relpath
from tempfile import NamedTemporaryFile
from urllib import unquote
import logging
logging.basicConfig(level=logging.DEBUG)

from bottle import route, run, static_file
from DNG import DNG

root = "/home/toledo/2014"


@route('/hello')
def hello():
    return "Hello World!"


@route('/')
def get_root():
    logging.debug("get_root")
    return folder('')


@route("/thumb/<path:path>")
def thumb(path):
    logging.debug("thumb %s" % path)
    thumb_path = get_thumb(path)
    filedir = join(root, dirname(thumb_path))
    filename = basename(thumb_path)
    res = static_file(filename, root=filedir)
    return res


@route('/<path:path>/')
def folder(path):
    logging.debug("path %s" % path)
    path = join(root, path)
    return {'listdir': os.listdir(path)}


@route("/<path:path>")
def file(path):
    path = unquote(path)
    logging.debug("file %s" % path)
    filedir = join(root, dirname(path))
    filename = basename(path)
    return static_file(filename, root=filedir)


def get_thumb(path):
    path = unquote(path)
    path = join(root, path)
    try:
        if isdir(path):
            return get_dir_thumb(path)
        elif isfile(path):
            return get_file_thumb(path)
        else:
            return ''
    except:
        return ""


def get_dir_thumb(path):
    img = [de for de in os.listdir(path)
           if splitext(de)[1].lower() == '.dng'][0]
    return get_file_thumb(join(path, img))


def get_file_thumb(path):
    with DNG(path) as dng:
        thumb = NamedTemporaryFile(
            dir=join(root, ".thumb"), suffix=".jpg", delete=False)
        thumb.write(dng.read_jpeg_preview(0))
        return relpath(thumb.name, root)


run(host='localhost', port=8080, debug=True)

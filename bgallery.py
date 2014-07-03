import os
from os.path import join, dirname, basename, isfile, isdir, splitext, relpath
from tempfile import NamedTemporaryFile
from urllib import unquote
import subprocess
import logging

from bottle import route, run, static_file
from DNG import DNG, JPG

FNULL = open(os.devnull, 'w')  # Se usa para redirigir a /dev/null
root = "/home/toledo/2014"

logging.basicConfig(level=logging.DEBUG)


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
    thumb_path, orientation = get_thumb(path)
    filedir = join(root, dirname(thumb_path))
    filename = basename(thumb_path)
    res = static_file(filename, root=filedir)
    res.set_header('Orientation', orientation)
    return res


@route('/<path:path>/')
def folder(path):
    logging.debug("path %s" % path)
    path = join(root, path)
    res  = [(de, get_thumb(de)[1])
            for de in sorted(os.listdir(path))]
    return {'listdir': res}


@route("/<path:path>")
def file(path):
    path = unquote(path)
    logging.debug("file %s" % path)
    filedir = join(root, dirname(path))
    filename = basename(path)
    return static_file(filename, root=filedir)


def get_thumb(path):
    path = unquote(path)
    logging.debug("get_thumb %s" % path)
    path = join(root, path)
    try:
        if isdir(path):
            return get_dir_thumb(path)
        elif isfile(path):
            return get_file_thumb(path)
        else:
            return ('', 1)
    except:
        return ("", 1)


def get_dir_thumb(path):
    logging.debug("get_dir_thumb %s" % path)
    img = [de for de in os.listdir(path)
           if splitext(de)[1].lower() in ('.dng', '.jpg', '.jpeg')][0]
    return get_file_thumb(join(path, img))


def get_file_thumb(path):
    logging.debug("get_file_thumb %s" % path)

    ext = splitext(path)[1].lower()
    IMG = {'.dng': DNG, '.jpg': JPG, '.jpeg': JPG}[ext]

    with IMG(path) as img:
        thumb = NamedTemporaryFile(
            dir=join(root, ".thumb"), suffix=".jpg", delete=False)
        thumb.write(img.read_jpeg_preview(0))
        thumb.close()
        try:
            orientation = img.Orientation
        except:
            orientation = 1
            logging.debug("Unable to set Orientation information")
        return (relpath(thumb.name, root), orientation)


run(host='localhost', port=8080, debug=True)

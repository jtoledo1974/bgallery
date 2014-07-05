import os
from os.path import join, dirname, basename, isfile, isdir, splitext, relpath
from urllib import unquote

from bottle import route, run, static_file
from previewcache import set_thumbdir, get_preview
from DNG import logging

root = "/srv/originales"
set_thumbdir('/srv/originales/.previewcache')

logging.basicConfig(level=logging.DEBUG)


class HiddenError(StandardError):
    pass


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
    res.set_header('Content-Type', 'image/jpeg')
    return res


@route('/<path:path>/')
def folder(path):
    path = unquote(path)
    logging.debug("folder %s" % path)
    realpath = join(root, path, '')
    res = [(de, get_thumb(join(realpath, de)))
           for de in sorted(os.listdir(realpath), reverse=True)]
    res = [(de, orientation)
           for de, (thumb_path, orientation) in res
           if thumb_path]
    return {'listdir': res, 'dir': path}


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
    except Exception as e:
        logging.warning(
            "Failed to retrieve a thumbnail for %s: %s" % (path, e))
        return ("", 1)


def get_dir_thumb(path):
    logging.debug("get_dir_thumb %s" % path)
    try:
        listdir = os.listdir(path)
        if ".nomedia" in listdir:
            raise HiddenError
        img = [de for de in listdir
               if splitext(de)[1].lower() in ('.dng', '.jpg', '.jpeg')][0]
        res = get_file_thumb(join(path, img))
        logging.debug("Got result %s %s" % res)
        return res
    except IndexError:
        # import pdb; pdb.set_trace()
        img = [d for d in os.listdir(path)
               if isdir(join(path, d))][0]
        return get_dir_thumb(join(path, d))


def get_file_thumb(path):
    logging.debug("get_file_thumb %s" % path)
    (thumb, orientation) = get_preview(path, thumbnail=True,
                                       return_orientation=True)
    return (relpath(thumb, root), orientation)


run(host='192.168.1.40', port=8888, debug=True)

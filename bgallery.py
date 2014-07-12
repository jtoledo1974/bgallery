import os
from os.path import join, dirname, basename, isfile, isdir
from urllib import unquote
from json import dumps

from bottle import route, run, static_file, response
from previewcache import set_thumbdir, get_preview, PreviewError
from DNG import logging

# Root directory
root = "/srv/originales"
root = join(root, '')  # Guarantees roots end in /, relevant in get_file_thumb

# Preview cache dirctory
thumbdir = join(root, '.previewcache')
set_thumbdir(thumbdir)
open(join(thumbdir, ".nomedia"), "w")  # Make sure  we dont't try to serve it

logging.basicConfig(level=logging.CRITICAL)

DIR = 'dir'
FILE = 'file'


class HiddenError(StandardError):
    pass


def trace():
    import pdb
    pdb.set_trace()


@route('/hello')
def hello():
    return "Hello World!"


@route('/')
def get_root():
    logging.debug("get_root")
    return folder('')


@route("/thumb/<path:path>.jpg")
def thumb(path):
    logging.debug("thumb %s" % path)
    thumb_path, orientation, file_type = get_thumb(path)
    filedir = join(root, dirname(thumb_path))
    filename = basename(thumb_path)
    res = static_file(filename, root=filedir)
    res.set_header('Orientation', orientation)
    res.set_header('Content-Type', 'image/jpeg')
    return res


@route("/jpeg/<path:path>.jpg")
def jpeg(path):
    logging.debug("jpeg %s" % path)
    preview_path, orientation = get_file_preview(path)
    filedir = join(root, dirname(preview_path))
    filename = basename(preview_path)
    res = static_file(filename, root=filedir)
    res.set_header('Orientation', orientation)
    res.set_header('Content-Type', 'image/jpeg')
    return res


@route('/<path:path>/')
def folder(path):
    path = unquote(path)
    logging.debug("folder %s" % path)
    realpath = join(root, path, '')

    response.content_type = 'text/utf-8'

    yield dumps({'dir': path})+'\n'

    direntries = []

    for de in os.listdir(realpath):
        thumb_path, orientation, file_type = get_thumb(join(realpath, de))
        if thumb_path:
            direntries.append([de, orientation, file_type])

    direntries = sorted([t for t in direntries if t[2] == DIR], reverse=True)\
        + sorted([t for t in direntries if t[2] == FILE])

    for t in direntries:
        de, orientation, file_type = t
        s = dumps([de, orientation, file_type])+'\n'
        logging.debug(s)
        yield s


@route("/<path:path>")
def file(path):
    path = unquote(path)
    logging.debug("file %s" % path)
    filedir = join(root, dirname(path))
    filename = basename(path)
    return static_file(filename, root=filedir)


# TODO The unquoting and joining should probably be done at
# the web level, it is certainly inconsistent, with the file here
# and the generic in the thumb case
def get_file_preview(path):
    path = unquote(path)
    logging.debug("get_preview %s" % path)
    path = join(root, path)
    (preview, orientation) = get_preview(path, return_orientation=True)
    # Using relpath is very inefficient here, so we don't do it
    return (preview[len(root):], orientation)


def get_thumb(path):
    path = unquote(path)
    logging.debug("get_thumb %s" % path)
    path = join(root, path)
    try:
        # TODO Might be worth avoiding this isdir check
        if isdir(path):
            return get_dir_thumb(path) + (DIR,)
        elif isfile(path):
            return get_file_thumb(path) + (FILE,)
        else:
            return ('', 0, None)
    except Exception as e:
        logging.warning(
            "Failed to retrieve a thumbnail for %s: %s" % (path, e))
        return ("", 0, None)


def get_dir_thumb(path):
    logging.debug("get_dir_thumb %s" % path)
    try:
        listdir = os.listdir(path)
        if ".nomedia" in listdir:
            raise HiddenError
        # splitext is very inefficient here, so we don't use it
        img = [de for de in listdir
               if de[-4:].lower() in ('.dng', '.jpg', 'jpeg')][0]
        res = get_file_thumb(join(path, img))
        logging.debug("Got result %s %s" % res)
        return res
    except (PreviewError, IndexError):
        # No proper images in the directory.
        # Recurse into the subdirectories
        dirlist = [d for d in os.listdir(path)
                   if isdir(join(path, d))]
        d = dirlist.pop(0)
        while(d):
            try:
                return get_dir_thumb(join(path, d))
            except (PreviewError, IndexError):
                d = dirlist.pop(0)


def get_file_thumb(path):
    logging.debug("get_file_thumb %s" % path)
    (thumb, orientation) = get_preview(path, thumbnail=True,
                                       return_orientation=True)
    # Using relpath is very inefficient here, so we don't do it
    return (thumb[len(root):], orientation)

if __name__ == '__main__':
    run(host='192.168.1.40', port=8888, debug=True)

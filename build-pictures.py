#!/usr/bin/env python3

import os
import datetime
import time
import logging

from subprocess import call, Popen, PIPE
from string import Template

from PIL import Image, ExifTags

OUT_DIR = "out/"
SRC_DIR = "src/"
IMAGE_DIR = "img/"
OUT_IMG_DIR = os.path.join(OUT_DIR, IMAGE_DIR)
SRC_IMG_DIR = os.path.join(SRC_DIR, IMAGE_DIR)

# IPTC lookup values
IMAGE_DESC = 270
TIMESTAMP = 36868

logging.basicConfig(level=logging.DEBUG)

def formatTitle(dirname):
    logging.debug("formatting title")
    return dirname.replace("_", " ")

# set up necessary dir structure
def ensure_dir(d):
    if not os.path.exists(d): 
        os.makedirs(d)

def isJpeg(f):
    return f.endswith(".jpg") or f.endswith(".JPG")

ensure_dir(OUT_DIR)
ensure_dir(OUT_IMG_DIR)

def createThumb(size, src, dest):
    if not os.path.exists(dest):
        print("creating thumbnail of", dest, "size", size)
        call("convert {0} -resize {2}x{2} {1}".format(src, dest, size), shell=True)
    else:
        logging.debug(dest, "already exists")
    

# generate compressed pics
# all go in one directory: out/img
print("generating compressed pics")
for dpath, dnames, fnames in os.walk(os.path.join(SRC_DIR, IMAGE_DIR)):
    for f in fnames:
        src = os.path.join(dpath, f) 
        dest = os.path.join(OUT_IMG_DIR, f)

        if not isJpeg(f):
            continue

        if not os.path.exists(dest): 
            print(src, "->", dest)
            call("convert -strip -interlace plane -gaussian-blur 0.05 -quality 85% {} {}".
                format(src, dest), shell=True)
        # else:
        #     print(src, "already exists")

        createThumb(800, dest, "{}.small".format(dest))


# remove pictures in out/img/ that don't exist in src/img/
src_files = [files for r, d, files in os.walk(SRC_IMG_DIR)]
src_files = [item for sublist in src_files for item in sublist]

for dpath, dnames, fnames in os.walk(OUT_IMG_DIR):
    for f in fnames:
        if isJpeg(f) and not f in src_files:
            print("removing", f)
            call("rm {}*".format(os.path.join(dpath, f)), shell=True)

# copy css
print("copying css")
call("cp {} {}".format(os.path.join(SRC_DIR, "*.css"), OUT_DIR), shell=True)

# use pictures to build html
print("generating html")

def makeStub(path):
    return Template(open(path).read())

index_template = makeStub(os.path.join(SRC_DIR, "index.html"))
pictures_template =  makeStub(os.path.join(SRC_DIR, "pictures.html"))
pic_stub_template = makeStub(os.path.join(SRC_DIR, "picture_stub.html"))
album_stub_template = makeStub(os.path.join(SRC_DIR, "album_stub.html"))

# do this for each directory in /img/
def build_pictures_page(d, title):
    pics = ""
    timestamps = []

    for dpath, dnames, fnames in os.walk(os.path.join(SRC_IMG_DIR, d)):
        for f in fnames:
            if isJpeg(f):
                uri= os.path.join(IMAGE_DIR, d, f)
                out_uri = os.path.join(IMAGE_DIR, f)

                src = os.path.join(SRC_DIR, uri)
                exif = Image.open(src)._getexif()

                if IMAGE_DESC in exif:
                    desc = exif[IMAGE_DESC]
                else:
                    desc = ""
                    logging.info("no description for {}".format(uri))

                if TIMESTAMP in exif:
                    t = datetime.datetime.strptime(exif[TIMESTAMP], "%Y:%m:%d %H:%M:%S")
                    timestamps.append(t)
                    date = t.strftime('%a %B %d %-H:%M:%S %Y')
                else: 
                    raise("No timestamp?!?!?")

                pics += pic_stub_template.substitute(large_uri=out_uri, 
                        img_uri=out_uri+".small", 
                        alt="",
                        caption=desc,
                        date=date)

    page = pictures_template.substitute(title=title, pictures=pics)
    open(os.path.join(OUT_DIR, d+".html"), 'w').write(page)

    return min(timestamps), max(timestamps)

def album_time_string(min_time, max_time):
    format_string = "%B %d, %Y"
    date = min_time.strftime(format_string)

    if (max_time - min_time).days > 0:
        date += " - {}".format(max_time.strftime(format_string))
    
    return date


# build a page for each subdir in /img/ and add a link to index.html
items = []
for d in next(os.walk(SRC_IMG_DIR))[1]:

    if not os.listdir(os.path.join(SRC_IMG_DIR, d)):
        print("empty dir", d)
        continue

    print("building page for", d)
    title = formatTitle(d)
    min_time, max_time = build_pictures_page(d, title)
    f = "{}.html".format(d)

    time_string = album_time_string(min_time, max_time)

    stub = album_stub_template.substitute(path=f, title=title, date=time_string)
    items.append((min_time, max_time, stub))

items = sorted(items, key=lambda x: x[0], reverse=True)

links = ""
for i in items:
    links += i[2]
    

# add links to index, and write index to out/
index = index_template.substitute(pictures=links)
open(os.path.join(OUT_DIR, "index.html"), 'w').write(index)

print("done!")

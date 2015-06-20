#!/usr/bin/env python3

# /img
#   /page1
#       /heading1
#             images...
#       /heading2
#   /page2
#       images...
# Nothing allowed in root img dir
# Anything in a subfolder gets a heading
# any images in direct child dir of /img are displayed without heading

import os
import datetime
import time

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
        print(dest, "already exists")

# generate compressed pics
for dpath, dnames, fnames in os.walk(os.path.join(SRC_DIR, IMAGE_DIR)):
    for f in fnames:
        src = os.path.join(dpath, f) 
        dest = os.path.join(OUT_IMG_DIR, f)

        if not isJpeg(f):
            continue

        if not os.path.exists(dest): 
            print(src, "->", dest)
            call("convert -strip -interlace Plane -gaussian-blur 0.05 -quality 85% {} {}".
                format(src, dest), shell=True)
        else:
            print(src, "already exists")

        createThumb(800, dest, "{}.small".format(dest))
        createThumb(400, dest, "{}.smaller".format(dest))
        

# remove pictures in out/img/ that don't exist in src/img/
for dpath, dnames, fnames in os.walk(OUT_IMG_DIR):
    for f in fnames:
        if isJpeg(f) and not os.path.exists(os.path.join(SRC_IMG_DIR, f)):
            print("removing", f)
            call("rm {}*".format(os.path.join(dpath, f)), shell=True)


# copy style.css
print("copying css")
call("cp {} {}".format(os.path.join(SRC_DIR, "*.css"), OUT_DIR), shell=True)

# use pictures to build html
print("generating index.html")

index = open(os.path.join(SRC_DIR, "index.html")).read()
pic_stub = open(os.path.join(SRC_DIR, "picture.html")).read()

pic_template = Template(pic_stub) 
index_template = Template(index)


pics = ""
for dpath, dnames, fnames in os.walk(OUT_IMG_DIR):
    for f in fnames:
        if isJpeg(f):
            uri= os.path.join(IMAGE_DIR, f)

            src = os.path.join(SRC_DIR, uri)
            exif = Image.open(src)._getexif()

            if IMAGE_DESC in exif:
                desc = exif[IMAGE_DESC] + "<br>"
                print(desc)
            else:
                desc = ""
                print("no description for", uri)

            if TIMESTAMP in exif:
                t = datetime.datetime.strptime(exif[TIMESTAMP], "%Y:%m:%d %H:%M:%S")
                date = t.strftime('%a %B %d %-H:%M:%S %Y')
            else: 
                raise("No timestamp?!?!?")

            pics += pic_template.substitute(large_uri=uri, 
                    img_uri=uri+".small", 
                    alt="",
                    caption="{}{}".format(desc, date))

index = index_template.substitute(pictures=pics)
open(os.path.join(OUT_DIR, "index.html"), 'w').write(index)

print("done!")


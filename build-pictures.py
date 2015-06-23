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

def formatTitle(dirname):
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
    # else: 
    #     print(dest, "already exists")
        

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
        else:
            print(src, "already exists")

        createThumb(800, dest, "{}.small".format(dest))


# remove pictures in out/img/ that don't exist in src/img/
def clean():
    # src_files = [f for f in [files for r, d, files in os.walk(SRC_IMG_DIR)]]
    src_files = [files for r, d, files in os.walk(SRC_IMG_DIR)]
    src_files = [item for sublist in src_files for item in sublist]

    for dpath, dnames, fnames in os.walk(OUT_IMG_DIR):
        for f in fnames:
            if isJpeg(f) and not f in src_files:
                print("removing", f)
                call("rm {}*".format(os.path.join(dpath, f)), shell=True)

clean()

# copy css
print("copying css")
call("cp {} {}".format(os.path.join(SRC_DIR, "*.css"), OUT_DIR), shell=True)

# use pictures to build html
print("generating index.html")

index = open(os.path.join(SRC_DIR, "index.html")).read()
pic_stub = open(os.path.join(SRC_DIR, "picture.html")).read()

pic_template = Template(pic_stub) 
index_template = Template(index)

# do this for each directory in /img/
def build_pictures_page(d):
    pics = ""

    for dpath, dnames, fnames in os.walk(os.path.join(SRC_IMG_DIR, d)):
        for f in fnames:
            if isJpeg(f):
                uri= os.path.join(IMAGE_DIR, d, f)
                out_uri = os.path.join(IMAGE_DIR, f)

                src = os.path.join(SRC_DIR, uri)
                exif = Image.open(src)._getexif()

                if IMAGE_DESC in exif:
                    desc = exif[IMAGE_DESC]
                    # print(desc)
                    desc += "<br>"
                else:
                    desc = ""
                    print("[no description for {}]".format(uri))

                if TIMESTAMP in exif:
                    t = datetime.datetime.strptime(exif[TIMESTAMP], "%Y:%m:%d %H:%M:%S")
                    date = t.strftime('%a %B %d %-H:%M:%S %Y')
                else: 
                    raise("No timestamp?!?!?")

                pics += pic_template.substitute(large_uri=out_uri, 
                        img_uri=out_uri+".small", 
                        alt="",
                        caption="{}{}".format(desc, date))

    page = index_template.substitute(pictures=pics)
    open(os.path.join(OUT_DIR, d+".html"), 'w').write(page)

# build a page for each subdir in /img/ and add a link to index.html
links = ""
for d in next(os.walk(SRC_IMG_DIR))[1]:
    print("building page for", d)
    build_pictures_page(d)
    links += '<li><a href="{}.html">{}<//a></li>'.format(d, formatTitle(d))

# add links to index, and write index to out/
index = index_template.substitute(pictures=links)
open(os.path.join(OUT_DIR, "index.html"), 'w').write(index)

print("done!")


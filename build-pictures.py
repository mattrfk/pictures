#!/usr/bin/env python

#TODO: multi-dir support

import os
import datetime

from subprocess import call
from subprocess import Popen
from subprocess import PIPE
from string import Template

OUT_DIR = "out/"
SRC_DIR = "src/"
IMAGE_DIR = "img/"
OUT_IMG_DIR = os.path.join(OUT_DIR, IMAGE_DIR)
SRC_IMG_DIR = os.path.join(SRC_DIR, IMAGE_DIR)


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
print("copying style.css")
call("cp {} {}".format(os.path.join(SRC_DIR, "style.css"), OUT_DIR), shell=True)

# use pictures to build html
print("generating index.html")
print("generating captions...")

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

            #TODO: this is real slow... maybe PIL/Pillow is faster??
            # get date and description
            desc = Popen(["identify", "-format", "%[IPTC:2:120]", src], stdout=PIPE).communicate()[0]
            desc = desc.decode("utf-8")

            dateCreated = Popen(["identify", "-format", "%[IPTC:2:55]", src], stdout=PIPE).communicate()[0]
            timeCreated = Popen(["identify", "-format", "%[IPTC:2:60]", src], stdout=PIPE).communicate()[0]

            dc = dateCreated.decode("utf-8") 
            tc = timeCreated.decode("utf-8")
            
            t = datetime.datetime(
                    int(dc[:4]),        # year
                    int(dc[4:6]),       # month 
                    int(dc[6:8]),       # day
                    int(tc[:2]),        # hour
                    int(tc[2:4]),       # min
                    int(tc[4:6]))       # second

            date = t.strftime('%a %B %d %-H:%M:%S %Y')

            if not desc == "":
                desc += "<br>"
                


            pics += pic_template.substitute(large_uri=uri, 
                    img_uri=uri+".small", 
                    alt="",
                    caption="{}{}".format(desc, date))

index = index_template.substitute(pictures=pics)
open(os.path.join(OUT_DIR, "index.html"), 'w').write(index)
print("done!")


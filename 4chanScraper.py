#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import os
import json
import urllib2
from optparse import OptionParser


#URLS
BOARDSURL = "http://a.4cdn.org/boards.json"
THREADSURL = "http://a.4cdn.org/{0}/threads.json"
THREADURL = "http://a.4cdn.org/{0}/thread/{1}.json"
FILEURL = "http://i.4cdn.org/{0}/{1}{2}"

BOARDSLIST = []
OUTPATH = ""

def getJson(url):
    try:
        f = urllib2.urlopen(url)
        data = f.read()
        return json.loads(data)
    except urllib2.HTTPError, e:
        sys.stderr.write("HTTP Error: {0} {1}\r\n".format(e.code, url))
    except urllib2.URLError, e:
        sys.stderr.write("URL Error: {0} {1}\r\n".format(e.reason, url))
    except :
        sys.stderr.write("Unknown error... \r\n")


def loadBoards(js, toprint):
    boards = js
    res = []
    for board in boards["boards"]:
        res.append(board["board"])
        if toprint:
            sys.stdout.write(unicode("{0}\t=> {1}\r\n").format(board["board"], board["title"]))
    return res

    
def loadThreads(js, toprint):
    threads = js
    res = []
    for page in threads:
        for thread in page["threads"]:
            res.append(str(thread["no"]))
            if toprint:
                sys.stdout.write(unicode("{0}\r\n").format(thread["no"]))
    return res


def loadFiles(js, toprint, board, filetype):
    ftype = ""
    if filetype != None:
        ftype = "."+filetype.lower()
    posts = js
    res = []
    for post in posts["posts"]:
        if "tim" in post:
            if ftype != "":
                if ftype == post["ext"]:
                    res.append(FILEURL.format(board, post["tim"], post["ext"]))
                    if toprint:
                        sys.stdout.write(FILEURL.format(board, post["tim"], post["ext"])+"\r\n")
            else:
                res.append(FILEURL.format(board, post["tim"], post["ext"]))
                if toprint:
                    sys.stdout.write(FILEURL.format(board, post["tim"], post["ext"])+"\r\n")
    return res
        
def downloadFiles(urllist, outdir):
    for url in urllist:
        try:
            filename = os.path.join(outdir, os.path.basename(url))
            if (os.path.isfile(filename)):
                sys.stdout.write("File {0} already exists... skipping !\r\n".format(filename))
                continue
            sys.stdout.write("Downloading {0}...\r\n".format(url))
            f = urllib2.urlopen(url)
            # Open our local file for writing
            with open(filename, "wb") as local_file:
                local_file.write(f.read())
        #handle errors
        except urllib2.HTTPError, e:
            sys.stderr.write("HTTP Error: {0} {1}\r\n".format(e.code, url))
        except urllib2.URLError, e:
            sys.stderr.write("URL Error: {0} {1}\r\n".format(e.reason, url))
        except :
            sys.stderr.write("Unknown error... \r\n")

parser = OptionParser()

parser.add_option("-b", "--board", dest="boardid", help="Specify the board name")
parser.add_option("-t", "--thread", dest="threadid", help="Specify the thread ID")
parser.add_option("-f", "--filetype", dest="filetype", help="Specify the filetype restriction")
parser.add_option("-o", "--output", dest="outdir", help="Specify the output directory")
parser.add_option("-l", "--list-boards", dest="listboards",action="store_true", help="Print the boards available")
parser.add_option("-m", "--list-threads", dest="listthreads",action="store_true", help="Print the threads available for a dedicated board")
parser.add_option("-n", "--list-files", dest="listfiles",action="store_true", help="Print the files available for a dedicated thread, filetype can be filtered with -f / --filetype")

(options, args) = parser.parse_args()


if options.listboards:
    loadBoards(getJson(BOARDSURL), True)
    exit(0)
else:
    BOARDSLIST = loadBoards(getJson(BOARDSURL), False)

if options.threadid != None and options.boardid == None:
    sys.stderr.write("ERROR: If you specify a thread ID you MUST specify a board name too !\r\n")
    exit(1)

if options.listthreads and options.boardid == None:
    sys.stderr.write("ERROR: You MUST specify a board name to list threads !\r\n")
    exit(1)
else:
    if options.listthreads:
        if options.boardid in BOARDSLIST:
            loadThreads(getJson(THREADSURL.format(options.boardid)), True)
            exit(0)
        else:
            sys.stderr.write("ERROR: Unknown board name !\r\n")
            exit(1)


if options.listfiles and (options.boardid == None or options.threadid == None):
    sys.stderr.write("ERROR: You MUST specify a board name AND a thread ID to list files !\r\n")
    exit(1)
else:
    if options.listfiles:
        if options.boardid in BOARDSLIST:
            THREADSLIST = loadThreads(getJson(THREADSURL.format(options.boardid)), False)
            if options.threadid in THREADSLIST:
                loadFiles(getJson(THREADURL.format(options.boardid, options.threadid)), True, options.boardid, options.filetype)
                exit(0)
            else:
                sys.stderr.write("ERROR: Unknown thread ID !\r\n")
                exit(1)
        else:
            sys.stderr.write("ERROR: Unknown board name !\r\n")
            exit(1)


if options.outdir != None:
    abspath = os.path.abspath(options.outdir)
    if not os.path.exists(abspath):
        os.makedirs(abspath)
    OUTPATH = abspath
else:
    OUTPATH = os.path.abspath(os.getcwd())


if options.threadid != None and options.boardid != None:
    if options.boardid in BOARDSLIST:
        THREADSLIST = loadThreads(getJson(THREADSURL.format(options.boardid)), False)
        if options.threadid in THREADSLIST:
            files = loadFiles(getJson(THREADURL.format(options.boardid, options.threadid)), False, options.boardid, options.filetype)
            downloadFiles(files, OUTPATH)
            exit(0)
        else:
            sys.stderr.write("ERROR: Unknown thread ID !\r\n")
            exit(1)
    else:
        sys.stderr.write("ERROR: Unknown board name !\r\n")
        exit(1)


if options.boardid != None and options.threadid == None:
    if options.boardid in BOARDSLIST:
        THREADSLIST = loadThreads(getJson(THREADSURL.format(options.boardid)), False)
        for thread in THREADSLIST:
            files = loadFiles(getJson(THREADURL.format(options.boardid, thread)), False, options.boardid, options.filetype)
            downloadFiles(files, OUTPATH)
        exit(0)
    else:
        sys.stderr.write("ERROR: Unknown board name !\r\n")
        exit(1)


if options.boardid == None and options.threadid == None:
    for board in BOARDSLIST:
        THREADSLIST = loadThreads(getJson(THREADSURL.format(board)), False)
        for thread in THREADSLIST:
            files = loadFiles(getJson(THREADURL.format(board, thread)), False, board, options.filetype)
            downloadFiles(files, OUTPATH)
            exit(0)


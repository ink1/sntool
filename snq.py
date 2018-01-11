#! /usr/bin/env python

################################################################################
## User level utility for dealing with StorNext filesystem
## implemented using Web Services API
##
## AUTHOR: Igor Kozin
## The Institute of Cancer Research, London
##
## CREATED: 15/07/2014
##
################################################################################

# import re
import os.path
import sys
import json
import urllib
import subprocess

# initialize global vars

# debug flag: 0 - no debug info, 1 - print debug info
debug = 0

# base URLs
urla = "http://12.34.56.78:81/axis2/services/stornext/"
urlb = "http://12.34.56.79:81/axis2/services/stornext/"
url = urla

# password and format are required for all requests so we set them here
# the password is not encrypted and goes in the open
#
#params = 'password=whatever&format=json'
#
# one way to obfuscate that is to do URL encoding
# URL-encoded password seems to work in the password field
# but if the word "password" is converted too it does not work
#
params = 'format=json&password=%77%68%61%74%65%76%65%72'

# operation to perform
operation = "help"

opslist = [
    "help",
    "checksum",
    "md5sum",
    "isondisk",
    "issafe",
    "info",
    "store",
    "store2",
    "truncate",
    "retrieve"]

# the name of file we are working on
fname = ''

################################################################################
################################################################################

def printHelp ():

    sys.stdout.write("Usage: snq <function> <filename>\n")
    sys.stdout.write("       functions: ")
    for i in opslist:
        sys.stdout.write(i+"/")
    sys.stdout.write("\n\n")
    sys.exit()


def printFullHelp ():
    
    print """
Usage: snq <function> <filename>

help      print this help

checksum  get checksum value stored by StorNext;
          throws an error if second checksum is different

md5sum    get checksum value stored by StorNext;
          otherwise compute md5sum

isondisk  standard error returns 0 if file is on disk
          or an error message otherwise

issafe    std error returns 0 if file has desired number of copies on
          tape, checksums are identical, or an error message otherwise

info      get information about file location, number of copies,
          associated tapes, file size

store     store file to tape - make one copy

store2    store file to tape - make two copies if policy allows

truncate  delete file from disk;
          will fail if not all copies to tape are made

retrieve  retrieve file from tape

"""
    sys.exit()


################################################################################
#
# check that file exists and the user can read it
#
# input:  file name string
# output: True or False

def checkFileExists(fname):
    if os.path.isfile(fname) and os.access(fname, os.R_OK):
        return True
    else:
        sys.exit("error: file does not exist or not allowed to read")


################################################################################
#
# process input

def input ():
    global url, params, operation, debug, fname

    # no arguments
    if len(sys.argv) < 2:
        printHelp()

    # at least one argument
    if sys.argv[1] in opslist:
        operation = sys.argv[1]
    else:
        printHelp()

    if operation == "help":
        printFullHelp()

    # second arg is requred for ops which are not help
    if len(sys.argv) < 3:
        printHelp()

    # at least two arguments and the 2nd is not help
    fname = sys.argv[2]

    # get the canonical path of the specified filename this 
    # a/ resolves symbolic links and 
    # b/ converts relative file names to absolute
    fname = os.path.realpath(fname)

    # StorNext name
    sname = ""

    # check the file exists; convert to StorNext path by cuting off the "/data" prefix
    if checkFileExists(fname):
        sname = fname[5:]

    params = params+'&files='+urllib.quote(sname)

    # We have four cases of the leading prefix: 
    #   /aaalt
    #   /aaast
    #   /bbblt
    #   /bbbst
    # The URL is selected depending on whether the file is in Sutton or Chelsea
    #print sname[1:4]
    if   sname[1:4] == "aaa":
        url = urla
    elif sname[1:4] == "bbb":
        url = urlb
    else:
        sys.exit("error: unknown file name prefix")

################################################################################
#
# generic url caller with json output
#
# startstring and endstring are strings which wrap the response from WS API
# They are cut off from the response.

def callUrl(startstring, endstring):
    global url, params, operation, debug 

    try:
        f = urllib.urlopen(url, params)
    except:
        sys.exit("error in urllib")

    x = f.read()

    if debug:
        print x

    if x.startswith(startstring):
        x = x[len(startstring):]
    else:
        sys.exit("error in processing first output line")

    if x.endswith(endstring):
        x = x[:-len(endstring)]
    else:
        sys.exit("error in processing last output line")

    try:
        data = json.loads(x)
    except:
        # The most likely reason for absence of json output
        # is that the StorNext server is down.
        sys.exit("error: no output")

    if debug:
        print data

    return data

################################################################################
#
# print generic status returned by url caller with json output

def printDataStatus(data):

    for x in data["statuses"]:
        a = "commandStatus"
        if x.has_key(a):
            print '{0:<30}'.format(a), x[a]
        a = "statusText"
        if x.has_key(a):
            print '{0:<30}'.format(a), x[a]

    if data["statuses"][-1]["commandStatus"] == "failed":
        sys.exit(1)

################################################################################
#
# getFileLocation

def getFileLocation():
    global url, params, operation, debug 

    url = url+"getFileLocation"

    # strings which wrap the response from WS API
    startstring = '<ns1:getFileLocationResponse xmlns:ns1="http://www.quantum.com/stornext/"><out>'
    endstring = '</out></ns1:getFileLocationResponse>'

    return callUrl(startstring, endstring)

################################################################################
#
# get file info

def info():
    global url, params, operation, debug

    # modifies the parameter field; e.g. we want checksums
    # since we don't have Wide Area Storage adding "showIds=1" makes no effect
    params = 'checksum=1&' + params

    data = getFileLocation()

    # location
    a = "location"
    x = data["fileInfos"][0][a]
    if   (x == "DISK" or x == "DISK AND TAPE" or x == "TAPE"):
        print '{0:<30}'.format(a), x
    elif x == "FOREIGN SYSTEM":
        print '{0:<30}'.format(a), "Pandorica"
        return
    else:
        print '{0:<30}'.format(a), "unknown"
        sys.exit()

    # list of
    properties = [
        "fileName",
        "storedPathFileName",
        "lastModificationDateString",
        "existingCopies",
        "targetCopies",
        "fileSize",
        "targetStubSize",
        "class"
    ]

    for a in properties:
        print '{0:<30}'.format(a), data["fileInfos"][0][a]

    # some files exist on disk only
    # find if the file has tape copies

    a = "medias"
    x = data["fileInfos"][0][a]
    #
    # x is an array of dictionaries
    #
    maxcopy = 1
    for xi in x:
        if ( xi.has_key("summary") and xi["summary"] == "N" ):
            print '{0:<30}'.format("tape"), "N/A"
            return
        elif xi.has_key("mediaId"):
            if maxcopy < xi["copy"]:
                maxcopy = xi["copy"]
            myitem = "tape (copy " + str(xi["copy"]) + ")"
            print '{0:<30}'.format(myitem), xi["mediaId"]
        else:
            print '{0:<30}'.format("tape"), "error"
            return

    # since the file is on tape there have to be checksums
    # but some files can contain more than one segment
    # in which case we are not interested in checksums

    a = "checksums"
    x = data["fileInfos"][0][a]
    #
    # x is an array of dictionaries
    #
    # check if the summary says No checksum or more than one segment
    maxseg = 1
    for xi in x:
        if ( xi.has_key("summary") and xi["summary"] == "N" ):
             print '{0:<30}'.format(a), "N/A"
             return
        elif xi.has_key("checksumValue"): 
             if maxseg < xi["fileSegment"]:
                 maxseg = xi["fileSegment"]
        else:
             print '{0:<30}'.format(a), "error"
             return

    # this creates an array [[copies],...<fragments>]
    # so that the reference is [segmentID][copyID]
    checksums = [['' for copyid in range(maxcopy)] for segment in range(maxseg)]
    for xi in x:
        if xi.has_key("checksumValue"): 
            checksums[ (xi["fileSegment"]-1) ][ (xi["copyId"]-1) ] = xi["checksumValue"]

    for segment in range(1,maxseg+1):
        for copyid in range(1,maxcopy+1):
            # print segment, " ", copyid
            myitem = "checksum " + str(copyid) + ", segment " + str(segment)
            if copyid==1:
                print '{0:<30}'.format(myitem), checksums[segment-1][0]
            elif checksums[segment-1][0] == checksums[segment-1][copyid-1]:
                print '{0:<30}'.format(myitem), "same"
            else:
                print '{0:<30}'.format(myitem), checksums[segment-1][copyid-1]

################################################################################
#
# check if the file is on disk or not
# breaks with error if on Tape, External System or unknown

def isondisk():
    global url, params, operation, debug

    data = getFileLocation()

    # location
    a = "location"
    x = data["fileInfos"][0][a]
    if   (x == "DISK" or x == "DISK AND TAPE"):
        return True
    elif x == "TAPE":
        sys.exit("error: file is on Tape")
    elif x == "FOREIGN SYSTEM":
        sys.exit("error: file is on External System")
    else:
        sys.exit("error: file status is unknown")

    return True


################################################################################
#
# check if file is safely stored to tape

def issafe():
    global url, params, operation, debug, fname 

    # yes, we need checksums
    params = 'checksum=1&' + params

    data = getFileLocation()

    # return error if file is not on StorNext
    if data["fileInfos"][0]["location"] == "FOREIGN SYSTEM":
        sys.exit("error: file is on External System")

    # return error if file size is zero
    if data["fileInfos"][0]["fileSize"] == 0:
        sys.exit("error: file size is zero")

    # return error if not all copies are done
    if data["fileInfos"][0]["existingCopies"] != data["fileInfos"][0]["targetCopies"]:
        s1 = "error: %d out of %d copies" % (data["fileInfos"][0]["existingCopies"], data["fileInfos"][0]["targetCopies"])
        sys.exit(s1)

    # Analyse checksums
    x = data["fileInfos"][0]["checksums"]

    # find number of copies
    maxcop = data["fileInfos"][0]["targetCopies"]

    # find number of segments
    maxseg = 1
    for xi in x:
        if xi.has_key("checksumValue"): 
             if maxseg < xi["fileSegment"]:
                 maxseg = xi["fileSegment"]

    # order all checksums
    checksums = []
    for segment in range(0, maxseg):
        checksums.insert( segment, [] )
    counter = 0
    for xi in x:
        if xi.has_key("checksumValue"):
            # print type(xi["copyId"]), xi["copyId"]
            # print type(xi["fileSegment"]), xi["fileSegment"]
            checksums[xi["fileSegment"]-1].insert( xi["copyId"]-1 , xi["checksumValue"] )
            counter = counter + 1

    if counter != maxseg*maxcop:
            sys.exit("error: checksum missing")

    # compare checksums in all segments with first checksum
    for segment in range(0, maxseg):
        for copynum in range(1, maxcop):
            if checksums[segment][0] != checksums[segment][copynum]:
                sys.exit("error: checksums differ")

    # Analyse tapes
    x = data["fileInfos"][0]["medias"]
    for xi in x:
        if ( xi.has_key("message") ):
            if xi["message"] == "unknown":
                sys.exit("error: missing tape")
            elif xi["message"] == "None":
                sys.exit("error: no tapes")
            else:
                s = "error: unknown error: " + xi["message"]
                sys.exit(s)

    return True


################################################################################
#
# get checksum from StorNext

def checksum():
    global url, params, operation, debug, fname 

    # yes, we need checksums
    params = 'checksum=1&' + params

    data = getFileLocation()
    x = data["fileInfos"][0]["checksums"]

    # return error if file is not on StorNext
    if data["fileInfos"][0]["location"] == "FOREIGN SYSTEM":
        sys.exit("error: file is on External System")

    # return error if file size is zero
    if data["fileInfos"][0]["fileSize"] == 0:
        sys.exit("error: file size is zero")

    # check if file has at least one copy
    # this assumes that if it does not have copies, 
    # it does not have checksums on SN
    if data["fileInfos"][0]["existingCopies"] == 0:
        sys.exit("error: no checksum - no file copies")

    # check if file has more than one segment
    maxseg = 1
    for xi in x:
        if xi.has_key("checksumValue"): 
             if maxseg < xi["fileSegment"]:
                 maxseg = xi["fileSegment"]

    # return error if file has more than one segment
    if maxseg > 1:
        sys.exit("error: no checksum - multi-segment file")

    # by now the only option remains the file is single-segment and
    # it has at least one copy ie checksum
    # initialise chesksum array
    checksums = []
    for xi in x:
        if ( xi.has_key("checksumValue") ):
            checksums.insert( xi["copyId"] , xi["checksumValue"] )

    if ( data["fileInfos"][0]["existingCopies"] != len(checksums) ):
        sys.exit("error: number of checksums in not equal to number of copies")

    # pick a checksum value
    csum = checksums.pop()
    # check if the list contains other values and return error if it does
    for i in checksums:
        if ( i != csum ):
            sys.exit("error: checksums differ")

    print csum, fname
    return csum, fname

################################################################################
#
# get md5sum, compute if on disk

def md5sum():
    global url, params, operation, debug, fname 

    # yes, we need checksums
    params = 'checksum=1&' + params

    data = getFileLocation()
    x = data["fileInfos"][0]["checksums"]

    # return error if file is not on StorNext
    if data["fileInfos"][0]["location"] == "FOREIGN SYSTEM":
        sys.exit("error: file is on External System")

    # return error if file size is zero
    if data["fileInfos"][0]["fileSize"] == 0:
        sys.exit("error: file size is zero")

    # compute md5sum if file has not been copied yet
    if data["fileInfos"][0]["existingCopies"] == 0:
        if ( data["fileInfos"][0]["location"] == "DISK" or
             data["fileInfos"][0]["location"] == "DISK AND TAPE"):
            run_md5sum()
        else:
            # this condition should not be possible
            sys.exit("error: not of disk and no copies!")
        return

    # check if file has more than one segment
    maxseg = 1
    for xi in x:
        if xi.has_key("checksumValue"): 
             if maxseg < xi["fileSegment"]:
                 maxseg = xi["fileSegment"]

    # compute checksum for multi-segment file,
    # return error if file is not on disk
    if maxseg > 1:
        if ( data["fileInfos"][0]["location"] == "DISK" or
             data["fileInfos"][0]["location"] == "DISK AND TAPE"):
            run_md5sum()
        else:
            # we don't want to retrieve the file if it's on tape only
            sys.exit("error: multi-segment file is not on disk")
        return

    # by now the only option remains the file is single-segment and
    # it has at least one copy ie checksum
    # initialise chesksum array
    checksums = []
    for xi in x:
        if ( xi.has_key("checksumValue") ):
            checksums.insert( xi["copyId"] , xi["checksumValue"] )

    if ( data["fileInfos"][0]["existingCopies"] != len(checksums) ):
        sys.exit("error: number of checksums in not equal to number of copies")

    # pick a checksum value
    csum = checksums.pop()
    # check if the list contains other values and return error if it does
    for i in checksums:
        if ( i != csum ):
            sys.exit("error: checksums differ")

    print csum, fname
    return csum, fname

################################################################################
#
# run md5sum 

def run_md5sum():
    global url, params, operation, debug, fname 

    subproc = subprocess.Popen(['md5sum', fname],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = subproc.communicate()
    if err:
        sys.exit("error: could not compute checksum")
    else:
        print out

################################################################################
#
# doStore and related operations

def doStore():
    global url, params, operation, debug

    url = url+"doStore"

    # strings which wrap the response from WS API
    startstring = '<ns1:doStoreResponse xmlns:ns1="http://www.quantum.com/stornext/"><out>'
    endstring = '</out></ns1:doStoreResponse>'

    return callUrl(startstring, endstring)


def store():
    global url, params, operation, debug

    data = doStore()
    printDataStatus(data)


def store2():
    global url, params, operation, debug

    params = 'copies=2&'+params
    data = doStore()
    printDataStatus(data)

################################################################################
#
# doTruncate and related operations

def doTruncate():
    global url, params, operation, debug

    url = url+"doTruncate"

    # strings which wrap the response from WS API
    startstring = '<ns1:doTruncateResponse xmlns:ns1="http://www.quantum.com/stornext/"><out>'
    endstring = '</out></ns1:doTruncateResponse>'

    return callUrl(startstring, endstring)


def truncate():
    global url, params, operation, debug

    data = doTruncate()
    printDataStatus(data)

################################################################################
#
# doRetrieve and related operations

def doRetrieve():
    global url, params, operation, debug

    url = url+"doRetrieve"

    # strings which wrap the response from WS API
    startstring = '<ns1:doRetrieveResponse xmlns:ns1="http://www.quantum.com/stornext/"><out>'
    endstring = '</out></ns1:doRetrieveResponse>'

    return callUrl(startstring, endstring)


def retrieve():
    global url, params, operation, debug

    data = doRetrieve()
    printDataStatus(data)


################################################################################

def main ():

    input()

    if   operation == "help":
        printFullHelp()
    if   operation == "info":
        info()
    elif operation == "checksum":
        checksum()
    elif operation == "md5sum":
        md5sum()
    elif operation == "isondisk":
        isondisk()
    elif operation == "issafe":
        issafe()
    elif operation == "store":
        store()
    elif operation == "store2":
        store2()
    elif operation == "truncate":
        truncate()
    elif operation == "retrieve":
        retrieve()
    else:
        print "not implemented yet"
        # print_help()

            
if __name__ == '__main__':
    main ()

# vim:ts=4:sw=4:et

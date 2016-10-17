#!/usr/bin/env python
#
# Adverb Version 3.0

import os
import cgi, cgitb
import tempfile
import subprocess

def print_file(filename):
    statinfo = os.stat(filename)
    print "File: %s, size = %s, contents:" % (filename, statinfo.st_size)
    with open(filename) as f:
        print f.read()

# fieldStorage
form = cgi.FieldStorage()

# sense the settings
formSelectors  = form.getvalue('selectors')
fileitem       = form['upfile']
# checkbox: searchhard
# checkbox: showpdml

# exit if bad input
if not os.environ['REQUEST_METHOD'] == 'POST':
    print "Content-Type: text/plain"
    print 
    print "Error: expected to receive POST but received %s" % os.environ['REQUEST_METHOD']
    sys.exit(0)

if not fileitem.filename:
    print "Content-Type: text/plain"
    print 
    print "Error: no .pcapng file specified"
    sys.exit(0)

# create workspace
workdir = tempfile.mkdtemp()

# working file names
fn = os.path.basename(fileitem.filename)
userBinFn  = workdir + "/" + fn
userPdmlFn = workdir + "/user.pdml"

# extract user binary trace file data
userBinFile = open(userBinFn, 'w+b')
userBinFile.write(fileitem.file.read())
userBinFile.close()

# extract port selector list
selectors = []
hisSelectors = formSelectors.split(" ")
for aSel in hisSelectors:
    aSel = aSel.strip()
    if len(aSel) > 0:
        selectors.append("-d")
        selectors.append("tcp.port==" + aSel + ",amqp")

# cd into adverb/bin work dir
os.chdir("adverb/bin")

# convert .pcapng to .pdml
#
# open out and err files
tsStdoutFn   = workdir + "/ts_stdout"
tsStderrFn   = workdir + "/ts_stderr"
f_stdout = open(tsStdoutFn, 'w')
f_stderr = open(tsStderrFn, 'w')

# generate tshark command line
args = []
args.append("tshark")
args.append("-2")
args.append("-r")
args.append(userBinFn)
args.extend(selectors)
if not form.getvalue('searchhard'):
    args.append("-Y")
    args.append("amqp")
args.append("-T")
args.append("pdml")

# run tshark .pcapng -> .pdml
try:
    subprocess.check_call(args, stdout=f_stdout, stderr=f_stderr)
except Exception, e:
    print "Status: 500 Internal Server Error"
    print "Content-Type: text/plain"
    print
    print "Tshark utility error %s processing %s" % (str(e), fn)
    print
    f_stdout.close()
    f_stderr.close()
    print_file(tsStdoutFn)
    print_file(tsStderrFn)
    sys.exit(0)

f_stdout.close()
f_stderr.close()

# show only pdml
if form.getvalue('showpdml'):
    print "Content-Type: text/text"
    print
    print "Generated with: %s" % args
    print
    print_file(tsStderrFn)
    print_file(tsStdoutFn)
    sys.exit(0)

# convert .pdml to .html
#
# open out and err files
advStdoutFn   = workdir + "/adv_stdout"
advStderrFn   = workdir + "/adv_stderr"
f_stdout = open(advStdoutFn, 'w')
f_stderr = open(advStderrFn, 'w')

# generate adverb command line
args = []
args.append("../scripts/adverb.py")
args.append(tsStdoutFn)
args.append(fileitem.filename)
args.append(formSelectors)
args.append("")     # deprecated comment

# run adverb script .pdml -> .html
try:
    subprocess.check_call(args, stdout=f_stdout, stderr=f_stderr)
except Exception, e:
    print "Status: 500 Internal Server Error"
    print "Content-Type: text/plain"
    print
    print "Adverb utility error %s processing %s" % (str(e), userPdmlFn)
    print
    f_stdout.close()
    f_stderr.close()
    print_file(advStdoutFn)
    print_file(advStderrFn)
    sys.exit(0)

f_stdout.close()
f_stderr.close()

# hereis
print "Content-Type: text/html"
print
with open(advStdoutFn) as f:
    print f.read()

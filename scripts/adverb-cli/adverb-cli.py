#!/usr/bin/env python
#
# Adverb Version 3.0
#
# Run adverb from a command prompt on the local system.
# The adverb web server fails with timeouts when processing large files.
# Also, the web scheme of saying which ports are amqp ports is lame.
# This scheme fixes both problems.

import sys
import os
import tempfile
import subprocess

def print_file(filename):
    statinfo = os.stat(filename)
    print "File: %s, size = %s, contents:" % (filename, statinfo.st_size)
    with open(filename) as f:
        print f.read()

#
#
class ExitStatus(Exception):
    """Raised if a command wants a non-0 exit status from the script"""
    def __init__(self, status): self.status = status

#
#
def main_except(argv):
    """Given a pcapng file name, generate pdml intermediate and Adverb html analysis files"""
    if len(sys.argv) < 2:
        sys.exit('Usage: %s pcapng-file-name' % sys.argv[0])

    arg_pcapng_file = sys.argv[1]

    if not os.path.exists(arg_pcapng_file):
        sys.exit('ERROR: pcapng file %s is not found.' % arg_pcapng_file)

    if not os.path.isfile(arg_pcapng_file):
        sys.exit('ERROR: pcapng file %s is not a file.' % arg_pcapng_file)

    (root, ext) = os.path.splitext(arg_pcapng_file)
    full_pdml_file = root + "-full.pdml"
    amqp_pdml_file = root + "-amqp.pdml"
    amqp_html_file = root + ".html"

    # create workspace
    workdir = tempfile.mkdtemp()

    # open out and err files
    tsStdoutFn   = full_pdml_file
    tsStderrFn   = workdir + "/ts_stderr"
    f_stdout = open(tsStdoutFn, 'w')
    f_stderr = open(tsStderrFn, 'w')

    # convert .pcapng to full.pdml
    #
    # generate tshark command line
    args = []
    args.append("tshark")
    args.append("-2")
    args.append("-r")
    args.append(arg_pcapng_file)
    args.append("-T")
    args.append("pdml")

    # run tshark .pcapng -> -full.pdml
    try:
        print "Generating full pdml..."
        subprocess.check_call(args, stdout=f_stdout, stderr=f_stderr)
    except Exception, e:
        print "Tshark utility error %s processing %s" % (str(e), arg_pcapng_file)
        print
        f_stdout.close()
        f_stderr.close()
        print_file(tsStdoutFn)
        print_file(tsStderrFn)
        sys.exit(0)

    f_stdout.close()
    f_stderr.close()

    # scan the full pdml to detect probable AMQP ports in use
    #
    print "Scanning for probable AMQP ports..."
    portlist = []
    src=""
    dst=""
    with open(full_pdml_file, "r") as ins:
        for line in ins:
            fields = line.split()
	    if line.startswith("    <field name=\"tcp.srcport\""):
	        src = fields[4]
	    if line.startswith("    <field name=\"tcp.dstport\""):
	        dst = fields[4]
	    if line.find("414d5150") > 0:
	        if dst not in portlist and src not in portlist:
		    portlist.append(dst)
	        src=""
	        dst=""
    portlist = filter(None, portlist)
    print ("AMQP Ports: ", portlist)
    
    # convert .pcapng to -amqp.pdml
    #
    # open out and err files
    tsStdoutFn   = amqp_pdml_file
    tsStderrFn   = workdir + "/ts_stderr"
    f_stdout = open(tsStdoutFn, 'w')
    f_stderr = open(tsStderrFn, 'w')

    # generate tshark command line
    args = []
    args.append("tshark")
    args.append("-2")
    args.append("-r")
    args.append(arg_pcapng_file)
    args.append("-Y")
    args.append("amqp")
    args.append("-T")
    args.append("pdml")
    for port in portlist:
        args.append("-d")
        args.append("tcp.port==" + port + ",amqp")

    # run tshark .pcapng -> -amqp.pdml
    try:
        print "Generating amqp-only pdml..."
        subprocess.check_call(args, stdout=f_stdout, stderr=f_stderr)
    except Exception, e:
        print "Tshark utility error %s processing %s" % (str(e), arg_pcapng_file)
        print
        f_stdout.close()
        f_stderr.close()
        print_file(tsStdoutFn)
        print_file(tsStderrFn)
        sys.exit(0)

    f_stdout.close()
    f_stderr.close()

    # convert -amqp.pdml to -amqp.html
    #
    # open out and err files
    advStdoutFn   = amqp_html_file
    advStderrFn   = workdir + "/adv_stderr"
    f_stdout = open(advStdoutFn, 'w')
    f_stderr = open(advStderrFn, 'w')

    # generate adverb command line
    args = []
    args.append("../adverb.py")
    args.append(amqp_pdml_file)
    args.append(arg_pcapng_file)
    args.append(' '.join(portlist))
    args.append("")     # deprecated comment

    # run adverb script -amqp.pdml -> .html
    try:
        print "Generating html..."
        subprocess.check_call(args, stdout=f_stdout, stderr=f_stderr)
    except Exception, e:
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
    print "Done. Open file://" + os.path.abspath(amqp_html_file)

def main(argv):
    try:
        main_except(argv)
        return 0
    except ExitStatus, e:
        return e.status
    except Exception, e:
        print "%s: %s"%(type(e).__name__, e)
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))

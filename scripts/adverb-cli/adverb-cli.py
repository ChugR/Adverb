#!/usr/bin/env python
#
# Adverb Version 3.0
#
# Run adverb from a command prompt on the local system.
# * Process large files that cause web server timeouts.
# * Automatically detect AMQP ports, or not.
#   CLI switch disables autodetect to scan for 5672 only.
#
# A pcapng file created during a run of qpid dispatch router self
# test is processed by this script. The file sizes of each stage are:
#
# -rwxrwxr-x. 1 chug chug      5893 Aug 26 06:24 adverb-cli.py
# -rw-rw-r--. 1 chug chug 168273447 Aug 26 06:24 q2-amqp.pdml
# -rw-rw-r--. 1 chug chug 178141270 Aug 26 06:24 q2-full.pdml
# -rw-rw-r--. 1 chug chug  54446399 Aug 26 06:24 q2.html
# -r--r--r--. 1 chug chug   3368332 Aug 25 16:23 q2.pcapng
#
# The interdediate pdml files are 50x the size of the pcapng file.
# The result html is 15x-20x the size of the pcapng file.
# These ratios may vary depending on the density of AMQP frames in
# the original capture file but be prepared for huge analysis files.
#

import sys
import os
import tempfile
import subprocess

#
#
class ExitStatus(Exception):
    """Raised if a command wants a non-0 exit status from the script"""
    def __init__(self, status): self.status = status

#
#
def main_except(argv):
    """Given a pcapng file name, generate pdml intermediate and Adverb html analysis files"""
    usagestr = 'Usage: %s pcapng-file-name [no-autodetect-amqp-ports]' % sys.argv[0]
    if len(sys.argv) < 2:
        sys.exit(usagestr)

    if (sys.argv[1].startswith("-h") or sys.argv[1].startswith("--help")):
        print usagestr
        print
        print ' pcapng-file-name - required path to pcapng file'
        print ' autodetect-amqp-ports - optional switch whose presence disables autodetect.'
        sys.exit(' ')

    arg_pcapng_file = sys.argv[1]
    enable_autodetect = (len(sys.argv) == 2)

    # sort out path names
    if not os.path.exists(arg_pcapng_file):
        sys.exit('ERROR: pcapng file %s is not found.' % arg_pcapng_file)

    if not os.path.isfile(arg_pcapng_file):
        sys.exit('ERROR: pcapng file %s is not a file.' % arg_pcapng_file)

    (root, ext) = os.path.splitext(arg_pcapng_file)
    full_pdml_file = root + "-full.pdml"
    amqp_pdml_file = root + "-amqp.pdml"
    amqp_html_file = root + ".html"

    # create empty port list to use when port scan is disabled
    portlist = []
    
    # create workspace
    workdir = tempfile.mkdtemp()

    if enable_autodetect:
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

#
#
def main(argv):
    try:
        main_except(argv)
        return 0
    except ExitStatus, e:
        return e.status
    except Exception, e:
        print "%s: %s"%(type(e).__name__, e)
        return 1

#
#
if __name__ == "__main__":
    sys.exit(main(sys.argv))

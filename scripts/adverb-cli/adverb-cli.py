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

    print arg_pcapng_file
    print full_pdml_file
    print amqp_pdml_file
    print amqp_html_file
    sys.exit('bye')
    
    # convert .pcapng to .pdml
    #
    # open out and err files
    #tsStdoutFn   = workdir + "/ts_stdout"
    #tsStderrFn   = workdir + "/ts_stderr"
    #f_stdout = open(tsStdoutFn, 'w')
    #f_stderr = open(tsStderrFn, 'w')

    # generate tshark command line
    #args = []
    #args.append("./tshark")
    #args.append("-2")
    #args.append("-r")
    #args.append(userBinFn)
    #args.extend(selectors)
    #if not form.getvalue('searchhard'):
    #    args.append("-Y")
    #    args.append("amqp")
    #args.append("-T")
    #args.append("pdml")

    # run tshark .pcapng -> .pdml
    #try:
    #    subprocess.check_call(args, stdout=f_stdout, stderr=f_stderr)
    #except Exception, e:
    #    print "Status: 500 Internal Server Error"
    #    print "Content-Type: text/plain"
    #    print
    #    print "Tshark utility error %s processing %s" % (str(e), fn)
    #    print
    #    f_stdout.close()
    #    f_stderr.close()
    #    print_file(tsStdoutFn)
    #    print_file(tsStderrFn)
    #    sys.exit(0)

    #f_stdout.close()
    #f_stderr.close()

    # show only pdml
    #if form.getvalue('showpdml'):
    #    print "Content-Type: text/text"
    #    print
    #    print "Generated with: %s" % args
    #    print
    #    print_file(tsStderrFn)
    #    print_file(tsStdoutFn)
    #    sys.exit(0)

    # convert .pdml to .html
    #
    # open out and err files
    #advStdoutFn   = workdir + "/adv_stdout"
    #advStderrFn   = workdir + "/adv_stderr"
    #f_stdout = open(advStdoutFn, 'w')
    #f_stderr = open(advStderrFn, 'w')

    # generate adverb command line
    #args = []
    #args.append("../scripts/adverb.py")
    #args.append(tsStdoutFn)
    #args.append(fileitem.filename)
    #args.append(formSelectors)
    #args.append("")     # deprecated comment

    # run adverb script .pdml -> .html
    #try:
    #    subprocess.check_call(args, stdout=f_stdout, stderr=f_stderr)
    #except Exception, e:
    #    print "Status: 500 Internal Server Error"
    #    print "Content-Type: text/plain"
    #    print
    #    print "Adverb utility error %s processing %s" % (str(e), userPdmlFn)
    #    print
    #    f_stdout.close()
    #    f_stderr.close()
    #    print_file(advStdoutFn)
    #    print_file(advStderrFn)
    #    sys.exit(0)

    #f_stdout.close()
    #f_stderr.close()

    # hereis
    #print "Content-Type: text/html"
    #print
    #with open(advStdoutFn) as f:
    #    print f.read()


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

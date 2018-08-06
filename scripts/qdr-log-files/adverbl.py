#!/usr/bin/env python

#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

# Adverbl concepts
# * Multiple log files may be displayed at the same time.
#   Each log file gets a letter prefix: A, B, C, ...
# * Log AMQP proton trace channel numbers get prefix
#    [1] becomes [A-1]
# * The log file line numbers are equivalent to a wireshark trace frame number.
# * There's no concept of client and server because the logs are from inside
#   a router.

import sys
import time
import os
import traceback
from datetime import *
from adverbl_log_parser import *
from adverbl_ooo import *
#from __future__ import print_function
import pdb

#
#
class ExitStatus(Exception):
    """Raised if a command wants a non-0 exit status from the script"""
    def __init__(self, status): self.status = status


def log_line_sort_key(lfl):
    return lfl.datetime


def get_router_version(fn):
    '''
    Extract router version string from a log file
    :param fn: the path to the log file
    :return: version string or 'unknown'
    '''
    with open(fn, 'r') as infile:
        for line in infile:
            if "ROUTER (info) Version:" in line:
                flds = line.split()
                ver = flds[-1]
                if ver.startswith('('):
                    ver = flds[-2]
                return ver
    return "unknown"


def parse_log_file(fn, log_id, ooo_tracker):
    '''
    Given a file name, return the parsed lines for display
    :param fn: file name
    :param log_id: router id (prefix letter)
    :return: list of ParsedLogLines
    '''
    lineno = 0
    parsed_lines = []
    with open(fn, 'r') as infile:
        for line in infile:
            lineno += 1
            ooo_tracker.process_line(lineno, line)
            if "[" in line and "]" in line:
                try:
                    pl = ParsedLogLine(log_id, lineno, line)
                    if pl is not None:
                        parsed_lines.append(pl)
                except Exception as e:
                    #t, v, tb = sys.exc_info()
                    if hasattr(e, 'message'):
                        sys.stderr.write("Failed to parse file '%s', line %d : %s\n" % (fn, lineno, e.message))
                    else:
                        sys.stderr.write("Failed to parse file '%s', line %d : %s\n" % (fn, lineno, e))
                    #raise t, v, tb
    return parsed_lines

#
#
def main_except(argv):
    #pdb.set_trace()
    """Given a pdml file name, send the javascript web page to stdout"""
    if len(sys.argv) < 2:
        sys.exit('Usage: %s log-file-name' % sys.argv[0])

    log_char = 'A'
    log_array = []
    log_fns = []
    ooo_array = []

    for log_i in range(1, len(sys.argv)):

        arg_log_file = sys.argv[log_i]
        log_fns.append(arg_log_file)

        if not os.path.exists(arg_log_file):
            sys.exit('ERROR: log file %s was not found!' % arg_log_file)

        # parse the log file
        ooo = LogLinesOoo(log_char)
        ooo_array.append(ooo)
        tree = parse_log_file(arg_log_file, log_char, ooo)
        if len(tree) == 0:
            sys.exit('WARNING: log file %s has no Adverb data!' % arg_log_file)

        log_array += tree
        log_char = chr(ord(log_char) + 1)

    tree = sorted(log_array, key=lambda lfl: lfl.datetime)

    # html head, start body
    fixed_head = '''
<!DOCTYPE html>
<html>
<head>
<title>Adverb Analysis - qpid-dispatch router logs</title>

<style>
table {
    border-collapse: collapse;
}
table, td, th {
    border: 1px solid black;
    padding: 3px;
}
</style>
</head>
<body>
'''
    print fixed_head

    # file(s) included in this doc
    print "<h3>Log files</h3>"
    for i in range(len(log_fns)):
        print "%s - %s - Version: %s<br>" % (chr(ord('A') + i), os.path.abspath(log_fns[i]), get_router_version(log_fns[i]))
    print "<br> <hr>"

    # the proton log lines
    print "<h3>Log data</h3>"
    for plf in tree:
        print plf.datetime, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction, plf.data.web_show_str, "<br>"
    print "<hr>"

    # Out-of-order histogram
    print "<h3>Out of order stats</h3><br>"
    print "<table>"
    heads = ooo_array[0].titles()
    print "  <tr>"
    print "    <th>File</th>"
    for h in heads:
        print "<th>%s</th>" % h
    print "<th>max</th> <th>line #</th>"
    print "  </tr>"
    for ooo in ooo_array:
        print "  <tr>"
        print "  <td>%s</td>" % ooo.prefix
        for h in ooo.histogram:
            print "  <td>%s</td>" % h
        print "  <td>%s</td> <td>%d</td>" % (ooo.high_delta, ooo.high_lineno)
        print "  </tr>"
    print "</table>"
    print "</body>"
    # all done

def main(argv):
    try:
        main_except(argv)
        return 0
    except ExitStatus, e:
        return e.status
    except Exception, e:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))

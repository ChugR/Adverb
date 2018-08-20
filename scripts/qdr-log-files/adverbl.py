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

from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import traceback

from adverbl_log_parser import *
from adverbl_ooo import *
from adverbl_name_shortener import *

#
#
class ExitStatus(Exception):
    """Raised if a command wants a non-0 exit status from the script"""
    def __init__(self, status): self.status = status

def log_line_sort_key(lfl):
    return lfl.datetime


def get_some_field(fn, fld_prefix):
    '''
    Extract some string from a log file
    :param fn: the path to the log file
    :param fnd_prefix: text before the intended field
    :return: field text or 'unknown'
    '''
    with open(fn, 'r') as infile:
        for line in infile:
            st = line.find(fld_prefix)
            if st > 0:
                res = line[(st + len(fld_prefix)):].strip().split()[0]
                return res
    return "unknown"


def get_router_version(fn):
    return get_some_field(fn, "ROUTER (info) Version:")


def get_router_id(fn):
    return get_some_field(fn, "SERVER (info) Container Name:")


def parse_log_file(fn, log_id, ooo_tracker, shorteners):
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
            if lineno == 162:
                pass # break
            ooo_tracker.process_line(lineno, line)
            if "[" in line and "]" in line:
                try:
                    pl = ParsedLogLine(log_id, lineno, line, shorteners)
                    if pl is not None:
                        parsed_lines.append(pl)
                except ValueError as ve:
                    pass
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
    """
    Given a list of log file names, send the javascript web page to stdout
    """
    if len(sys.argv) < 2:
        sys.exit('Usage: %s log-file-name' % sys.argv[0])

    log_char_base = 'A'
    log_array = []
    log_fns = []
    ooo_array = []

    shorteners = Shorteners()

    for log_i in range(1, len(sys.argv)):

        arg_log_file = sys.argv[log_i]
        log_fns.append(arg_log_file)

        if not os.path.exists(arg_log_file):
            sys.exit('ERROR: log file %s was not found!' % arg_log_file)

        # parse the log file
        ooo = LogLinesOoo(chr(ord(log_char_base) + log_i - 1))
        ooo_array.append(ooo)
        tree = parse_log_file(arg_log_file, chr(ord(log_char_base) + log_i - 1), ooo, shorteners)
        if len(tree) == 0:
            sys.exit('WARNING: log file %s has no Adverb data!' % arg_log_file)

        log_array += tree

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
    print(fixed_head)

    # file(s) included in this doc
    print("<h3>Log files</h3>")
    print("<table><tr><th>Log</th> <th>Container Name</th> <th>Version</th> <th>Log file path</th></tr>")
    for i in range(len(log_fns)):
        log_letter = chr(ord('A') + i)
        print("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
              (log_letter, get_router_id(log_fns[i]), get_router_version(log_fns[i]), os.path.abspath(log_fns[i])))
    print("</table>")
    print("<hr>")

    # the proton log lines
    print("<h3>Log data</h3>")
    for plf in tree:
        print(plf.datetime, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction, plf.data.web_show_str, "<br>")
    print("<hr>")

    # short data index
    shorteners.short_data_names.htmlDump()

    # Out-of-order histogram
    # Don't print if all zeros
    printooo = False
    for ooo in ooo_array:
        for h in ooo.histogram:
            if not str(h) == '0':
                printooo = True
    if printooo:
        print("<h3>Out of order stats</h3><br>")
        print("<table>")
        heads = ooo_array[0].titles()
        print("  <tr>")
        print("    <th>File</th>")
        for h in heads:
            print("<th>%s</th>" % h)
        print("<th>max</th> <th>line #</th>")
        print("  </tr>")
        for ooo in ooo_array:
            print("  <tr>")
            print("  <td>%s</td>" % ooo.prefix)
            for h in ooo.histogram:
                print("  <td>%s</td>" % h)
            print("  <td>%s</td> <td>%d</td>" % (ooo.high_delta, ooo.high_lineno))
            print("  </tr>")
        print("</table>")

    print("</body>")
    # all done

def main(argv):
    try:
        main_except(argv)
        return 0
    except ExitStatus as e:
        return e.status
    except Exception as e:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))

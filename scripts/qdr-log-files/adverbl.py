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
import cgi

from adverbl_log_parser import *
from adverbl_ooo import *
from adverbl_name_shortener import *

#
#
class ExitStatus(Exception):
    """Raised if a command wants a non-0 exit status from the script"""
    def __init__(self, status): self.status = status


def lozenge():
    '''
    :return: HTML document lozenge character
    '''
    return "&#9674;"


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


def time_offset(ttest, t0):
    delta = ttest - t0
    t = float(delta.seconds) + float(delta.microseconds) / 1000000.0
    return "%0.06f" % t


def get_router_version(fn):
    return get_some_field(fn, "ROUTER (info) Version:")


def get_router_id(fn):
    return get_some_field(fn, "SERVER (info) Container Name:")


def conn_id_of(log_letter, conn_num):
    return log_letter + "_" + str(conn_num)


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

    # the discovered container names for each router
    router_ids = []

    # list of list of connections as discovered in files
    # [ [1,2,3], [1,3,2,4]], that is: [[A's conns], [B's conns], ...]
    conn_lists = []

    # connection direction. Who oritinated the connection?

    # connection peers
    # key=decorated name 'A_3'
    conn_peers = {}         # val = peer container-id
    conn_dirs = {}          # val = direction arrow
    conn_log_lines = {}     # val = count of log lines
    conn_xfer_bytes = {}    # val = transfer byte count

    shorteners = Shorteners()

    for log_i in range(1, len(sys.argv)):
        log_letter = chr(ord(log_char_base) + log_i - 1) # A, B, C, ...
        arg_log_file = sys.argv[log_i]
        log_fns.append(arg_log_file)

        if not os.path.exists(arg_log_file):
            sys.exit('ERROR: log file %s was not found!' % arg_log_file)

        # parse the log file
        ooo = LogLinesOoo(log_letter)
        ooo_array.append(ooo)
        tree = parse_log_file(arg_log_file, log_letter, ooo, shorteners)
        if len(tree) == 0:
            sys.exit('WARNING: log file %s has no Adverb data!' % arg_log_file)

        # marshall facts about the run
        router_ids.append(get_router_id(arg_log_file))
        conns = []
        for item in tree:
            # first-instance handling
            if not int(item.data.conn_num) in conns:
                conns.append(int(item.data.conn_num))
                cdir = ""
                if not item.data.direction == "":
                    cdir = item.data.direction
                else:
                    if "Connecting" in item.data.web_show_str:
                        cdir = item.data.direction_out()
                    elif "Accepting" in item.data.web_show_str:
                        cdir = item.data.direction_in()
                conn_dirs[item.data.conn_id] = cdir
                conn_log_lines[item.data.conn_id] = 0
                conn_xfer_bytes[item.data.conn_id] = 0
            # inbound open handling
            if item.data.name == "open" and item.data.direction == item.data.direction_in():
                if item.data.conn_id in conn_peers:
                    sys.exit('ERROR: file: %s connection %s has multiple connection peers' % (arg_log_file, item.data.conn_id))
                conn_peers[item.data.conn_id] = item.data.conn_peer
            # per-log-line count
            conn_log_lines[item.data.conn_id] += 1
            # transfer byte count
            if item.data.name == "transfer":
                conn_xfer_bytes[item.data.conn_id] += int(item.data.transfer_size)
        conn_lists.append(sorted(conns))

        log_array += tree

    tree = sorted(log_array, key=lambda lfl: lfl.datetime)

    # create a map of (connection, [list of associated frames])
    conn_to_frame_map = {}
    for i in range(len(log_fns)):
        log_letter = chr(ord('A') + i)
        conn_list = conn_lists[i]
        for conn in conn_list:
            id = conn_id_of(log_letter, conn)
            conn_to_frame_map[id] = []
    for plf in tree:
        conn_to_frame_map[plf.data.conn_id].append(plf)

    # html head, start body
    fixed_head = '''
<!DOCTYPE html>
<html>
<head>
<title>Adverbl Analysis - qpid-dispatch router logs</title>

<style>
table {
    border-collapse: collapse;
}
table, td, th {
    border: 1px solid black;
    padding: 3px;
}
</style>

<script src="http://ajax.googleapis.com/ajax/libs/dojo/1.4/dojo/dojo.xd.js" type="text/javascript"></script>
<!-- <script src="http://ajax.googleapis.com/ajax/libs/dojo/1.4/dojo/dojo.xd.js" type="text/javascript"></script> -->
<script type="text/javascript">
function node_is_visible(node)
{
  if(dojo.isString(node))
    node = dojo.byId(node);
  if(!node) 
    return false;
  return node.style.display == "block";
}
function set_node(node, str)
{
  if(dojo.isString(node))
    node = dojo.byId(node);
  if(!node) return;
  node.style.display = str;
}
function toggle_node(node)
{
  if(dojo.isString(node))
    node = dojo.byId(node);
  if(!node) return;
  set_node(node, (node_is_visible(node)) ? 'none' : 'block');
}
function hide_node(node)
{
  set_node(node, 'none');
}
function show_node(node)
{
  set_node(node, 'block');
}

function go_back()
{
  window.history.back();
}
'''
    end_head_start_body = '''
</head>
<body>
'''
    print (fixed_head)

    # output the frame show/hide functions into the header
    for conn_id, plfs in conn_to_frame_map.iteritems():
        print("function show_%s() {" % conn_id)
        for plf in plfs:
            print("  javascript:show_node(\'%s\');" % plf.fid)
        print("}")
        print("function hide_%s() {" % conn_id)
        for plf in plfs:
            print("  javascript:hide_node(\'%s\');" % plf.fid)
        print("}")
        # manipulate checkboxes
        print("function show_if_cb_sel_%s() {" % conn_id)
        print("  if (document.getElementById(\"cb_sel_%s\").checked) {" % conn_id)
        print("    javascript:show_%s();" % conn_id)
        print("  } else {")
        print("    javascript:hide_%s();" % conn_id)
        print("  }")
        print("}")
        print("function select_cb_sel_%s() {" % conn_id)
        print("  document.getElementById(\"cb_sel_%s\").checked = true;" % conn_id)
        print("  javascript:show_%s();" % conn_id)
        print("}")
        print("function deselect_cb_sel_%s() {" % conn_id)
        print("  document.getElementById(\"cb_sel_%s\").checked = false;" % conn_id)
        print("  javascript:hide_%s();" % conn_id)
        print("}")
        print("function toggle_cb_sel_%s() {" % conn_id)
        print("  if (document.getElementById(\"cb_sel_%s\").checked) {" % conn_id)
        print("    document.getElementById(\"cb_sel_%s\").checked = false;" % conn_id)
        print("  } else {")
        print("    document.getElementById(\"cb_sel_%s\").checked = true;" % conn_id)
        print("  }")
        print("  javascript:show_if_cb_sel_%s();" % conn_id)
        print("}")

    # Select/Deselect/Toggle All Connections functions
    print("function select_all() {")
    for conn_id, frames_ids in conn_to_frame_map.iteritems():
        print("  javascript:select_cb_sel_%s();" % conn_id)
    print("}")
    print("function deselect_all() {")
    for conn_id, frames_ids in conn_to_frame_map.iteritems():
        print("  javascript:deselect_cb_sel_%s();" % conn_id)
    print("}")
    print("function toggle_all() {")
    for conn_id, frames_ids in conn_to_frame_map.iteritems():
        print("  javascript:toggle_cb_sel_%s();" % conn_id)
    print("}")

    print("</script>")

    #
    print(end_head_start_body)
    #

    # Table of contents
    print("<h3>Contents</h3>")
    print("<ul>")
    print("<li><a href=\"#c_logfiles\">Log files</a></li>")
    print("<li><a href=\"#c_connections\">Connections</a></li>")
    print("<li><a href=\"#c_logdata\">Log data</a></li>")
    print("<li><a href=\"#c_messageprogress\">Message progress</a></li>")
    print("<li><a href=\"#c_msgdump\">Transfer name index</a></li>")
    print("</ul>")
    # file(s) included in this doc
    print("<a name=\"c_logfiles\"></a>")
    print("<h3>Log files</h3>")
    print("<table><tr><th>Log</th> <th>Container name</th> <th>Version</th> <th>Log file path</th></tr>")
    for i in range(len(log_fns)):
        log_letter = chr(ord('A') + i)
        print("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
              (log_letter, router_ids[i], get_router_version(log_fns[i]), os.path.abspath(log_fns[i])))
    print("</table>")
    print("<hr>")

    # print the connection peer table
    print("<a name=\"c_connections\"></a>")
    print("<h3>Connections</h3>")

    print("<p>")
    print("<button onclick=\"javascript:select_all()\">Select All</button>")
    print("<button onclick=\"javascript:deselect_all()\">Deselect All</button>")
    print("<button onclick=\"javascript:toggle_all()\">Toggle All</button>")
    print("</p>")

    print("<table><tr><th>View</th> <th>Id</th> <th>Dir</th> <th>Inbound open peer</th> <th>Log lines</th> <th>Transfer bytes</th> </tr>")
    tConn = 0
    tLines = 0
    tBytes = 0
    for i in range(len(log_fns)):
        log_letter = chr(ord('A') + i)
        conn_list = conn_lists[i]
        for conn in conn_list:
            tConn += 1
            id = conn_id_of(log_letter, conn)
            peer = conn_peers[id] if id in conn_peers else ""
            print("<tr>")
            print("<td> <input type=\"checkbox\" id=\"cb_sel_%s\" " % id)
            print("checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\"> </td>" % (id))

            print("<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
                  (id, conn_dirs[id], peer, conn_log_lines[id], conn_xfer_bytes[id]))
            tLines += conn_log_lines[id]
            tBytes += conn_xfer_bytes[id]
    print("<td>Sum</td><td>%d</td><td> </td><td> </td><td>%d</td><td>%d</td></tr>" %
          (tConn, tLines, tBytes))

    print("</table>")
    print("<hr>")

    # the proton log lines
    print("<a name=\"c_logdata\"></a>")
    print("<h3>Log data</h3>")
    for plf in tree:
        print("<div width=\"100%%\" style=\"display:block  margin-bottom: 2px\" id=\"%s\">" % plf.fid)
        print("<a name=\"%s\"></a>" % plf.fid)
        print(plf.datetime, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction, plf.data.web_show_str, "<br>")
        print("</div>")
    print("<hr>")

    # data traversing network
    print("<a name=\"c_messageprogress\"></a>")
    print("<h3>Message progress</h3>")
    for i in range(0, shorteners.short_data_names.len()):
        sname = shorteners.short_data_names.shortname(i)
        size = 0
        for plf in tree:
            if plf.data.name == "transfer" and plf.transfer_short_name == sname:
                size = plf.data.transfer_size
                break
        print("<a name=\"%s\"></a> <h4>%s (%s)" % (sname, sname, size))
        print(" <span> <a href=\"javascript:toggle_node('%s')\"> %s</a>" % ("data_" + sname, lozenge()))
        print(" <div width=\"100%%\"; style=\"display:none; font-weight: normal; margin-bottom: 2px\" id=\"%s\">" % ("data_" + sname))
        print(" ",  shorteners.short_data_names.longname(i, True))
        print("</div> </span>")
        print("</h4>")
        print("<table>")
        print("<tr><th>Link</th> <th>Time</th> <th>Log Line</th> <th>ConnId</th> <th>Dir</th> <th>Peer</th> <th>T delta</th> <th>T elapsed</th></tr>")
        t0 = None
        tlast = None
        for plf in tree:
            if plf.data.name == "transfer" and plf.transfer_short_name == sname:
                if t0 is None:
                    t0 = plf.datetime
                    tlast = plf.datetime
                    delta = "0.000000"
                    epsed = "0.000000"
                else:
                    delta = time_offset(plf.datetime, tlast)
                    epsed = time_offset(plf.datetime, t0)
                    tlast = plf.datetime
                peer = conn_peers[plf.data.conn_id] if plf.data.conn_id in conn_peers else ""
                link = "<a href=\"#%s\">src</a>" % plf.fid
                print("<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td></tr>" %
                      (link, plf.datetime, plf.lineno, plf.data.conn_id, plf.data.direction, peer, delta, epsed))
        print("</table>")

    print("<hr>")


    # short data index
    print("<a name=\"c_msgdump\"></a>")
    shorteners.short_data_names.htmlDump(True)

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

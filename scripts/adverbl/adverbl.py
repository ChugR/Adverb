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
from adverbl_globals import *
from adverbl_per_link_details import *

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


def nbsp():
    '''
    :return: HTML Non-breaking space
    '''
    return "&#160;"


    # html head, start body
def fixed_head():
    return '''<!DOCTYPE html>
<html>
<head>
<title>Adverbl Analysis - qpid-dispatch router logs</title>

<style>
    * { 
    font-family: sans-serif; 
}
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


def get_some_field(fn, fld_prefix):
    '''
    Extract some string from a log file using simple text search.
    A typical call is:
        get_some_field(fn, "ROUTER (info) Version:")
    This finds the version field without all the formal parsing complications
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
    '''
    Return a string time delta between two datetime objects in seconds formatted
    to six significant decimal places.
    :param ttest:
    :param t0:
    :return:
    '''
    delta = ttest - t0
    t = float(delta.seconds) + float(delta.microseconds) / 1000000.0
    return "%0.06f" % t


def get_router_version(fn):
    return get_some_field(fn, "ROUTER (info) Version:")


def get_router_id(fn):
    return get_some_field(fn, "SERVER (info) Container Name:")


def parse_log_file(fn, log_id, ooo_tracker, gbls):
    '''
    Given a file name, return the parsed lines for display.
    Lines that don't parse are identified on stderr and then discarded.
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
                    pl = ParsedLogLine(log_id, lineno, line, gbls)
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
        sys.exit('Usage: %s log-file-name [log-file-name ...]' % sys.argv[0])

    gbls = adverbl_globals()

    # per log file workspace

    log_array = []
    ooo_array = []

    # connection peers
    # key=decorated name 'A_3'
    conn_log_lines = {}     # val = count of log lines
    conn_xfer_bytes = {}    # val = transfer byte count

    # process the log files and add the results to log_array
    for log_i in range(1, len(sys.argv)):
        log_letter = gbls.log_letter_of(log_i - 1) # A, B, C, ...
        arg_log_file = sys.argv[log_i]
        gbls.log_fns.append(arg_log_file)
        gbls.n_logs += 1

        if not os.path.exists(arg_log_file):
            sys.exit('ERROR: log file %s was not found!' % arg_log_file)

        # parse the log file
        ooo = LogLinesOoo(log_letter)
        ooo_array.append(ooo)
        tree = parse_log_file(arg_log_file, log_letter, ooo, gbls)
        if len(tree) == 0:
            sys.exit('WARNING: log file %s has no Adverb data!' % arg_log_file)

        # marshall facts about the run
        gbls.router_ids.append(get_router_id(arg_log_file))
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
                gbls.conn_dirs[item.data.conn_id] = cdir
                conn_log_lines[item.data.conn_id] = 0
                conn_xfer_bytes[item.data.conn_id] = 0
            # inbound open handling
            if item.data.name == "open" and item.data.direction == item.data.direction_in():
                if item.data.conn_id in gbls.conn_peers:
                    sys.exit('ERROR: file: %s connection %s has multiple connection peers' % (arg_log_file, item.data.conn_id))
                gbls.conn_peers[item.data.conn_id] = item.data.conn_peer
                gbls.conn_peers_popup[item.data.conn_id] = gbls.shorteners.short_peer_names.translate(item.data.conn_peer, True)
            # per-log-line count
            conn_log_lines[item.data.conn_id] += 1
            # transfer byte count
            if item.data.name == "transfer":
                conn_xfer_bytes[item.data.conn_id] += int(item.data.transfer_size)
        gbls.conn_lists.append(sorted(conns))

        log_array += tree

    # sort the combined log entries based on the log line timestamps
    tree = sorted(log_array, key=lambda lfl: lfl.datetime)

    # populate a list with all connectionIds
    # populate a map with key=connectionId, val=[list of associated frames])
    for i in range(gbls.n_logs):
        for conn in gbls.conn_lists[i]:
            id = gbls.conn_id_of( gbls.log_letter_of(i), conn)
            gbls.all_conn_names.append(id)
            gbls.conn_to_frame_map[id] = []
    for plf in tree:
        gbls.conn_to_frame_map[plf.data.conn_id].append(plf)

    # generate connection details and per-connection-session-link relationships
    gbls.all_details = AllDetails(tree, gbls)

    # generate router-to-router connection peer relationships
    peer_list = []
    if gbls.shorteners.short_link_names.len() > 0:
        for i in range(0, gbls.shorteners.short_link_names.len()):
            # Strategy 1 before Open holds connid field:
            # search for short names of links where the link name
            # is passed back and forth between routers
            sname = gbls.shorteners.short_link_names.shortname(i)
            cand = []
            for plf in tree:
                if plf.data.name == "attach" and plf.data.link_short_name == sname:
                    peer = gbls.conn_peers.get(plf.data.conn_id, "")
                    if len(peer) > 0:
                        cand.append(plf.data.conn_id)
            if len(cand) == 4:
                if (cand[0] == cand[3] and cand[1] == cand[2]) and (not cand[0] == cand[1]):
                    hit = sorted((cand[0], cand[1]))
                    if not hit in peer_list:
                        peer_list.append( hit )
    for (key, val) in peer_list:
        if key in gbls.conn_peers_connid:
            sys.exit('key val messed up')
        if val in gbls.conn_peers_connid:
            sys.exit('key val messed up')
        gbls.conn_peers_connid[key] = val
        gbls.conn_peers_connid[val] = key

    #
    # Start producing the output stream
    #
    print (fixed_head())

    # output the frame show/hide functions into the header
    for conn_id, plfs in gbls.conn_to_frame_map.iteritems():
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
    for conn_id, frames_ids in gbls.conn_to_frame_map.iteritems():
        print("  javascript:select_cb_sel_%s();" % conn_id)
    print("}")
    print("function deselect_all() {")
    for conn_id, frames_ids in gbls.conn_to_frame_map.iteritems():
        print("  javascript:deselect_cb_sel_%s();" % conn_id)
    print("}")
    print("function toggle_all() {")
    for conn_id, frames_ids in gbls.conn_to_frame_map.iteritems():
        print("  javascript:toggle_cb_sel_%s();" % conn_id)
    print("}")

    #
    print("</script>")
    print("</head>")
    print("<body>")
    #

    # Table of contents
    print("<h3>Contents</h3>")
    print("<ul>")
    print("<li><a href=\"#c_logfiles\">Log files</a></li>")
    print("<li><a href=\"#c_connections\">Connections</a></li>")

    print("<li><a href=\"#c_noteworthy\">Noteworthy log lines</a></li>")
    print("<li><a href=\"#c_logdata\">Log data</a></li>")
    print("<li><a href=\"#c_messageprogress\">Message progress</a></li>")
    print("<li><a href=\"#c_linkprogress\">Link name propagation</a></li>")
    print("<li><a href=\"#c_peerdump\">Peer name index</a></li>")
    print("<li><a href=\"#c_linkdump\">Link name index</a></li>")
    print("<li><a href=\"#c_msgdump\">Transfer name index</a></li>")
    print("</ul>")

    # file(s) included in this doc
    print("<a name=\"c_logfiles\"></a>")
    print("<h3>Log files</h3>")
    print("<table><tr><th>Log</th> <th>Container name</th> <th>Version</th> <th>Log file path</th></tr>")
    for i in range(gbls.n_logs):
        print("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
              (gbls.log_letter_of(i), gbls.router_ids[i], get_router_version(gbls.log_fns[i]),
               os.path.abspath(gbls.log_fns[i])))
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

    print("<table><tr> <th rowspan=\"2\">View</th> <th colspan=\"2\">Router</th> <th rowspan=\"2\">Dir</th> <th colspan=\"2\">Peer</th> <th rowspan=\"2\">Log lines</th> "
          "<th rowspan=\"2\">N links</th><th rowspan=\"2\">Transfer bytes</th> <th rowspan=\"2\">AMQP errors</th></tr>")
    print("<tr> <th>container</th> <th>connid</th> <th>connid</th> <th>container</th></tr>")
    tConn = 0
    tLines = 0
    tBytes = 0
    tErrs = 0
    tLinks = 0
    for i in range(gbls.n_logs):
        conn_list = gbls.conn_lists[i]
        for conn in conn_list:
            tConn += 1
            rid = gbls.router_ids[i]    # this router container id
            id = gbls.conn_id_of(gbls.log_letter_of(i), conn) # this router connid
            peer = gbls.conn_peers_popup.get(id, "") # peer container id
            peerconnid = gbls.conn_peers_connid.get(id, "")
            n_links = gbls.all_details.links_in_connection(id)
            tLinks += n_links
            errs = sum(1 for plf in gbls.conn_to_frame_map[id] if plf.data.amqp_error)
            tErrs += errs
            print("<tr>")
            print("<td> <input type=\"checkbox\" id=\"cb_sel_%s\" " % id)
            print("checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\"> </td>" % (id))

            print("<td>%s</td><td><a href=\"#cd_%s\">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td><td>%d</td></tr>" %
                  (rid, id, id, gbls.conn_dirs[id], peerconnid, peer, conn_log_lines[id], n_links, conn_xfer_bytes[id], errs))
            tLines += conn_log_lines[id]
            tBytes += conn_xfer_bytes[id]
    print("<td>Total</td><td>%d</td><td> </td><td> </td><td> </td><td> </td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>" %
          (tConn, tLines, tLinks, tBytes, tErrs))

    print("</table>")
    print("<hr>")

    # connection details
    print("<a name=\"c_conndetails\"></a>")
    print("<h3>Connection Details</h3>")
    gbls.all_details.show_html()
    print("<hr>")

    # noteworthy log lines: highlight errors and stuff
    print("<a name=\"c_noteworthy\"></a>")
    print("<h3>Noteworthy</h3>")
    nErrors = 0
    nSettled = 0
    nMore = 0
    nResume = 0
    nAborted = 0
    nDrain = 0
    for plf in tree:
        if plf.data.amqp_error:
            nErrors += 1
        if plf.data.transfer_settled:
            nSettled += 1
        if plf.data.transfer_more:
            nMore += 1
        if plf.data.transfer_resume:
            nResume += 1
        if plf.data.transfer_aborted:
            nAborted += 1
        if plf.data.flow_drain:
            nDrain += 1
    # amqp errors
    print("<a href=\"javascript:toggle_node('noteworthy_errors')\">%s%s</a> AMQP errors: %d<br>" %
          (lozenge(), nbsp(), nErrors))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_errors\">")
    for plf in tree:
        if plf.data.amqp_error:
            print("<a href=\"#%s\">line %s</a> %s %s %s %s<br>" %
                  (plf.fid, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction,
                   gbls.conn_peers_connid.get(plf.data.conn_id, ""), plf.data.web_show_str))
    print("</div>")
    # transfers with settled=true
    print("<a href=\"javascript:toggle_node('noteworthy_settled')\">%s%s</a> Presettled transfers: %d<br>" %
          (lozenge(), nbsp(), nSettled))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_settled\">")
    for plf in tree:
        if plf.data.transfer_settled:
            print("<a href=\"#%s\">line %s</a> %s %s %s %s<br>" %
                  (plf.fid, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction,
                   gbls.conn_peers_connid.get(plf.data.conn_id, ""), plf.data.web_show_str))
    print("</div>")
    # transfers with more=true
    print("<a href=\"javascript:toggle_node('noteworthy_more')\">%s%s</a> Partial transfers with 'more' set: %d<br>" %
          (lozenge(), nbsp(), nMore))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_more\">")
    for plf in tree:
        if plf.data.transfer_more:
            print("<a href=\"#%s\">line %s</a> %s %s %s %s<br>" %
                  (plf.fid, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction,
                   gbls.conn_peers_connid.get(plf.data.conn_id, ""), plf.data.web_show_str))
    print("</div>")
    # transfers with resume=true, whatever that is
    print("<a href=\"javascript:toggle_node('noteworthy_resume')\">%s%s</a> Resumed transfers: %d<br>" %
          (lozenge(), nbsp(), nResume))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_resume\">")
    for plf in tree:
        if plf.data.transfer_resume:
            print("<a href=\"#%s\">line %s</a> %s %s %s %s<br>" %
                  (plf.fid, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction,
                   gbls.conn_peers_connid.get(plf.data.conn_id, ""), plf.data.web_show_str))
    print("</div>")
    # transfers with abort=true
    print("<a href=\"javascript:toggle_node('noteworthy_aborts')\">%s%s</a> Aborted transfers: %d<br>" %
          (lozenge(), nbsp(), nAborted))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_aborts\">")
    for plf in tree:
        if plf.data.transfer_aborted:
            print("<a href=\"#%s\">line %s</a> %s %s %s %s<br>" %
                  (plf.fid, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction,
                   gbls.conn_peers_connid.get(plf.data.conn_id, ""), plf.data.web_show_str))
    print("</div>")
    # flow with drain=true
    print("<a href=\"javascript:toggle_node('noteworthy_drain')\">%s%s</a> Flow with 'drain' set: %d<br>" %
          (lozenge(), nbsp(), nDrain))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_drain\">")
    for plf in tree:
        if plf.data.flow_drain:
            print("<a href=\"#%s\">line %s</a> %s %s %s %s<br>" %
                  (plf.fid, plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction,
                   gbls.conn_peers_connid.get(plf.data.conn_id, ""), plf.data.web_show_str))
    print("</div>")
    print("<hr>")

    # the proton log lines
    # log lines in         f_A_116
    # log line details in  f_A_116_d
    print("<a name=\"c_logdata\"></a>")
    print("<h3>Log data</h3>")
    for plf in tree:
        dict = plf.data.described_type.dict
        print("<div width=\"100%%\" style=\"display:block  margin-bottom: 2px\" id=\"%s\">" % plf.fid)
        print("<a name=\"%s\"></a>" % plf.fid)
        detailname = plf.fid + "_d"
        loz = "<a href=\"javascript:toggle_node('%s')\">%s%s</a>" % (detailname, lozenge(), nbsp())
        peer = gbls.conn_peers.get(plf.data.conn_id, "")
        print(loz, plf.datetime, "l:", plf.lineno, ("[%s]" % plf.data.conn_id), plf.data.direction, peer,
              plf.data.web_show_str, plf.data.disposition_display, "<br>")
        print(" <div width=\"100%%\"; "
              "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
              "id=\"%s\">" %
              (detailname))
        for key in sorted(dict.iterkeys()):
            val = dict[key]
            print("%s : %s <br>" % (key, cgi.escape( str(val) )))
        print("</div>")
        print("</div>")
    print("<hr>")

    # data traversing network
    print("<a name=\"c_messageprogress\"></a>")
    print("<h3>Message progress</h3>")
    for i in range(0, gbls.shorteners.short_data_names.len()):
        sname = gbls.shorteners.short_data_names.shortname(i)
        size = 0
        for plf in tree:
            if plf.data.name == "transfer" and plf.transfer_short_name == sname:
                size = plf.data.transfer_size
                break
        print("<a name=\"%s\"></a> <h4>%s (%s)" % (sname, sname, size))
        print(" <span> <a href=\"javascript:toggle_node('%s')\"> %s</a>" % ("data_" + sname, lozenge()))
        print(" <div width=\"100%%\"; style=\"display:none; font-weight: normal; margin-bottom: 2px\" id=\"%s\">" %
              ("data_" + sname))
        print(" ",  gbls.shorteners.short_data_names.longname(i, True))
        print("</div> </span>")
        print("</h4>")
        print("<table>")
        print("<tr><th>Src</th> <th>Time</th> <th>Log Line</th> <th>ConnId</th> <th>Dir</th> <th>Peer</th> "
              "<th>T delta</th> <th>T elapsed</th><th>Settlement</th><th>S elapsed</th></tr>")
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
                sepsed = ""
                if not plf.data.final_disposition is None:
                    sepsed = time_offset(plf.data.final_disposition.datetime, t0)
                peer = gbls.conn_peers.get(plf.data.conn_id, "")
                print("<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> "
                      "<td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> </tr>" %
                      (plf.adverbl_link_to(), plf.datetime, plf.lineno, plf.data.conn_id, plf.data.direction, peer, delta, epsed,
                       plf.data.disposition_display, sepsed))
        print("</table>")

    print("<hr>")

    # link names traversing network
    print("<a name=\"c_linkprogress\"></a>")
    print("<h3>Link name propagation</h3>")
    for i in range(0, gbls.shorteners.short_link_names.len()):
        if gbls.shorteners.short_link_names.len() == 0:
            break
        sname = gbls.shorteners.short_link_names.shortname(i)
        print("<a name=\"%s\"></a> <h4>%s" % (sname, sname))
        print(" <span> <div width=\"100%%\"; style=\"display:block; font-weight: normal; margin-bottom: 2px\" >")
        print(gbls.shorteners.short_link_names.longname(i, True))
        print("</div> </span>")
        print("</h4>")
        print("<table>")
        print("<tr><th>src</th> <th>Time</th> <th>Log Line</th> <th>ConnId</th> <th>Dir</th> <th>Peer</th> "
              "<th>T delta</th> <th>T elapsed</th></tr>")
        t0 = None
        tlast = None
        for plf in tree:
            if plf.data.name == "attach" and plf.data.link_short_name == sname:
                if t0 is None:
                    t0 = plf.datetime
                    delta = "0.000000"
                    epsed = "0.000000"
                else:
                    delta = time_offset(plf.datetime, tlast)
                    epsed = time_offset(plf.datetime, t0)
                tlast = plf.datetime
                peer = gbls.conn_peers.get(plf.data.conn_id, "")
                print("<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> "
                      "<td>%s</td> <td>%s</td></tr>" %
                      (plf.adverbl_link_to(), plf.datetime, plf.lineno, plf.data.conn_id, plf.data.direction, peer, delta, epsed))
        print("</table>")

    print("<hr>")


    # short data index
    print("<a name=\"c_peerdump\"></a>")
    gbls.shorteners.short_peer_names.htmlDump(True)

    print("<a name=\"c_linkdump\"></a>")
    gbls.shorteners.short_link_names.htmlDump(True)

    print("<a name=\"c_msgdump\"></a>")
    gbls.shorteners.short_data_names.htmlDump(True)

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

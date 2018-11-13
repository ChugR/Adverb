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

import ast
import cgi
import os
import sys
import traceback

import common
import parser
import router
import text


def time_offset(ttest, t0):
    """
    Return a string time delta between two datetime objects in seconds formatted
    to six significant decimal places.
    :param ttest:
    :param t0:
    :return:
    """
    delta = ttest - t0
    t = float(delta.seconds) + float(delta.microseconds) / 1000000.0
    return "%0.06f" % t


def show_noteworthy_line(plf, comn):
    """
    Given a log line, print the noteworthy display line
    :param plf: parsed log line
    :param comn:
    :return:
    """
    rid = plf.router.iname
    id = "[%s]" % plf.data.conn_id
    peerconnid = "[%s]" % comn.conn_peers_connid.get(plf.data.conn_id, "")
    peer = plf.router.conn_peer_display.get(plf.data.conn_id, "")  # peer container id
    print("%s %s %s %s %s %s %s<br>" %
          (plf.adverbl_link_to(), rid, id, plf.data.direction, peerconnid, peer,
           plf.data.web_show_str))


#
#
def main_except(argv):
    """
    Given a list of log file names, send the javascript web page to stdout
    """
    if len(argv) < 2:
        sys.exit('Usage: %s [--no-data] log-file-name [log-file-name ...]' % argv[0])

    # Instantiate a common block
    comn = common.Common()

    # optparse - look for --no-data switch
    if argv[1] == "--no-data":
        comn.arg_index_data = False
        del argv[1]

    # process the log files and add the results to router_array
    for log_i in range(0, len(sys.argv) - 1):
        arg_log_file = sys.argv[log_i + 1]
        comn.log_fns.append(arg_log_file)
        comn.n_logs += 1

        if not os.path.exists(arg_log_file):
            sys.exit('ERROR: log file %s was not found!' % arg_log_file)

        # parse the log file
        rtrs = parser.parse_log_file(arg_log_file, log_i, comn)
        comn.routers.append(rtrs)

        # marshall facts about the run
        for rtr in rtrs:
            rtr.discover_connection_facts(comn)

    # Create lists of various things sorted by time
    tree = []  # log line
    ls_tree = []  # link state lines
    rr_tree = []  # restart records
    for rtrlist in comn.routers:
        for rtr in rtrlist:
            tree += rtr.lines
            ls_tree += rtr.router_ls
            rr_tree.append(rtr.restart_rec)
    tree = sorted(tree, key=lambda lfl: lfl.datetime)
    ls_tree = sorted(ls_tree, key=lambda lfl: lfl.datetime)
    rr_tree = sorted(rr_tree, key=lambda lfl: lfl.datetime)

    # Back-propagate a router name/version/mode to each list's router0.
    # Complain if container name or version changes between instances.
    # Fill in container_id and shortened display_name tables
    for fi in range(comn.n_logs):
        rtrlist = comn.routers[fi]
        if len(rtrlist) > 1:
            if rtrlist[0].container_name is None:
                rtrlist[0].container_name = rtrlist[1].container_name
            if rtrlist[0].version is None:
                rtrlist[0].version = rtrlist[1].version
            if rtrlist[0].mode is None:
                rtrlist[0].mode = rtrlist[1].mode
            for i in range(0, len(rtrlist) - 1):
                namei = rtrlist[i].container_name
                namej = rtrlist[i + 1].container_name
                if namei != namej:
                    sys.exit('Inconsistent container names, log file %s, instance %d:%s but instance %d:%s' %
                             (comn.log_fns[fi], i, namei, i + 1, namej))
                namei = rtrlist[i].version
                namej = rtrlist[i + 1].version
                if namei != namej:
                    sys.exit('Inconsistent router versions, log file %s, instance %d:%s but instance %d:%s' %
                             (comn.log_fns[fi], i, namei, i + 1, namej))
                namei = rtrlist[i].mode
                namej = rtrlist[i + 1].mode
                if namei != namej:
                    sys.exit('Inconsistent router modes, log file %s, instance %d:%s but instance %d:%s' %
                             (comn.log_fns[fi], i, namei, i + 1, namej))
        name = rtrlist[0].container_name if len(rtrlist) > 0 and rtrlist[0].container_name is not None else ("Unknown_%d" % fi)
        mode = rtrlist[0].mode if len(rtrlist) > 0 and rtrlist[0].mode is not None else "standalone"
        comn.router_ids.append(name)
        comn.router_display_names.append(comn.shorteners.short_rtr_names.translate(name))
        comn.router_modes.append(mode)

    # aggregate connection-to-frame maps into big map
    for rtrlist in comn.routers:
        for rtr in rtrlist:
            comn.conn_to_frame_map.update(rtr.conn_to_frame_map)

    # generate router-to-router connection peer relationships
    peer_list = []
    for plf in tree:
        if plf.data.name == "open" and plf.data.direction_is_in():
            cid = plf.data.conn_id  # the router that generated this log file
            if "properties" in plf.data.described_type.dict:
                peer_conn = plf.data.described_type.dict["properties"].get(':"qd.conn-id"',
                                                                           "")  # router that sent the open
                if peer_conn != "" and plf.data.conn_peer != "":
                    pid_peer = plf.data.conn_peer.strip('\"')
                    rtr, rtridx = router.which_router_id_tod(comn.routers, pid_peer, plf.datetime)
                    if rtr is not None:
                        pid = rtr.conn_id(peer_conn)
                        hit = sorted((cid, pid))
                        if hit not in peer_list:
                            peer_list.append(hit)

    for (key, val) in peer_list:
        if key in comn.conn_peers_connid:
            sys.exit('key val messed up')
        if val in comn.conn_peers_connid:
            sys.exit('key val messed up')
        comn.conn_peers_connid[key] = val
        comn.conn_peers_connid[val] = key
        cn_k = comn.router_ids[common.index_of_log_letter(key)]
        cn_v = comn.router_ids[common.index_of_log_letter(val)]
        comn.conn_peers_display[key] = comn.shorteners.short_rtr_names.translate(cn_v)
        comn.conn_peers_display[val] = comn.shorteners.short_rtr_names.translate(cn_k)
    #
    # Start producing the output stream
    #
    print(text.web_page_head())

    #
    # Generate javascript
    #
    # output the frame show/hide functions into the header
    for conn_id, plfs in common.dict_iteritems(comn.conn_to_frame_map):
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
    for conn_id, frames_ids in common.dict_iteritems(comn.conn_to_frame_map):
        print("  javascript:select_cb_sel_%s();" % conn_id)
    print("}")
    print("function deselect_all() {")
    for conn_id, frames_ids in common.dict_iteritems(comn.conn_to_frame_map):
        print("  javascript:deselect_cb_sel_%s();" % conn_id)
    print("}")
    print("function toggle_all() {")
    for conn_id, frames_ids in common.dict_iteritems(comn.conn_to_frame_map):
        print("  javascript:toggle_cb_sel_%s();" % conn_id)
    print("}")

    #
    print("</script>")
    print("</head>")
    print("<body>")
    #

    # Table of contents
    print(text.web_page_toc())

    # Report how much data was skipped if --no-data switch in effect
    if not comn.arg_index_data:
        print("--no-data switch in effect. %d log lines skipped" % comn.data_skipped)
        print("<p><hr>")

    # file(s) included in this doc
    print("<a name=\"c_logfiles\"></a>")
    print("<h3>Log files</h3>")
    print("<table><tr><th>Log</th> <th>Container name</th> <th>Version</th> <th>Mode</th>"
          "<th>Instances</th> <th>Log file path</th></tr>")
    for i in range(comn.n_logs):
        rtrlist = comn.routers[i]
        if len(rtrlist) > 0:
            print("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
                  (common.log_letter_of(i), rtrlist[0].container_name, rtrlist[0].version, rtrlist[0].mode,
                   str(len(rtrlist)), os.path.abspath(comn.log_fns[i])))
        else:
            print("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
                  (common.log_letter_of(i), text.nbsp(), text.nbsp(),
                   str(len(rtrlist)), os.path.abspath(comn.log_fns[i])))
    print("</table>")
    print("<hr>")

    # reboot chronology
    print("<a name=\"c_rtrinstances\"></a>")
    print("<h3>Router Reboot Chronology</h3>")
    print("<table><tr><th>Log</th> <th>Time</th> <th>Container name</th> ")
    for i in range(len(comn.routers)):
        print("<td>%s</td>" % common.log_letter_of(i))
    print("</tr>")
    for rr in rr_tree:
        print("<tr><td>%s</td><td>%s</td><td>%s</td>" %
              (rr.router.iname, rr.datetime, rr.router.container_name))
        for i in range(len(comn.routers)):
            print("<td>%s</td> " % (rr.router.iname if i == rr.router.log_index else text.nbsp()))
        print("</tr>")
    print("</table>")
    print("<hr>")

    # print the connection peer tables
    #
    # +------+--------------------+-----+--------------------+-------+-------+----------+--------+
    # | View |       Router       | Dir |       Peer         | Log   | N     | Transfer | AMQP   |
    # |      +-----------+--------+     +--------+-----------+ lines | links | bytes    | errors |
    # |      | container | connid |     | connid | container |       |       |          |        |
    # +------+-----------+--------+-----+--------+-----------+-------+-------+----------+--------+

    print("<a name=\"c_connections\"></a>")
    print("<h3>Connections</h3>")

    print("<p>")
    print("<button onclick=\"javascript:select_all()\">Select All</button>")
    print("<button onclick=\"javascript:deselect_all()\">Deselect All</button>")
    print("<button onclick=\"javascript:toggle_all()\">Toggle All</button>")
    print("</p>")

    print("<h3>Connections by ConnectionId</h3>")
    print(
        "<table><tr> <th rowspan=\"2\">View</th> <th colspan=\"2\">Router</th> <th rowspan=\"2\">Dir</th> <th colspan=\"2\">Peer</th> <th rowspan=\"2\">Log lines</th> "
        "<th rowspan=\"2\">N links</th><th rowspan=\"2\">Transfer bytes</th> <th rowspan=\"2\">AMQP errors</th> <th rowspan=\"2\">Open time</th> <th rowspan=\"2\">Close time</th></tr>")
    print("<tr> <th>container</th> <th>connid</th> <th>connid</th> <th>container</th></tr>")

    tConn = 0
    tLines = 0
    tBytes = 0
    tErrs = 0
    tLinks = 0
    for rtrlist in comn.routers:
        for rtr in rtrlist:
            rid = rtr.container_name
            for conn in rtr.conn_list:
                tConn += 1
                id = rtr.conn_id(conn)  # this router's full connid 'A0_3'
                peer = rtr.conn_peer_display.get(id, "")  # peer container id
                peerconnid = comn.conn_peers_connid.get(id, "")
                n_links = rtr.details.links_in_connection(id)
                tLinks += n_links
                errs = sum(1 for plf in rtr.conn_to_frame_map[id] if plf.data.amqp_error)
                tErrs += errs
                stime = rtr.conn_open_time.get(id, text.nbsp())
                if stime != text.nbsp():
                    stime = stime.datetime
                etime = rtr.conn_close_time.get(id, text.nbsp())
                if etime != text.nbsp():
                    etime = etime.datetime
                print("<tr>")
                print("<td> <input type=\"checkbox\" id=\"cb_sel_%s\" " % id)
                print("checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\"> </td>" % (id))
                print("<td>%s</td><td><a href=\"#cd_%s\">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                      "<td>%d</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td></tr>" %
                      (rid, id, id, rtr.conn_dir[id], peerconnid, peer, rtr.conn_log_lines[id], n_links,
                       rtr.conn_xfer_bytes[id], errs, stime, etime))
                tLines += rtr.conn_log_lines[id]
                tBytes += rtr.conn_xfer_bytes[id]
    print(
        "<td>Total</td><td>%d</td><td> </td><td> </td><td> </td><td> </td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>" %
        (tConn, tLines, tLinks, tBytes, tErrs))
    print("</table>")

    print("<h3>Router Restart and Connection chronology</h3>")

    cl = []
    for rtrlist in comn.routers:
        for rtr in rtrlist:
            rid = rtr.container_name
            cl.append(common.RestartRec(rtr.iname, rtr, "restart", rtr.restart_rec.datetime))
            for conn in rtr.conn_list:
                id = rtr.conn_id(conn)
                if id in rtr.conn_open_time:
                    cl.append(common.RestartRec(id, rtr, "open", rtr.conn_open_time[id].datetime))
                if id in rtr.conn_close_time:
                    cl.append(common.RestartRec(id, rtr, "close", rtr.conn_close_time[id].datetime))
    cl = sorted(cl, key=lambda lfl: lfl.datetime)

    print("<table><tr> <th>Time</th> <th>Id</th> <th>Event</th> <th>container</th> <th>connid</th> "
          "<th>Dir</th> <th>connid</th> <th>container</th>")
    for i in range(len(comn.routers)):
        print("<td>%s</td>" % common.log_letter_of(i))
    print("</tr>")
    for c in cl:
        if c.event == "restart":
            rid = c.router.container_name
            print("<tr><td>%s</td> <td>%s</td> <td><span style=\"background-color:yellow\">%s</span></td><td>%s</td> "
                  "<td>%s</td> <td>%s</td><td>%s</td> <td>%s</td>" %
                  (c.datetime, c.id, c.event, rid, "", "", "", ""))
            for i in range(len(comn.routers)):
                print("<td>%s</td> " % (c.id if i == c.router.log_index else text.nbsp()))
            print("</tr>")
        else:
            rid = c.router.container_name
            cdir = c.router.conn_dir[c.id]
            peer = c.router.conn_peer_display.get(c.id, "")  # peer container id
            peerconnid = comn.conn_peers_connid.get(c.id, "")
            print("<tr><td>%s</td> <td>%s</td> <td>%s</td><td>%s</td> <td>%s</td> <td>%s</td><td>%s</td> <td>%s</td>" %
                  (c.datetime, c.id, c.event, rid, c.id, cdir, peerconnid, peer))
            for i in range(len(comn.routers)):
                print("<td>%s</td> " % (text.nbsp()))
            print("</tr>")
    print("</table>")
    print("<hr>")

    # connection details
    print("<a name=\"c_conndetails\"></a>")
    print("<h3>Connection Details</h3>")
    for rtrlist in comn.routers:
        for rtr in rtrlist:
            rtr.details.show_html()
    print("<hr>")

    # noteworthy log lines: highlight errors and stuff
    print("<a name=\"c_noteworthy\"></a>")
    print("<h3>Noteworthy</h3>")
    n_errors = 0
    n_settled = 0
    n_more = 0
    n_resume = 0
    n_aborted = 0
    n_drain = 0
    for plf in tree:
        if plf.data.amqp_error:
            n_errors += 1
        if plf.data.transfer_settled:
            n_settled += 1
        if plf.data.transfer_more:
            n_more += 1
        if plf.data.transfer_resume:
            n_resume += 1
        if plf.data.transfer_aborted:
            n_aborted += 1
        if plf.data.flow_drain:
            n_drain += 1
    # amqp errors
    print("<a href=\"javascript:toggle_node('noteworthy_errors')\">%s%s</a> AMQP errors: %d<br>" %
          (text.lozenge(), text.nbsp(), n_errors))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_errors\">")
    for plf in tree:
        if plf.data.amqp_error:
            show_noteworthy_line(plf, comn)
    print("</div>")
    # transfers with settled=true
    print("<a href=\"javascript:toggle_node('noteworthy_settled')\">%s%s</a> Presettled transfers: %d<br>" %
          (text.lozenge(), text.nbsp(), n_settled))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_settled\">")
    for plf in tree:
        if plf.data.transfer_settled:
            show_noteworthy_line(plf, comn)
    print("</div>")
    # transfers with more=true
    print("<a href=\"javascript:toggle_node('noteworthy_more')\">%s%s</a> Partial transfers with 'more' set: %d<br>" %
          (text.lozenge(), text.nbsp(), n_more))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_more\">")
    for plf in tree:
        if plf.data.transfer_more:
            show_noteworthy_line(plf, comn)
    print("</div>")
    # transfers with resume=true, whatever that is
    print("<a href=\"javascript:toggle_node('noteworthy_resume')\">%s%s</a> Resumed transfers: %d<br>" %
          (text.lozenge(), text.nbsp(), n_resume))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_resume\">")
    for plf in tree:
        if plf.data.transfer_resume:
            show_noteworthy_line(plf, comn)
    print("</div>")
    # transfers with abort=true
    print("<a href=\"javascript:toggle_node('noteworthy_aborts')\">%s%s</a> Aborted transfers: %d<br>" %
          (text.lozenge(), text.nbsp(), n_aborted))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_aborts\">")
    for plf in tree:
        if plf.data.transfer_aborted:
            show_noteworthy_line(plf, comn)
    print("</div>")
    # flow with drain=true
    print("<a href=\"javascript:toggle_node('noteworthy_drain')\">%s%s</a> Flow with 'drain' set: %d<br>" %
          (text.lozenge(), text.nbsp(), n_drain))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"noteworthy_drain\">")
    for plf in tree:
        if plf.data.flow_drain:
            show_noteworthy_line(plf, comn)
    print("</div>")
    print("<hr>")

    # the proton log lines
    # log lines in         f_A_116
    # log line details in  f_A_116_d
    print("<a name=\"c_logdata\"></a>")
    print("<h3>Log data</h3>")
    for plf in tree:
        l_dict = plf.data.described_type.dict
        print("<div width=\"100%%\" style=\"display:block  margin-bottom: 2px\" id=\"%s\">" % plf.fid)
        print("<a name=\"%s\"></a>" % plf.fid)
        detailname = plf.fid + "_d"  # type: str
        loz = "<a href=\"javascript:toggle_node('%s')\">%s%s</a>" % (detailname, text.lozenge(), text.nbsp())
        rtr = plf.router
        rid = comn.router_display_names[rtr.log_index]

        peerconnid = "%s" % comn.conn_peers_connid.get(plf.data.conn_id, "")
        peer = rtr.conn_peer_display.get(plf.data.conn_id, "")  # peer container id
        print(loz, plf.datetime, ("%s#%d" % (plf.prefixi, plf.lineno)), rid, ("[%s]" % plf.data.conn_id),
              plf.data.direction, ("[%s]" % peerconnid), peer,
              plf.data.web_show_str, plf.data.disposition_display, "<br>")
        print(" <div width=\"100%%\"; "
              "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
              "id=\"%s\">" %
              detailname)
        for key in sorted(common.dict_iterkeys(l_dict)):
            val = l_dict[key]
            print("%s : %s <br>" % (key, cgi.escape(str(val))))
        if plf.data.name == "transfer":
            print("Header and annotations : %s <br>" % plf.data.transfer_hdr_annos)
        print("</div>")
        print("</div>")
    print("<hr>")

    # data traversing network
    print("<a name=\"c_messageprogress\"></a>")
    print("<h3>Message progress</h3>")
    for i in range(0, comn.shorteners.short_data_names.len()):
        sname = comn.shorteners.short_data_names.shortname(i)
        size = 0
        for plf in tree:
            if plf.data.name == "transfer" and plf.transfer_short_name == sname:
                size = plf.data.transfer_size
                break
        print("<a name=\"%s\"></a> <h4>%s (%s)" % (sname, sname, size))
        print(" <span> <a href=\"javascript:toggle_node('%s')\"> %s</a>" % ("data_" + sname, text.lozenge()))
        print(" <div width=\"100%%\"; style=\"display:none; font-weight: normal; margin-bottom: 2px\" id=\"%s\">" %
              ("data_" + sname))
        print(" ", comn.shorteners.short_data_names.longname(i, True))
        print("</div> </span>")
        print("</h4>")
        print("<table>")
        print(
            "<tr><th>Src</th> <th>Time</th> <th>Router</th> <th>ConnId</th> <th>Dir</th> <th>ConnId</th> <th>Peer</th> "
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
                if plf.data.final_disposition is not None:
                    sepsed = time_offset(plf.data.final_disposition.datetime, t0)
                rid = plf.router.iname
                peerconnid = "%s" % comn.conn_peers_connid.get(plf.data.conn_id, "")
                peer = plf.router.conn_peer_display.get(plf.data.conn_id, "")  # peer container id
                print("<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> "
                      "<td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> </tr>" %
                      (plf.adverbl_link_to(), plf.datetime, rid, plf.data.conn_id, plf.data.direction,
                       peerconnid, peer, delta, epsed,
                       plf.data.disposition_display, sepsed))
        print("</table>")

    print("<hr>")

    # link names traversing network
    print("<a name=\"c_linkprogress\"></a>")
    print("<h3>Link name propagation</h3>")
    for i in range(0, comn.shorteners.short_link_names.len()):
        if comn.shorteners.short_link_names.len() == 0:
            break
        sname = comn.shorteners.short_link_names.prefixname(i)
        print("<a name=\"%s\"></a> <h4>%s" % (sname, sname))
        print(" <span> <div width=\"100%%\"; style=\"display:block; font-weight: normal; margin-bottom: 2px\" >")
        print(comn.shorteners.short_link_names.longname(i, True))
        print("</div> </span>")
        print("</h4>")
        print("<table>")
        print("<tr><th>src</th> <th>Time</th> <th>Router</th> <th>ConnId</th> <th>Dir</th> <th>ConnId> <th>Peer</th> "
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
                rid = plf.router.iname
                peerconnid = "%s" % comn.conn_peers_connid.get(plf.data.conn_id, "")
                peer = plf.router.conn_peer_display.get(plf.data.conn_id, "")  # peer container id
                print("<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> "
                      "<td>%s</td> <td>%s</td> <td>%s</td></tr>" %
                      (plf.adverbl_link_to(), plf.datetime, rid, plf.data.conn_id, plf.data.direction, peerconnid, peer,
                       delta, epsed))
        print("</table>")

    print("<hr>")

    # short data index
    print("<a name=\"c_rtrdump\"></a>")
    comn.shorteners.short_rtr_names.htmlDump(False)
    print("<hr>")

    print("<a name=\"c_peerdump\"></a>")
    comn.shorteners.short_peer_names.htmlDump(False)
    print("<hr>")

    print("<a name=\"c_linkdump\"></a>")
    comn.shorteners.short_link_names.htmlDump(True)
    print("<hr>")

    print("<a name=\"c_msgdump\"></a>")
    comn.shorteners.short_data_names.htmlDump(True)
    print("<hr>")

    # link state info
    # merge link state and restart records into single time based list
    cl = []
    for rtrlist in comn.routers:
        for rtr in rtrlist:
            rid = rtr.container_name
            cl.append(common.RestartRec(rtr.iname, rtr, "restart", rtr.restart_rec.datetime))
    for plf in ls_tree:
        if "costs" in plf.line:
            cl.append(common.RestartRec("ls", plf, "ls", plf.datetime))
    cl = sorted(cl, key=lambda lfl: lfl.datetime)

    # create a map of lists for each router
    # the list holds the name of other routers for which the router publishes a cost
    costs_pub = {}
    for i in range(0, comn.n_logs):
        costs_pub[comn.router_ids[i]] = []

    # cur_costs is a 2D array of costs used to tell when cost calcs have stabilized
    # Each incoming LS cost line replaces a row in this table
    # cur_costs tracks only interior routers
    interior_rtrs = []
    for rtrs in comn.routers:
        if rtrs[0].is_interior():
            interior_rtrs.append(rtrs[0].container_name)

    PEER_COST_REBOOT = -1
    PEER_COST_ABSENT = 0
    def new_costs_row(val):
        """
        return a costs row.
        :param val: -1 when router reboots, 0 when router log line processed
        :return:
        """
        res = {}
        for rtr in interior_rtrs:
            res[rtr] = val
        return res

    cur_costs = {}
    for rtr in interior_rtrs:
        cur_costs[rtr] = new_costs_row(PEER_COST_REBOOT)

    print("<a name=\"c_ls\"></a>")
    print("<h3>Routing link state</h3>")
    print("<h4>Link state costs</h4>")
    print("<table>")
    print("<tr><th>Time</th> <th>Router</th>")
    for i in range(0, comn.n_logs):
        print("<th>%s</th>" % common.log_letter_of(i))
    print("</tr>")
    for c in cl:
        if c.event == "ls":
            # link state computed costs and router reachability
            plf = c.router # cruel overload here: router is a parsed line not a router
            # Processing: Computed costs: {u'A': 1, u'C': 51L, u'B': 101L}
            print("<tr><td>%s</td> <td>%s</td>" % (plf.datetime, ("%s#%d" % (plf.router.iname, plf.lineno))))
            try:
                line = plf.line
                sti = line.find("{")
                line = line[sti:]
                l_dict = ast.literal_eval(line)
                costs_row = new_costs_row(PEER_COST_ABSENT)
                for i in range(0, comn.n_logs):
                    if len(comn.routers[i]) > 0:
                        tst_name = comn.routers[i][0].container_name
                        if tst_name in l_dict:
                            val = l_dict[tst_name]
                            costs_row[tst_name] = val
                        elif i == plf.router.log_index:
                            val = text.nbsp()
                        else:
                            val = "<span style=\"background-color:orange\">%s</span>" % (text.nbsp() * 2)
                    else:
                        val = "<span style=\"background-color:orange\">%s</span>" % (text.nbsp() * 2)
                    print("<td>%s</td>" % val)
                # track costs published when there is no column to put the number
                tgts = costs_pub[c.router.router.container_name]
                for k, v in common.dict_iteritems(l_dict):
                    if k not in comn.router_ids:
                        if k not in tgts:
                            tgts.append(k)  # this cost went unreported
                # update this router's cost view in running table
                if plf.router.is_interior():
                    cur_costs[plf.router.container_name] = costs_row
            except:
                pass
            print("</tr>")
            # if the costs are stable across all routers then put an indicator in table
            costs_stable = True
            for c_rtr in interior_rtrs:
                for r_rtr in interior_rtrs:
                    if r_rtr != c_rtr \
                            and (cur_costs[r_rtr][c_rtr] != cur_costs[c_rtr][r_rtr] \
                            or cur_costs[c_rtr][r_rtr] <= PEER_COST_ABSENT):
                        costs_stable = False
                        break
                if not costs_stable:
                    break
            if costs_stable:
                print("<tr><td><span style=\"background-color:green\">stable</span></td></tr>")
        else:
            # restart
            print("<tr><td>%s</td> <td>%s</td>" % (c.datetime, ("%s restart" % (c.router.iname))))
            for i in range(0, comn.n_logs):
                color = "green" if i == c.router.log_index else "orange"
                print("<td><span style=\"background-color:%s\">%s</span></td>" % (color, text.nbsp() * 2))
            print("</tr>")
            if c.router.is_interior():
                cur_costs[c.router.container_name] = new_costs_row(PEER_COST_REBOOT)
    print("</table>")
    print("<br>")

    # maybe display cost declarations that were not displayed
    costs_clean = True
    for k, v in common.dict_iteritems(costs_pub):
        if len(v) > 0:
            costs_clean = False
            break
    if not costs_clean:
        print("<h4>Router costs declared in logs but not displayed in Link state cost table</h4>")
        print("<table>")
        print("<tr><th>Router</th><Peers whose logs are absent</th></tr>")
        for k, v in common.dict_iteritems(costs_pub):
            if len(v) > 0:
                print("<tr><td>%s</td><td>%s</td></tr>" % (k, str(v)))
        print("</table>")
        print("<br>")

    print("<a href=\"javascript:toggle_node('ls_costs')\">%s%s</a> Link state costs data<br>" %
          (text.lozenge(), text.nbsp()))
    print(" <div width=\"100%%\"; "
          "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
          "id=\"ls_costs\">")
    print("<table>")
    print("<tr><th>Time</th> <th>Router</th> <th>Name</th> <th>Log</th></tr>")
    for plf in ls_tree:
        if "costs" in plf.line:
            print("<tr><td>%s</td> <td>%s</td>" % (plf.datetime, ("%s#%d" % (plf.router.iname, plf.lineno))))
            print("<td>%s</td>" % plf.router.container_name)
            print("<td>%s</td></tr>" % plf.line)
    print("</table>")
    print("</div>")

    print("<hr>")

    print("</body>")


def main(argv):
    try:
        main_except(argv)
        return 0
    except Exception as e:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

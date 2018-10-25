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

import amqp_detail
import common
import nicknamer
import parser
import text


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


def show_noteworthy_line(plf, gbls):
    '''
    Given a log line, print the noteworthy display line
    :param plf:
    :param glbs:
    :return:
    '''
    rid = gbls.router_display_by_prefix[plf.prefix]
    id = "[%s]" % plf.data.conn_id
    peerconnid = "[%s]" % gbls.conn_peers_connid.get(plf.data.conn_id, "")
    peer = gbls.conn_peers_popup.get(plf.data.conn_id, "")  # peer container id
    print("%s %s %s %s %s %s %s<br>" %
          (plf.adverbl_link_to(), rid, id, plf.data.direction, peerconnid, peer,
           plf.data.web_show_str))


#
#
def main_except(argv):
    #pdb.set_trace()
    """
    Given a list of log file names, send the javascript web page to stdout
    """
    if len(sys.argv) < 2:
        sys.exit('Usage: %s log-file-name [log-file-name ...]' % sys.argv[0])

    comn = common.Common()

    # connection peers
    # key=decorated connection name 'A0_3'
    conn_log_lines = {}     # val = count of log lines
    conn_xfer_bytes = {}    # val = transfer byte count

    # process the log files and add the results to router_array
    for log_i in range(0, len(sys.argv)-1):
        arg_log_file = sys.argv[log_i + 1]
        comn.log_fns.append(arg_log_file)
        comn.n_logs += 1

        if not os.path.exists(arg_log_file):
            sys.exit('ERROR: log file %s was not found!' % arg_log_file)

        # parse the log file
        rtrs = parser.parse_log_file(arg_log_file, log_i, comn)
        if len(rtrs) == 0:
            sys.exit('WARNING: log file %s has no Adverbl data!' % arg_log_file)
        comn.routers.append(rtrs)

        # marshall facts about the run
        for rtr in rtrs:
            rtr.get_connection_facts()

    # create trees to hold list of all log lines and link state lines sorted by time
    tree = []
    ls_tree = []
    for rtrlist in comn.routers:
        for rtr in rtrlist:
            tree += rtr.lines
            ls_tree += rtr.router_ls
    tree = sorted(tree, key=lambda lfl: lfl.datetime)
    ls_tree = sorted(ls_tree, key=lambda lfl: lfl.datetime)

    # back-propagate a router name/version to each list's router0.
    # complain if container name or version changes between runs
    for fi in range(comn.n_logs):
        rtrlist = comn.routers[fi]
        if len(rtrlist) > 1:
            if rtrlist[0].container_name is None:
                rtrlist[0].container_name = rtrlist[1].container_name
            if rtrlist[0].version is None:
                rtrlist[0].version = rtrlist[1].version
            for i in range(0, len(rtrlist) - 1):
                namei = rtrlist[i].container_name
                namej = rtrlist[i+1].container_name
                if  namei != namej:
                    sys.exit('Inconsistent container names, log file %s, instance %d:%s but instance %d:%s' %
                             (comn.log_fns[fi], i, namei, i+1, namej))
                namei = rtrlist[i].version
                namej = rtrlist[i+1].version
                if  namei != namej:
                    sys.exit('Inconsistent router versions, log file %s, instance %d:%s but instance %d:%s' %
                             (comn.log_fns[fi], i, namei, i+1, namej))

    # # generate the router name display helper lists
    # for i in range(comn.n_logs):
    #     log_letter = comn.log_letter_of(i)
    #     id = comn.router_ids[i]
    #     dispname = comn.shorteners.short_rtr_names.translate( id, show_popup=True )
    #     comn.router_display_names.append( dispname )
    #     comn.router_ids_by_prefix[log_letter] = id
    #     comn.router_display_by_prefix[log_letter] = dispname
    #     comn.router_prefix_by_id[id] = log_letter
    #
    # # populate a list with all connectionIds
    # # populate a map with key=connectionId, val=[list of associated frames])
    # for i in range(comn.n_logs):
    #     for conn in comn.conn_lists[i]:
    #         id = comn.conn_id_of( comn.log_letter_of(i), conn)
    #         comn.all_conn_names.append(id)
    #         comn.conn_to_frame_map[id] = []
    # for plf in tree:
    #     comn.conn_to_frame_map[plf.data.conn_id].append(plf)
    #
    # # generate connection details and per-connection-session-link relationships
    # comn.all_details = AllDetails(tree, comn)
    #
    # # generate router-to-router connection peer relationships
    # peer_list = []
    # STRATEGY_1 = False
    # STRATEGY_2 = True
    #
    # # Strategy 1 before Open holds connid field:
    # # search for short names of links where the link name
    # # is passed back and forth between routers
    # if STRATEGY_1:
    #     if comn.shorteners.short_link_names.len() > 0:
    #         for i in range(0, comn.shorteners.short_link_names.len()):
    #             sname = comn.shorteners.short_link_names.shortname(i)
    #             cand = []
    #             for plf in tree:
    #                 if plf.data.name == "attach" and plf.data.link_short_name == sname:
    #                     peer = comn.conn_peers.get(plf.data.conn_id, "")
    #                     if len(peer) > 0:
    #                         cand.append(plf.data.conn_id)
    #             if len(cand) == 4:
    #                 if (cand[0] == cand[3] and cand[1] == cand[2]) and (not cand[0] == cand[1]):
    #                     hit = sorted((cand[0], cand[1]))
    #                     if not hit in peer_list:
    #                         peer_list.append( hit )
    #
    # # Strategy 2 is to find conn-id in Open frames:
    # if STRATEGY_2:
    #     for plf in tree:
    #         if plf.data.name == "open" and plf.data.direction_is_in():
    #             cid = plf.data.conn_id     # the router that generated this log file
    #             if "properties" in plf.data.described_type.dict:
    #                 peer_conn = plf.data.described_type.dict["properties"].get(':"qd.conn-id"', "") # router that sent the open
    #                 if not peer_conn == "" and not plf.data.conn_peer == "":
    #                     pid_peer = plf.data.conn_peer.strip('\"')
    #                     pid = comn.router_prefix_by_id.get(pid_peer, "")
    #                     if not pid == "":
    #                         pid = pid + "_" + peer_conn
    #                         hit = sorted((cid, pid))
    #                         if not hit in peer_list:
    #                             peer_list.append( hit )
    #
    #
    # for (key, val) in peer_list:
    #     if key in comn.conn_peers_connid:
    #         sys.exit('key val messed up')
    #     if val in comn.conn_peers_connid:
    #         sys.exit('key val messed up')
    #     comn.conn_peers_connid[key] = val
    #     comn.conn_peers_connid[val] = key

    #
    # Start producing the output stream
    #
    print (text.web_page_head())

    # #
    # # Generate javascript
    # #
    # # output the frame show/hide functions into the header
    # for conn_id, plfs in gbls.conn_to_frame_map.iteritems():
    #     print("function show_%s() {" % conn_id)
    #     for plf in plfs:
    #         print("  javascript:show_node(\'%s\');" % plf.fid)
    #     print("}")
    #     print("function hide_%s() {" % conn_id)
    #     for plf in plfs:
    #         print("  javascript:hide_node(\'%s\');" % plf.fid)
    #     print("}")
    #     # manipulate checkboxes
    #     print("function show_if_cb_sel_%s() {" % conn_id)
    #     print("  if (document.getElementById(\"cb_sel_%s\").checked) {" % conn_id)
    #     print("    javascript:show_%s();" % conn_id)
    #     print("  } else {")
    #     print("    javascript:hide_%s();" % conn_id)
    #     print("  }")
    #     print("}")
    #     print("function select_cb_sel_%s() {" % conn_id)
    #     print("  document.getElementById(\"cb_sel_%s\").checked = true;" % conn_id)
    #     print("  javascript:show_%s();" % conn_id)
    #     print("}")
    #     print("function deselect_cb_sel_%s() {" % conn_id)
    #     print("  document.getElementById(\"cb_sel_%s\").checked = false;" % conn_id)
    #     print("  javascript:hide_%s();" % conn_id)
    #     print("}")
    #     print("function toggle_cb_sel_%s() {" % conn_id)
    #     print("  if (document.getElementById(\"cb_sel_%s\").checked) {" % conn_id)
    #     print("    document.getElementById(\"cb_sel_%s\").checked = false;" % conn_id)
    #     print("  } else {")
    #     print("    document.getElementById(\"cb_sel_%s\").checked = true;" % conn_id)
    #     print("  }")
    #     print("  javascript:show_if_cb_sel_%s();" % conn_id)
    #     print("}")
    #
    # # Select/Deselect/Toggle All Connections functions
    # print("function select_all() {")
    # for conn_id, frames_ids in gbls.conn_to_frame_map.iteritems():
    #     print("  javascript:select_cb_sel_%s();" % conn_id)
    # print("}")
    # print("function deselect_all() {")
    # for conn_id, frames_ids in gbls.conn_to_frame_map.iteritems():
    #     print("  javascript:deselect_cb_sel_%s();" % conn_id)
    # print("}")
    # print("function toggle_all() {")
    # for conn_id, frames_ids in gbls.conn_to_frame_map.iteritems():
    #     print("  javascript:toggle_cb_sel_%s();" % conn_id)
    # print("}")

    #
    print("</script>")
    print("</head>")
    print("<body>")
    #

    # Table of contents
    print(text.web_page_toc())

    # file(s) included in this doc
    print("<a name=\"c_logfiles\"></a>")
    print("<h3>Log files</h3>")
    print("<table><tr><th>Log</th> <th>Container name</th> <th>Version</th> <th>Log file path</th></tr>")
    for i in range(comn.n_logs):
        rtrlist = comn.routers[i]
        print("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
              (common.log_letter_of(i), rtrlist[0].container_name, rtrlist[0].version, os.path.abspath(comn.log_fns[i])))
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

    # +------+--------------------+-----+--------------------+-------+-------+----------+--------+
    # | View |       Router       | Dir |       Peer         | Log   | N     | Transfer | AMQP   |
    # |      +-----------+--------+     +--------+-----------+ lines | links | bytes    | errors |
    # |      | container | connid |     | connid | container |       |       |          |        |
    # +------+-----------+--------+-----+--------+-----------+-------+-------+----------+--------+

    print("<table><tr> <th rowspan=\"2\">View</th> <th colspan=\"2\">Router</th> <th rowspan=\"2\">Dir</th> <th colspan=\"2\">Peer</th> <th rowspan=\"2\">Log lines</th> "
          "<th rowspan=\"2\">N links</th><th rowspan=\"2\">Transfer bytes</th> <th rowspan=\"2\">AMQP errors</th></tr>")
    print("<tr> <th>container</th> <th>connid</th> <th>connid</th> <th>container</th></tr>")

    for rtrlist in comn.routers:
        for rtr in rtrlist:
            for conn in rtr.conn_list:
                print("<tr><td>%s</td></tr>" % (rtr.conn_id(conn)))

    #
    #
    # tConn = 0
    # tLines = 0
    # tBytes = 0
    # tErrs = 0
    # tLinks = 0
    # for i in range(gbls.n_logs):
    #     conn_list = gbls.conn_lists[i]
    #     for conn in conn_list:
    #         tConn += 1
    #         rid = gbls.router_ids[i]    # this router container id
    #         id = gbls.conn_id_of(gbls.log_letter_of(i), conn) # this router connid
    #         peer = gbls.conn_peers_popup.get(id, "") # peer container id
    #         peerconnid = gbls.conn_peers_connid.get(id, "")
    #         n_links = gbls.all_details.links_in_connection(id)
    #         tLinks += n_links
    #         errs = sum(1 for plf in gbls.conn_to_frame_map[id] if plf.data.amqp_error)
    #         tErrs += errs
    #         print("<tr>")
    #         print("<td> <input type=\"checkbox\" id=\"cb_sel_%s\" " % id)
    #         print("checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\"> </td>" % (id))
    #
    #         print("<td>%s</td><td><a href=\"#cd_%s\">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td><td>%d</td></tr>" %
    #               (rid, id, id, gbls.conn_dirs[id], peerconnid, peer, conn_log_lines[id], n_links, conn_xfer_bytes[id], errs))
    #         tLines += conn_log_lines[id]
    #         tBytes += conn_xfer_bytes[id]
    # print("<td>Total</td><td>%d</td><td> </td><td> </td><td> </td><td> </td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>" %
    #       (tConn, tLines, tLinks, tBytes, tErrs))

    print("</table>")
    print("<hr>")

    # # connection details
    # print("<a name=\"c_conndetails\"></a>")
    # print("<h3>Connection Details</h3>")
    # gbls.all_details.show_html()
    # print("<hr>")
    #
    # # noteworthy log lines: highlight errors and stuff
    # print("<a name=\"c_noteworthy\"></a>")
    # print("<h3>Noteworthy</h3>")
    # nErrors = 0
    # nSettled = 0
    # nMore = 0
    # nResume = 0
    # nAborted = 0
    # nDrain = 0
    # for plf in tree:
    #     if plf.data.amqp_error:
    #         nErrors += 1
    #     if plf.data.transfer_settled:
    #         nSettled += 1
    #     if plf.data.transfer_more:
    #         nMore += 1
    #     if plf.data.transfer_resume:
    #         nResume += 1
    #     if plf.data.transfer_aborted:
    #         nAborted += 1
    #     if plf.data.flow_drain:
    #         nDrain += 1
    # # amqp errors
    # print("<a href=\"javascript:toggle_node('noteworthy_errors')\">%s%s</a> AMQP errors: %d<br>" %
    #       (lozenge(), nbsp(), nErrors))
    # print(" <div width=\"100%%\"; "
    #       "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
    #       "id=\"noteworthy_errors\">")
    # for plf in tree:
    #     if plf.data.amqp_error:
    #         show_noteworthy_line(plf, gbls)
    # print("</div>")
    # # transfers with settled=true
    # print("<a href=\"javascript:toggle_node('noteworthy_settled')\">%s%s</a> Presettled transfers: %d<br>" %
    #       (lozenge(), nbsp(), nSettled))
    # print(" <div width=\"100%%\"; "
    #       "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
    #       "id=\"noteworthy_settled\">")
    # for plf in tree:
    #     if plf.data.transfer_settled:
    #         show_noteworthy_line(plf, gbls)
    # print("</div>")
    # # transfers with more=true
    # print("<a href=\"javascript:toggle_node('noteworthy_more')\">%s%s</a> Partial transfers with 'more' set: %d<br>" %
    #       (lozenge(), nbsp(), nMore))
    # print(" <div width=\"100%%\"; "
    #       "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
    #       "id=\"noteworthy_more\">")
    # for plf in tree:
    #     if plf.data.transfer_more:
    #         show_noteworthy_line(plf, gbls)
    # print("</div>")
    # # transfers with resume=true, whatever that is
    # print("<a href=\"javascript:toggle_node('noteworthy_resume')\">%s%s</a> Resumed transfers: %d<br>" %
    #       (lozenge(), nbsp(), nResume))
    # print(" <div width=\"100%%\"; "
    #       "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
    #       "id=\"noteworthy_resume\">")
    # for plf in tree:
    #     if plf.data.transfer_resume:
    #         show_noteworthy_line(plf, gbls)
    # print("</div>")
    # # transfers with abort=true
    # print("<a href=\"javascript:toggle_node('noteworthy_aborts')\">%s%s</a> Aborted transfers: %d<br>" %
    #       (lozenge(), nbsp(), nAborted))
    # print(" <div width=\"100%%\"; "
    #       "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
    #       "id=\"noteworthy_aborts\">")
    # for plf in tree:
    #     if plf.data.transfer_aborted:
    #         show_noteworthy_line(plf, gbls)
    # print("</div>")
    # # flow with drain=true
    # print("<a href=\"javascript:toggle_node('noteworthy_drain')\">%s%s</a> Flow with 'drain' set: %d<br>" %
    #       (lozenge(), nbsp(), nDrain))
    # print(" <div width=\"100%%\"; "
    #       "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
    #       "id=\"noteworthy_drain\">")
    # for plf in tree:
    #     if plf.data.flow_drain:
    #         show_noteworthy_line(plf, gbls)
    # print("</div>")
    # print("<hr>")

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
        loz = "<a href=\"javascript:toggle_node('%s')\">%s%s</a>" % (detailname, text.lozenge(), text.nbsp())
        rid =  "RID" # gbls.router_display_by_prefix[plf.prefix]
        peerconnid = "PEERCONNID" # ""[%s]" % gbls.conn_peers_connid.get(plf.data.conn_id, "")
        peer = "PEER" #gbls.conn_peers_popup.get(plf.data.conn_id, "")  # peer container id
        print(loz, plf.datetime, ("%s#%d" % (plf.prefixi, plf.lineno)), rid, ("[%s]" % plf.data.conn_id),
              plf.data.direction, peerconnid, peer,
              plf.data.web_show_str, plf.data.disposition_display, "<br>")
        print(" <div width=\"100%%\"; "
              "style=\"display:none; font-weight: normal; margin-bottom: 2px; margin-left: 10px\" "
              "id=\"%s\">" %
              (detailname))
        for key in sorted(dict.iterkeys()):
            val = dict[key]
            print("%s : %s <br>" % (key, cgi.escape( str(val) )))
        if plf.data.name == "transfer":
            print("Header and annotations : %s <br>" % plf.data.transfer_hdr_annos)
        print("</div>")
        print("</div>")
    print("<hr>")

    # # data traversing network
    # print("<a name=\"c_messageprogress\"></a>")
    # print("<h3>Message progress</h3>")
    # for i in range(0, gbls.shorteners.short_data_names.len()):
    #     sname = gbls.shorteners.short_data_names.shortname(i)
    #     size = 0
    #     for plf in tree:
    #         if plf.data.name == "transfer" and plf.transfer_short_name == sname:
    #             size = plf.data.transfer_size
    #             break
    #     print("<a name=\"%s\"></a> <h4>%s (%s)" % (sname, sname, size))
    #     print(" <span> <a href=\"javascript:toggle_node('%s')\"> %s</a>" % ("data_" + sname, lozenge()))
    #     print(" <div width=\"100%%\"; style=\"display:none; font-weight: normal; margin-bottom: 2px\" id=\"%s\">" %
    #           ("data_" + sname))
    #     print(" ",  gbls.shorteners.short_data_names.longname(i, True))
    #     print("</div> </span>")
    #     print("</h4>")
    #     print("<table>")
    #     print("<tr><th>Src</th> <th>Time</th> <th>Router</th> <th>ConnId</th> <th>Dir</th> <th>ConnId</th> <th>Peer</th> "
    #           "<th>T delta</th> <th>T elapsed</th><th>Settlement</th><th>S elapsed</th></tr>")
    #     t0 = None
    #     tlast = None
    #     for plf in tree:
    #         if plf.data.name == "transfer" and plf.transfer_short_name == sname:
    #             if t0 is None:
    #                 t0 = plf.datetime
    #                 tlast = plf.datetime
    #                 delta = "0.000000"
    #                 epsed = "0.000000"
    #             else:
    #                 delta = time_offset(plf.datetime, tlast)
    #                 epsed = time_offset(plf.datetime, t0)
    #                 tlast = plf.datetime
    #             sepsed = ""
    #             if not plf.data.final_disposition is None:
    #                 sepsed = time_offset(plf.data.final_disposition.datetime, t0)
    #             rid = gbls.router_display_by_prefix[plf.prefix]
    #             peerconnid = gbls.conn_peers_connid.get(plf.data.conn_id, "")
    #             peer = gbls.conn_peers_popup.get(plf.data.conn_id, "")  # peer container id
    #             print("<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> "
    #                   "<td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> </tr>" %
    #                   (plf.adverbl_link_to(), plf.datetime, rid, plf.data.conn_id, plf.data.direction,
    #                    peerconnid, peer, delta, epsed,
    #                    plf.data.disposition_display, sepsed))
    #     print("</table>")
    #
    # print("<hr>")
    #
    # # link names traversing network
    # print("<a name=\"c_linkprogress\"></a>")
    # print("<h3>Link name propagation</h3>")
    # for i in range(0, gbls.shorteners.short_link_names.len()):
    #     if gbls.shorteners.short_link_names.len() == 0:
    #         break
    #     sname = gbls.shorteners.short_link_names.shortname(i)
    #     print("<a name=\"%s\"></a> <h4>%s" % (sname, sname))
    #     print(" <span> <div width=\"100%%\"; style=\"display:block; font-weight: normal; margin-bottom: 2px\" >")
    #     print(gbls.shorteners.short_link_names.longname(i, True))
    #     print("</div> </span>")
    #     print("</h4>")
    #     print("<table>")
    #     print("<tr><th>src</th> <th>Time</th> <th>Router</th> <th>ConnId</th> <th>Dir</th> <th>ConnId> <th>Peer</th> "
    #           "<th>T delta</th> <th>T elapsed</th></tr>")
    #     t0 = None
    #     tlast = None
    #     for plf in tree:
    #         if plf.data.name == "attach" and plf.data.link_short_name == sname:
    #             if t0 is None:
    #                 t0 = plf.datetime
    #                 delta = "0.000000"
    #                 epsed = "0.000000"
    #             else:
    #                 delta = time_offset(plf.datetime, tlast)
    #                 epsed = time_offset(plf.datetime, t0)
    #             tlast = plf.datetime
    #             rid = gbls.router_display_by_prefix[plf.prefix]
    #             peerconnid = gbls.conn_peers_connid.get(plf.data.conn_id, "")
    #             peer = gbls.conn_peers_popup.get(plf.data.conn_id, "")  # peer container id
    #             print("<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> "
    #                   "<td>%s</td> <td>%s</td> <td>%s</td></tr>" %
    #                   (plf.adverbl_link_to(), plf.datetime, rid, plf.data.conn_id, plf.data.direction, peerconnid, peer, delta, epsed))
    #     print("</table>")
    #
    # print("<hr>")
    #
    #
    # # short data index
    # print("<a name=\"c_rtrdump\"></a>")
    # gbls.shorteners.short_rtr_names.htmlDump(False)
    # print("<hr>")
    #
    # print("<a name=\"c_peerdump\"></a>")
    # gbls.shorteners.short_peer_names.htmlDump(False)
    # print("<hr>")
    #
    # print("<a name=\"c_linkdump\"></a>")
    # gbls.shorteners.short_link_names.htmlDump(True)
    # print("<hr>")
    #
    # print("<a name=\"c_msgdump\"></a>")
    # gbls.shorteners.short_data_names.htmlDump(True)
    # print("<hr>")
    #
    # # link state info
    # print("<a name=\"c_ls\"></a>")
    # print("<h3>Routing link state</h3>")
    # print("<h4>Link state costs</h4>")
    # print("<table>")
    # print("<tr><th>Time</th> <th>Router</th>")
    # for i in range(0, gbls.n_logs):
    #     print("<th>%s</th>" % gbls.router_ids[i])
    # print("</tr>")
    # for plf in ls_tree:
    #     if "costs" in plf.line:
    #         # Processing: Computed costs: {u'A': 1, u'C': 51L, u'B': 101L}
    #         print("<tr><td>%s</td> <td>%s</td>" % (plf.datetime, ("%s#%d" %(plf.prefix, plf.lineno))))
    #         try:
    #             line = plf.line
    #             sti = line.find("{")
    #             line = line[sti:]
    #             dict = ast.literal_eval(line)
    #             for i in range(0, gbls.n_logs):
    #                 if gbls.router_ids[i] in dict:
    #                     val = dict[gbls.router_ids[i]]
    #                 elif gbls.log_letter_of(i) == plf.prefix:
    #                     val = nbsp()
    #                 else:
    #                     val = "<span style=\"background-color:yellow\">%s</span>" % (nbsp() * 4)
    #                 print("<td>%s</td>" % val)
    #         except:
    #             pass
    #         print("</tr>")
    # print ("</table>")
    # print("<hr>")

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

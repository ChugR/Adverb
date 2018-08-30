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
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
import sys
import traceback
from adverbl_globals import *

'''
Given a map of all connections with lists of the associated frames
analyze and show per-connection, per-session, and per-link details.

This is done in a two-step process: 
 * Run through the frame lists and generates an intermediate structure 
   with the the details for display.
 * Generate the html from the detail structure.
This strategy allows for a third step that would allow more details
to be gleaned from the static details. For instance, if router A
sends a transfer to router B then router A's details could show 
how long it took for the transfer to reach router B. Similarly
router B's details could show how long ago router A sent the transfer. 
'''

class ConnectionDetail():
    '''
    Holds facts about sessions over the connection's lifetime
    '''
    def __init__(self, id):
        # id in form 'A_15':
        #   A is the router logfile key
        #   15 is the log connection number [15]
        self.id = id

        # seq_no number differentiates items that otherwise have same identifiers.
        # Sessions, for example: a given connection may have N distinct session
        # with local channel 0.
        self.seq_no = 0

        # combined amqp_error frames on this connection
        self.amqp_errors = 0

        # session_list holds all SessionDetail records either active or retired
        # Sessions for a connection are identified by the local channel number.
        # There may be many sessions all using the same channel number.
        # This list holds all of them.
        self.session_list = []

        # this map indexed by the channel refers to the current item in the session_list
        self.chan_map = {}

        # count of AMQP performatives for this connection that are not accounted
        # properly in session and link processing.
        # Server Accepting, SASL mechs, init, outcome, AMQP, and so on
        self.unaccounted_frame_list = []

    def FindSession(self, channel):
        '''
        Find the current session by channel number
        :param channel: the performative channel
        :return: the session or None
        '''
        return self.chan_map[channel] if channel in self.chan_map else None

    def GetId(self):
        return self.id

    def GetSeqNo(self):
        self.seq_no += 1
        return str(self.seq_no)

    def EndChannel(self, channel):
        # take existing session out of connection chan map
        if channel in self.chan_map:
            del self.chan_map[channel]

    def GetLinkEventCount(self):
        c = 0
        for session in self.session_list:
            c += session.GetLinkEventCount()
        return c

class SessionDetail():
    '''
    Holds facts about a session
    '''
    def __init__(self, conn_detail, conn_seq, start_time):
        # parent connection
        self.conn_detail = conn_detail

        # some seq number
        self.conn_epoch = conn_seq

        # Timing
        self.time_start = start_time
        self.time_end = start_time

        self.amqp_errors = 0

        self.channel = -1
        self.peer_chan = -1

        self.direction = ""

        # seq_no number differentiates items that otherwise have same identifiers.
        # links for example
        self.seq_no = 0

        self.log_line_list = []

        # link_list holds LinkDetail records
        # Links for a session are identified by a (handle, remote-handle) number pair.
        # There may be many links all using the same handle pairs.
        # This list holds all of them.
        self.link_list = []

        # link_list holds all links either active or retired
        # this map indexed by the handle refers to the current item in the link_list
        self.input_handle_link_map = {}   # link created by peer
        self.output_handle_link_map = {}  # link created locally

        # Link name in attach finds link details in link_list
        self.link_name_to_detail_map = {}

        # count of AMQP performatives for this connection that are not accounted
        # properly in link processing
        self.unaccounted_frame_list = []

        # Session dispositions
        # dict[delivery-id] = ['disp info 0', 'disp info 1', ...]
        self.dispositions_rcvd = {} # inbound dispositions
        self.dispositions_sent = {} # outbound dispositions
        ## summary is appended to transfer display lines
        #self.disposition_summary_l2r = {} # client to broker
        #self.disposition_summary_r2l = {} # broker to client

    def FrameCount(self):
        count = 0
        for link in self.link_list:
            count += len(link.frame_list)
        count += len(self.unaccounted_frame_list)
        return count

    def FindLinkByName(self, attach_name):
        nl = None
        if attach_name in self.link_name_to_detail_map:
            nl = self.link_name_to_detail_map[attach_name]
            if nl.input_handle == -1 and nl.output_handle == -1:
                nl = None
        return nl

    def FindLinkByHandle(self, handle, find_remote):
        '''
        Find the current link by handle number
        qualify lookup based on packet direction
        :param link: the performative channel
        :param dst_is_broker: packet direction
        :return: the session or None
        '''
        if find_remote:
            return self.input_handle_link_map[handle] if handle in self.input_handle_link_map else None
        else:
            return self.output_handle_link_map[handle] if handle in self.output_handle_link_map else None

    def GetId(self):
        return self.conn_detail.GetId() + "_" + str(self.conn_epoch)

    def GetSeqNo(self):
        self.seq_no += 1
        return self.seq_no

    def DetachOutputHandle(self, handle):
        # take existing link out of session handle map
        if handle in self.output_handle_link_map:
            nl = self.output_handle_link_map[handle]
            del self.output_handle_link_map[handle]
            nl.output_handle = -1

    def DetachInputHandle(self, handle):
        # take existing link out of session remote handle map
        if handle in self.input_handle_link_map:
            nl = self.input_handle_link_map[handle]
            del self.input_handle_link_map[handle]
            nl.input_handle = -1

    def DetachHandle(self, handle, is_remote):
        if is_remote:
            self.DetachInputHandle(handle)
        else:
            self.DetachOutputHandle(handle)

    def GetLinkEventCount(self):
        c = 0
        for link in self.link_list:
            c += link.GetLinkEventCount()
        return c

class LinkDetail():
    '''
    Holds facts about a link endpoint
    This structure binds input and output links with same name
    '''
    def __init__(self, session_detail, session_seq, link_name, start_time):
        # parent session
        self.session_detail = session_detail

        # some seq number
        self.session_seq = session_seq

        # link name
        self.name = link_name
        self.display_name = link_name # show short name; hover to see long name

        # Timing
        self.time_start = start_time
        self.time_end = start_time

        self.amqp_errors = 0

        # paired handles
        self.output_handle = -1
        self.input_handle = -1

        # link originator
        self.direction = ""
        self.is_receiver = True
        self.first_address = ''

        # set by sender
        self.snd_settle_mode = ''
        self.sender_target_address = "none"
        self.sender_class = ''

        # set by receiver
        self.rcv_settle_mode = ''
        self.receiver_source_address = "none"
        self.receiver_class = ''

        self.frame_list = []

    def GetId(self):
        return self.session_detail.GetId() + "_" + str(self.session_seq)

    def FrameCount(self):
        return len(self.frame_list)



class AllDetails():
#
#
    def lozenge(self):
        '''
        :return: HTML document lozenge character
        '''
        return "&#9674;"


    def nbsp(self):
        '''
        :return: HTML Non-breaking space
        '''
        return "&#160;"

    def format_errors(self, n_errors):
        return ("<span style=\"background-color:yellow\">%d</span>" % n_errors) if n_errors > 0 else ""

    def classify_connection(self, id):
        '''
        Return probable connection class based on the kinds of links the connection uses.
        TODO: This assumes that the connection has one session and one
        :param id:
        :return:
        '''
        return "oops"

    def links_in_connection(self, id):
        conn_details = self.gbls.conn_details_map[id]
        n_links = 0
        for sess in conn_details.session_list:
            n_links += len(sess.link_list)
        return n_links

    def __init__(self, _tree, _globals):
        self.tree = _tree
        self.gbls = _globals

        for id in self.gbls.all_conn_names:
            self.gbls.conn_details_map[id] = ConnectionDetail(id)
            conn_details = self.gbls.conn_details_map[id]
            conn_frames = self.gbls.conn_to_frame_map[id]
            for plf in conn_frames:
                pname = plf.data.name
                if plf.data.amqp_error:
                    conn_details.amqp_errors += 1
                if pname in ['', 'open', 'close']:
                    conn_details.unaccounted_frame_list.append(plf)
                    continue
                # session required
                channel = plf.data.channel
                sess_details = conn_details.FindSession(channel)
                if sess_details == None:
                    sess_details = SessionDetail(conn_details, conn_details.GetSeqNo(), plf.datetime)
                    conn_details.session_list.append(sess_details)
                    conn_details.EndChannel(channel)
                    conn_details.chan_map[channel] = sess_details
                    sess_details.direction = plf.data.direction
                    sess_details.channel = channel
                if plf.data.amqp_error:
                    sess_details.amqp_errors += 1

                if pname in ['begin', 'end', 'disposition']:
                    sess_details.unaccounted_frame_list.append(plf)

                elif pname in ['attach']:
                    handle = plf.data.handle # proton local handle
                    link_name = plf.data.link_short_name
                    nl = sess_details.FindLinkByName(link_name)
                    if nl is None:
                        # Creating a new link from scratch resulting in a half attached link pair
                        nl = LinkDetail(sess_details, sess_details.GetSeqNo(), link_name, plf.datetime)
                        sess_details.link_list.append(nl)
                        sess_details.link_name_to_detail_map[link_name] = nl
                        nl.display_name = plf.data.link_short_name_popup
                        nl.direction = plf.data.direction
                        nl.is_receiver = plf.data.role == "receiver"
                        nl.first_address = plf.data.source if nl.is_receiver else plf.data.target
                    if plf.data.amqp_error:
                        nl.amqp_errors += 1

                    if plf.data.direction_is_in():
                        # peer is creating link
                        nl.input_handle = handle
                        sess_details.DetachInputHandle(handle)
                        sess_details.input_handle_link_map[handle] = nl
                    else:
                        # local is creating link
                        nl.output_handle = handle
                        sess_details.DetachOutputHandle(handle)
                        sess_details.output_handle_link_map[handle] = nl
                    if plf.data.is_receiver:
                        nl.rcv_settle_mode = plf.data.rcv_settle_mode
                        nl.receiver_source_address = plf.data.source
                        nl.receiver_class = plf.data.link_class
                    else:
                        nl.snd_settle_mode = plf.data.snd_settle_mode
                        nl.sender_target_address = plf.data.target
                        nl.sender_class = plf.data.link_class
                    nl.frame_list.append(plf)

                elif pname in ['detach']:
                    ns = conn_details.FindSession(channel)
                    if ns is None:
                        conn_details.unaccounted_frame_list.append(plf)
                        continue
                    handle = plf.data.handle
                    nl = ns.FindLinkByHandle(handle, plf.data.direction_is_in())
                    ns.DetachHandle(handle, plf.data.direction_is_in())
                    if nl is None:
                        ns.unaccounted_frame_list.append(plf)
                    else:
                        if plf.data.amqp_error:
                            nl.amqp_errors += 1
                        nl.frame_list.append(plf)

                elif pname in ['transfer', 'flow']:
                    ns = conn_details.FindSession(channel)
                    if ns is None:
                        conn_details.unaccounted_frame_list.append(plf)
                        continue
                    handle = plf.data.handle
                    nl = ns.FindLinkByHandle(handle, plf.data.direction_is_in())
                    if nl is None:
                        ns.unaccounted_frame_list.append(plf)
                    else:
                        if plf.data.amqp_error:
                            nl.amqp_errors += 1
                        nl.frame_list.append(plf)


    def show_html(self):
        for id in self.gbls.all_conn_names:
            conn_detail = self.gbls.conn_details_map[id]
            conn_frames = self.gbls.conn_to_frame_map[id]
            print("<a name=\"cd_%s\"></a>" % id)
            # This lozenge shows/hides the connection's data
            print("<a href=\"javascript:toggle_node('%s_data')\">%s%s</a>" %
                  (id, self.lozenge(), self.nbsp()))
            dir = self.gbls.conn_dirs[id] if id in self.gbls.conn_dirs else ""
            peer = self.gbls.conn_peers[id] if id in self.gbls.conn_peers else ""
            # show the connection title
            print("%s %s %s (nFrames=%d) %s<br>" % \
                 (id, dir, peer, len(conn_frames), self.format_errors(conn_detail.amqp_errors)))
            # data div
            print("<div id=\"%s_data\" style=\"display:none; margin-bottom: 2px; margin-left: 10px\">" % id)

            # unaccounted frames
            print("<a href=\"javascript:toggle_node('%s_data_unacc')\">%s%s</a>" %
                  (id, self.lozenge(), self.nbsp()))
            # show the connection-level frames
            errs = sum(1 for plf in conn_detail.unaccounted_frame_list if plf.data.amqp_error)
            print("Connection-based entries %s<br>" % self.format_errors(errs))
            print("<div id=\"%s_data_unacc\" style=\"display:none; margin-bottom: 2px; margin-left: 10px\">" % id)
            for plf in conn_detail.unaccounted_frame_list:
                print(plf.datetime, plf.data.direction, peer, plf.data.web_show_str, "<br>")
            print("</div>") # end unaccounted frames

            # loop to print session details
            for sess in conn_detail.session_list:
                # show the session toggle and title
                print("<a href=\"javascript:toggle_node('%s_sess_%s')\">%s%s</a>" %
                      (id, sess.conn_epoch, self.lozenge(), self.nbsp()))
                print("Session %s: channel: %s, peer channel: %s; Time: start %s, Counts: frames: %d %s<br>" % \
                (sess.conn_epoch, sess.channel, sess.peer_chan, sess.time_start, \
                 sess.FrameCount(), self.format_errors(sess.amqp_errors)))
                print("<div id=\"%s_sess_%s\" style=\"display:none; margin-bottom: 2px; margin-left: 10px\">" %
                      (id, sess.conn_epoch))
                # show the unaccounted session frames
                errs = sum(1 for plf in sess.unaccounted_frame_list if plf.data.amqp_error)
                print("<a href=\"javascript:toggle_node('%s_sess_%s_unacc')\">%s%s</a>" %
                      (id, sess.conn_epoch, self.lozenge(), self.nbsp()))
                print("Session-based entries %s<br>" % self.format_errors(errs))
                print("<div id=\"%s_sess_%s_unacc\" style=\"display:none; margin-bottom: 2px; margin-left: 10px\">" %
                      (id, sess.conn_epoch))
                for plf in sess.unaccounted_frame_list:
                    print(plf.datetime, plf.data.direction, peer, plf.data.web_show_str, "<br>")
                print("</div>") # end <id>_sess_<conn_epoch>_unacc
                # loops to print session link details
                # first loop prints link table
                print("<table")
                print("<tr><th>Link</th> <th>Dir</th> <th>Name</th>  <th>Role</th>  <th>Address</th>  <th>Class</th>  "
                      "<th>snd-settle-mode</th>  <th>rcv-settle-mode</th>  <th>Start time</th>  <th>Frames</th> "
                      "<th>AMQP errors</tr>")
                for link in sess.link_list:
                    # show the link toggle and title
                    showthis = ("<a href=\"javascript:toggle_node('%s_sess_%s_link_%s')\">link %s</a>" %
                                (id, sess.conn_epoch, link.session_seq, link.session_seq))
                    role = "receiver" if link.is_receiver else "sender"
                    print("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                          "<td>%s</td><td>%d</td><td>%s</td></tr>" % \
                          (showthis, link.direction, link.display_name, role, link.first_address,
                           (link.sender_class + '-' + link.receiver_class), link.snd_settle_mode,
                           link.rcv_settle_mode, link.time_start, link.FrameCount(), self.format_errors(link.amqp_errors)))
                print("</table>")
                # second loop prints the link's frames
                for link in sess.link_list:
                    print("<div id=\"%s_sess_%s_link_%s\" style=\"display:none; margin-top: 2px; margin-bottom: 2px; margin-left: 10px\">" %
                          (id, sess.conn_epoch, link.session_seq))
                    print("<h4>Connection %s Session %s Link %s: %s</h4>" %
                          (id, sess.conn_epoch, link.session_seq, link.display_name))
                    for plf in link.frame_list:
                        commat = "<a href=\"#%s\">@</a>" % plf.fid
                        print(commat, plf.datetime, "l:", plf.lineno, plf.data.direction, peer, plf.data.web_show_str, "<br>")
                    print("</div>") # end link <id>_sess_<conn_epoch>_link_<sess_seq>

                print("</div>") # end session <id>_sess_<conn_epoch>

            print("</div>") # end current connection data


if __name__ == "__main__":

    try:
        pass
    except:
        traceback.print_exc(file=sys.stdout)
        pass

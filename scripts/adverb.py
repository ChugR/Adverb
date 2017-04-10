#!/usr/bin/env python
#
# Version 4.1

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

# Mapping of what's expandable
#
# +--- div f_id "f10"                   level:1 <- connection show toggles this
# | This is the whole frame
# | <>frameid-c  Frame 10 AMQP perf'ive, perf'ive
# |
# | +--- div f_idc "f10c"              level:2  <> frame lozenge toggles this
# | | This is the frame's content
# | |
# | | +--- div frameid-c-1 "f10c1"         level:3 <- always on
# | | | This is the first performative, or amqp 'proto' from the frame
# | | | <>frameid-c-1-d Performative n-stuff
# | | |
# | | | +--- div frameid-c-1-d "f10c1d"    level:4 <>
# | | | | All the details of the fields in this proto
# | | | | ...
# | | | +---
# | | +---
# | | +--- div frameid-c-2 "f10c2"
# | | | This is the next performative, or amqp 'proto' from the frame
# | | | <>frameid-c-2-details Performative n-stuff
# | | |
# | | | +--- div frameid-c-2-details "f10c2d"
# | | | | All the details of the fields in this proto
# | | | | ...
# | | | +---
# | | +---
# | +---
# +---
#
# For instance:
#
# <h3>AMQP frames</h3>
# <div width="100%" style="display:block  margin-bottom: 2px" id="f51">              Level 1
# <a href="javascript:toggle_node('f51c')">&#9674;&#160;</a>
# <font color="black">
# Frame 51
# &#160;127.0.0.1:56397&#160;&#160;->&#160;127.0.0.1:27201
# </font>&#160;2.060455&#160;<strong>init</strong> ProtocoId: (1,1) ProtocolVersion: (0,10)
# <div width="100%" id="f51c" style="display:none">                                  Level 2
# <div width="100%" style="background-color:#e5e5e5; margin-bottom: 2px" id="f51c0">0 Level 3
# &#160;&#160;&#160;<a href="javascript:toggle_node('f51c0d')">&#9674;&#160;</a>
# <strong>init</strong> ProtocoId: (1,1) ProtocolVersion: (0,10)
# <div width="100%" id="f51c0d" style="display:none">                                Level 4
# &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;Protocol: AMQP<br>
# &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;Protocol ID Major: 1<br>
# &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;Protocol ID Minor: 1<br>
# &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;Version Major: 0<br>
# &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;Version Minor: 10<br>
# </div>
# </div>
# </div>
# </div>

import sys
import xml.etree.ElementTree as ET
import time
import os
import traceback
#import pdb

def amqp_port_str():
    '''
    :return: string value of AMQP default port
    '''
    return "5672"

def amqp_port_int():
    '''
    :return: integer value of AMQP default port
    '''
    return int(amqp_port_str())

#
# Various web symbols and canned strings
#
def nbsp():
    '''
    :return: HTML Non-breaking space
    '''
    return "&#160;"

def shaded_background_begin():
    '''
    :return: HTML leading for shaded span
    '''
    return "<span style=\"background-color:#e0e0e0\">"

def shaded_background_end():
    '''
    :return: HTML trailing for shaded span
    '''
    return "</span>"

def l_arrow():
    '''
    :return: Text left arrow (HTML arrow is ugly)
    '''
    return "<-"

def r_arrow():
    '''
    :return: Text right arror
    '''
    return "->"

def l_arrow_spaced():
    '''
    :return: Spaced text left arrow
    '''
    return nbsp() + l_arrow() + nbsp()

def r_arrow_spaced():
    '''
    :return: Spaced text right arrow
    '''
    return nbsp() + r_arrow() + nbsp()

def l_arrow_str():
    '''
    :return: Spaced left arrow with a space for visual direction clue
    '''
    return l_arrow_spaced() + nbsp()

def r_arrow_str():
    '''
    :return: Spaced right arrow with a space for visual direction clue
    '''
    return nbsp() + r_arrow_spaced()

def lozenge():
    '''
    :return: HTML document lozenge character
    '''
    return "&#9674;"

def double_lozenge():
    '''
    :return: two HTML document lozenge characters
    '''
    return lozenge() + lozenge()

def leading(level):
    '''
    Calculate some leading space based on indent level.
    There is no magic about these indents. They just have to look nice.
    Only indent so far.
    @type level: int
    :param level: desired indent
    :return: a string of Non-breaking spaces
    '''
    sizes = [3, 8, 13, 18, 23, 27, 31, 35, 39]
    if level < len(sizes):
        return nbsp() * sizes[level]
    return nbsp() * 39

#
# font color
color_list = ["black", "red", "blue", "green", "purple", "darkblue", "blueviolet", "darkred", "darkgreen"]
def color_of(index):
    '''
    Return an HTML color name to differentiate various display text elements.
    If the index is bigger than the table then wrap around and use colors again.
    @type index: int
    :param index: some qualifier about the item being displayed
    :return: a string naming the HTML color
    '''
    i = int(index)
    return color_list[i % len(color_list)]

#
# TODO: make bg_color a class
# bg color
bg_color_list = ["#ffffff", "#e0e0e0", "#ffccff", "#99FFFF", "#ffffcc"]
def bg_color_of(index):
    '''
    Return an HTML color name to differentiate various display background elements.
    If the index is bigger than the table then wrap around and use colors again.
    @type index: int
    :param index: some qualifier about the item being displayed
    :return: a string naming the HTML color
    '''
    i = int(index)
    return bg_color_list[i % len(bg_color_list)]
#
# colorize function for [channel,handle]
pattern_bg_color_list = []
pattern_bg_color_map = {}
def colorize_bg(pattern):
    '''
    When displaying a [channel,handle] string colorize the background.
    Memorize and reuse color patterns.
    @type pattern: str`
    :param pattern: the string being colorized
    :return: HTML text string with colorized background span
    '''
    if pattern not in pattern_bg_color_list:
        pattern_bg_color_list.append(pattern)
        pattern_bg_color_map[pattern] = bg_color_of(pattern_bg_color_list.index(pattern))
    return "<span style=\"background-color:%s\">%s</span>" % (pattern_bg_color_map[pattern], pattern)

#
# Globals
#
class GlobalVars():
    def __init__(self):
        self.highlighted_errors = 0
        self.tcp_expert_notices = 0
        self.dispositions_accepted = 0
        self.dispositions_rejected = 0
        self.dispositions_released = 0
        self.dispositions_modified = 0
        self.dispositions_no_delivery_state = 0
        self.broker_ports_list = []
        self.malformed_amqp_packets = []

#
# Detect and return colorized tcp expert warning
def detect_tcp_expert_warning(packet):
    tcp_message = ""
    try:
        tcp_proto = packet.find("./proto[@name='tcp']")
        tcp_analysis = tcp_proto.find("./field[@name='tcp.analysis']")
        tcp_a_flags = tcp_analysis.find("./field[@name='tcp.analysis.flags']")
        ws_expert = tcp_a_flags.find("./field[@name='_ws.expert']")
        expert_text = ws_expert.get("showname")
        tcp_message = "<span style=\"background-color:orange\">%s</span>" % expert_text
    except:
        pass
    return tcp_message

#
# colorize a directive with an error indication
def colorize_performative_error(proto, res, global_vars, count=False):
    '''
    Colorize and count AMQP performatives with errors
    :param proto: XML element tree type proto, name = amqp
    :param res: PerformativeInfo result variable, set only if error
    :return: if error detected then highlight given res.name value
    '''
    args        = proto.find("./field[@name='amqp.method.arguments']")
    error       = args.find("./field[@name='amqp.performative.arguments.error']")
    if not error is None:
        e_size      = error.get("size")
        if int(e_size) > 1:
            res.name = "<span style=\"background-color:yellow\">" + res.name + "</span>"
            if count:
                global_vars.highlighted_errors += 1

#
# colorize a disposition directive that does not have delivery-state.accepted
# TODO: choices are: absent, accepted, rejected, released, modified
def colorize_dispositions_not_accepted(proto, res, global_vars, count=False):
    '''
    Colorize and count AMQP dispositions not 'accepted'
    :param proto: XML element tree type proto, name = amqp
    :param res: PerformativeInfo result variable, set only if error
    :return: if condition detected then highlight given res.name value
    '''
    colorize = False
    args  = proto.find("./field[@name='amqp.method.arguments']")
    state = args.find("./field[@name='amqp.delivery-state.accepted']")
    if not state is None:
        if count:
            global_vars.dispositions_accepted += 1
    else:
        colorize = True
        state = args.find("./field[@name='amqp.delivery-state.rejected']")
        if not state is None:
            if count:
                global_vars.dispositions_rejected += 1
        else:
            state = args.find("./field[@name='amqp.delivery-state.released']")
            if not state is None:
                if count:
                    global_vars.dispositions_released += 1
            else:
                state = args.find("./field[@name='amqp.delivery-state.modified']")
                if count:
                    if not state is None:
                        global_vars.dispositions_modified += 1
                    else:
                        global_vars.dispositions_no_delivery_state += 1
        if colorize:
            res.name = "<span style=\"background-color:gold\">" + res.name + "</span>"


#
# Given a hex ascii string, return printable string w/o control codes
def dehexify_no_control_chars(valuetext):
    '''
    Return a printable string from a blob of hex characters.
    Non printable ascii control chars or chars >= 127 are printed as '.'.
    :param valuetext:
    :return:
    '''
    tmp = valuetext.decode("hex")
    res = ""
    for ch in tmp:
        if ord(ch) < 32 or ord(ch) >= 127:
            ch = '.'
        res += ch
    return res


#
#
class ExitStatus(Exception):
    """Raised if a command wants a non-0 exit status from the script"""
    def __init__(self, status): self.status = status

#
#
class PerformativeInfo():
    '''
    Holds facts about an XML proto tree item from a PDML file
    '''
    def __init__(self):
        self.web_show_str = ""
        self.name = ""
        self.channel = ""          # undecorated number - '0'
        self.handle = ""           # undecorated number - '1'
        self.delivery_id = ""      # "0"
        self.delivery_tag = ""     # "00:00:00:00"
        self.remote = ""           # undecorated number - '2'
        self.channel_handle = ""   # decorated - '[0,0]'
        self.channel_remote = ""   # decorated - '[1,2]'
        self.flow_deliverycnt = "" # undecorated number - '50'
        self.flow_linkcredit = ""  # undecorated number - '100'
        self.flow_cnt_credit = ""  # decorated - '(50,100)'
        self.transfer_id = ""
        self.role = ""
        self.source = ""
        self.target = ""
        self.first = ""            # undecorated number - '10'
        self.last = ""             # undecorated number - '20'
        self.settled = ""          # Disposition or Transfer settled field
        self.snd_settle_mode = ""  # Attach
        self.rcv_settle_mode = ""  # Attach
        self.transfer_data = ""    # dehexified transfer data value

    def __repr__(self):
        return self._representation()

    def _representation(self):
        all_lines = []
        all_lines.append("web_show_str : '%s'" % self.web_show_str)
        all_lines.append("name : '%s'" % self.name)
        all_lines.append("channel : '%s'" % self.channel)
        all_lines.append("handle : '%s'" % self.handle)
        all_lines.append("delivery_id : '%s'" % self.delivery_id)
        all_lines.append("delivery_tag : '%s'" % self.delivery_tag)
        all_lines.append("remote : '%s'" % self.remote)
        all_lines.append("channel_handle : '%s'" % self.channel_handle)
        all_lines.append("channel_remote : '%s'" % self.channel_remote)
        all_lines.append("flow_deliverycnt : '%s'" % self.flow_deliverycnt)
        all_lines.append("flow_linkcredit : '%s'" % self.flow_linkcredit)
        all_lines.append("flow_cnt_credit : '%s'" % self.flow_cnt_credit)
        all_lines.append("transfer_id : '%s'" % self.transfer_id)
        all_lines.append("role : '%s'" % self.role)
        all_lines.append("source : '%s'" % self.source)
        all_lines.append("target : '%s'" % self.target)
        all_lines.append("first : '%s'" % self.first)
        all_lines.append("last : '%s'" % self.last)
        all_lines.append("settled : '%s'" % self.settled)
        all_lines.append("transfer_data : '%s'" % self.transfer_data)
        return ('\n'.join(all_lines))

    def isConsecutiveTransfer(self, candidate):
        #assert self.name == "transfer"
        #assert candidate.name == "transfer"
        if not self.channel == candidate.channel:
            return False
        if not self.handle == candidate.handle:
            return False
        nextTransferId = (int)(self.transfer_id) + 1
        if not nextTransferId == (int)(candidate.transfer_id):
            return False
        return True

    def showTransferRange(self, transfer_last):
        if transfer_last is None:
            return self.web_show_str
        else:
            return ("<strong>%s</strong>  %s (%s..%s)" % 
                (self.name, colorize_bg(self.channel_handle), self.transfer_id, transfer_last.transfer_id))

class ConnectionDetail():
    '''
    Holds facts about sessions over the connections lifetime
    '''
    def __init__(self, id):
        # id in form 'clienthost_port_serverhost_port'
        self.id = id

        # seq_no number differentiates items that otherwise have same identifiers.
        # sessions, for example
        self.seq_no = 0

        # session_list holds SessionDetail records
        # Sessions for a connection are identified by the client-to-broker and
        # broker-to-client channel number pair.
        # There may be many sessions all using the same channel pairs.
        # This list holds all of them.
        self.session_list = []

        # session_list holds all sessions either active or retired
        # this map indexed by the channel refers to the current item in the session_list
        self.client_to_broker_chan_map = {}
        self.broker_to_client_chan_map = {}

        # count of AMQP performatives for this connection that are not accounted
        # properly in session and link processing
        self.unaccounted_frame_proto_list = []

    def FindSession(self, channel, dst_is_broker):
        '''
        Find the current session by channel number
        qualify lookup based on packet direction
        :param channel: the performative channel
        :param dst_is_broker: packet direction
        :return: the session or None
        '''
        result = None
        if dst_is_broker:
            if channel in self.client_to_broker_chan_map:
                result = self.client_to_broker_chan_map[channel]
        else:
            if channel in self.broker_to_client_chan_map:
                result = self.broker_to_client_chan_map[channel]
        return result

    def GetId(self):
        return self.id

    def GetSeqNo(self):
        self.seq_no += 1
        return str(self.seq_no)

    def EndClientChannel(self, channel):
        # take existing session out of connection chan map
        if channel in self.client_to_broker_chan_map:
            del self.client_to_broker_chan_map[channel]

    def EndBrokerChannel(self, channel):
        # take existing session out of connection chan map
        if channel in self.broker_to_client_chan_map:
            del self.broker_to_client_chan_map[channel]

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

        self.client_chan = -1
        self.broker_chan = -1

        self.originated_by_client = True

        # seq_no number differentiates items that otherwise have same identifiers.
        # links for example
        self.seq_no = 0

        self.frame_list = []
        self.frame_proto_list = []

        # link_list holds LinkDetail records
        # Links for a session are identified by the client-to-broker and
        # broker-to-client handle number pair.
        # There may be many links all using the same handle pairs.
        # This list holds all of them.
        self.link_list = []

        # link_list holds all links either active or retired
        # this map indexed by the handle refers to the current item in the link_list
        self.client_to_broker_link_map = {}
        self.broker_to_client_link_map = {}

        # Link name in attach finds link details in link_list
        self.link_name_to_detail_map = {}

        # count of AMQP performatives for this connection that are not accounted
        # properly in link processing
        self.unaccounted_frame_proto_list = []

        # Session dispositions
        # dict[delivery-id] = ['disp info 0', 'disp info 1', ...]
        self.dispositions_l2r = {} # client to broker
        self.dispositions_r2l = {} # broker to client
        # summary is appended to transfer display lines
        self.disposition_summary_l2r = {} # client to broker
        self.disposition_summary_r2l = {} # broker to client

    def FrameCount(self):
        count = 0
        for link in self.link_list:
            count += len(link.frame_list)
        count += len(self.frame_list)
        return count

    def ProtoCount(self):
        count = 0
        for link in self.link_list:
            count += len(link.frame_proto_list)
        count += len(self.frame_proto_list)
        count += len(self.unaccounted_frame_proto_list)
        return count

    def FindLinkByName(self, attach_name):
        nl = None
        if attach_name in self.link_name_to_detail_map:
            nl = self.link_name_to_detail_map[attach_name]
            if nl.client_handle == -1 and nl.broker_handle == -1:
                nl = None
        return nl

    def FindLinkByHandle(self, handle, dst_is_broker):
        '''
        Find the current link by handle number
        qualify lookup based on packet direction
        :param link: the performative channel
        :param dst_is_broker: packet direction
        :return: the session or None
        '''
        result = None
        if dst_is_broker:
            if handle in self.client_to_broker_link_map:
                result = self.client_to_broker_link_map[handle]
        else:
            if handle in self.broker_to_client_link_map:
                result = self.broker_to_client_link_map[handle]
        return result

    def GetId(self):
        return self.conn_detail.GetId() + "_" + str(self.conn_epoch)

    def GetSeqNo(self):
        self.seq_no += 1
        return self.seq_no

    def DetachClientHandle(self, handle):
        # take existing link out of session handle map
        if handle in self.client_to_broker_link_map:
            nl = self.client_to_broker_link_map[handle]
            del self.client_to_broker_link_map[handle]
            nl.client_handle = -1

    def DetachBrokerHandle(self, handle):
        # take existing link out of session handle map
        if handle in self.broker_to_client_link_map:
            nl = self.broker_to_client_link_map[handle]
            del self.broker_to_client_link_map[handle]
            nl.broker_handle = -1

    def DetachHandle(self, handle, dst_is_broker):
        if dst_is_broker:
            self.DetachClientHandle(handle)
        else:
            self.DetachBrokerHandle(handle)

    def GetLinkEventCount(self):
        c = 0
        for link in self.link_list:
            c += link.GetLinkEventCount()
        return c

class LinkDetail():
    '''
    Holds facts about a link endpoint
    '''
    def __init__(self, session_detail, session_seq, link_name, start_time):
        # parent session
        self.session_detail = session_detail

        # some seq number
        self.session_seq = session_seq

        # link name
        self.name = link_name

        # Timing
        self.time_start = start_time
        self.time_end = start_time

        self.client_handle = -1
        self.broker_handle = -1

        self.originated_by_client = True
        self.originator_is_receiver = True

        self.snd_settle_mode = ''
        self.rcv_settle_mode = ''

        self.receiver_source = "none"
        self.sender_target = "none"

        self.frame_list = []
        self.frame_proto_list = []

        # account for credit. History[n] holds credit after processing frame n
        self.link_credit = 0
        self.link_credit_history = []

        self.credit_went_zero_events = 0
        self.credit_went_negative_events = 0

        self.credit_timing_in_progress = False
        self.credit_timer = 0.0 # running with non-zero
        self.time_with_no_credit = 0.0
        self.time_with_credit = 0.0

    def GetId(self):
        return self.session_detail.GetId() + "_" + str(self.session_seq)

    def FrameCount(self):
        return len(self.frame_list)

    def ProtoCount(self):
        return len(self.frame_proto_list)

    def GetLinkEventCount(self):
        return self.credit_went_zero_events + self.credit_went_negative_events
#
#
class ShortNames():
    '''
    Name shortener.
    The short name for display is "name_" + index(longName)
    Embellish the display name with an html popup
    Link and endpoint names, and data are tracked separately
    Names longer than threshold are shortened
    Each class has a prefix used when the table is dumped as HTML
    '''
    def __init__(self, prefixText):
        self.longnames = []
        self.prefix = prefixText
        self.threshold = 25

    def translate(self, lname):
        '''
        Translate a long name into a short name, maybe.
        Memorize all names, translated or not
        :param lname: the name
        :return: If shortened HTML string of shortened name with popup containing long name else
        not-so-long name.
        '''
        idx = 0
        try:
            idx = self.longnames.index(lname)
        except:
            self.longnames.append(lname)
            idx = self.longnames.index(lname)
        # return as-given if short enough
        if len(lname) < self.threshold:
            return lname
        return "<span title=\"" + lname + "\">" + self.prefix + "_" + str(idx) + "</span>"

    def htmlDump(self):
        '''
        Print the name table as an unnumbered list to stdout
        :return: null
        '''
        if len(self.longnames) > 0:
            print "<h3>" + self.prefix + " Name Index</h3>"
            print "<ul>"
            for i in range(0, len(self.longnames)):
                print ("<li> " + self.prefix + "_" + str(i) + " - " + self.longnames[i] + "</li>")
            print "</ul>"

short_link_names = ShortNames("link")
short_endp_names = ShortNames("endpoint")
short_data_names = ShortNames("message_data")

#
#
def process_port_args(ostring, global_vars):
    """Given the string of broker ports, return an expanded list"""
    port_args = ostring.strip().split(" ")
    for port_arg in port_args:
        seq = port_arg.strip().split(":")
        if len(seq) == 2:
            start = int(seq[0])
            count = int(seq[1])
            for x in range (0, count):
                global_vars.broker_ports_list.append(str(start + x))
        else:
            rng = port_arg.strip().split("-")
            if len(rng) == 2:
                current = int(rng[0])
                upper   = int(rng[1])
                while current <= upper:
                    global_vars.broker_ports_list.append(str(current))
                    current += 1
            else:
                if len(port_arg) > 0:
                    global_vars.broker_ports_list.append(port_arg)

#
#
def is_broker_a(a, b, global_vars):
    """Given two integer ports guess if 'a' is the broker/server port"""
    # 5672 is the 'server' address
    if a == amqp_port_int():
        return True
    if b == amqp_port_int():
        return False
    # If only one or the other is in the current lookup then
    # ports given in command line identify other broker/server ports
    a_in_list = str(a) in global_vars.broker_ports_list
    b_in_list = str(b) in global_vars.broker_ports_list
    if a_in_list != b_in_list:
        return a_in_list
    # If both or neither are in the command line list then the lower port wins by guess
    return a < b

#
#
def connection_is_broker_dst(packet, global_vars):
    """Given a packet, sense if broker is packet destination"""
    assert packet is not None, "connection_is_broker_dst receives null packet"
    proto_tcp = packet.find("./proto[@name='tcp']")
    assert proto_tcp is not None, "connection_show_util cannot find tcp proto"
    field_tcp_src = proto_tcp.find("./field[@name='tcp.srcport']")
    field_tcp_dst = proto_tcp.find("./field[@name='tcp.dstport']")
    tcp_src = field_tcp_src.get("show")
    tcp_dst = field_tcp_dst.get("show")
    s_port = int(tcp_src)
    d_port = int(tcp_dst)
    return is_broker_a(d_port, s_port, global_vars)

#
#
def connection_dst_is_broker(packet, global_vars):
    """Given a packet, return true if destination is the broker"""
    assert packet is not None, "connection_show_util receives null packet"
    proto_tcp = packet.find("./proto[@name='tcp']")
    assert proto_tcp is not None, "connection_dst_is_broker cannot find tcp proto"
    field_tcp_src = proto_tcp.find("./field[@name='tcp.srcport']")
    field_tcp_dst = proto_tcp.find("./field[@name='tcp.dstport']")
    tcp_src = field_tcp_src.get("show")
    tcp_dst = field_tcp_dst.get("show")
    s_port = int(tcp_src)
    d_port = int(tcp_dst)
    return is_broker_a(d_port, s_port, global_vars)
    
#
#
def connection_src_string(packet):
    """Given a packet, return the connection source string: src:port, """
    assert packet is not None, "connection_src_string receives null packet"
    proto_tcp = packet.find("./proto[@name='tcp']")
    assert proto_tcp is not None, "connection_src_string cannot find tcp proto"
    field_tcp_src = proto_tcp.find("./field[@name='tcp.srcport']")
    tcp_src = field_tcp_src.get("show")
    s_port = int(tcp_src)
    ip_src = ""

    proto_ip = packet.find("./proto[@name='ip']")
    if proto_ip is not None:
        ip_src = proto_ip.find("./field[@name='ip.src']").get("show")
    else:
        proto_ip = packet.find("./proto[@name='ipv6']")
        if proto_ip is not None:
            ip_src = "[" + proto_ip.find("./field[@name='ipv6.src']").get("show") + "]"
        else:
            assert False, "connection_src_string cannot find ip or ipv6"
    src_addr = "%s:%s" % (ip_src, tcp_src)
    return src_addr


#
#
def connection_dst_string(packet):
    """Given a packet, return the connection source string: dst:port, """
    assert packet is not None, "connection_dst_string receives null packet"
    proto_tcp = packet.find("./proto[@name='tcp']")
    assert proto_tcp is not None, "connection_dst_string cannot find tcp proto"
    field_tcp_dst = proto_tcp.find("./field[@name='tcp.dstport']")
    tcp_dst = field_tcp_dst.get("show")
    d_port = int(tcp_dst)
    ip_dst = ""

    proto_ip = packet.find("./proto[@name='ip']")
    if proto_ip is not None:
        ip_dst = proto_ip.find("./field[@name='ip.dst']").get("show")
    else:
        proto_ip = packet.find("./proto[@name='ipv6']")
        if proto_ip is not None:
            ip_dst = "[" + proto_ip.find("./field[@name='ipv6.dst']").get("show") + "]"
        else:
            assert False, "connection_dst_string cannot find ip or ipv6"
    dst_addr = "%s:%s" % (ip_dst, tcp_dst)
    return dst_addr


#
#
def connection_show_util(packet, sep_broker_r, sep_broker_l, global_vars, bg_start="", bg_end=""):
    """Given a packet, return the connection to be displayed/stored"""
    assert packet is not None, "connection_show_util receives null packet"
    proto_tcp = packet.find("./proto[@name='tcp']")
    assert proto_tcp is not None, "connection_show_util cannot find tcp proto"
    field_tcp_src = proto_tcp.find("./field[@name='tcp.srcport']")
    field_tcp_dst = proto_tcp.find("./field[@name='tcp.dstport']")
    tcp_src = field_tcp_src.get("show")
    tcp_dst = field_tcp_dst.get("show")
    s_port = int(tcp_src)
    d_port = int(tcp_dst)
    ip_src = ""
    ip_dst = ""

    proto_ip = packet.find("./proto[@name='ip']")
    if proto_ip is not None:
        ip_src = proto_ip.find("./field[@name='ip.src']").get("show")
        ip_dst = proto_ip.find("./field[@name='ip.dst']").get("show")
    else:
        proto_ip = packet.find("./proto[@name='ipv6']")
        if proto_ip is not None:
            ip_src = "[" + proto_ip.find("./field[@name='ipv6.src']").get("show") + "]"
            ip_dst = "[" + proto_ip.find("./field[@name='ipv6.dst']").get("show") + "]"
        else:
            assert False, "connection_show_util cannot find ip or ipv6"
    src_addr = "%s:%s" % (ip_src, tcp_src)
    dst_addr = "%s:%s" % (ip_dst, tcp_dst)

    result = ""
    if is_broker_a(d_port, s_port, global_vars):
        result = "%s%s%s%s%s%s" % (bg_start, src_addr, sep_broker_r, bg_end, dst_addr, sep_broker_r)
    else:
        result = "%s%s%s%s%s%s" % (dst_addr, bg_start, sep_broker_l, src_addr, bg_end, sep_broker_l)

    return result


#
#
def connection_name_for_web(packet, global_vars):
    """Given a packet, return the display connection name client-broker for html"""
    return connection_show_util(packet, r_arrow_str(), l_arrow_str(), global_vars, shaded_background_begin(), shaded_background_end())

#
#
def connection_name(packet, global_vars):
    """Given a packet, return the human readable name"""
    return connection_show_util(packet, "-", "-", global_vars)

#
#
def connection_id(packet, global_vars):
    """Given a packet, return the internal connection name (no special chars)"""
    tmp =  connection_show_util(packet, "_", "_", global_vars)
    tmp = tmp.replace('.', '_')
    tmp = tmp.replace(':', '_')
    tmp = tmp.replace('[', '_')
    tmp = tmp.replace(']', '_')
    return tmp

def frame_num_str(packet):
    '''
    Given a packet, return the frame number as a string
    :param packet:
    :return:
    '''
    return (packet
            .find("./proto[@name='frame']")
            .find("./field[@name='frame.number']")
            .get("show"))

def frame_num(packet):
    '''
    Given a packet, return the frame number as an integer
    :param packet:
    :return:
    '''
    return int(frame_num_str(packet))

def frame_id(packet):
    '''
    Given a packet, return the frame identifier string
    :param packet:
    :return:
    '''
    return "f" + frame_num_str(packet)

def frame_time_relative(packet):
    '''
    Given a packet, return the frame relative time as a string
    :param packet:
    :return: the time in uS as a string, or '0.0' if not found
    '''
    result = "0.0"
    proto_frame = packet.find("./proto[@name='frame']")
    if proto_frame is not None:
        ftr = proto_frame.find("./field[@name='frame.time_relative']")
        if ftr is not None:
            result = "%.6f" % float(ftr.get("show"))
    return result

def field_show_value_or_null(field):
    '''
    hassle with displaying a decent null as a string
    If the field is not null then return the 'show' value string
    '''
    if field is None:
        return "null"
    tmp = field.get('value')
    if tmp == '40':
        return "null"
    else:
        return field.get('show')


def get_link_event_display_string(event_count, prefix="LinkEvents: "):
    '''
    Generate the title display string for the given credit events value.
    Highlight positive count, hide zero count
    :param credit:
    :return:
    '''
    result = ""
    if event_count > 0:
        result = "<span style=\"background-color:yellow\">%s%d</span>" % (prefix, event_count)
    return result


def get_performative_name(proto):
    '''
    Given a proto, return the performative name
    :param proto:
    :return: performative name or 'none'
    '''
    perf_field = proto.find("./field[@name='amqp.performative']")
    if perf_field is None:
        # No performative. init frames and amqp0-X stuff
        return 'none'

    perf = perf_field.get("value")
    if perf is None:
        # unusual return path. could assert instead. probably.
        return 'none'

    if perf == '10':
        return 'open'
    elif perf == '11':
        return 'begin'
    elif perf == '12':
        return 'attach'
    elif perf == '13':
        return 'flow'
    elif perf == '14':
        return 'transfer'
    elif perf == '15':
        return 'disposition'
    elif perf == '16':
        return 'detach'
    elif perf == '17':
        return 'end'
    elif perf == '18':
        return 'close'
    return 'none'

def extract_name(three_words):
    '''Return second word of a string'''
    # The pdml has many instances of fields with attributes showname and show,
    #   showname="Role: receiver (65)" show="65"
    #   showname="Method: sasl.mechanisms (64)" show="64" 
    #   showname="Type: SASL (1)" show="1" 
    # For Adverb's display purposes the show attribute is undecoded and 
    # the showname attribute is too verbose and redundant.
    # This function gets the second word of the showname attribute for display.
    words = three_words.split()
    if len(words) >= 2:
        return words[1]
    return three_words

def safe_field_attr_extract(object, fieldname, attrname, default):
    '''
    Given an object and a field name, extract the attribute value.
    If the field does not exist then return the default.
    '''
    res = default
    try:
        field = object.find(fieldname)
        if not field is None:
            res = field.get(attrname)
    except:
        pass
    return res

def amqp_discover_inner_workings(frames, conn_details_map, global_vars):
    '''
    Follow connections, sessions, and links to discover details
    :param frames: the amqp packets
    :param conn_details_map: storage for details
    :return: None
    '''
    for frame in frames:
        cid = connection_id(frame, global_vars)
        conn_details = conn_details_map[cid]
        assert conn_details is not None, "can't find connection details"
        f_id = frame_id(frame)  # f123
        f_idc = f_id + "c"  # f123c - frame's contents
        dst_is_broker = connection_dst_is_broker(frame, global_vars)
        protos = frame.findall('proto')
        proto_index = 0
        for proto in protos:
            if proto.get("name") == "amqp":
                proto_id = f_idc + str(proto_index) + "d"
                proto_index += 1
                pname = get_performative_name(proto)
                if pname == 'none' or pname == 'open' or pname == 'close':
                    # not all protos have a channel and these we don't care about
                    conn_details.unaccounted_frame_proto_list.append((frame, proto))
                    continue

                channel = proto.find("./field[@name='amqp.channel']").get("show")
                assert channel is not None and len(channel) > 0, "amqp proto must have a channel"
                args = proto.find("./field[@name='amqp.method.arguments']")
                frame_time = float(frame_time_relative(frame))
                if pname == 'begin':
                    # session establishment
                    remote = args.find("./field[@name='amqp.performative.arguments.remoteChannel']")
                    remote = field_show_value_or_null(remote)
                    if remote == 'null':
                        # Creating a new session from scratch
                        ns = SessionDetail(conn_details, conn_details.GetSeqNo(), frame_time_relative(frame))
                        conn_details.session_list.append(ns)

                        if dst_is_broker:
                            # client is creating a new session
                            conn_details.EndClientChannel(channel)
                            conn_details.client_to_broker_chan_map[channel] = ns
                            ns.client_chan = channel
                            ns.originated_by_client = True
                        else:
                            # broker is creating a new session
                            conn_details.EndBrokerChannel(channel)
                            conn_details.broker_to_client_chan_map[channel] = ns
                            ns.broker_chan = channel
                            ns.originated_by_client = False
                    else:
                        # Second half of session creation. Completes a pending session.
                        ns = conn_details.FindSession(remote, not dst_is_broker)
                        if not ns is None:
                            if dst_is_broker:
                                # Client is completing session created by broker
                                ns.client_chan = channel
                                conn_details.client_to_broker_chan_map[channel] = ns
                            else:
                                # Broker is completing session created by client
                                ns.broker_chan = channel
                                conn_details.broker_to_client_chan_map[channel] = ns
                        else:
                            # peer's channel does not exist. Create a new session and supply both channels
                            ns = SessionDetail(conn_details, conn_details.GetSeqNo(), frame_time_relative(frame))
                            if dst_is_broker:
                                ns.client_chan = channel
                                ns.broker_chan = remote
                                conn_details.client_to_broker_chan_map[channel] = ns
                                conn_details.broker_to_client_chan_map[remote] = ns
                            else:
                                ns.broker_chan = channel
                                ns.client_chan = remote
                                conn_details.client_to_broker_chan_map[channel] = ns
                                conn_details.client_to_broker_chan_map[remote] = ns

                    if frame not in ns.frame_list:
                        ns.frame_list.append(frame)
                    ns.frame_proto_list.append((frame, proto))
                    ns.time_end = frame_time_relative(frame)

                elif pname == 'end':
                    # session teardown
                    ns = conn_details.FindSession(channel, dst_is_broker)
                    if not ns is None:
                        if dst_is_broker:
                            conn_details.EndClientChannel(channel)
                        else:
                            conn_details.EndBrokerChannel(channel)
                        if frame not in ns.frame_list:
                            ns.frame_list.append(frame)
                        ns.frame_proto_list.append((frame,proto))
                        ns.time_end = frame_time_relative(frame)
                    else:
                        # an End with no session
                        conn_details.unaccounted_frame_proto_list.append((frame, proto))

                elif pname == 'attach':
                    # link establishment
                    # Find the session
                    ns = conn_details.FindSession(channel, dst_is_broker)
                    if ns is None:
                        conn_details.unaccounted_frame_proto_list.append((frame, proto))
                        continue

                    pi = amqp_decode(proto, global_vars)
                    args = proto.find("./field[@name='amqp.method.arguments']")

                    link_name_field = args.find("./field[@name='amqp.performative.arguments.name']")
                    assert link_name_field is not None, "Link name is required"
                    link_name = extract_name(link_name_field.get('showname'))

                    handle_field = args.find("./field[@name='amqp.performative.arguments.handle']")
                    assert handle_field is not None, "Link handle is required"
                    handle = handle_field.get('show')

                    role_field = args.find("./field[@name='amqp.performative.arguments.role']")
                    assert role_field is not None, "Link role is required"
                    role_is_receiver = role_field.get('value') == '41'

                    source = "undefined"
                    target = "undefined"
                    if role_is_receiver:
                        source_field = args.find("./field[@name='amqp.performative.arguments.source']")
                        if source_field is not None: # "Source required for receiver"?
                            address_field = source_field.find("./field[@name='amqp.performative.arguments.address.string']")
                            source = address_field.get('show') if address_field is not None else "none"
                    else:
                        target_field = args.find("./field[@name='amqp.performative.arguments.target']")
                        if target_field is not None: # "Target required for sender"?
                            address_field = target_field.find("./field[@name='amqp.performative.arguments.address.string']")
                            target = address_field.get('show') if address_field is not None else "none"

                    nl = ns.FindLinkByName(link_name)
                    if nl is None:
                        # Creating a new link from scratch resulting in a half attached link
                        nl = LinkDetail(ns, ns.GetSeqNo(), link_name, frame_time_relative(frame))
                        ns.link_list.append(nl)
                        ns.link_name_to_detail_map[link_name] = nl

                        if dst_is_broker:
                            # client is creating a new link
                            ns.DetachClientHandle(handle)
                            ns.client_to_broker_link_map[handle] = nl
                            nl.client_handle = handle
                            nl.originated_by_client = True
                            nl.originator_is_receiver = role_is_receiver
                        else:
                            # broker is creating a new link
                            ns.DetachBrokerHandle(handle)
                            ns.broker_to_client_link_map[handle] = nl
                            nl.broker_handle = handle
                            nl.originated_by_client = False
                            nl.originator_is_receiver = role_is_receiver

                        nl.receiver_source = source
                        nl.sender_target = target
                        # link creator sets settle modes?
                        # sender link creator sets definitive snd mode, begs for rcv mode
                        #   peer link creator does best effort for other half
                        # these are the proposed settle modes
                        nl.rcv_settle_mode = pi.rcv_settle_mode
                        nl.snd_settle_mode = pi.snd_settle_mode

                    else:
                        if dst_is_broker:
                            ns.client_to_broker_link_map[handle] = nl
                            nl.client_handle = handle
                        else:
                            ns.broker_to_client_link_map[handle] = nl
                            nl.broker_handle = handle

                        if role_is_receiver:
                            if nl.snd_settle_mode != pi.snd_settle_mode:
                                nl.snd_settle_mode += ' (modified?)'
                            if nl.rcv_settle_mode == pi.rcv_settle_mode:
                                nl.rcv_settle_mode = pi.rcv_settle_mode
                            else:
                                nl.rcv_settle_mode = pi.rcv_settle_mode + ' (overridden)'
                        else:
                            if nl.rcv_settle_mode != pi.rcv_settle_mode:
                                nl.rcv_settle_mode += ' (modofied)'
                            if nl.snd_settle_mode == pi.snd_settle_mode:
                                nl.snd_settle_mode = pi.snd_settle_mode
                            else:
                                nl.snd_settle_mode = pi.snd_settle_mode + ' (overridden)'

                    if frame not in nl.frame_list:
                        nl.frame_list.append(frame)

                    nl.frame_proto_list.append((frame, proto))
                    nl.time_end = frame_time_relative(frame)
                    nl.link_credit_history.append(nl.link_credit)

                elif pname == 'detach':
                    # Find the sessionframe_id
                    ns = conn_details.FindSession(channel, dst_is_broker)
                    if ns is None:
                        conn_details.unaccounted_frame_proto_list.append((frame, proto))
                        continue

                    handle_field = args.find("./field[@name='amqp.performative.arguments.handle']")
                    assert handle_field is not None, "Link handle is required"
                    handle = handle_field.get('show')

                    nl = ns.FindLinkByHandle(handle, dst_is_broker)
                    if nl is None:
                        ns.unaccounted_frame_proto_list.append((frame, proto))
                        continue

                    ns.DetachHandle(handle, dst_is_broker)

                    if frame not in nl.frame_list:
                        nl.frame_list.append(frame)
                    nl.frame_proto_list.append((frame, proto))
                    nl.time_end = frame_time_relative(frame)
                    nl.link_credit_history.append(nl.link_credit)

                    # shut off link timers on first detach
                    if nl.credit_timer > 0.0:
                        # was running. apply trailing time accumulation
                        if nl.link_credit > 0:
                            nl.time_with_credit += frame_time - nl.credit_timer
                        else:
                            nl.time_with_no_credit += frame_time - nl.credit_timer
                        nl.credit_timer = 0.0

                elif pname == 'flow':
                    ns = conn_details.FindSession(channel, dst_is_broker)
                    if ns is None:
                        conn_details.unaccounted_frame_proto_list.append((frame, proto))
                        continue

                    handle = args.find("./field[@name='amqp.performative.arguments.handle']").get("show")

                    nl = ns.FindLinkByHandle(handle, dst_is_broker)
                    if nl is None:
                        ns.unaccounted_frame_proto_list.append((frame, proto))
                        continue

                    if frame not in nl.frame_list:
                        nl.frame_list.append(frame)
                    nl.frame_proto_list.append((frame, proto))
                    nl.time_end = frame_time_relative(frame)

                    # account for credit
                    # Does this flow carry a normal credit?
                    #   Link created by  Link type  Who sends flow with credit?
                    #   ---------------  ---------  ---------------------------
                    # 1 client           receiver   client
                    # 2 client           sender     server
                    # 3 server           receiver   server
                    # 4 server           sender     client
                    afc = False
                    if dst_is_broker:
                        # client sending this flow
                        if nl.originated_by_client:
                            # client created this link
                            if nl.originator_is_receiver:
                                # client created a receiver
                                afc = True # case 1
                            else:
                                pass # back channel
                        else:
                            # server created this link
                            if nl.originator_is_receiver:
                                pass # back channel
                            else:
                                afc = True # case 4
                    else:
                        # server sending this flow
                        if nl.originated_by_client:
                            # client created this link
                            if nl.originator_is_receiver:
                                # client created a receiver
                                pass # back channel
                            else:
                                afc = True # case 2
                        else:
                            # server created this link
                            if nl.originator_is_receiver:
                                afc = True # case 3
                            else:
                                pass # back channel

                    if afc:
                        credit = args.find("./field[@name='amqp.performative.arguments.linkCredit']").get("show")
                        credit = int(credit)
                        if credit > 0:
                            # positive non-zero credit is granted
                            if not nl.credit_timing_in_progress:
                                # this is the first credit to come along
                                nl.credit_timing_in_progress = True
                                nl.credit_timer = frame_time
                            else:
                                # timer is running
                                if nl.link_credit > 0:
                                    # already had credit and still do
                                    pass
                                else:
                                    # had no credit and now have some
                                    nl.time_with_no_credit += frame_time - nl.credit_timer
                                    nl.credit_timer = frame_time # timer is measuring with-credit state
                        else:
                            # no credit granted. Who would do this?
                            pass

                        nl.link_credit = credit

                    nl.link_credit_history.append(nl.link_credit)



                elif pname == 'transfer':

                    ns = conn_details.FindSession(channel, dst_is_broker)
                    if ns is None:
                        conn_details.unaccounted_frame_proto_list.append((frame, proto))
                        continue

                    handle = args.find("./field[@name='amqp.performative.arguments.handle']").get("show")

                    nl = ns.FindLinkByHandle(handle, dst_is_broker)
                    if nl is None:
                        ns.unaccounted_frame_proto_list.append((frame, proto))
                        continue

                    if frame not in nl.frame_list:
                        nl.frame_list.append(frame)
                    nl.frame_proto_list.append((frame, proto))
                    nl.time_end = frame_time_relative(frame)

                    # account for credit
                    nl.link_credit -= 1
                    nl.link_credit_history.append(nl.link_credit)
                    if nl.link_credit == -1:
                        # in-flight transfers arriving after credit exhaustion
                        nl.credit_went_negative_events += 1
                    if nl.link_credit == 0:
                        # link had credit and now has none
                        nl.credit_went_zero_events += 1
                        nl.time_with_credit += frame_time - nl.credit_timer
                        nl.credit_timer = frame_time   # timer is measuring no-credit state

                elif pname == "disposition":
                    ns = conn_details.FindSession(channel, dst_is_broker)
                    if ns is None:
                        conn_details.unaccounted_frame_proto_list.append((frame, proto))
                        continue
                    # put proto into session frame list despite upcoming accounting
                    if frame not in ns.frame_list:
                        ns.frame_list.append(frame)
                    ns.frame_proto_list.append((frame,proto))

                    # delivery state
                    dstate = "no-delivery-state"
                    state = args.find("./field[@name='amqp.delivery-state.accepted']")
                    if not state is None:
                        dstate = "accepted"
                    else:
                        state = args.find("./field[@name='amqp.delivery-state.rejected']")
                        if not state is None:
                            dstate = "rejected"
                        else:
                            state = args.find("./field[@name='amqp.delivery-state.released']")
                            if not state is None:
                                dstate = "released"
                            else:
                                state = args.find("./field[@name='amqp.delivery-state.modified']")
                                if not state is None:
                                    dstate = "modified"

                    pi = amqp_decode(proto, global_vars)
                    fnum = frame_num(frame)
                    dirarrow = r_arrow_str() if dst_is_broker else l_arrow_str()
                    i_start = int(pi.first)
                    if pi.last == 'null':
                        i_end = i_start
                    else:
                        i_end = int(pi.last)

                    # Choose where this disposition applies
                    # a normal disposition is a 'receiver' sending a disp back to a sender
                    #   this type applies to the opposite direction of the original transfer
                    # a 'receive settle second' disposition is the sender sending a disp
                    #   in the same direction as the initial transfer

                    for i in range(i_start, i_end+1):
                        if dst_is_broker == (pi.role == 'receiver'):
                            if not i in ns.dispositions_l2r:
                                ns.dispositions_l2r[i] = []
                                ns.disposition_summary_l2r[i] = ""
                            info = "disposition id:%d  %.6f Frame: %d %s role: %s, settled: %s, %s" % \
                                   (i, frame_time, fnum, dirarrow, pi.role, pi.settled, dstate)
                            ns.dispositions_l2r[i].append(info)
                            info = "(DISP:%s settled:%s, %s)" % (dirarrow, pi.settled, dstate)
                            ns.disposition_summary_l2r[i] += info
                        else:
                            if not i in ns.dispositions_r2l:
                                ns.dispositions_r2l[i] = []
                                ns.disposition_summary_r2l[i] = ""
                            info = "disposition id:%d  %.6f Frame: %d %s role: %s, settled: %s, %s" % \
                                   (i, frame_time, fnum, dirarrow, pi.role, pi.settled, dstate)
                            ns.dispositions_r2l[i].append(info)
                            info = "(DISP:%s settled:%s, %s)" % (dirarrow, pi.settled, dstate)
                            ns.disposition_summary_r2l[i] += info

                else:
                    # other performatives: using the channel in due course
                    ns = conn_details.FindSession(channel, dst_is_broker)
                    if ns is not None:
                        if frame not in ns.frame_list:
                            ns.frame_list.append(frame)
                        ns.frame_proto_list.append((frame,proto))
                    else:
                        # TODO: Count a stray
                        conn_details.unaccounted_frame_proto_list.append((frame, proto))
                        pass

def amqp_other_decode(proto):
    '''
    Given a proto that isn't a nice, clean performative,
    return a parsed summary PerformativeInfo object
    '''
    res = PerformativeInfo()

    f_aip = proto.find("./field[@name='amqp.init.protocol']")
    if f_aip is not None:
        # init
        res.name = "init"
        f_id    = proto.find("./field[@name='amqp.init.id']")
        if f_id is not None:
            id = f_id.get("show")
            v_mjr = proto.find("./field[@name='amqp.init.version_major']").get("show")
            v_mnr = proto.find("./field[@name='amqp.init.version_minor']").get("show")
            v_rev = proto.find("./field[@name='amqp.init.version_revision']").get("show")
            if id == "2":
                id = "TLS (2):"
            elif id == "3":
                id = "SASL (3):"
            elif id == "0":
                id = "AMQP (0):"
            else:
                id = "UNKNOWN (%s):" % id
            res.web_show_str = "<strong>%s</strong> %s (%s.%s.%s)" % (res.name, id, v_mjr, v_mnr, v_rev)
            return res

        f_id_mjr = proto.find("./field[@name='amqp.init.id_major']")
        if f_id_mjr is not None:
            id_mjr = proto.find("./field[@name='amqp.init.id_major']").get("show")
            id_mnr = proto.find("./field[@name='amqp.init.id_minor']").get("show")
            v_mjr  = proto.find("./field[@name='amqp.init.version_major']").get("show")
            v_mnr  = proto.find("./field[@name='amqp.init.version_minor']").get("show")
            res.web_show_str = ("<strong>%s</strong> ProtocoId: (%s,%s) ProtocolVersion: (%s,%s)" %
                                (res.name, id_mjr, id_mnr, v_mjr, v_mnr))
            return res

        res.web_show_str = "<strong>%s</strong> UNDECODED: %s" % (res.name, f_id.get("show"))
        return res


    for m_type in (["sasl", "connection", "session", "message", "exchange", "queue", 
                    "execution", "dtx", "file", "method", "stream", "tx"]):
        field_name = "./field[@name='amqp.%s.method']" % m_type
        f_method = proto.find(field_name)
        if f_method is not None:
            method = extract_name( f_method.get("showname") )
            res.name = "method"
            res.web_show_str = "<strong>%s</strong> %s" % (res.name, method)
            return res

    f_message_body = proto.find("./field[@name='amqp.message-body']")
    if f_message_body is not None:
        res.name = "message_body"
        res.web_show_str = "<strong>%s</strong>" % res.name
        return res
    
    f_undissected = proto.find("./field[@name='amqp.undissected']")
    if f_undissected is not None:
        res.name = "undissected"
        res.web_show_str = "<strong>%s</strong>" % f_undissected.get("showname")
        return res
    
    res.web_show_str = "<strong>???</strong> Undecoded frame"
    return res

def amqp_decode(proto, global_vars, arg_display_xfer=False, count_anomalies=False):
    assert proto is not None, "amqp_decode receives null proto"

    '''Given an amqp proto, return parsed PerformativeInfo summary'''
    perf_field = proto.find("./field[@name='amqp.performative']")
    if perf_field is None:
        # No performative. Go decode init frames and amqp0-X stuff
        return amqp_other_decode(proto)

    res = PerformativeInfo()
    perf = perf_field.get("value")
    if perf is None:
        res.name = "none"
        res.web_show_str = "ERROR: can't decode performative from: " + str(proto.tag) + str(proto.attrib)
        return res

    if perf == '10':
        # Performative: open [0] always channel 0
        res.name = "open"
        res.channel = "0"
        res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

    elif perf == '11':
        # Performative: begin [channel,remoteChannel] 
        res.channel = proto.find("./field[@name='amqp.channel']").get("show")
        args        = proto.find("./field[@name='amqp.method.arguments']")
        remote      = args.find("./field[@name='amqp.performative.arguments.remoteChannel']")
        res.name           = "begin"
        res.remote         = field_show_value_or_null(remote)
        res.channel_remote = "[%s,%s]" % (res.channel, res.remote)
        res.web_show_str   = "<strong>%s</strong> %s" % (res.name, res.channel_remote)
        
    elif perf == '12':
        # Performative:  attach [channel,handle] role name (source: src, target: tgt) 
        res.channel = proto.find("./field[@name='amqp.channel']").get("show")
        args        = proto.find("./field[@name='amqp.method.arguments']")
        handle      = args.find("./field[@name='amqp.performative.arguments.handle']").get("showname")
        role        = args.find("./field[@name='amqp.performative.arguments.role']").get("showname")
        tmpname     = args.find("./field[@name='amqp.performative.arguments.name']")
        tmpsrc      = args.find("./field[@name='amqp.performative.arguments.source']")
        tmptgt      = args.find("./field[@name='amqp.performative.arguments.target']")
        tmpssm      = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.sndSettleMode']", "showname", "mixed")
        tmprsm      = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.rcvSettleMode']", "showname", "first")

        src         = None
        tgt         = None
        if tmpsrc is not None:
            src       = tmpsrc.find("./field[@name='amqp.performative.arguments.address']")
            if src is None:
                src   = tmpsrc.find("./field[@name='amqp.performative.arguments.address.string']")
        if tmptgt is not None:
            tgt       = tmptgt.find("./field[@name='amqp.performative.arguments.address']")
            if tgt is None:
                tgt   = tmptgt.find("./field[@name='amqp.performative.arguments.address.string']")
        if tmpname is not None:
            name = extract_name(tmpname.get("showname"))
        else:
            name = ""
        res.name           = "attach"
        res.handle         = extract_name(handle)
        res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
        res.role           = extract_name(role)
        res.source         = field_show_value_or_null(src)
        res.target         = field_show_value_or_null(tgt)
        name               = short_link_names.translate(name)
        res.source         = short_endp_names.translate(res.source)
        res.target         = short_endp_names.translate(res.target)
        res.snd_settle_mode= extract_name(tmpssm)
        res.rcv_settle_mode= extract_name(tmprsm)
        if res.snd_settle_mode == 'null':
            res.snd_settle_mode = 'mixed'
        if res.rcv_settle_mode == 'null':
            res.rcv_settle_mode = 'first'
        res.web_show_str   = ("<strong>%s</strong> %s %s %s (source: %s, target: %s)" %
                              (res.name, colorize_bg(res.channel_handle), res.role, name, res.source, res.target))

    elif perf == '13':
        # Performative: flow [channel,handle] 
        res.channel = proto.find("./field[@name='amqp.channel']").get("show")
        args        = proto.find("./field[@name='amqp.method.arguments']")
        arg_handle  = args.find("./field[@name='amqp.performative.arguments.handle']")
        if arg_handle is not None:
            handle     = arg_handle.get("showname")
            res.handle = extract_name(handle)
        arg_del_cnt = args.find("./field[@name='amqp.performative.arguments.deliveryCount']")
        if arg_del_cnt is not None:
            del_cnt    = arg_del_cnt.get("showname")
            res.flow_deliverycnt = extract_name(del_cnt)
        arg_link_credit  = args.find("./field[@name='amqp.performative.arguments.linkCredit']")
        if arg_link_credit is not None:
            link_credit = arg_link_credit.get("showname")
            res.flow_linkcredit = extract_name(link_credit)
        res.name           = "flow"
        res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
        res.flow_cnt_credit = "(%s,%s)" % (res.flow_deliverycnt, res.flow_linkcredit)
        res.web_show_str   = "<strong>%s</strong> %s (%s,%s)" % (res.name, colorize_bg(res.channel_handle), res.flow_deliverycnt, res.flow_linkcredit)

    elif perf == '14':
        # Performative: transfer [channel,handle] (id)
        res.channel     = proto.find("./field[@name='amqp.channel']").get("show")
        args            = proto.find("./field[@name='amqp.method.arguments']")
        handle          = args.find("./field[@name='amqp.performative.arguments.handle']").get("showname")
        res.handle      = extract_name(handle)

        delivery_id     = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.deliveryId']", "showname", "none")
        res.delivery_id = extract_name(delivery_id)
        delivery_tag    = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.deliveryTag']", "showname", "none")
        res.delivery_tag= extract_name(delivery_tag)
        transfer_id     = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.deliveryId']", "showname", "none")
        res.transfer_id = extract_name(transfer_id)
        settled     = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.settled']", "showname", "false")
        res.settled = extract_name(settled)
        res.name        = "transfer"
        res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
        res.web_show_str  = "<strong>%s</strong>  %s (%s)" % (res.name, colorize_bg(res.channel_handle), res.transfer_id)
        if arg_display_xfer:
            res.transfer_data = get_transfer_data(proto)

    elif perf == '15':
        # Performative: disposition [channel] (role first-last)
        res.channel = proto.find("./field[@name='amqp.channel']").get("show")
        args        = proto.find("./field[@name='amqp.method.arguments']")
        role        = args.find("./field[@name='amqp.performative.arguments.role']").get("showname")
        first       = args.find("./field[@name='amqp.performative.arguments.first']").get("showname")
        last        = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.last']", "showname", first)
        settled     = safe_field_attr_extract(args, "./field[@name='amqp.performative.arguments.settled']", "showname", "false")
        res.first   = extract_name(first)
        res.last    = extract_name(last)
        res.settled = extract_name(settled)
        res.name    = "disposition"
        colorize_dispositions_not_accepted(proto, res, global_vars, count_anomalies)
        res.role    = extract_name(role)
        res.web_show_str  = ("<strong>%s</strong>  [%s] (%s %s-%s)" % 
                             (res.name, res.channel, res.role, res.first, res.last))

    elif perf == '16':
        # Performative: detach [channel, handle] 
        res.channel = proto.find("./field[@name='amqp.channel']").get("show")
        args        = proto.find("./field[@name='amqp.method.arguments']")
        handle      = args.find("./field[@name='amqp.performative.arguments.handle']").get("showname")
        res.handle         = extract_name(handle)
        res.name           = "detach"
        colorize_performative_error(proto, res, global_vars, count_anomalies)
        res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
        res.web_show_str   = "<strong>%s</strong> %s" % (res.name, colorize_bg(res.channel_handle))
    
    elif perf == '17':
        # Performative: end [channel] 
        res.channel      = proto.find("./field[@name='amqp.channel']").get("show")
        res.name         = "end"
        colorize_performative_error(proto, res, global_vars, count_anomalies)
        res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

    elif perf == '18':
        # Performative: close [0] always channel 0
        res.channel      = "0"
        res.name         = "close"
        colorize_performative_error(proto, res, global_vars, count_anomalies)
        res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

    else:
        res.web_show_str = "HELP I'M A ROCK - Unknown performative: %s" % perf

    return res

#
#
def show_fields(parent, level):
    '''Print indented fields values and child values'''
    for child in parent:
        childname = child.get("name")
        showname = child.get("showname")
        valuetext = child.get("value")
        # python2
        showascii = ""
        if (childname == "amqp.data" or childname == "amqp.amqp_value" or childname == "amqp.value"):
            try:
                asascii   = dehexify_no_control_chars(valuetext)
                asascii   = short_data_names.translate(asascii)
                showascii = " <span style=\"background-color:white\">\'" + asascii + "\'</span>"
            except:
                pass
        if showname is not None and len(showname) > 0:
            print "%s%s<br>" % (leading(level), showname + showascii)
        else:
            print "%s%s<br>" % (leading(level), showascii)
        show_fields(child, level+1)

#
#
def get_transfer_data(parent):
    '''
    Find transfer proto's amqp.data or amqp.amqp_value field as printable text
    '''
    global short_data_names
    result = ''
    for child in parent:
        childname = child.get("name")
        valuetext = child.get("value")
        if (childname == "amqp.data" or childname == "amqp.amqp_value" or childname == "amqp.value"):
            try:
                result = dehexify_no_control_chars(valuetext)
                result = short_data_names.translate(result)
            except:
                pass
            break
        #result = get_transfer_data(child)
        #if not result == '':
        #    break
    return result

#
#
def show_flow_list(title, flow_list, label):
    '''Print non-empty flow list'''
    if len(flow_list) > 0:
        print "<a href=\"javascript:toggle_node('%s')\">%s%s</a>%d %s<br>" % (label, lozenge(), nbsp(), len(flow_list), title)
        print "<div width=\"100%%\" style=\"display:none\"  margin-bottom:\"2px\" id=\"%s\">" % label
        print "<ul>"
        for flow in flow_list:
            print "<li>%s</li>" % flow
        print "</ul><br>"
        print "</div>"


#
#
def main_except(argv):
    #pdb.set_trace()
    """Given a pdml file name, send the javascript web page to stdout"""
    if len(sys.argv) < 5:
        sys.exit('Usage: %s pdml-file-name trace-file-display-name broker-ports displayXferCorrelation' % sys.argv[0])

    arg_pdml_file    = sys.argv[1]
    arg_display_name = sys.argv[2]
    arg_broker_ports = sys.argv[3]
    arg_display_xfer = sys.argv[4] == 'true'

    global_vars = GlobalVars()

    #for x in range (0, 5):
    #    print "arg %s: %s<br>" % (x, sys.argv[x])

    if not os.path.exists(arg_pdml_file):
        sys.exit('ERROR: pdml file %s was not found!' % arg_pdml_file)

    process_port_args(arg_broker_ports, global_vars)

    #for x in range (0, len(global_broker_ports_list)):
    #    print " port %s = %s<br>" % (x, global_broker_ports_list[x])

    # parse the pdml file
    tree = ET.parse(arg_pdml_file)
    root = tree.getroot()
    packets = root.findall("packet")

    # Discover probable/possible ampq flows not marked as AMQP.
    # The trick here is to look for 'fake-field-wrapper' proto types which
    # identify frames for which wireshark has no decoder. Then if the payload
    # starts with literal 'AMQP' then this frame is a 'PROBABLE' AMQP
    # connection startup. Frames captured after the AMQP handshake are
    # also listed but we are not so sure and call them 'POSSIBLE' frames;
    # even though they could be any other protocol equally as well.
    probable_flows = []
    possible_flows = []
    probable_flows_display = []
    possible_flows_display = []
    for packet in packets:
        try:
            candidate_proto = packet.find("./proto[@name='fake-field-wrapper']")
            if candidate_proto is not None:
                isProbable = False
                flow_id = connection_id(packet, global_vars)
                flow_id_display = connection_show_util(packet, " - ", " - ", global_vars)
                try:
                    data_field = candidate_proto.find("./field[@name='data']")
                    data_value = data_field.get("value")
                    if data_value.startswith('414d5150'):
                        isProbable = True
                except:
                    pass
                if isProbable:
                    if not flow_id in probable_flows:
                        probable_flows.append(flow_id)
                        probable_flows_display.append(flow_id_display)
                else:
                    if not flow_id in probable_flows and not flow_id in possible_flows:
                        possible_flows.append(flow_id)
                        possible_flows_display.append(flow_id_display)
        except:
            pass

    # select only well-formed AMQP packets
    amqp_packets = []
    for packet in packets:
        amqp_frame = packet.find("./proto[@name='amqp']")
        if __name__ == '__main__':
            if amqp_frame is not None:
                # Don't try to decode packets that have malformed AMQP
                mal_frame = packet.find("./proto[@name='_ws.malformed']")
                if mal_frame is None:
                    amqp_packets.append(packet)
                else:
                    # The other protos in this frame are likely to be
                    # profoundly out-of-spec and cause parse errors
                    # throughout this program. Log skip them.
                    global_vars.malformed_amqp_packets.append(packet)


    # calculate a list of connections and a map
    # of {internal name: formal display name}
    connection_id_list = []
    conn_id_to_name_map = {}
    conn_id_to_color_map = {}
    conn_frame_count = {}
    color_index = 0
    for packet in amqp_packets:
        cid = connection_id(packet, global_vars)
        cname = connection_name(packet, global_vars)
        if cid not in connection_id_list:
            connection_id_list.append(cid)
            conn_id_to_name_map[cid] = cname
            conn_id_to_color_map[cid] = color_of(color_index)
            color_index += 1
            conn_frame_count[cid] = 0
        conn_frame_count[cid] += 1

    # create a map of (connection, [list of associated frames])
    conn_to_frame_map = {}
    for conn in connection_id_list:
        conn_to_frame_map[conn] = []

    # create a map of (connection, ConnectionDetail(connection))
    # all connections are known and this map needs no more additions
    conn_details_map = {}
    for conn in connection_id_list:
        details = ConnectionDetail(conn)
        conn_details_map[conn] = details

    # index the frames by connection
    for packet in amqp_packets:
        conn_to_frame_map[ connection_id(packet, global_vars) ].append( frame_id(packet) )

    # create a map of (frame_id, [list of protos])     - level:4
    frame_to_protos_map = {}
    for conn_id, frame_ids in conn_to_frame_map.iteritems():
        for fid in frame_ids:
            frame_to_protos_map[ fid ] = []

    for packet in amqp_packets:
        f_id = frame_id(packet) # f123
        f_idc = f_id + "c"      # f123c - frame's contents
        protos = packet.findall('proto')
        proto_index = 0
        for proto in protos:
            if proto.get("name") == "amqp":
                proto_id = f_idc + str(proto_index) + "d"
                frame_to_protos_map[ f_id ].append( proto_id )
                proto_index += 1

    # Fill in connection details with info about sessions.
    # Manage sessions as they are found.
    amqp_discover_inner_workings(amqp_packets, conn_details_map, global_vars)

    # create a map of transfer performatives. key=transfer data, value=list of frames sending that data
    transfer_data = {}
    transfer_data_list = []

    # start up the web stuff
    print "<html>"
    print "<head>"
    print "<title>%s - Adverb Analysis</title>" % arg_display_name
    print '''<script src="http://ajax.googleapis.com/ajax/libs/dojo/1.4/dojo/dojo.xd.js" type="text/javascript"></script>
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
    # output the frame show/hide functions into the header
    for conn_id, frame_ids in conn_to_frame_map.iteritems():
        print "function show_%s() {" % conn_id
        for fid in frame_ids:
            print "  javascript:show_node(\'%s\');" % fid
        print "}"
        print "function hide_%s() {" % conn_id
        for fid in frame_ids:
            print "  javascript:hide_node(\'%s\');" % fid
        print "}"
        # manipulate checkboxes
        print "function show_if_cb_sel_%s() {" % conn_id
        print "  if (document.getElementById(\"cb_sel_%s\").checked) {" % conn_id
        print "    javascript:show_%s();" % conn_id
        print "  } else {"
        print "    javascript:hide_%s();" % conn_id
        print "  }"
        print "}"
        print "function select_cb_sel_%s() {" % conn_id
        print "  document.getElementById(\"cb_sel_%s\").checked = true;" % conn_id
        print "  javascript:show_%s();" % conn_id
        print "}"
        print "function deselect_cb_sel_%s() {" % conn_id
        print "  document.getElementById(\"cb_sel_%s\").checked = false;" % conn_id
        print "  javascript:hide_%s();" % conn_id
        print "}"
        print "function toggle_cb_sel_%s() {" % conn_id
        print "  if (document.getElementById(\"cb_sel_%s\").checked) {" % conn_id
        print "    document.getElementById(\"cb_sel_%s\").checked = false;" % conn_id
        print "  } else {"
        print "    document.getElementById(\"cb_sel_%s\").checked = true;" % conn_id
        print "  }"
        print "  javascript:show_if_cb_sel_%s();" % conn_id
        print "}"

    # Select/Deselect/Toggle All Connections functions
    print "function select_all() {"
    for conn_id, frames_ids in conn_to_frame_map.iteritems():
        print "  javascript:select_cb_sel_%s();" % conn_id
    print "}"
    print "function deselect_all() {"
    for conn_id, frames_ids in conn_to_frame_map.iteritems():
        print "  javascript:deselect_cb_sel_%s();" % conn_id
    print "}"
    print "function toggle_all() {"
    for conn_id, frames_ids in conn_to_frame_map.iteritems():
        print "  javascript:toggle_cb_sel_%s();" % conn_id
    print "}"

    # Show/Hide all details for each frame
    for fid, proto_ids in frame_to_protos_map.iteritems():
        print "function show_level_4_%s() {" % fid
        for proto_id in proto_ids:
            print "  javascript:show_node(\'%s\');" % proto_id
        print "}"

        print "function hide_level_4_%s() {" % fid
        for proto_id in proto_ids:
            print "  javascript:hide_node(\'%s\');" % proto_id
        print "}"

        print "function toggle_frame_details_%s() {" % fid
        print "  if( node_is_visible(\'%s\') ) {" % (fid + 'c')
        print "    javascript:hide_level_4_%s();" % fid
        print "    javascript:hide_node(\'%s\');" % (fid + 'c')
        print "  } else {"
        print "    javascript:show_level_4_%s();" % fid
        print "    javascript:show_node(\'%s\');" % (fid + 'c')
        print "  }"
        print "}"

    # Reset the entire page
    print "function page_view_collapse() {"
    print "  javascript:cursor_wait();"
    for conn_id, frame_ids in conn_to_frame_map.iteritems():
        for fid in frame_ids:
            # Hide level 4
            print "  javascript:hide_level_4_%s();" % fid
            # Hide level 2
            print "  javascript:hide_node(\'%s\');" % (fid + "c")
    # Show level 1
    print "  javascript:select_all();"
    print "  javascript:cursor_default();"
    print "}"

    # Expose entire page
    print "function page_view_expand() {"
    print "  javascript:cursor_wait();"
    for conn_id, frame_ids in conn_to_frame_map.iteritems():
        for fid in frame_ids:
            # Show level 4
            print "  javascript:show_level_4_%s();" % fid
            # Show level 2
            print "  javascript:show_node(\'%s\');" % (fid + "c")
    # Show level 1
    print "  javascript:select_all();"
    print "  javascript:cursor_default();"
    print "}"

    # Cursor
    print "function cursor_wait() {"
    print "  document.body.style.cursor = 'wait';"
    print "}"
    print "function cursor_default() {"
    print "  document.body.style.cursor = 'default';"
    print "}"

    # output the frame show/hide functions per session
    for conn in connection_id_list:
        conn_detail = conn_details_map[conn]
        for session in conn_detail.session_list:
            sid = session.GetId()
            print "function show_%s() {" % (sid)
            for frame in session.frame_list:
                print "  javascript:show_node(\'%s\');" % frame_id(frame)
            print "}"
            print "function hide_%s() {" % (sid)
            for frame in session.frame_list:
                print "  javascript:hide_node(\'%s\');" % frame_id(frame)
            print "}"
            # manipulate checkboxes
            print "function show_if_cb_sel_%s() {" % (sid)
            print "  if (document.getElementById(\"cb_sel_%s\").checked) {" % (sid)
            print "    javascript:show_%s();" % (sid)
            print "  } else {"
            print "    javascript:hide_%s();" % (sid)
            print "  }"
            print "}"
            print "function select_cb_sel_%s() {" % (sid)
            print "  document.getElementById(\"cb_sel_%s\").checked = true;" % (sid)
            print "  javascript:show_%s();" % (sid)
            print "}"
            print "function deselect_cb_sel_%s() {" % (sid)
            print "  document.getElementById(\"cb_sel_%s\").checked = false;" % (sid)
            print "  javascript:hide_%s();" % (sid)
            print "}"
            print "function toggle_cb_sel_%s() {" % (sid)
            print "  if (document.getElementById(\"cb_sel_%s\").checked) {" % (sid)
            print "    document.getElementById(\"cb_sel_%s\").checked = false;" % (sid)
            print "  } else {"
            print "    document.getElementById(\"cb_sel_%s\").checked = true;" % (sid)
            print "  }"
            print "  javascript:show_if_cb_sel_%s();" % (sid)
            print "}"

            for link in session.link_list:
                sid = link.GetId()
                print "function show_%s() {" % (sid)
                for frame in link.frame_list:
                    print "  javascript:show_node(\'%s\');" % frame_id(frame)
                print "}"
                print "function hide_%s() {" % (sid)
                for frame in link.frame_list:
                    print "  javascript:hide_node(\'%s\');" % frame_id(frame)
                print "}"
                # manipulate checkboxes
                print "function show_if_cb_sel_%s() {" % (sid)
                print "  if (document.getElementById(\"cb_sel_%s\").checked) {" % (sid)
                print "    javascript:show_%s();" % (sid)
                print "  } else {"
                print "    javascript:hide_%s();" % (sid)
                print "  }"
                print "}"
                print "function select_cb_sel_%s() {" % (sid)
                print "  document.getElementById(\"cb_sel_%s\").checked = true;" % (sid)
                print "  javascript:show_%s();" % (sid)
                print "}"
                print "function deselect_cb_sel_%s() {" % (sid)
                print "  document.getElementById(\"cb_sel_%s\").checked = false;" % (sid)
                print "  javascript:hide_%s();" % (sid)
                print "}"
                print "function toggle_cb_sel_%s() {" % (sid)
                print "  if (document.getElementById(\"cb_sel_%s\").checked) {" % (sid)
                print "    document.getElementById(\"cb_sel_%s\").checked = false;" % (sid)
                print "  } else {"
                print "    document.getElementById(\"cb_sel_%s\").checked = true;" % (sid)
                print "  }"
                print "  javascript:show_if_cb_sel_%s();" % (sid)
                print "}"


    # continue with the header
    print '''</script>

</head>
<body>
<style>
    * { font-family: sans-serif; }
</style>
Capture Filename: <b>'''
    print arg_display_name,
    print '''</b><br>
Generated from PDML on <b>'''
    print time.asctime( time.localtime(time.time()) ),
    print "</b><br>"
    print "User ports decoded as AMQP (in addition to 5672): <b>%s</b><br>" % arg_broker_ports

    # probable/possible AMQP connections
    if len(probable_flows_display) > 0 or len(possible_flows_display) > 0:
        print "<h3>Diagnostic: Additional AMQP decode ports</h3>"
        print "NOTE: There may be more AMQP frames in the uploaded trace that are not displayed here.<br>"
        show_flow_list("Probable AMQP connections", probable_flows_display, "probable_flows")
        show_flow_list("Possible AMQP or other connections", possible_flows_display, "possible_flows")
        print "You may want to note which ports appear to be server ports. Then go back to the submission form, "
        print "and add these ports to the list of additional ports to be decoded as AMQP, and upload again.<br>"


    # done generating html head and body introduction

    # do the dirty work of categorizing, indexing, colorizing, 'n stuff
    print "<h3>Page controls</h3>"
    print "<button onclick=\"go_back()\">Back to web form</button>"
    print "<br><button onclick=\"javascript:page_view_collapse()\">Default page view</button>"
    print "<button onclick=\"javascript:page_view_expand()\">Expand-all page view</button>"

    # error/warning statistics
    print "<br>"
    print "<h3>Link to analysis statistics.</h3>"
    print "<a href=\"#analysisStats\">View post-run analysis statistics</a>"

    print "<h3>Show/Hide frames per connection</h3>"
    print "<button onclick=\"javascript:select_all()\">Select All</button>"
    print "<button onclick=\"javascript:deselect_all()\">Deselect All</button>"
    print "<button onclick=\"javascript:toggle_all()\">Toggle All</button>"
    print "<br>"
    for conn in connection_id_list:
        print "<input type=\"checkbox\" id=\"cb_sel_%s\" " % conn
        print "checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\">%s" % (conn, nbsp())
        # This lozenge shows/hides the sessions
        conn_detail = conn_details_map[conn]
        print "<a href=\"javascript:toggle_node('%s_sessions')\">%s%s</a>" % (conn, lozenge(), nbsp())
        print "<font color=\"%s\">" % conn_id_to_color_map[ conn ]
        print "%s</font>%s%s(nFrames=%d) %s<br>" % (conn_id_to_name_map[conn], nbsp(), nbsp(), conn_frame_count[conn], \
                                                    get_link_event_display_string(conn_detail.GetLinkEventCount()))
        # sessions div
        print "<div width=\"100%%\" id=\"%s_sessions\" style=\"display:none\">" % conn

        # This lozenge shows/hides the connection performatives not part of any session
        print "%s<a href=\"javascript:toggle_node('%s_conn_unaccounted')\">%s%s</a>" % (leading(2), conn, lozenge(), nbsp())
        print "Connection-based Performatives<br>"
        print "<div width=\"100%%\" id=\"%s_conn_unaccounted\" style=\"display:none\">" % conn
        idx = 0
        for frame, proto in conn_detail.unaccounted_frame_proto_list:
            info = amqp_decode(proto, global_vars)
            dir_arrow = r_arrow_str() if connection_dst_is_broker(frame, global_vars) else l_arrow_str()
            # This lozenge shows/hides performative details
            print "%s<a href=\"javascript:toggle_node('%s_conn_unacc_%d_details')\">%s%s</a>" % (
                leading(3), conn, idx, lozenge(), nbsp())
            print "Frame: %s %s %s %s<br>" % (frame_num_str(frame), frame_time_relative((frame)),
                                              dir_arrow, info.web_show_str)
            print "<div width=\"100%%\" id=\"%s_conn_unacc_%d_details\" style=\"display:none\">" % (
                conn, idx)
            show_fields(proto, 4)
            print "</div>"
            idx += 1
        print "</div>"

        for session in conn_detail.session_list:
            # This button toggles the frame display for the session
            sid = session.GetId()
            print "%s<input type=\"checkbox\" id=\"cb_sel_%s\" " % (nbsp() * 4, sid)
            print "checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\">%s" % (sid, nbsp())
            # This lozenge shows/hides session details
            print "<a href=\"javascript:toggle_node('%s_ssn_details')\">%s%s</a>" % (sid, lozenge(), nbsp())
            print "Session %s: Channels: client: %s, server: %s; Time: start %s, end %s; Counts: frames: %d, performatives: %d %s<br>" % \
                  (session.conn_epoch, session.client_chan, session.broker_chan, session.time_start, session.time_end, \
                   session.FrameCount(), session.ProtoCount(), get_link_event_display_string(session.GetLinkEventCount()))
            print "<div width=\"100%%\" id=\"%s_ssn_details\" style=\"display:none\">" % (sid)

            # This lozenge shows/hides the session performatives not part of any link
            print "%s%s<a href=\"javascript:toggle_node('%s_sess_unaccounted')\">%s%s</a>" % (
                leading(2), nbsp() * 2, sid, lozenge(), nbsp())
            print "Session-based Performatives<br>"
            print "<div width=\"100%%\" id=\"%s_sess_unaccounted\" style=\"display:none\">" % sid
            idx = 0
            for frame,proto in session.frame_proto_list:
                info = amqp_decode(proto, global_vars)
                dir_arrow = r_arrow_str() if connection_dst_is_broker(frame, global_vars) else l_arrow_str()
                # This lozenge shows/hides performative details
                print "%s<a href=\"javascript:toggle_node('%s_session_perf_%d_details')\">%s%s</a>" % (
                    leading(3), sid, idx, lozenge(), nbsp())
                print "Frame: %s %s %s %s<br>" % (frame_num_str(frame), frame_time_relative((frame)),
                                                    dir_arrow, info.web_show_str)
                print "<div width=\"100%%\" id=\"%s_session_perf_%d_details\" style=\"display:none\">" % (
                    sid, idx)
                show_fields(proto, 4)
                print "</div>"
                idx += 1
            print "</div>"
            idx = 0
            for link in session.link_list:
                # This button toggles the frame display for the link
                lid = link.GetId()
                info = "client " if link.originated_by_client else "server "
                info += "%s %s" % ("receiver ", link.receiver_source) if link.originator_is_receiver else \
                    "%s %s" % ("sender ", link.sender_target)
                print "%s<input type=\"checkbox\" id=\"cb_sel_%s\" " % (nbsp() * 8, lid)
                print "checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\">%s" % (lid, nbsp())
                # This lozenge shows/hides link details
                print "<a href=\"javascript:toggle_node('%s_link_details')\">%s%s</a>" % (lid, lozenge(), nbsp())
                lec = link.GetLinkEventCount()
                print "Link %s: %s %s; Time: start %s, end %s; SettleModes snd: %s, rcv: %s; Counts: frames: %d, performatives: %d %s<br>" % \
                      (link.session_seq, short_link_names.translate(link.name), info, link.time_start, link.time_end, \
                       link.snd_settle_mode, link.rcv_settle_mode, \
                       link.FrameCount(), link.ProtoCount(), get_link_event_display_string(lec))
                print "<div width=\"100%%\" id=\"%s_link_details\" style=\"display:none\">" % (lid)
                if lec > 0:
                    print "%s%.6f S - Elapsed time with no link credit<br>" % \
                          (leading(5), link.time_with_no_credit)
                    print "%s%.6f S - Elapsed time with link credit<br>" % \
                          (leading(5), link.time_with_credit)
                    print "%s%d - Link credit went to zero<br>" % \
                          (leading(5), link.credit_went_zero_events)
                    print "%s%d - Link credit went below zero<br>" % \
                          (leading(5), link.credit_went_negative_events)
                idx = 0
                show_credits = False
                for frame, proto in link.frame_proto_list:
                    info = amqp_decode(proto, global_vars)
                    dir_arrow = r_arrow_str() if connection_dst_is_broker(frame, global_vars) else l_arrow_str()
                    # This lozenge shows/hides performative details
                    print "%s<a href=\"javascript:toggle_node('%s_link_perf_%d_details')\">%s%s</a>" % (
                        leading(4), lid, idx, lozenge(), nbsp())
                    # sort out credits
                    if link.link_credit_history[idx] > 0:
                        show_credits = True
                    if info.name == "detach":
                        show_credits = False
                    if show_credits:
                        credit_text = "<i>credit%s%d</i>" % (r_arrow_spaced(), link.link_credit_history[idx])
                        if link.link_credit_history[idx] == 0:
                            credit_text = "<span style=\"background-color:yellow\">%s</span>" % credit_text
                        elif link.link_credit_history[idx] < 0:
                            credit_text = "<span style=\"background-color:orange\">%s</span>" % credit_text
                    else:
                        credit_text = ""
                    # sort out transfer/disposition settlement
                    dst_is_broker = connection_dst_is_broker(frame, global_vars)
                    show_disposition_info = (info.name == "transfer" and info.delivery_id != 'none')
                    disp_hint = ""
                    if show_disposition_info:
                        did = int(info.delivery_id)
                        # if the transfer is TO the broker then the dispositions we want are FROM the broker
                        disp_hint = "{(txSettled: %s)}" % (info.settled)
                        if dst_is_broker:
                            if did in session.disposition_summary_r2l:
                                disp_hint = "{(txSettled: %s) %s}" % (info.settled, session.disposition_summary_r2l[did])
                        else:
                            if did in session.disposition_summary_l2r:
                                disp_hint = "{(txSettled: %s) %s}" % (info.settled, session.disposition_summary_l2r[did])

                    print "Frame: %s %s %s %s %s %s<br>" % (frame_num_str(frame), frame_time_relative((frame)),
                                                      dir_arrow, info.web_show_str, credit_text, disp_hint)
                    print "<div width=\"100%%\" id=\"%s_link_perf_%d_details\" style=\"display:none\">" % (
                        lid, idx)
                    if show_disposition_info:
                        if dst_is_broker:
                            if did in session.dispositions_r2l:
                                for disp in session.dispositions_r2l[did]:
                                    print "%s%s<br>" % (leading(5), disp)
                        else:
                            if did in session.dispositions_l2r:
                                for disp in session.dispositions_l2r[did]:
                                    print "%s%s<br>" % (leading(5), disp)
                    show_fields(proto, 5)
                    print "</div>"
                    idx += 1
                print "</div>"
            # End of session details
            print "</div>"
        print "</div>"

    # print the frames
    print "<br>"
    print "<h3>AMQP frames</h3>"
    for packet in amqp_packets:
        f_id = frame_id(packet) # f123
        f_idc = f_id + "c"      # f123c - frame's contents

        # Flag tcp expert notices
        tcp_message = detect_tcp_expert_warning(packet)
        if tcp_message != "":
            global_vars.tcp_expert_notices += 1

        # compute performative list for Frame line
        # collapse consecutive transfers into a transfer range for display
        transfer_first = None
        transfer_last = None
        all_transfers = True
        performatives = ""
        sep = ""
        protos = packet.findall('proto')
        for proto in protos:
            if proto.get("name") == "amqp":
                decoded_proto = amqp_decode(proto, global_vars, False, count_anomalies=True)
                if decoded_proto.name == "transfer":
                    if transfer_first is None:
                        transfer_first = decoded_proto
                    else:
                        if transfer_last is None:
                            if transfer_first.isConsecutiveTransfer(decoded_proto):
                                transfer_last = decoded_proto
                            else:
                                # had a transfer but this isn't consecutive
                                performatives += sep + transfer_first.web_show_str
                                transfer_first = decoded_proto
                        else:
                            # working with an existing last
                            if transfer_last.isConsecutiveTransfer(decoded_proto):
                                # add current to ongoing range
                                transfer_last = decoded_proto
                            else:
                                # had a transfer range before but this one is not consecutive
                                # ALERT: this is a protocol anomaly. TODO: flag it somehow
                                performatives += sep + transfer_first.showTransferRange(transfer_last)
                                transfer_first = decoded_proto
                                transfer_last = None
                else:
                    # now not a transfer. Dump accumulated xfers if any
                    if not transfer_first is None:
                        if not all_transfers:
                            performatives += sep
                        performatives += transfer_first.showTransferRange(transfer_last)
                        transfer_last = None
                        transfer_first = None
                        sep = "," + nbsp()
                    performatives += sep + decoded_proto.web_show_str
                    all_transfers = False
                sep = "," + nbsp()
        if not transfer_first is None:
            if not all_transfers:
                performatives += sep
            performatives += transfer_first.showTransferRange(transfer_last)
        # TODO: track transfer id for this (channel,handle) and flag retransmits or gaps.

        print "<div width=\"100%%\" style=\"display:block  margin-bottom: 2px\" id=\"%s\">" % f_id # start level:1
        # this lozenge shows/hides frame contents
        print "<a href=\"javascript:toggle_node('%s')\">%s%s</a>" % (f_idc, lozenge(), nbsp())
        # dobule lozenge shows all frame details
        print "<a href=\"javascript:toggle_frame_details_%s()\">%s%s</a>%s%s" % (f_id, double_lozenge(), nbsp(), frame_time_relative(packet), nbsp())
        print "<font color=\"%s\">" % conn_id_to_color_map[ connection_id(packet, global_vars) ]
        print "Frame %s" % frame_num(packet)
        print "%s%s" % (nbsp(), connection_name_for_web(packet, global_vars))
        print "</font>%s%s %s" % (nbsp(), performatives, tcp_message)

        # Create a div that holds the frame's contents
        print "<div width=\"100%%\" id=\"%s\" style=\"display:none\">" % f_idc # begin level:2
        # Loop through the packet's proto blocks and display a title for each
        proto_index = 0
        for proto in protos:
            if proto.get("name") == "amqp":
                decoded_proto = amqp_decode(proto, global_vars, arg_display_xfer)
                proto_id = f_idc + str(proto_index) + "d"
                print ("<div width=\"100%%\" style=\"background-color:#e5e5e5; margin-bottom: 2px\" id=\"%s\">" 
                       % (f_idc + str(proto_index)))                             # begin level:3
                print ("%s<a href=\"javascript:toggle_node('%s')\">%s%s</a>" 
                       % (leading(0), proto_id, lozenge(), nbsp()))
                print "%s" % decoded_proto.web_show_str
                # Create a div that holds this proto's contents
                print ("<div width=\"100%%\" id=\"%s\" style=\"display:none\">" # begin level:4
                       % proto_id)
                show_fields(proto, 1)
                proto_index += 1
                print "</div>"                                                 # end level:4
                print "</div>"                                                 # end level:3
                # Emit cross indexed transfer data info
                if arg_display_xfer and decoded_proto.name == "transfer":
                    info = "%s, %s, %s, %s, %s, %s, %s, %s, \"%s\"" % (frame_num(packet), frame_time_relative(packet), connection_src_string(packet),
                                                                   connection_dst_string(packet), decoded_proto.channel, decoded_proto.handle,
                                                                   decoded_proto.delivery_id, decoded_proto.delivery_tag, decoded_proto.transfer_data)
                    if not decoded_proto.transfer_data in transfer_data:
                        transfer_data[decoded_proto.transfer_data] = []
                        transfer_data_list.append(decoded_proto.transfer_data)
                    transfer_data[decoded_proto.transfer_data].append(info)

        print "</div>"                                                         # end level:2
        print "</div>"                                                         # end level:1

    # totalize link events
    le = 0
    for conn in connection_id_list:
        conn_detail = conn_details_map[conn]
        le += conn_detail.GetLinkEventCount()

    # post run analysis counts.
    print "<br><h3><a name=\"analysisStats\">Post-run Analysis Statistics</a></h3>"
    print "<TABLE border=\"1\" summary=\"This table shows counts of interesting or anomalous things observed during processing.\">"
    print "<CAPTION><EM>Analysis Statistics</EM></CAPTION>"
    print "<TR>"
    print "<TH>Count"
    print "<TH>Description"
    print "</TR>"
    print "<TR><TD><span style=\"background-color:orange\">%d</span><TD>Wireshark TCP Expert Info" % (global_vars.tcp_expert_notices)
    print "<TR><TD><span style=\"background-color:yellow\">%d</span><TD>AMQP In-Band Detach/End/Close Errors" % (global_vars.highlighted_errors)
    print "<TR><TD>%d<TD>AMQP Disposition state Accepted" % (global_vars.dispositions_accepted)
    print "<TR><TD><span style=\"background-color:gold\">%d</span><TD>AMQP Disposition state Rejected" % (global_vars.dispositions_rejected)
    print "<TR><TD><span style=\"background-color:gold\">%d</span><TD>AMQP Disposition state Released" % (global_vars.dispositions_released)
    print "<TR><TD><span style=\"background-color:gold\">%d</span><TD>AMQP Disposition state Modified" % (global_vars.dispositions_modified)
    print "<TR><TD><span style=\"background-color:gold\">%d</span><TD>AMQP Disposition state Not Specified" % (global_vars.dispositions_no_delivery_state)
    print "<TR><TD><span style=\"background-color:gold\">%d</span><TD>Link Events" % (le)
    print "<TR><TD><span style=\"background-color:gold\">%d</span><TD>Malformed AMQP frames Not Shown" % (len(global_vars.malformed_amqp_packets))
    print "</TABLE>"

    # shortened names, if any
    short_link_names.htmlDump()
    short_endp_names.htmlDump()
    short_data_names.htmlDump()

    # legend
    print '''
<div width=\"100%%\" style=\"display:block  margin-bottom: 2px\" id=\"legend\">
<h3>Decode Legend</h3>
The decode web page default view shows information about the capture, a view of all the connections with the number frames associated with that connection, and a summary of every AMQP frame. The summary includes:
<ul>
<li>The capture file frame number. Note that not all frames from the capture file are AMQP frames and that there are normally gaps in the frame number sequence.</li>
<li>The TCP/IP source and destination addresses of the hosts with an arrow indicating the direction of the frame. The frames from the broker to the client have the direction arrow highlighted with a light gray background.<br>
The AMQP 'server' port (either 5672, or one of the decode-as ports) is always on the right</li>
<li>The frame timestamp in seconds relative to the beginning of the capture</li>
<li>The AMQP 1.0 performative(s) and important details:
<ul>
<li><strong>open</strong> [0] always channel 0</li>
<li><strong>close</strong> [0] always channel 0</li>
<li><strong>begin</strong> [channel,remoteChannel]</li>
<li><strong>end</strong> [channel]</li>
<li><strong>attach</strong> [channel,handle] role name (source: src, target: tgt)</li>
<li><strong>detach</strong> [channel, handle]</li>
<li><strong>flow</strong> [channel,handle](deliveryCount, linkCredit)</li>
<li><strong>transfer</strong> [channel,handle] (id)|(id..id)</li>
<li><strong>disposition</strong> [channel] (role first-last) </li>
</ul>
<li>AMQP version-independent <strong>init</strong> details
<li>AMQP 0.x <strong>method(s)</strong>
<li>Names of links, sources, and targets longer than 25 characters are shortened to the form "name_XX". Generated temporary names may exceed 150 characters and contribute little to understanding the protocol. You can hover over the shortened names in the displayed frames to see the full text in a popup and you may refer to a table of shortened names that appears after the AMQP Frames display to see all the translated names.
</ul>
<h3>Protocol frame expansion</h3>
<ul>
<li>The single lozenge expands to show each performative on a separate line</li>
<li>The double lozenge expands each performative in the frame to expose the full details of the decoded Wireshark trace.</li>
</ul>
<h3>Notes</h3>
<ul>
<li>Close, End, or Detach performatives that indicate errors are highlighted in yellow.</li>
<li>Note that the <strong>[channel,handle]</strong> fields are highlighted with background colors to make protocol exchanges easier to see.</li>
<li>Wireshark generally displays hex data for AMQP message payloads. Adverb attempts to show transfer frame AMQP-value fields in readable ascii.</li>
</ul>
<h3>Notes on searching</h3>
You may use your browser's Ctrl-F search feature to search for text on the screen. However, this search does not find any of the hidden text. You may use the <strong>Expand-all page view</strong> Page control to expand all the details in every frame. Then use the Ctrl-F to search for text anywhere in the details of each frame.
</div>
'''

    # print the indexed content
    if arg_display_xfer:
        print "<h3>Indexed content</h3>"
        print ("Frame, Time, Src, Dst, Channel, Handle, DeliveryId, DeliveryTag, Data<br>")
        for key in transfer_data_list:
            hits = transfer_data[key]
            for hit in hits:
                print ("%s<br>" % (hit))

    # close the html page
    print '''</body>
</html>
'''
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

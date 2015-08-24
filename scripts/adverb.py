#!/usr/bin/env python
#
# Version 3.1

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

#
#
def amqp_port_str():
    return "5672"

def amqp_port_int():
    return int(amqp_port_str())

#
# Various web symbols
#
def nbsp():
    return "&#160;"

def shaded_background_begin():
    return "<span style=\"background-color:#e0e0e0\">"

def shaded_background_end():
    return "</span>"

def l_arrow():
    return "<-"

def r_arrow():
    return "->"

def l_arrow_spaced():
    return nbsp() + l_arrow() + nbsp()

def r_arrow_spaced():
    return nbsp() + r_arrow() + nbsp()

def l_arrow_str():
    return l_arrow_spaced() + nbsp()

def r_arrow_str():
    return nbsp() + r_arrow_spaced()

def lozenge():
    return "&#9674;"

def double_lozenge():
    return lozenge() + lozenge()

def leading(level):
    sizes = [3, 8, 13, 18, 23]
    if level < len(sizes):
        return nbsp() * sizes[level]
    return nbsp() * 23

#
# font color
color_list = ["black", "red", "blue", "green", "purple", "darkblue", "blueviolet", "darkred", "darkgreen"]
def color_of(index):
    i = int(index)
    return color_list[i % len(color_list)]

#
# bg color
bg_color_list = ["#ffffff", "#e0e0e0", "#ffccff", "#99FFFF", "#ffffcc"]
def bg_color_of(index):
    i = int(index)
    return bg_color_list[i % len(bg_color_list)]
#
# colorize function for [channel,handle]
pattern_bg_color_list = []
pattern_bg_color_map = {}
def colorize_bg(pattern):
    if pattern not in pattern_bg_color_list:
        pattern_bg_color_list.append(pattern)
        pattern_bg_color_map[pattern] = bg_color_of(pattern_bg_color_list.index(pattern))
    return "<span style=\"background-color:%s\">%s</span>" % (pattern_bg_color_map[pattern], pattern)

#
# colorize a directive with an error indication
def colorize_performative_error(proto, res):
    args        = proto.find("./field[@name='amqp.method.arguments']")
    error       = args.find("./field[@name='amqp.performative.arguments.error']")
    if not error is None:
        e_size      = error.get("size")
        if int(e_size) > 1:
            res.name = "<span style=\"background-color:yellow\">" + res.name + "</span>"

#
# Given a hex ascii string, return printable string w/o control codes
def dehexify_no_control_chars(valuetext):
    tmp = valuetext.decode("hex")
    res = ""
    for ch in tmp:
        if ord(ch) < 32 or ord(ch) >= 127:
            ch = '.'
        res += ch
    return res

#
#
global_broker_ports_list = []

#
#
class ExitStatus(Exception):
    """Raised if a command wants a non-0 exit status from the script"""
    def __init__(self, status): self.status = status

#
#
class PerformativeInfo():
    def __init__(self):
        self.web_show_str = ""
        self.name = ""
        self.channel = ""          # undecorated number - '0'
        self.handle = ""           # undecorated number - '1'
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

#
# Name shortener.
# The short name for display is "name_" + index(longName)
# Embellish the display name with an html popup
# Link and endpoint names are tracked separately
# 
class ShortNames():
    def __init__(self, prefixText):
        self.longnames = []
        self.prefix = prefixText
        self.threshold = 25

    def translate(self, lname):
        # add all names, even if not translated
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
        if len(self.longnames) > 0:
            print "<h3>" + self.prefix + " Name Index</h3>"
            print "<ul>"
            for i in range(0, len(self.longnames)):
                print ("<li> " + self.prefix + "_" + str(i) + " - " + self.longnames[i] + "</li>")
            print "</ul>"

short_link_names = ShortNames("link")
short_endp_names = ShortNames("endpoint")

#
#
def process_port_args(ostring, res_list):
    """Given the string of broker ports, return an expanded list"""
    port_args = ostring.strip().split(" ")
    for port_arg in port_args:
        seq = port_arg.strip().split(":")
        if len(seq) == 2:
            start = int(seq[0])
            count = int(seq[1])
            for x in range (0, count):
                res_list.append(str(start + x))
        else:
            rng = port_arg.strip().split("-")
            if len(rng) == 2:
                current = int(rng[0])
                upper   = int(rng[1])
                while current <= upper:
                    res_list.append(str(current))
                    current += 1
            else:
                if len(port_arg) > 0:
                    res_list.append(port_arg)

#
#
def is_broker_a(a, b, ports_list):
    """Given two ports guess if 'a' is the broker port"""
    a_is_broker = True
    if a == amqp_port_int() or str(a) in ports_list:
        a_is_broker = True
    elif b == amqp_port_int() or str(b) in ports_list:
        a_is_broker = False
    elif a < b:
        a_is_broker = True
    else:
        a_is_broker = False
    return a_is_broker

#
#
def connection_dst_is_broker(packet):
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
    return is_broker_a(d_port, s_port, global_broker_ports_list)
    
#
#
def connection_show_util(packet, sep_broker_r, sep_broker_l, bg_start="", bg_end=""):
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
    if is_broker_a(d_port, s_port, global_broker_ports_list):
        result = "%s%s%s%s%s%s" % (bg_start, src_addr, sep_broker_r, bg_end, dst_addr, sep_broker_r)
    else:
        result = "%s%s%s%s%s%s" % (dst_addr, bg_start, sep_broker_l, src_addr, bg_end, sep_broker_l)

    return result


#
#
def connection_name_for_web(packet):
    """Given a packet, return the display connection name client-broker for html"""
    return connection_show_util(packet, r_arrow_str(), l_arrow_str(), shaded_background_begin(), shaded_background_end())

#
#
def connection_name(packet):
    """Given a packet, return the human readable name"""
    return connection_show_util(packet, "-", "-")

#
#
def connection_id(packet):
    """Given a packet, return the internal connection name (no special chars)"""
    tmp =  connection_show_util(packet, "_", "_")
    tmp = tmp.replace('.', '_')
    tmp = tmp.replace(':', '_')
    tmp = tmp.replace('[', '_')
    tmp = tmp.replace(']', '_')
    return tmp

def frame_num_str(packet):
    return (packet
            .find("./proto[@name='frame']")
            .find("./field[@name='frame.number']")
            .get("show"))

def frame_num(packet):
    return int(frame_num_str(packet))

def frame_id(packet):
    return "f" + frame_num_str(packet)

def frame_time_relative(packet):
    result = "0.0"
    proto_frame = packet.find("./proto[@name='frame']")
    if proto_frame is not None:
        ftr = proto_frame.find("./field[@name='frame.time_relative']")
        if ftr is not None:
            result = "%.6f" % float(ftr.get("show"))
    return result

def field_show_value_or_null(field):
    '''hassle with displaying a decent null'''
    if field is None:
        return "null"
    tmp = field.get('value')
    if tmp == '40':
        return "null"
    else:
        return field.get('show')

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
    return words[1]

def amqp_other_decode(proto):
    '''Given a proto that isn't a nice, clean performative, return a parsed summary'''
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

def amqp_decode(proto):
    assert proto is not None, "amqp_decode receives null proto"

    '''Given an amqp proto, return parsed PerformativeInfo summary'''
    perf_field = proto.find("./field[@name='amqp.performative']")
    if perf_field is None:
        # No performative. Go decode init frames and amqp0-X stuff
        return amqp_other_decode(proto)

    res = PerformativeInfo()
    perf = perf_field.get("value")
    if perf is None:
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
        name        = None
        src         = None
        tgt         = None
        if tmpsrc is not None:
            src       = tmpsrc.find("./field[@name='amqp.performative.arguments.address']")
        if tmptgt is not None:
            tgt       = tmptgt.find("./field[@name='amqp.performative.arguments.address']")
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
        transfer_id     = args.find("./field[@name='amqp.performative.arguments.deliveryId']").get("showname")
        res.transfer_id = extract_name(transfer_id)
        res.name        = "transfer"
        res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
        res.web_show_str  = "<strong>%s</strong>  %s (%s)" % (res.name, colorize_bg(res.channel_handle), res.transfer_id)

    elif perf == '15':
        # Performative: disposition [channel] (role first-last)
        res.channel = proto.find("./field[@name='amqp.channel']").get("show")
        args        = proto.find("./field[@name='amqp.method.arguments']")
        role        = args.find("./field[@name='amqp.performative.arguments.role']").get("showname")
        first       = args.find("./field[@name='amqp.performative.arguments.first']").get("showname")
        last        = args.find("./field[@name='amqp.performative.arguments.last']").get("showname")
        res.first   = extract_name(first)
        res.last    = extract_name(last)
        res.name    = "disposition"
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
        colorize_performative_error(proto, res)
        res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
        res.web_show_str   = "<strong>%s</strong> %s" % (res.name, colorize_bg(res.channel_handle))
    
    elif perf == '17':
        # Performative: end [channel] 
        res.channel      = proto.find("./field[@name='amqp.channel']").get("show")
        res.name         = "end"
        colorize_performative_error(proto, res)
        res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

    elif perf == '18':
        # Performative: close [0] always channel 0
        res.channel      = "0"
        res.name         = "close"
        colorize_performative_error(proto, res)
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
        if (childname == "amqp.data" or childname == "amqp.amqp_value"):
            try:
                showascii = " <span style=\"background-color:white\">\'" + dehexify_no_control_chars(valuetext) + "\'</span>"
            except:
                pass
        if showname is not None and len(showname) > 0:
            print "%s%s<br>" % (leading(level), showname + showascii)
        else:
            print "%s%s<br>" % (leading(level), showtext + showascii)
        show_fields(child, level+1)

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
    """Given a pdml file name, send the javascript web page to stdout"""
    if len(sys.argv) < 5:
        sys.exit('Usage: %s pdml-file-name trace-file-display-name broker-ports user-note' % sys.argv[0])

    arg_pdml_file    = sys.argv[1]
    arg_display_name = sys.argv[2]
    arg_broker_ports = sys.argv[3]

    #for x in range (0, 5):
    #    print "arg %s: %s<br>" % (x, sys.argv[x])

    if not os.path.exists(arg_pdml_file):
        sys.exit('ERROR: pdml file %s was not found!' % arg_pdml_file)

    process_port_args(arg_broker_ports, global_broker_ports_list)

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
                flow_id = connection_id(packet)
                flow_id_display = connection_show_util(packet, " - ", " - ")
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

    # select only AMQP packets
    amqp_packets = []
    for packet in packets:
        amqp_frame = packet.find("./proto[@name='amqp']")
        if amqp_frame is not None:
            amqp_packets.append(packet)
        
    # calculate a list of connections and a map
    # of {internal name: formal display name}
    connection_id_list = []
    conn_id_to_name_map = {}
    conn_id_to_color_map = {}
    conn_frame_count = {}
    color_index = 0
    for packet in amqp_packets:
        cid = connection_id(packet)
        cname = connection_name(packet)
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
        
    # index the frames by connection
    for packet in amqp_packets:
        conn_to_frame_map[ connection_id(packet) ].append( frame_id(packet) )

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
            # Hide level 4
            print "  javascript:show_level_4_%s();" % fid
            # Hide level 2
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

    print "<h3>Show/Hide frames per connection</h3>"
    print "<button onclick=\"javascript:select_all()\">Select All</button>"
    print "<button onclick=\"javascript:deselect_all()\">Deselect All</button>"
    print "<button onclick=\"javascript:toggle_all()\">Toggle All</button>"
    print "<br>"
    for conn in connection_id_list:
        print "<input type=\"checkbox\" id=\"cb_sel_%s\" " % conn
        print "checked=\"true\" onclick=\"javascript:show_if_cb_sel_%s()\">" % conn
        print "<font color=\"%s\">" % conn_id_to_color_map[ conn ]
        print "%s</font>%s%s(n=%d)<br>" % (conn_id_to_name_map[conn], nbsp(), nbsp(), conn_frame_count[conn])

    # print the frames
    print "<br>"
    print "<h3>AMQP frames</h3>"
    for packet in amqp_packets:
        f_id = frame_id(packet) # f123
        f_idc = f_id + "c"      # f123c - frame's contents

        # Flag tcp retransmits
        tcp_message = ""
        try:
            tcp_proto = packet.find("./proto[@name='tcp']")
            tcp_analysis = tcp_proto.find("./field[@name='tcp.analysis']")
            tcp_a_flags = tcp_analysis.find("./field[@name='tcp.analysis.flags']")
            ws_expert = tcp_a_flags.find("./field[@name='_ws.expert']")
            expert_text = ws_expert.get("showname")
            if "(suspected) retransmission" in expert_text:
                tcp_message = "<span style=\"background-color:orange\">Suspected TCP retransmission</span>"
        except:
            pass

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
                decoded_proto = amqp_decode(proto)
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
        print "<font color=\"%s\">" % conn_id_to_color_map[ connection_id(packet) ]
        print "Frame %s" % frame_num(packet)
        print "%s%s" % (nbsp(), connection_name_for_web(packet))
        print "</font>%s%s %s" % (nbsp(), performatives, tcp_message)

        # Create a div that holds the frame's contents
        print "<div width=\"100%%\" id=\"%s\" style=\"display:none\">" % f_idc # begin level:2
        # Loop through the packet's proto blocks and display a title for each
        proto_index = 0
        for proto in protos:
            if proto.get("name") == "amqp":
                decoded_proto = amqp_decode(proto)
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
        print "</div>"                                                         # end level:2
        print "</div>"                                                         # end level:1

    # shortened names, if any
    short_link_names.htmlDump()
    short_endp_names.htmlDump()

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
<li>Wireshark generally displays hex data for AMQP message payloads. Adverb attempts to show transfer frame AMQP-value fields readable ascii.</li>
</ul>
<h3>Notes on searching</h3>
You may use your browser's Ctrl-F search feature to search for text on the screen. However, this search does not find any of the hidden text. You may use the <strong>Expand-all page view</strong> Page control to expand all the details in every frame. Then use the Ctrl-F to search for text anywhere in the details of each frame.
</div>
'''

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
        print "%s: %s"%(type(e).__name__, e)
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))

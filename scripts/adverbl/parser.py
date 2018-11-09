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

from datetime import *
import re
import sys
import traceback

import splitter
import test_data as td
import common
import text
import router


def colorize_bg(what):
    # TODO: use the real colorize_bg
    return what


class LogLineData:

    def direction_is_in(self):
        return self.direction == text.direction_in()

    def direction_is_out(self):
        return self.direction == text.direction_out()

    def __init__(self):
        self.web_show_str = ""
        self.name = ""
        self.conn_num = ""  # source router's undecorated conn num
        self.conn_id = ""  # decorated routerPrefixLetter'instanceNumber-conn_num
        self.conn_peer = ""  # display name of peer in seen in Open 'A - routerId.Test'
        self.channel = ""  # undecorated number - '0'
        self.direction = ""  # '<-' IN, or '->' OUT, or '--'
        self.described_type = DescribedType()  # DescribedType object
        self.handle = ""  # undecorated number - '1'
        self.delivery_id = ""  # "0"
        self.delivery_tag = ""  # "00:00:00:00"
        self.remote = ""  # undecorated number - '2'
        self.channel_handle = ""  # decorated - '[0,0]'
        self.channel_remote = ""  # decorated - '[1,2]'
        self.flow_deliverycnt = ""  # undecorated number - '50'
        self.flow_linkcredit = ""  # undecorated number - '100'
        self.flow_cnt_credit = ""  # decorated - '(50,100)'
        self.flow_drain = False
        self.transfer_id = ""
        self.role = ""
        self.is_receiver = False
        self.source = ""
        self.target = ""
        self.first = ""  # undecorated number - '10'
        self.last = ""  # undecorated number - '20'
        self.settled = ""  # Disposition or Transfer settled field
        self.disposition_state = "?absent?"
        self.snd_settle_mode = ""  # Attach
        self.rcv_settle_mode = ""  # Attach
        self.transfer_data = ""  # protonized transfer data value
        self.transfer_bare = ""  # bare message from transfer_data
        self.transfer_hdr_annos = ""  # header and annotation sections
        self.transfer_size = ""  # size declared by number in parenthesis
        self.transfer_short_name = ""
        self.transfer_settled = False
        self.transfer_more = False
        self.transfer_resume = False
        self.transfer_aborted = False
        self.link_short_name = ""
        self.link_short_name_popup = ""
        self.is_policy_trace = False  # line is POLICY (trace)
        self.is_server_info = False  # line is SERVER (info)
        self.is_router_ls = False  # line is ROUTER_LS (info)
        self.fid = ""  # Log line (frame) id as used in javascript code
        self.amqp_error = False
        self.link_class = "normal"  # attach sees: normal, router, router-data (, management?)
        self.disposition_display = ""
        self.final_disposition = None


class DescribedType:
    """
    Given a line like:
        @typename(00) [key1=val1, ...]
    Extract the typename and create a map of the key-val pairs
    May recursively find embedded described types
    """

    @staticmethod
    def is_dtype_name(name):
        """
        Return true if the name is a pn_trace described type name
        :param name:
        :return:
        """
        return (name.startswith('@') and
                '(' in name and
                name.endswith(')'))

    @staticmethod
    def get_key_and_val(kvp):
        eqi = kvp.find('=')
        return kvp[:eqi], kvp[eqi + 1:]

    @staticmethod
    def dtype_name(name):
        if not DescribedType.is_dtype_name(name):
            raise ValueError("Name '%s' is not a described type name" % name)
        return name[1: name.find('(')]

    @staticmethod
    def dtype_number(name):
        if not DescribedType.is_dtype_name(name):
            raise ValueError("Name '%s' is not a described type name" % name)
        return int(name[name.find('(') + 1: -1])

    def __init__(self):
        self.dict = {}
        self.dtype_name = "unparsed"
        self.dtype_number = 0

    def __repr__(self):
        return self._representation()

    def _representation(self):
        return "DescribedType %s( %d ) : %s" % (self.dtype_name, self.dtype_number, self.dict)

    def add_field_to_dict(self, f_text, expected_key=None):
        if '=' not in f_text:
            raise ValueError("Field does not contain equal sign '%s'" % self.line)
        if expected_key is not None and not f_text.startswith(expected_key):
            raise ValueError("Transfer field %s not in order from line: %s" % (expected_key, self.line))
        key, val = DescribedType.get_key_and_val(f_text)
        if val.endswith(','):
            val = val[:-1]
        self.dict[key] = val

    def process_transfer_tail_key(self):
        keys = ["batchable", "aborted", "resume", "state", "rcv-settle-mode", "more", "settled", "message-format"]
        for key in keys:
            idx = self.line.rfind(key)
            if idx != -1:
                field = self.line[idx:]
                self.add_field_to_dict(field, key)
                self.line = self.line[:idx].strip()
                return True
        return False

    def parseTransfer(self):
        """
        Figure out the described type fields for the transfer.
        Transfers are handled specially with the ill-formatted binary delivery-tag field
        :return:
        """
        # strip leading '[' and trailing ']'
        if not (self.line.startswith('[') and self.line.endswith(']')):
            raise ValueError("Described type not delimited with square brackets: '%s'" % self.line)
        self.line = self.line[1:]
        self.line = self.line[:-1]

        # process fields from head
        fHandle = self.line.split()[0]
        self.add_field_to_dict(fHandle)
        self.line = self.line[(len(fHandle) + 1):]

        fDelId = self.line.split()[0]
        self.add_field_to_dict(fDelId)
        self.line = self.line[(len(fDelId) + 1):]

        # process fields from tail
        while len(self.line) > 0 and self.process_transfer_tail_key():
            pass

        # the remainder, no matter how unlikely, must be the delivery-tag
        self.add_field_to_dict(self.line, "delivery-tag")

    def parse_dtype_line(self, _dtype, _line):
        """
        Figure out the fields for the described type.
        The line format is:

        Transfers are handled specially with the ill-formatted binary delivery-tag field
        Note other performatives with ill-formatted binary data might get rejected. We
        only struggle figuring out the delivery-tag because it happens so often.
        :param _dtype: @describedtypename(num)
        :param _line: [key=val [, key=val]...]
        :return:
        """
        self.dtype = _dtype
        self.oline = str(_line)
        self.line = self.oline
        self.dtype_name = DescribedType.dtype_name(self.dtype)
        self.dtype_number = DescribedType.dtype_number(self.dtype)

        # Process transfers separately..
        # Transfer perfomatives will not call parse recursively while others might
        if self.dtype_name == "transfer":
            self.parseTransfer()
            return

        # strip leading '[' and trailing ']'
        if not (self.line.startswith('[') and self.line.endswith(']')):
            raise ValueError("Described type not delimited with square brackets: '%s'" % _line)
        self.line = self.line[1:]
        self.line = self.line[:-1]

        # process fields
        fields = splitter.Splitter.split(self.line)
        while len(fields) > 0 and len(fields[0]) > 0:
            if '=' not in fields[0]:
                raise ValueError("Field does not contain equal sign '%s'" % fields[0])
            key, val = DescribedType.get_key_and_val(fields[0])
            del fields[0]
            if DescribedType.is_dtype_name(val):
                # recursing to process subtype
                # pull subtype's data out of fields. The fields list belongs to parent.
                subfields = []
                if fields[0] == "[]":
                    # degenerate case of empty subtype closing parent type
                    #  @disposition .. state=@accepted(36) []]
                    subfields.append("[]")
                    del fields[0]
                else:
                    while len(fields) > 0:
                        if fields[0].endswith('],'):
                            subfields.append(fields[0][:-2])
                            subfields.append(']')
                            del fields[0]
                            break
                        if fields[0].endswith(']'):
                            subfields.append(fields[0][:-1])
                            subfields.append(']')
                            del fields[0]
                            break
                        subfields.append(fields[0])
                        del fields[0]

                subtype = DescribedType()
                subtype.parse_dtype_line(val, ' '.join(subfields))
                self.dict[key] = subtype
            elif val.startswith('{'):
                # handle some embedded map: properties={:product=\"qpid-dispatch-router\", :version=\"1.3.0-SNAPSHOT\"}
                # pull subtype's data out of fields. The fields list belongs to parent.
                submap = {}
                fields.insert(0, val)
                skey, sval = DescribedType.get_key_and_val(fields[0][1:])
                submap[skey] = sval
                del fields[0]
                while len(fields) > 0:
                    if fields[0].endswith('},'):
                        skey, sval = DescribedType.get_key_and_val(fields[0][:-2])
                        submap[skey] = sval
                        del fields[0]
                        break
                    if fields[0].endswith('}'):
                        skey, sval = DescribedType.get_key_and_val(fields[0][:-1])
                        submap[skey] = sval
                        del fields[0]
                        break
                    skey, sval = DescribedType.get_key_and_val(fields[0])
                    submap[skey] = sval
                    del fields[0]
                self.dict[key] = submap

            else:
                self.dict[key] = val


class ParsedLogLine(object):
    """
    Grind through the log line and record some facts about it.
    * Constructor returns Null if the log line is to be ignored
    * Constructor args:
    ** log_index          0 for 'A', 1 for 'B'
    ** routerInstance     which instance in log file
    ** lineno             line number
    ** line               the log line
    ** common             common block object
    """
    server_trace_key = "SERVER (trace) ["
    server_info_key = "SERVER (info) ["
    policy_trace_key = "POLICY (trace) ["
    router_ls_key = "ROUTER_LS (info)"
    transfer_key = "@transfer(20)"

    def sender_settle_mode_of(self, value):
        if value == "0":
            return "unsettled(0)"
        elif value == "1":
            return "settled(1)"
        elif value == "2":
            return "mixed(2)"  # default
        else:
            return "unknown(%s) % value"

    def receiver_settle_mode_of(self, value):
        if value == "0":
            return "first(0)"
        elif value == "1":
            return "second(1)"
        else:
            return "unknown(%s) % value"

    def resdict_value(self, resdict, key, if_absent):
        return resdict[key] if key in resdict else if_absent

    def highlighted(self, name, value, color):
        result = ""
        if value:
            result = "<span style=\"background-color:%s\">%s</span>" % (color, name)
        return result

    def extract_facts(self):
        perf = self.data.described_type.dtype_number
        res = self.data
        resdict = self.data.described_type.dict

        # the performatives
        # Note: res.channel is already populated
        if perf == 0x10:
            # Performative: open [0] always channel 0
            res.name = "open"
            res.channel = "0"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)
            if res.direction == text.direction_in():
                res.conn_peer = self.resdict_value(resdict, "container-id", "unknown")
                res.web_show_str += (" (peer: %s)" % res.conn_peer)

        elif perf == 0x11:
            # Performative: begin [channel,remoteChannel]
            # TODO: This has a bug where the local and remote channel numbers are confused.
            #       Usually they are the same. See if anyone notices!
            # res.channel
            res.name = "begin"
            res.remote = self.resdict_value(resdict, "remote-channel", "None)")
            res.channel_remote = "[%s,%s]" % (res.channel, res.remote)
            res.web_show_str = "<strong>%s</strong> %s" % (res.name, res.channel_remote)

        elif perf == 0x12:
            # Performative:  attach [channel,handle] role name (source: src, target: tgt)
            res.name = "attach"
            res.handle = resdict["handle"]
            res.role = "receiver" if resdict["role"] == "true" else "sender"
            res.is_receiver = res.role == "receiver"
            name = self.resdict_value(resdict, "name", "None")
            res.link_short_name_popup = self.shorteners.short_link_names.translate(name, True)
            res.link_short_name = self.shorteners.short_link_names.translate(name, False)
            tmpsrc = self.resdict_value(resdict, "source", None)
            tmptgt = self.resdict_value(resdict, "target", None)
            res.snd_settle_mode = self.sender_settle_mode_of(
                resdict["snd-settle-mode"]) if "snd-settle-mode" in resdict else "mixed"
            res.rcv_settle_mode = self.receiver_settle_mode_of(
                resdict["rcv-settle-mode"]) if "rcv-settle-mode" in resdict else "first"
            caps = ""
            if tmpsrc is not None:
                res.source = self.resdict_value(tmpsrc.dict, "address", "none")
                caps = self.resdict_value(tmpsrc.dict, "capabilities", "")
            else:
                res.source = "none"
            if tmptgt is not None:
                res.target = self.resdict_value(tmptgt.dict, "address", "none")
                if caps == "":
                    caps = self.resdict_value(tmptgt.dict, "capabilities", "")
            else:
                res.target = "none"
            res.channel_handle = "[%s,%s]" % (res.channel, res.handle)

            if 'qd.router-data' in caps:
                res.link_class = 'router-data'
            elif 'qd.router' in caps:
                res.link_class = 'router'
            """
            TODO:
            res.source = short_endp_names.translate(res.source)
            res.target = short_endp_names.translate(res.target)
            res.snd_settle_mode = extract_name(tmpssm)
            res.rcv_settle_mode = extract_name(tmprsm)
            """
            res.web_show_str = ("<strong>%s</strong> %s %s %s (source: %s, target: %s, class: %s)" %
                                (res.name, colorize_bg(res.channel_handle), res.role, res.link_short_name_popup,
                                 res.source, res.target, res.link_class))

        elif perf == 0x13:
            # Performative: flow [channel,handle]
            res.name = "flow"
            res.handle = resdict["handle"]
            res.flow_deliverycnt = self.resdict_value(resdict, "delivery-count", "0")
            res.flow_linkcredit = self.resdict_value(resdict, "link-credit", "0")
            res.flow_drain = resdict.get("drain", "") == "true"
            res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
            res.flow_cnt_credit = "(%s,%s)" % (res.flow_deliverycnt, res.flow_linkcredit)
            res.web_show_str = "<strong>%s</strong> %s (%s,%s) %s" % (
                res.name, colorize_bg(res.channel_handle), res.flow_deliverycnt, res.flow_linkcredit,
                self.highlighted("drain", res.flow_drain, "yellow"))

        elif perf == 0x14:
            # Performative: transfer [channel,handle] (id)
            res.name = "transfer"
            res.handle = resdict["handle"]
            res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
            res.delivery_id = self.resdict_value(resdict, "delivery-id", "none")
            res.delivery_tag = self.resdict_value(resdict, "delivery-tag", "none")
            res.settled = self.resdict_value(resdict, "settled", "false")
            res.transfer_settled = resdict.get("settled", "") == "true"
            res.transfer_more = resdict.get("more", "") == "true"
            res.transfer_resume = resdict.get("resume", "") == "true"
            res.transfer_aborted = resdict.get("aborted", "") == "true"
            self.transfer_short_name = self.shorteners.short_data_names.translate(res.transfer_bare)
            showdat = "<a href=\"#%s\">%s</a>" % (self.transfer_short_name, self.transfer_short_name)
            res.web_show_str = "<strong>%s</strong>  %s (%s) %s %s %s %s %s - %s bytes" % (
                res.name, colorize_bg(res.channel_handle), res.delivery_id,
                self.highlighted("settled", res.transfer_settled, "green"),
                self.highlighted("more", res.transfer_more, "purple"),
                self.highlighted("resume", res.transfer_resume, "orange"),
                self.highlighted("aborted", res.transfer_aborted, "yellow"),
                showdat, res.transfer_size)

        elif perf == 0x15:
            # Performative: disposition [channel] (role first-last)
            res.name = "disposition"
            res.role = "receiver" if resdict["role"] == "true" else "sender"
            res.is_receiver = res.role == "receiver"
            res.first = self.resdict_value(resdict, "first", "0")
            res.last = self.resdict_value(resdict, "last", res.first)
            res.settled = self.resdict_value(resdict, "settled", "false")
            state = resdict.get("state")
            if state is not None:
                res.disposition_state = state.dtype_name
            ###    colorize_dispositions_not_accepted(proto, res, global_vars, count_anomalies)
            res.web_show_str = ("<strong>%s</strong>  [%s] (%s %s-%s)" %
                                (res.name, res.channel, res.role, res.first, res.last))

        elif perf == 0x16:
            # Performative: detach [channel, handle]
            res.name = "detach"
            res.handle = resdict["handle"]
            ### TODO: colorize_performative_error(proto, res, global_vars, count_anomalies)
            res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
            res.web_show_str = "<strong>%s</strong> %s" % (res.name, colorize_bg(res.channel_handle))

        elif perf == 0x17:
            # Performative: end [channel]
            res.name = "end"
            ### TODO: colorize_performative_error(proto, res, global_vars, count_anomalies)
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x18:
            # Performative: close [0] always channel 0
            res.channel = "0"
            res.name = "close"
            ### colorize_performative_error(proto, res, global_vars, count_anomalies)
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x1d:
            # transport:definitions error
            res.name = "error"
            descr = self.resdict_value(resdict, "description", "none")
            res.web_show_str = "<strong>%s</strong> [%s] %s" % (res.name, res.channel, descr)

        elif perf == 0x23:
            # messaging:delivery-state received
            res.name = "received"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x24:
            # messaging:delivery-state accepted
            res.name = "accepted"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x25:
            # messaging:delivery-state rejected
            res.name = "rejected"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x26:
            # messaging:delivery-state released
            res.name = "released"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x27:
            # messaging:delivery-state modified
            res.name = "modified"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x28:
            # messaging:addressing source
            res.name = "source"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x29:
            # messaging:addressing target
            res.name = "target"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x2b:
            # messaging:addressing delete-on-close
            res.name = "delete-on-close"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x2c:
            # messaging:addressing delete-on-no-links
            res.name = "delete-on-no-links"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x2d:
            # messaging:addressing delete-on-no-messages
            res.name = "delete-on-no-messages"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x2e:
            # messaging:addressing delete-on-no-links-or-messages
            res.name = "delete-on-no-links-or-messages"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x30:
            # transactions:coordination coordinator
            res.name = "coordinator"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x31:
            # transactions:coordination declare
            res.name = "declare"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x32:
            # transactions:coordination discharge
            res.name = "discharge"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x33:
            # transactions:coordination declared
            res.name = "declared"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x34:
            # transactions:coordination transactional-state
            res.name = "transactional-state"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x40:
            # security:sasl sasl-mechanisms
            res.name = "sasl-mechanisms"
            mechs = self.resdict_value(resdict, "sasl-server-mechanisms", "none")
            res.web_show_str = "<strong>%s</strong> [%s] %s" % (res.name, res.channel, mechs)

        elif perf == 0x41:
            # security:sasl sasl-init
            res.name = "sasl-init"
            mech = self.resdict_value(resdict, "mechanism", "none")
            res.web_show_str = "<strong>%s</strong> [%s] %s" % (res.name, res.channel, mech)

        elif perf == 0x42:
            # security:sasl sasl-challenge
            res.name = "sasl-challenge"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x43:
            # security:sasl sasl-response
            res.name = "sasl-response"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x44:
            # security:sasl sasl-outcome
            res.name = "sasl-outcome"
            code = self.resdict_value(resdict, "code", "none")
            res.web_show_str = "<strong>%s</strong> [%s] code=%s" % (res.name, res.channel, code)

        elif perf == 0x70:
            # messaging:message-format header
            res.name = "header"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x71:
            # messaging:message-format delivery-annotations
            res.name = "delivery-annotations"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x72:
            # messaging:message-format message-annotations
            res.name = "message-annotations"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x73:
            # messaging:message-format properties
            res.name = "properties"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x74:
            # messaging:message-format application-properties
            res.name = "application-properties"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x75:
            # messaging:message-format data
            res.name = "data"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x76:
            # messaging:message-format amqp-sequence
            res.name = "amqp-sequence"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x77:
            # messaging:message-format amqp-value
            res.name = "amqp-value"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        elif perf == 0x78:
            # messaging:message-format footer
            res.name = "footer"
            res.web_show_str = "<strong>%s</strong> [%s]" % (res.name, res.channel)

        else:
            res.web_show_str = "HELP I'M A ROCK - Unknown performative: %s" % perf

        if "error" in resdict:
            res.amqp_error = True
            res.web_show_str += (" <span style=\"background-color:yellow\">error</span> "
                                 "%s %s" % (resdict["error"].dict["condition"], resdict["error"].dict["description"]))

    def adverbl_link_to(self):
        """
        :return: html link to the main adverbl data display for this line
        """
        return "<a href=\"#%s\">%s</a>" % (self.fid, "%s%d_%s" %
                                           (common.log_letter_of(self.index), self.instance, str(self.lineno)))

    def __init__(self, _log_index, _instance, _lineno, _line, _comn, _router):
        """
        Process a naked qpid-dispatch log line
        A log line looks like this:
          2018-07-20 10:58:40.179187 -0400 SERVER (trace) [2]:0 -> @begin(17) [next-outgoing-id=0, incoming-window=2147483647, outgoing-window=2147483647] (/home/chug/git/qpid-dispatch/src/server.c:106)
        The process is:
         1. If the line ends with a filename:fileline then strip that away
         2. Peel off the leading time of day and put that into data.datetime.
            Lines with no datetime are presumed start-of-epoch.
         3. Find (SERVER) or (POLICY). If absent then raise to reject message.
         4. If connection number in square brackets '[2]' is missing then raise.
         5. Extract connection number; save in data.conn_num
         6. Create decorated data.conn_id "A0_2"
         7. Extract data.channel if present. Raise if malformed.
         8. Create a web_show_str for lines that may not parse any further. Like policy lines.
         9. Extract the direction arrows

        The log line is now reduced to a described type:
          @describedtypename(num) [key=val [, key=val ...]]
            except for transfers that have the funky transfer data at end.

        :param _log_index:   The router prefix index 0 for A, 1 for B, ...
        :param _instance     The router instance
        :param _lineno:
        :param _line:
        :param _comn:
        :param _router:
        """
        if not (ParsedLogLine.server_trace_key in _line or
                (ParsedLogLine.policy_trace_key in _line and "lookup_user:" in _line) or  # open (not begin, attach)
                ParsedLogLine.server_info_key in _line or
                ParsedLogLine.router_ls_key in _line):
            raise ValueError("Line is not a candidate for parsing")
        self.oline = _line  # original line
        self.index = _log_index  # router prefix 0 for A, 1 for B
        self.instance = _instance  # router instance in log file
        self.lineno = _lineno  # log line number
        self.comn = _comn
        self.router = _router
        self.prefixi = common.log_letter_of(self.index) + str(self.instance)  # prefix+instance A0
        self.fid = "f_" + self.prefixi + "_" + str(self.lineno)  # frame id A0_100
        self.shorteners = _comn.shorteners  # name shorteners

        self.line = _line  # working line chopped, trimmed

        self.data = LogLineData()  # parsed line fact store

        # strip optional trailing file:line field
        self.line = self.line.rstrip()
        hasFileLine = False
        if self.line.endswith(')'):
            idxOP = self.line.rfind('(')
            idxColon = self.line.rfind(':')
            if idxOP != -1 and idxColon != -1:
                if idxColon > idxOP:
                    lNumStr = self.line[(idxColon + 1): (-1)]
                    try:
                        lnum = int(lNumStr)
                        hasFileLine = True
                    except:
                        pass
        if hasFileLine:
            self.line = self.line[:self.line.rfind('(')].rstrip()

        # Handle optional timestamp
        # This whole project is brain dead without a timestamp. Just sayin'.
        self.datetime = None
        try:
            self.datetime = datetime.strptime(self.line[:26], '%Y-%m-%d %H:%M:%S.%f')
        except:
            self.datetime = datetime(1970, 1, 1)

        # extract connection number
        sti = self.line.find(self.server_trace_key)
        if sti < 0:
            sti = self.line.find(self.policy_trace_key)
            if sti < 0:
                sti = self.line.find(self.server_info_key)
                if sti < 0:
                    sti = self.line.find(self.router_ls_key)
                    if sti < 0:
                        raise ValueError("Log keyword/level not found in line %s" % (self.line))
                    else:
                        self.line = self.line[sti + len(self.router_ls_key):]
                        self.data.is_router_ls = True
                        # this has no relationship to AMQP log lines
                        return
                else:
                    self.line = self.line[sti + len(self.server_info_key):]
                    self.data.is_server_info = True
            else:
                self.line = self.line[sti + len(self.policy_trace_key):]
                self.data.is_policy_trace = True
        else:
            self.line = self.line[sti + len(self.server_trace_key):]
        ste = self.line.find(']')
        if ste < 0:
            print("Failed to parse line ", _lineno, " : ", _line)
            raise ValueError("'%s' not found in line %s" % ("]", self.line))
        self.data.conn_num = self.line[:ste]
        self.line = self.line[ste + 1:]

        # create decorated connection id
        self.data.conn_id = self.prefixi + "_" + self.data.conn_num

        # get the session (channel) number
        if self.line.startswith(':'):
            self.line = self.line[1:]
        sti = self.line.find(' ')
        if sti < 0:
            raise ValueError("space not found after channel number at head of line %s" % (self.line))
        if sti > 0:
            self.data.channel = self.line[:sti]
        self.line = self.line[sti + 1:]
        self.line = self.line.lstrip()

        # cover for traces that don't get any better
        self.data.web_show_str = ("<strong>%s</strong>" % self.line)

        # policy lines have no direction and described type fields
        if self.data.is_policy_trace or self.data.is_server_info:
            return

        # direction
        if self.line.startswith('<') or self.line.startswith('-'):
            self.data.direction = self.line[:2]
            self.line = self.line[3:]
            self.data.web_show_str = ("<strong>%s</strong>" % self.line)

        # The log line is now reduced to a described type:
        #  @describedtypename(num) [key=val [, key=val ...]]
        # extract descriptor name
        dname = self.line.split()[0]
        self.line = self.line[(len(dname) + 1):]

        # Dispose of the transfer data
        if dname == self.transfer_key:
            # Look for the '] (NNN) "' that separates the described type fields
            # from the '(size) "data"'. Stick the required '(size) data' into
            # data.transfer_data and delete it from the line.
            rz = re.compile(r'\] \(\d+\) \"').search(self.line)
            # aborted transfers may or may not have size/data in the log line
            if rz is not None and len(rz.regs) > 0:
                splitSt, splitTo = rz.regs[0]
                self.data.transfer_size = self.line[splitSt + 3: splitTo - 3]
                self.data.transfer_data = self.line[splitTo - 1:]  # discard (NNN) size field
                self.line = self.line[: splitSt + 1]
                # try to isolate the bare message
                sti = self.data.transfer_data.find(r"\x00Ss")
                if sti > 0:
                    self.data.transfer_hdr_annos = self.data.transfer_data[:sti]
                    self.data.transfer_bare = self.data.transfer_data[sti:]
                else:
                    raise ValueError("Transfer with no properties. Not really an error but just checking...")
            else:
                self.data.transfer_size = "0"
                self.data.transfer_data = "(none)"

        if DescribedType.is_dtype_name(dname):
            self.data.described_type.parse_dtype_line(dname, self.line)
            # data fron incoming line is now parsed out into facts in .data
            # Now cook the data to get useful displays
            self.extract_facts()


def parse_log_file(fn, log_index, comn):
    """
    Given a file name, return an array of Routers that hold the parsed lines.
    Lines that don't parse are identified on stderr and then discarded.
    :param fn: file name
    :param log_index: router id 0 for 'A', 1 for 'B', ...
    :param comn: common data
    :return: list of Routers
    """
    instance = 0
    lineno = 0
    search_for_in_progress = True
    rtrs = []
    rtr = None
    key1 = "SERVER (trace) ["  # AMQP traffic
    key2 = "SERVER (info) Container Name:"  # Normal 'router is starting' restart discovery line
    key3 = "ROUTER_LS (info)"  # a log line placed in separate pool of lines
    keys = [key1, key3]
    key4 = "ROUTER (info) Version:"  # router version line
    key5 = "ROUTER (info) Router started in " # router mode
    with open(fn, 'r') as infile:
        for line in infile:
            if search_for_in_progress:
                # What if the log file has no record of the router starting?
                # This is an in_progress router and it is a pre-existing router instance
                # and not one found by restart discovery.
                # Any key or AMQP line indicates a router in-progress
                if any(s in line for s in keys) or ("[" in line and "]" in line):
                    assert rtr is None
                    rtr = router.Router(fn, log_index, instance)
                    rtrs.append(rtr)
                    search_for_in_progress = False
                    rtr.restart_rec = router.RestartRecord(rtr, line, lineno + 1)
            lineno += 1
            if key2 in line:
                # This line closes the current router, if any, and opens a new one
                if rtr is not None:
                    instance += 1
                rtr = router.Router(fn, log_index, instance)
                rtrs.append(rtr)
                rtr.restart_rec = router.RestartRecord(rtr, line, lineno)
                search_for_in_progress = False
                rtr.container_name = line[(line.find(key2) + len(key2)):].strip().split()[0]
            elif key3 in line:
                pl = ParsedLogLine(log_index, instance, lineno, line, comn, rtr)
                if pl is not None:
                    if pl.data.is_router_ls:
                        rtr.router_ls.append(pl)
            elif key4 in line:
                rtr.version = line[(line.find(key4) + len(key4)):].strip().split()[0]
            elif key5 in line:
                rtr.mode = line[(line.find(key5) + len(key5)):].strip().split()[0].lower()
            elif "[" in line and "]" in line:
                try:
                    if lineno == 130:
                        pass
                    do_this = comn.arg_index_data
                    if not do_this:
                        # not indexing data. maybe do this line anyway
                        do_this = not any(s in line for s in [' @transfer', ' @disposition', ' @flow', 'EMPTY FRAME'])
                    if do_this:
                        pl = ParsedLogLine(log_index, instance, lineno, line, comn, rtr)
                        if pl is not None:
                            rtr.lines.append(pl)
                    else:
                        comn.data_skipped += 1
                except ValueError as ve:
                    pass
                except Exception as e:
                    # t, v, tb = sys.exc_info()
                    if hasattr(e, 'message'):
                        sys.stderr.write("Failed to parse file '%s', line %d : %s\n" % (fn, lineno, e.message))
                    else:
                        sys.stderr.write("Failed to parse file '%s', line %d : %s\n" % (fn, lineno, e))
                    # raise t, v, tb
            else:
                # ignore this log line
                pass
    return rtrs


if __name__ == "__main__":

    data = td.TestData().data()
    log_index = 0  # from file for router A
    instance = 0  # all from router instance 0
    comn = common.Common()
    try:
        for i in range(len(data)):
            temp = ParsedLogLine(log_index, instance, i, data[i], comn, None)
            print(temp.datetime, temp.data.conn_id, temp.data.direction, temp.data.web_show_str)
        pass
    except:
        traceback.print_exc(file=sys.stdout)
        pass

    comn2 = common.Common()
    routers = parse_log_file('test_data/A-two-instances.log', 0, comn2)
    if len(routers) != 2:
        print("ERROR: Expected two router instances in log file")

    t_b4_0 = datetime.strptime('2018-10-15 10:57:32.151673', '%Y-%m-%d %H:%M:%S.%f')
    t_in_0 = datetime.strptime('2018-10-15 10:57:32.338183', '%Y-%m-%d %H:%M:%S.%f')
    t_in_1 = datetime.strptime('2018-10-15 10:59:07.584498', '%Y-%m-%d %H:%M:%S.%f')
    t_af_1 = datetime.strptime('2019-10-15 10:59:07.584498', '%Y-%m-%d %H:%M:%S.%f')

    rtr, idx = router.which_router_tod(routers, t_b4_0)
    assert rtr is routers[0] and idx == 0
    rtr, idx = router.which_router_tod(routers, t_in_0)
    assert rtr is routers[0] and idx == 0
    rtr, idx = router.which_router_tod(routers, t_in_1)
    assert rtr is routers[1] and idx == 1
    rtr, idx = router.which_router_tod(routers, t_af_1)
    assert rtr is routers[1] and idx == 1

    pass

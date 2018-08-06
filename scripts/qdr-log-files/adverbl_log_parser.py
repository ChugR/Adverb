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

import sys
import time
import os
import traceback
from datetime import *
import pdb
#from adverb_name_shortener import *
#from adverb_strings import *
from adverbl_splitter import *
from adverbl_test_data import *


def colorize_bg(what):
    # TODO: use the real colorize_bg
    return what

class LogLineData():

    def __init__(self):
        self.web_show_str = ""
        self.name = ""
        self.conn_num = "" # source router's undecorated conn num
        self.conn_id = "" # decorated routerPrefix-conn_num
        self.channel = ""  # undecorated number - '0'
        self.direction = "" # '<-' IN, or '->' OUT
        self.described_type = DescribedType() # DescribedType object
        self.handle = ""  # undecorated number - '1'
        self.delivery_id = ""  # "0"
        self.delivery_tag = ""  # "00:00:00:00"
        self.remote = ""  # undecorated number - '2'
        self.channel_handle = ""  # decorated - '[0,0]'
        self.channel_remote = ""  # decorated - '[1,2]'
        self.flow_deliverycnt = ""  # undecorated number - '50'
        self.flow_linkcredit = ""  # undecorated number - '100'
        self.flow_cnt_credit = ""  # decorated - '(50,100)'
        self.transfer_id = ""
        self.role = ""
        self.source = ""
        self.target = ""
        self.first = ""  # undecorated number - '10'
        self.last = ""  # undecorated number - '20'
        self.settled = ""  # Disposition or Transfer settled field
        self.snd_settle_mode = ""  # Attach
        self.rcv_settle_mode = ""  # Attach
        self.transfer_data = ""  # dehexified transfer data value
        self.is_policy_info = False

    def __repr__(self):
        return self._representation()

    def _representation(self):
        all = []
        all.append("web_show_str : '%s'" % self.web_show_str)
        all.append("name : '%s'" % self.name)
        all.append("conn_num : '%s'" % self.conn_num)
        all.append("conn_id : '%s'" % self.conn_id)
        all.append("channel : '%s'" % self.channel)
        all.append("direction : '%s'" % self.direction)
        all.append("described_type : '%s'" % self.described_type)
        all.append("handle : '%s'" % self.handle)
        all.append("delivery_id : '%s'" % self.delivery_id)
        all.append("delivery_tag : '%s'" % self.delivery_tag)
        all.append("remote : '%s'" % self.remote)
        all.append("channel_handle : '%s'" % self.channel_handle)
        all.append("channel_remote : '%s'" % self.channel_remote)
        all.append("flow_deliverycnt : '%s'" % self.flow_deliverycnt)
        all.append("flow_linkcredit : '%s'" % self.flow_linkcredit)
        all.append("flow_cnt_credit : '%s'" % self.flow_cnt_credit)
        all.append("transfer_id : '%s'" % self.transfer_id)
        all.append("role : '%s'" % self.role)
        all.append("source : '%s'" % self.source)
        all.append("target : '%s'" % self.target)
        all.append("first : '%s'" % self.first)
        all.append("last : '%s'" % self.last)
        all.append("settled : '%s'" % self.settled)
        all.append("transfer_data : '%s'" % self.transfer_data)
        return ('\n'.join(all))


class DescribedType():
    '''
    Given a line like:
        @typename(00) [key1=val1, ...]
    Extract the typename and create a map of the key-val pairs
    May recursively find embedded described types
    '''
    @staticmethod
    def is_dtype_name(name):
        '''
        Return true if the name is a pn_trace described type name
        :param name:
        :return:
        '''
        return ( name.startswith ( '@' ) and
                 '(' in name and
                 name.endswith ( ')' ) )

    @staticmethod
    def get_key_and_val(kvp):
        eqi = kvp.find('=')
        return kvp[:eqi], kvp[eqi + 1:]

    @staticmethod
    def dtype_name(name):
        if not DescribedType.is_dtype_name(name):
            raise ValueError("Name '%s' is not a described type name" % name)
        return name [ 1 : name.find ( '(' ) ]

    @staticmethod
    def dtype_number(name):
        if not DescribedType.is_dtype_name(name):
            raise ValueError("Name '%s' is not a described type name" % name)
        return int ( name [ name.find ( '(' ) + 1 : -1 ] )

    def __init__(self):
        self.dict = {}
        self.dtype_name = "unparsed"
        self.dtype_number = 0
        self.extra = []
        self.transfer_data_truncated = False

    def __repr__(self):
        return self._representation()

    def _representation(self):
        return "DescribedType %s( %d ) : %s" % (self.dtype_name, self.dtype_number, self.dict)

    def parse(self, _dtype, _line):
        self.dtype = _dtype
        self.line = _line
        self.dtype_name = DescribedType.dtype_name(self.dtype)
        self.dtype_number = DescribedType.dtype_number(self.dtype)

        ## stash transfer extra data keeping performative in .line
        is_transfer = self.dtype_name == "transfer"
        if is_transfer:
            fields = Splitter.split(self.line, is_transfer)
            t1 = fields.pop()
            t2 = fields.pop()
            if t1 == "(truncated)":
                t3 = fields.pop()
                self.extra.append(t3)
            self.extra.append(t2)
            self.extra.append(t1)
            self.line = ' '.join(fields)

        # strip leading '[' and trailing ']'
        if not ( self.line.startswith ( '[' ) and self.line.endswith ( ']' ) ) :
            raise ValueError("Described type not delimited with square brackets: '%s'" % _line)
        self.line = self.line[1:]
        self.line = self.line[:-1]

        # process fields
        fields = Splitter.split(self.line, is_transfer)
        while len ( fields ) > 0 and len ( fields [ 0 ] ) >  0:
            if not '=' in fields[0]:
                raise ValueError("Field does not contain equal sign '%s'" % fields[0])
            key, val = DescribedType.get_key_and_val( fields[0] )
            del fields[0]
            if DescribedType.is_dtype_name(val):
                # recursing to process subtype
                # pull subtype's data out of fields. The fields list belongs to parent.
                subfields = []
                if fields[0] == "[]" :
                    # degenerate case of empty subtype closing parent type
                    #  @disposition .. state=@accepted(36) []]
                    subfields.append("[]")
                    del fields[0]
                else :
                    while len ( fields ) > 0 :
                        if fields[0].endswith('],'):
                            subfields.append( fields[0][:-2] )
                            subfields.append( ']' )
                            del fields[0]
                            break
                        if fields[0].endswith(']'):
                            subfields.append( fields[0][:-1] )
                            subfields.append( ']' )
                            del fields[0]
                            break
                        subfields.append( fields[0] )
                        del fields[0]

                subtype = DescribedType()
                subtype.parse(val, ' '.join(subfields))
                self.dict[key] = subtype
            elif val.startswith( '{' ):
                # handle some embedded map: properties={:product=\"qpid-dispatch-router\", :version=\"1.3.0-SNAPSHOT\"}
                # pull subtype's data out of fields. The fields list belongs to parent.
                submap = {}
                skey, sval = DescribedType.get_key_and_val( fields[0][1:] )
                submap[skey] = sval
                del fields[0]
                while len ( fields ) > 0 :
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
    '''
    Grind through the log line and record some facts about it.
    * Constructor returns Null if the log line is to be ignored
    * Constructor args:
    ** router-name prefix letter A..Z
    ** lineno             line number
    ** line               the log line

   **
    '''
    server_trace_key = "SERVER (trace) ["
    policy_trace_key = "POLICY (trace) ["

    def sender_settle_mode_of(self, value):
        if value == "0":
            return "unsettled(0)"
        elif value == "1":
            return "settled(1)"
        elif value == "2":
            return "mixed(2)"   # default
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

        elif perf == 0x11:
            # Performative: begin [channel,remoteChannel]
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
            name = self.resdict_value(resdict, "name", "None")
            tmpsrc = self.resdict_value(resdict, "source", None)
            tmptgt = self.resdict_value(resdict, "target", None)
            res.snd_settle_mode = self.sender_settle_mode_of(resdict["snd-settle-mode"]) if "snd-settle-mode" in resdict else "mixed"
            res.rcv_settle_mode = self.receiver_settle_mode_of(resdict["rcv-settle-mode"]) if "rcv-settle-mode" in resdict else "first"
            if tmpsrc is not None:
                res.source = self.resdict_value(resdict, "address", "none")
            else:
                res.source = "none"
            if tmptgt is not None:
                res.target = self.resdict_value(resdict, "address", "none")
            else:
                res.target = "none"
            res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
            '''
            TODO:
            name = short_link_names.translate(name)
            res.source = short_endp_names.translate(res.source)
            res.target = short_endp_names.translate(res.target)
            res.snd_settle_mode = extract_name(tmpssm)
            res.rcv_settle_mode = extract_name(tmprsm)
            '''
            res.web_show_str = ("<strong>%s</strong> %s %s %s (source: %s, target: %s)" %
                                (res.name, colorize_bg(res.channel_handle), res.role, name, res.source, res.target))

        elif perf == 0x13:
            # Performative: flow [channel,handle]
            res.name = "flow"
            res.handle = resdict["handle"]
            res.flow_deliverycnt = self.resdict_value(resdict, "delivery-count", "0")
            res.flow_linkcredit = self.resdict_value(resdict, "link-credit", "0")
            res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
            res.flow_cnt_credit = "(%s,%s)" % (res.flow_deliverycnt, res.flow_linkcredit)
            res.web_show_str = "<strong>%s</strong> %s (%s,%s)" % (
                res.name, colorize_bg(res.channel_handle), res.flow_deliverycnt, res.flow_linkcredit)

        elif perf == 0x14:
            # Performative: transfer [channel,handle] (id)
            res.name = "transfer"
            res.handle = resdict["handle"]
            res.delivery_id = self.resdict_value(resdict, "delivery-id", "none")
            res.delivery_tag = self.resdict_value(resdict, "delivery-tag", "none")
            res.settled = self.resdict_value(resdict, "settled", None)
            v_aborted = self.resdict_value(resdict, "aborted", None)
            res.channel_handle = "[%s,%s]" % (res.channel, res.handle)
            aborted = ""
            if not v_aborted is None:
                aborted = " <span style=\"background-color:yellow\">aborted</span>" if v_aborted == '1' else ""
            res.web_show_str = "<strong>%s</strong>  %s (%s) %s" % (
                res.name, colorize_bg(res.channel_handle), res.delivery_id, aborted)

        elif perf == 0x15:
            # Performative: disposition [channel] (role first-last)
            res.name = "disposition"
            res.role = "receiver" if resdict["role"] == "true" else "sender"
            res.first = self.resdict_value(resdict, "first", "0")
            res.last = self.resdict_value(resdict, "last", res.first)
            res.settled = self.resdict_value(resdict, "settled", "true")
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

    def __new__(cls, *args, **kwargs):
        (prefix, lineno, line) = args
        if not (ParsedLogLine.server_trace_key in line or
                (ParsedLogLine.policy_trace_key in line and "lookup_user:" in line)): # open (not begin, attach)
            return None
        return object.__new__(cls, *args, **kwargs)

    def __init__(self, _prefix, _lineno, _line):
        '''
        Process a naked qpid-dispatch log line
        :param _prefix: The router prefix letter A, B, C, ...
        :param _lineno:
        :param _line:
        '''
        self.oline = _line        # original line
        self.prefix = _prefix     # router prefix
        self.lineno = _lineno     # log line number

        self.line = _line         # working line chopped, trimmed

        self.data = LogLineData() # parsed line fact store

        # strip optional trailing file:line field
        self.line = self.line.rstrip()
        if self.line.endswith(')'):
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
                raise ValueError("'%s' not found in line %s" % (self.server_trace_key, self.line))
            else:
                self.line = self.line[sti + len(self.policy_trace_key):]
                self.data.is_policy_info = True
        else:
            self.line = self.line[sti + len(self.server_trace_key):]
        ste = self.line.find(']')
        if ste < 0:
            print "Failed to parse line ", _lineno, " : ", _line
            raise ValueError("'%s' not found in line %s" % ("]", self.line))
        self.data.conn_num = self.line[:ste]
        self.line = self.line[ste + 1:]

        # create decorated connection id
        self.data.conn_id = self.prefix + "-" + self.data.conn_num

        # get the session (channel) number
        if self.line.startswith(':'):
            self.line = self.line[1:]
        sti = self.line.find(' ')
        if sti < 0:
            raise ValueError("'%s' not found in line %s" % (" ", self.line))
        if sti > 0:
            self.data.channel = self.line[:sti]
        self.line = self.line[sti + 1 :]
        self.line = self.line.lstrip()

        # cover for traces that don't get any better
        self.data.web_show_str = ("<strong>%s</strong>" % self.line)

        # policy lines have no direction and described type fields
        if self.data.is_policy_info:
            return

        # direction
        if self.line.startswith('<') or self.line.startswith('-'):
            self.data.direction = self.line[:2]
            self.line = self.line[3:]
            self.data.web_show_str = ("<strong>%s</strong>" % self.line)

        # extract fields with list data
        fields = Splitter.split(self.line)
        dname = fields[0]
        if DescribedType.is_dtype_name ( dname ) :
            del fields[0]
            self.data.described_type.parse(dname, ' '.join(fields))
            # data fron incoming line is now parsed out into facts in .data
            # Now cook the data to get useful displays
            self.extract_facts()


if __name__ == "__main__":

    data_source = TestData()
    data = data_source.data()
    try:
        for i in range(len(data)):
            temp = ParsedLogLine('A', i, data[i])
            print temp.datetime, temp.data.conn_id, temp.data.direction, temp.data.web_show_str
        pass
    except:
        traceback.print_exc(file=sys.stdout)
        pass

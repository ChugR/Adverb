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

import os
import sys
import xml.etree.ElementTree as ET
#import time

import unittest
from unittest import TestCase
try:
  from unittest import SkipTest
except:
  try:
    from unittest2 import SkipTest
  except:
    class SkipTest(Exception):
      pass

# import adverb from parent directory
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(cwd))
import adverb
from adverb import ExitStatus as ExitStatus
from adverb import PerformativeInfo as PI

def get_amqp_proto(packet, which=1):
    '''
    Find the AMQP proto decode part of the packet
    :param packet:  pdml packet exposed by ElementTree
    :param which: Packets hold many protocol decodes.
    :return: the proto or None
    '''
    protos = packet.findall('proto')
    found = 0
    for proto in protos:
        if proto.get('name') == 'amqp':
            found += 1
            if found == which:
                return proto
    return None


class AmqpProtoDecodeTest(unittest.TestCase):
    def setUp(self):
        # Read a known pdml file
        self.tree = ET.parse(os.path.abspath(os.path.join(cwd, "data/t1-amqp.pdml")))
        self.root = self.tree.getroot()
        self.packets = self.root.findall("packet")

    def tearDown(self):
        self.tree = None
        self.root = None
        self.packets = None

    def test_00_check_data_file(self):
        self.assertEqual(26, len(self.packets))

    def test_01_other_init(self):
        packet_i = 0
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto into PerformativeInfo")
        self.assertTrue('init' == pi.name, 'Expected init ')
        self.assertTrue('init' in pi.web_show_str, 'Expected init')
        self.assertTrue('1.0.0' in pi.web_show_str, 'Expected version 1.0.0')

        proto = get_amqp_proto(self.packets[packet_i], 2)
        self.assertIsNone(proto, "There is only one proto in this packet")

    def test_16_client_open(self):
        packet_i = 1
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto into PerformativeInfo")
        self.assertTrue('open' == pi.name, 'Expected open')
        self.assertTrue('open' in pi.web_show_str, 'Expected open')
        self.assertTrue('[0]' in pi.web_show_str, 'Expected channel [0]')

    def test_17_client_begin(self):
        packet_i = 2
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto begin PerformativeInfo")
        self.assertTrue('begin' == pi.name, 'Expected begin')
        self.assertTrue('null' == pi.remote, 'Expected no remote channel')
        self.assertTrue('begin' in pi.web_show_str, 'Expected begin')
        self.assertTrue('0' in pi.web_show_str, 'Expected channel [0]')

    def test_18_client_attach(self):
        packet_i = 3
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto attach PerformativeInfo")
        self.assertTrue('attach' == pi.name, 'Expected attach')
        self.assertTrue('attach' in pi.web_show_str, 'Expected begin')
        self.assertTrue('0' == pi.channel, 'Expected channel 0')
        self.assertTrue('0' == pi.handle, 'Expected handle 0')
        self.assertTrue('[0,0]' == pi.channel_handle, 'Expected channel,handle 0,0')
        self.assertTrue('sender' == pi.role, 'Expected sender')
        self.assertTrue('null' == pi.source, 'Expected null source')
        self.assertTrue('q1' == pi.target)

    def test_18_client_attach2(self):
        packet_i = 4
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")

        proto = get_amqp_proto(self.packets[packet_i], 2)
        self.assertIsNotNone(proto, ("Could not find amqp proto 2 in packet %s" % packet_i))
        self.assertTrue('init' == pi.name, 'Expected init')

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
        self.assertTrue('open' == pi.name, 'Expected open')

    def test_19_flow(self):
        packet_i = 17
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
        # print ("pi: %s" % pi)
        self.assertTrue('flow' == pi.name, 'Expected flow')
        self.assertTrue('0' == pi.channel, 'Expected channel 0')
        self.assertTrue('0' == pi.handle, 'Expected handle 0')
        self.assertTrue('[0,0]' == pi.channel_handle, 'Expected channel,handle 0,0')
        self.assertTrue('0' == pi.flow_deliverycnt, 'Expected 0 deliverycnt')
        self.assertTrue('200' == pi.flow_linkcredit, 'Expected 200 credits')
        self.assertTrue('(0,200)' == pi.flow_cnt_credit, 'Expected 0,200 count,credit')

    def test_20_client_transfer(self):
        packet_i = 6
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
        self.assertTrue('transfer' == pi.name, 'Expected transfer')
        self.assertTrue('0' == pi.channel, 'Expected channel 0')
        self.assertTrue('0' == pi.handle, 'Expected handle 0')
        self.assertTrue('[0,0]' == pi.channel_handle, 'Expected channel,handle 0,0')

    def test_21_disposition(self):
        packet_i = 7
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
        self.assertTrue('disposition' == pi.name, 'Expected disposition')
        self.assertTrue('0' == pi.channel, 'Expected channel 0')
        self.assertTrue('receiver' == pi.role, 'Expected role receiver')
        self.assertTrue('0' == pi.first, 'Expected first : 0')
        self.assertTrue('0' == pi.last, 'Expected last : 0')

    def test_22_detach(self):
        packet_i = 8
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
        self.assertTrue('detach' == pi.name, 'Expected detach')
        self.assertTrue('0' == pi.channel, 'Expected channel 0')
        self.assertTrue('0' == pi.handle, 'Expected handle 0')
        self.assertTrue('[0,0]' == pi.channel_handle, 'Expected channel,handle 0,0')

    def test_23_end(self):
        packet_i = 23 # packet 23 holds performative 23? Hmmm.
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
        self.assertTrue('end' == pi.name, 'Expected end')
        self.assertTrue('0' == pi.channel, 'Expected channel 0')

    def test_24_close(self):
        packet_i = 24
        proto = get_amqp_proto(self.packets[packet_i])
        self.assertIsNotNone(proto, ("Could not find amqp proto in packet %s" % packet_i))

        pi = adverb.amqp_decode(proto)
        self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
        self.assertTrue('close' == pi.name, 'Expected close')
        self.assertTrue('0' == pi.channel, 'Expected channel 0')

    def debug_datafile_test_dump(self):
        '''
        Debug me. Rename this function to test_dump to see a dump
        of all the performatives in the test file.
        :return:
        '''
        for packet_i in range(25):
            proto_i = 1
            proto = get_amqp_proto(self.packets[packet_i], proto_i)
            if not proto is None:
                pi = adverb.amqp_decode(proto)
                self.assertIsNotNone(pi, "Could not decode proto init PerformativeInfo")
                print ("\nPacket %d, proto %d\n%s" %(packet_i, proto_i, pi))


if __name__ == "__main__":
    unittest.main()

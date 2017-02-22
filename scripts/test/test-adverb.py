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

    def test_check_data_file(self):
        self.assertEqual(26, len(self.packets))

if __name__ == "__main__":
    unittest.main()

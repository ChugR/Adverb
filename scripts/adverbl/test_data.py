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

'''
TODO: Get these lines to parse so they are not rejected by adverbl:

Priceless.
 Timestamp has 'Dow, mon, day, hh:mm:ss, year'
 Log entry is a truncated transfer
  Transfer is from 'qdstat --log' where 
  the log line being sent logs an 'attach' and a 'flow'
Mon Aug 13 11:38:16 2018 SERVER (none) [30]:0 -> @transfer(20) [handle=1, delivery-id=0, delivery-tag=b"\x1d\x00\x00\x00\x00\x00\x00\x00", message-format=0, settled=true] (54542) "\x00Sp\xd0\x00\x00\x00\x05\x00\x00\x00\x01B\x00Ss\xd0\x00\x00\x007\x00\x00\x00\x06@@\xa1*amqp:/_topo/0/log-log/temp.gbxqFr6bjZ5EOrY@@\xa1\x011\x00St\xd1\x00\x00\x00,\x00\x00\x00\x04\xa1\x11statusDescription\xa1\x02OK\xa1\x0astatusCodeq\x00\x00\x00\xc8\x00Sw\xd0\x00\x00\xd4\x86\x00\x00\x00\xc8\xd0\x00\x00\x01\xc8\x00\x00\x00\x06\xa1\x06SERVER\xa1\x04none\xb1\x00\x00\x01\x7f[22]:0 -> @attach(18) [name="28b2f390-f2ed-4d04-b0b1-bf0c000e8b3e-$management", handle=0, role=true, snd-settle-mode=2, rcv-settle-mode=0, source=@source(40) [durable=0, expiry-policy=:"session-end", timeout=0, dynamic=false], target=@target(41) [address="$management", durable=0, expiry-policy=:"session-end", timeout=0, dynamic=false], initial-delivery-count=0, max-message-size=0]\xa1)/home/chug/git/qpid-dispatch/src/server.cTjq[q\xa5\xe2\xd0\x00\x00\x00\xf4\x00\x00\x00\x06\xa1\x06SERVER\xa1\x04none\xa1\xae[22]:0 -> @flow(19) [next-incoming-id=0, incoming-window=2147483647, next-outgoing-id=0, outgoing-window=2147483647, handle=0, delivery"... (truncated)

'''
class TestData():
    '''
    Extract list of test log lines from a data file.
    The file holds literal log lines from some noteworthy test logs.
    Embedding the lines as a data statement involves escaping double quotes
    and runs the risk of corrupting the data.
    '''
    def __init__(self):
        with open('adverbl_test_data.txt', 'r') as f:
            self.lines = [line.rstrip('\n') for line in f]

    def data(self):
        return self.lines


if __name__ == "__main__":

    try:
        datasource = TestData()
        for line in datasource.data():
            print (line)
        pass
    except:
        traceback.print_exc(file=sys.stdout)
        pass
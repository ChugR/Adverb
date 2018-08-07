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

Space in delivery tag
2018-08-03 10:59:37.457537 -0400 SERVER (trace) [5]:0 -> @transfer(20) [handle=0, delivery-id=6, delivery-tag=b" \x00\x00\x00\x00\x00\x00\x00", message-format=0, settled=true] (258) "\x00Sp\xd0\x00\x00\x00\x05\x00\x00\x00\x01B\x00Sr\xd1\x00\x00\x00_\x00\x00\x00\x08\xa3\x0ex-opt-qd.trace\xd0\x00\x00\x00\x13\x00\x00\x00\x03\xa1\x030/C\xa1\x030/B\xa1\x030/A\xa3\x10x-opt-qd.ingress\xa1\x030/C\xa3\x09x-opt-qd.\xa1\x01X\xa3\x09x-opt-qd.\xa1\x01X\x00Ss\xd0\x00\x00\x00%\x00\x00\x00\x06@@\xa1\x1aamqp:/_topo/0/all/qdrouter@@@\x00St\xd1\x00\x00\x00\x10\x00\x00\x00\x02\xa1\x06opcode\xa1\x02RA\x00Sw\xd1\x00\x00\x00A\x00\x00\x00\x0c\xa1\x06ls_seqT\x01\xa1\x02pvT\x01\xa1\x04area\xa1\x010\xa1\x08instanceq[dm\xd7\xa1\x0amobile_seqT\x00\xa1\x02id\xa1\x01C" (/home/chug/git/qpid-dispatch/src/server.c:106)

Double quote in delivery tag
2018-08-03 10:59:48.006844 -0400 SERVER (trace) [6]:0 -> @transfer(20) [handle=0, delivery-id=447, delivery-tag=b""\x02\x00\x00\x00\x00\x00\x00", message-format=0, settled=true] (208) "\x00Sp\xd0\x00\x00\x00\x05\x00\x00\x00\x01B\x00Sr\xd1\x00\x00\x00U\x00\x00\x00\x08\xa3\x0ex-opt-qd.trace\xd0\x00\x00\x00\x09\x00\x00\x00\x01\xa1\x030/A\xa3\x10x-opt-qd.ingress\xa1\x030/A\xa3\x09x-opt-qd.\xa1\x01X\xa3\x09x-opt-qd.\xa1\x01X\x00Ss\xd0\x00\x00\x00#\x00\x00\x00\x06@@\xa1\x18amqp:/_topo/0/D/qdrouter@@@\x00St\xd1\x00\x00\x00\x11\x00\x00\x00\x02\xa1\x06opcode\xa1\x03LSR\x00Sw\xd1\x00\x00\x00\x1a\x00\x00\x00\x06\xa1\x02pvT\x01\xa1\x02id\xa1\x01A\xa1\x04area\xa1\x010" (/home/chug/git/qpid-dispatch/src/server.c:106)

Naked space in message content
2018-08-03 10:59:49.480073 -0400 SERVER (trace) [7]:0 -> @transfer(20) [handle=0, delivery-id=3, delivery-tag=b"\x8b\x01\x00\x00\x00\x00\x00\x00", message-format=0, settled=true] (233) "\x00Sp\xd0\x00\x00\x00\x05\x00\x00\x00\x01B\x00Sr\xd1\x00\x00\x00U\x00\x00\x00\x08\xa3\x0ex-opt-qd.trace\xd0\x00\x00\x00\x09\x00\x00\x00\x01\xa1\x030/C\xa3\x10x-opt-qd.ingress\xa1\x030/C\xa3\x09x-opt-qd.\xa1\x01X\xa3\x09x-opt-qd.\xa1\x01X\x00Ss\xd0\x00\x00\x00/\x00\x00\x00\x06@@\xa1$amqp:/_topo/0/C/temp.y0iWM_zBNSbDane@@@\x00St\xd1\x00\x00\x004\x00\x00\x00\x04\xa1\x11statusDescription\xa1\x0aNo Content\xa1\x0astatusCodeq\x00\x00\x00\xcc\x00Sw\xd1\x00\x00\x00\x04\x00\x00\x00\x00" (/home/chug/git/qpid-dispatch/src/server.c:106)

Difficult formatting when content is truncated
2018-08-03 10:59:43.485362 -0400 SERVER (trace) [8]:0 -> @transfer(20) [handle=0, delivery-id=3, delivery-tag=b"o\x00\x00\x00\x00\x00\x00\x00", message-format=0, settled=true] (1589) "\x00Sp\xd0\x00\x00\x00\x05\x00\x00\x00\x01B\x00Ss\xd0\x00\x00\x00/\x00\x00\x00\x06@@\xa1$amqp:/_topo/0/D/temp._HHAoiYZ39HlEEH@@@\x00St\xd1\x00\x00\x00,\x00\x00\x00\x04\xa1\x11statusDescription\xa1\x02OK\xa1\x0astatusCodeq\x00\x00\x00\xc8\x00Sw\xd1\x00\x00\x05\xb5\x00\x00\x00\x04\xa1\x0eattributeNames\xd0\x00\x00\x00\x95\x00\x00\x00\x0b\xa1\x08linkType\xa1\x07linkDir\xa1\x08linkName\xa1\x0aowningAddr\xa1\x08capacity\xa1\x10undeliveredCount\xa1\x0eunsettledCount\xa1\x0dacceptedCount\xa1\x0drejectedCount\xa1\x0dreleasedCount\xa1\x0dmodifiedCount\xa1\x07results\xd0\x00\x00\x04\xf9\x00\x00\x00\x10\xd0\x00\x00\x00<\x00\x00\x00\x0b\xa1\x0erouter-control\xa1\x02in\xa1\x16qdlink.EZD43Jm5VvSht0w@p\x00\x00\x03\xe8DDDDDD\xd0\x00\x00\x00F\x00\x00\x00\x0b\xa1\x0erouter-control\xa1\x03out\xa1\x16qdlink.STppD563DOcP2ZR\xa1\x08Lqdhellop\x00\x00\x03\xe8DDDDDD\xd0\x00\x00\x00:\x00\x00\x00\x0b\xa1\x0cinter-router\xa1\x02in\xa1\x16qdlink.inIy3q1zJObSUhB@p\x00\x00\x03\xe8DDDDDD\xd0\x00\x00\x00<\x00\x00\x00\x0b\xa1\x0cinter-route"... (truncated) (/home/chug/git/qpid-dispatch/src/server.c:106)
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
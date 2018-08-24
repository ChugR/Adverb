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


class LogLinesOoo():
    '''
    Track log lines out of order
    * make histogram of how far out of order
    * <10uS, <100uS, <1mS, <10mS, <100mS, >= 1S
    * track worst case
    '''
    def __init__(self, _prefix):
        self.prefix = _prefix
        self.histogram = [0,0,0,0,0,0,0]
        self.deltas = []
        for i in range(6):
            self.deltas.append(timedelta(microseconds=(10.0 ** (i+1))))
        self.deltas.append(timedelta(10000)) # many days
        self.high_delta = timedelta(0)
        self.high_lineno = 0
        self.last_datetime = None

    def process_line(self, lineno, line):
        if not (line.startswith("20") and len(line) >= 26):
            return
        try:
            dt = datetime.strptime(line[:26], '%Y-%m-%d %H:%M:%S.%f')
        except:
            return
        if self.last_datetime is None:
            self.last_datetime = dt
        else:
            if self.last_datetime > dt:
                delta = self.last_datetime - dt
                if delta > self.high_delta:
                    self.high_delta = delta
                    self.high_lineno = lineno
                for i in range(7):
                    if delta < self.deltas[i]:
                        self.histogram[i] += 1
                        break;
            self.last_datetime = dt

    def titles(self):
        return [ "< 10uS", "< 100uS", "< 1mS", "< 10mS", "< 100mS", "< 1S", ">= 1S" ]

if __name__ == "__main__":

    ooo = LogLinesOoo('A')

    ooo.process_line(1, "2018-07-20 10:58:40.176528 -0400")
    ooo.process_line(2, "2018-07-20 10:58:40.176628 -0400")
    ooo.process_line(3, "2018-07-20 10:58:40.176618 -0400 -10")
    ooo.process_line(4, "2018-07-20 10:58:40.176869 -0400")
    ooo.process_line(5, "2018-07-20 10:58:40.176769 -0400 -100")
    ooo.process_line(6, "2018-07-20 10:58:40.178470 -0400")
    ooo.process_line(7, "2018-07-20 10:58:39.178470 -0400 -1S")
    ooo.process_line(8, "wooba")

    print ("Expect [0,1,1,0,0,0,1]: %s" % ooo.histogram)
    print ("Expect max 1S on line 7 : %s on line %d" % (ooo.high_delta, ooo.high_lineno))
    print (ooo.titles())
    pass

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
import string
from adverbl_test_data import *


class Splitter():
    '''
    '''
    @staticmethod
    def split(line, in_transfer=False):
        if in_transfer or "@transfer(20)" in line:
            fields = string.split(line)
            nf = []
            for field in fields:
                if field.endswith(','):
                    nf.append(field[:-1])
                elif not field == '\"':
                    nf.append(field)
                else:
                    pass
            return nf
        result = []
        indqs = False
        pending_comma = False
        res = ""
        for i in range(len(line)):
            c = line[i]
            if c == '\"':
                if pending_comma:
                    res += ','
                    pending_comma = False
                indqs = not indqs
                res += c
            elif c == ',':
                pending_comma = True
            elif c == ' ':
                    if indqs:
                        if pending_comma:
                            res += ','
                            pending_comma = False
                        res += c
                    else:
                        if not res == '':
                            if pending_comma:
                                pending_comma = False
                            result.append(res)
                            res = ''
            else:
                res += c
        if not res == '':
            result.append(res)
        if indqs:
            raise ValueError("SPLIT ODD QUOTES: %s", line)
        #print ("SPLIT: line: %s" % line)
        #print ("SPLIT: flds: %s" % result)
        return result


if __name__ == "__main__":

    data_source = TestData()
    data = data_source.data()
    try:
        for line in data:
            print Splitter.split(line)
            print ""
        pass
    except:
        traceback.print_exc(file=sys.stdout)
        pass
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

# Common data storage and utilities

import sys

import nicknamer

class Common():

    # first letter of the connection names
    log_char_base = 'A'

    # number of logs processed
    n_logs = 0

    # array of file name strings from command line
    # len=n_logs
    log_fns = []

    # discovered router container names
    # len=n_logs
    router_ids = [] # raw long names

    # list of router-instance lists
    # [[A0, A1], [B0], [C0, C1, C2]]
    routers = []

    # ordered list of connection names across all routers
    all_conn_names = []

    shorteners = nicknamer.Shorteners()

def log_letter_of(idx):
    '''
    Return the letter A, B, C, ... from the index 0..n
    :param idx:
    :return: A..Z
    '''
    if idx >= 26:
        sys.exit('ERROR: too many log files')
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[idx]


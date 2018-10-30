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

    # router display names shortened with popups
    router_display_names = []

    # list of router-instance lists
    # [[A0, A1], [B0], [C0, C1, C2]]
    routers = []

    # ordered list of connection names across all routers
    all_conn_names = []

    # conn_details_map -
    # key=conn_id, val=ConnectionDetail for that connection
    conn_details_map = {}

    # mapping of connected routers by connection id
    # A0_1 is connected to B3_2
    # key = full conn_id 'A0_5'
    # val = full conn_id 'B0_8'
    # note names[key]=val and names[val]=key mutual reference
    conn_peers_connid = {}

    # short display name for peer indexed by connection id
    # A0_1 maps to B's container_name nickname
    conn_peers_display = {}

    # conn_to_frame_map - global list for easier iteration in main
    # key = conn_id full A0_3
    # val = list of plf lines
    conn_to_frame_map = {}

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

def index_of_log_letter(letter):
    '''
    Return the index 0..25 of the firster letter of the 'letter' string
    Raise error if out of range
    :param letter:
    :return:
    '''
    val = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(letter[0].upper())
    if val < 0 or val > 25:
        raise ValueError("index_of_log_letter Invalid log letter: %s", letter)
    return val

class RestartRec():
    def __init__(self, _id, _router, _event, _datetime):
        self.id = _id
        self.router = _router
        self.event = _event
        self.datetime = _datetime


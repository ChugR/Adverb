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
from adverbl_name_shortener import *

class adverbl_globals:

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
    router_display_names = []
    router_ids_by_prefix = {}
    router_display_by_prefix = {}

    # list of list of connections as discovered in files
    # [ [1,2,3], [1,3,2,4]], that is: [[A's conns], [B's conns], ...]
    # Each router's conn_list is sorted by connection number
    # but is not necessarily a packed sequence.
    conn_lists = []

    # connection peers
    # key=decorated name 'A_3'
    conn_peers = {}         # val = peer container-id
    conn_peers_popup = {}   # val = peer display name with popup
    conn_peers_connid = {}  # val = peer connection id
    conn_dirs = {}          # val = direction arrow

    # ordered list of connection names across all routers
    all_conn_names = []

    # create a map with key=connectionId, val=[list of associated frames])
    conn_to_frame_map = {}

    # details map populated by per-connection, per-session, per-link details
    conn_details_map = {}

    shorteners = Shorteners()

    all_details = None

    # router_ls lines
    router_ls = []

    def log_letter_of(self, idx):
        '''
        Return the letter A, B, C, ... from the index 0..n
        :param idx:
        :return: A..Z
        '''
        if idx >= 26:
            sys.exit('ERROR: too many log files')
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[idx]


    def conn_id_of(self, log_letter, conn_num):
        '''
        Construct the decorated connection id given a log letter and connection number
        :param log_letter:
        :param conn_num:
        :return:
        '''
        return log_letter + "_" + str(conn_num)

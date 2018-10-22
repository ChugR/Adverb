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

# A single router log file may contain data from multiple instances of
# that router booting and running. Thus there may be several different
# connections labeled [0] and these connections may be to different
# routers on each run.
#
# The 'router' class defined here represents a single boot-and-run
# instance from the log file.
#

from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import traceback
import cgi
import ast

from adverbl_log_parser import *
from adverbl_name_shortener import *
from adverbl_globals import *
from adverbl_per_link_details import *

class Router():
    '''A single dispatch boot-and-run instance from a log file'''

    def __init__(self, _log_index, _instance):
        log_index = _log_index   # 0=A, 1=B, ...
        instance = _instance     # log file instance of router

        # lines - the raw log lines
        lines = []

        # conn_list - List of connections discovered in log lines
        # Sorted in ascending order. Not necessarily in packed sequence.
        conn_list = []

        # conn_peer - peer container long name
        #   key= connection id '1', '2'
        #   val= original peer container name
        conn_peer = {}

        # conn_peer_display - peer container display name
        #   key= connection id '1', '2'
        #   val= display name
        # Peer display name shortened with popup if necessary
        conn_peer_display = {}

        # conn_peer_connid - display value for peer's connection id
        #   key= connection id '1', '2'
        #   val= peer's connid 'A.0_3', 'D.3_18'
        conn_peer_connid = {}

        # conn_dir - arrow indicating connection origin direction
        #   key= connection id '1', '2'
        #   val= '<-' peer created conn, '->' router created conn
        conn_dir = {}

        # conn_details - AMQP analysis
        #   key= connection id '1', '2'
        #   val= ConnectionDetails
        # for each connection, for each session, for each link:
        #   what happened
        conn_details = {}

        # router_ls - link state 'ROUTER_LS (info)' lines
        router_ls = []




if __name__ == "__main__":
    try:
        pass
    except:
        traceback.print_exc(file=sys.stdout)
        pass

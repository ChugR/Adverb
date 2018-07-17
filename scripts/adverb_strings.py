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

#
# Various web symbols and canned strings
#
def nbsp():
    '''
    :return: HTML Non-breaking space
    '''
    return "&#160;"

def shaded_background_begin():
    '''
    :return: HTML leading for shaded span
    '''
    return "<span style=\"background-color:#e0e0e0\">"

def shaded_background_end():
    '''
    :return: HTML trailing for shaded span
    '''
    return "</span>"

def l_arrow():
    '''
    :return: Text left arrow (HTML arrow is ugly)
    '''
    return "<-"

def r_arrow():
    '''
    :return: Text right arror
    '''
    return "->"

def l_arrow_spaced():
    '''
    :return: Spaced text left arrow
    '''
    return nbsp() + l_arrow() + nbsp()

def r_arrow_spaced():
    '''
    :return: Spaced text right arrow
    '''
    return nbsp() + r_arrow() + nbsp()

def l_arrow_str():
    '''
    :return: Spaced left arrow with a space for visual direction clue
    '''
    return l_arrow_spaced() + nbsp()

def r_arrow_str():
    '''
    :return: Spaced right arrow with a space for visual direction clue
    '''
    return nbsp() + r_arrow_spaced()

def lozenge():
    '''
    :return: HTML document lozenge character
    '''
    return "&#9674;"

def double_lozenge():
    '''
    :return: two HTML document lozenge characters
    '''
    return lozenge() + lozenge()

def leading(level):
    '''
    Calculate some leading space based on indent level.
    There is no magic about these indents. They just have to look nice.
    Only indent so far.
    @type level: int
    :param level: desired indent
    :return: a string of Non-breaking spaces
    '''
    sizes = [3, 8, 13, 18, 23, 27, 31, 35, 39]
    if level < len(sizes):
        return nbsp() * sizes[level]
    return nbsp() * 39

#
# Given a hex ascii string, return printable string w/o control codes
def dehexify_no_control_chars(valuetext):
    '''
    Return a printable string from a blob of hex characters.
    Non printable ascii control chars or chars >= 127 are printed as '.'.
    :param valuetext:
    :return:
    '''
    tmp = valuetext.decode("hex")
    res = ""
    for ch in tmp:
        if ord(ch) < 32 or ord(ch) >= 127:
            ch = '.'
        res += ch
    return res

if __name__ == "__main__":
    pass


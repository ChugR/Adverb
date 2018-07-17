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

class ShortNames():
    '''
    Name shortener.
    The short name for display is "name_" + index(longName)
    Embellish the display name with an html popup
    Link and endpoint names, and data are tracked separately
    Names longer than threshold are shortened
    Each class has a prefix used when the table is dumped as HTML
    '''
    def __init__(self, prefixText):
        self.longnames = []
        self.prefix = prefixText
        self.threshold = 25

    def translate(self, lname):
        '''
        Translate a long name into a short name, maybe.
        Memorize all names, translated or not
        :param lname: the name
        :return: If shortened HTML string of shortened name with popup containing long name else
        not-so-long name.
        '''
        idx = 0
        try:
            idx = self.longnames.index(lname)
        except:
            self.longnames.append(lname)
            idx = self.longnames.index(lname)
        # return as-given if short enough
        if len(lname) < self.threshold:
            return lname
        return "<span title=\"" + lname + "\">" + self.prefix + "_" + str(idx) + "</span>"

    def htmlDump(self):
        '''
        Print the name table as an unnumbered list to stdout
        :return: null
        '''
        if len(self.longnames) > 0:
            print "<h3>" + self.prefix + " Name Index</h3>"
            print "<ul>"
            for i in range(0, len(self.longnames)):
                print ("<li> " + self.prefix + "_" + str(i) + " - " + self.longnames[i] + "</li>")
            print "</ul>"

if __name__ == "__main__":
    pass

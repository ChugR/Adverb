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

import cgi

class ShortNames():
    '''
    Name shortener.
    The short name for display is "name_" + index(longName)
    Embellish the display name with an html popup
    Link and endpoint names, and data are tracked separately
    Names longer than threshold are shortened
    Each class has a prefix used when the table is dumped as HTML
    '''
    def __init__(self, prefixText, _threshold=25):
        self.longnames = []
        self.prefix = prefixText
        self.threshold = _threshold

    def translate(self, lname, show_popup=False):
        '''
        Translate a long name into a short name, maybe.
        Memorize all names, translated or not
        :param lname: the name
        :return: If shortened HTML string of shortened name with popup containing long name else
        not-so-long name.
        '''
        idx = 0
        if lname.startswith("\""):
            lname = lname[1:-1]
        try:
            idx = self.longnames.index(lname)
        except:
            self.longnames.append(lname)
            idx = self.longnames.index(lname)
        # return as-given if short enough
        if len(lname) < self.threshold:
            return lname
        if show_popup:
            return "<span title=\"" + cgi.escape(lname) + "\">" + self.prefix + "_" + str(idx) + "</span>"
        else:
            return self.prefix + "_" + str(idx)

    def len(self):
        return len(self.longnames)

    def prefix(self):
        return self.prefix

    def shortname(self, idx):
        name = self.longnames[idx]
        if len(name) < self.threshold:
            return name
        return self.prefix + "_" + str(idx)

    def longname(self, idx, cgi_escape=False):
        '''
        Get the cgi.escape'd long name
        :param idx:
        :param cgi_escape: true if caller wants the string for html display
        :return:
        '''
        return cgi.escape(self.longnames[idx]) if cgi_escape else self.longnames[idx]

    def htmlDump(self, with_link=False):
        '''
        Print the name table as an unnumbered list to stdout
        long names are cgi.escape'd
        :param with_link: true if link name link name is hyperlinked targeting itself
        :return: null
        '''
        if len(self.longnames) > 0:
            print "<h3>" + self.prefix + " Name Index</h3>"
            print "<ul>"
            for i in range(0, len(self.longnames)):
                name = self.prefix + "_" + str(i)
                if with_link:
                    name = "<a href=\"#%s\">%s</a>" % (name, name)
                print ("<li> " + name + " - " + cgi.escape(self.longnames[i]) + "</li>")
            print "</ul>"


class Shorteners():
    def __init__(self):
        self.short_link_names = ShortNames("link", 5)
        self.short_endp_names = ShortNames("endpoint")
        self.short_data_names = ShortNames("transfer")


if __name__ == "__main__":
    pass
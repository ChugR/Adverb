#  Adverbl - Render qpid-dispatch log files

Adverbl is a spinoff of the base Adverb that uses qpid-dispatch log 
files as the data source. Adverbl is a pure, local Python processing
engine that does not require wireshark.

## Apache License, Version 2.0

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License.  You may obtain a copy of the
License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.  See the License for the
specific language governing permissions and limitations under the License.


## Concepts

### The basics

* Enable router logging

The routers need to generate proper logging for Adverbl. 
At a minimum the router configuration must specify:

    log {
      module: SERVER
      enable: trace+
      outputFile: somefile.log
      includeTimestamp: yes
    }

Include the same settings for module POLICY in order for Adverbl to 
display connection authenticated user names and connection hosts.

* Run your tests to populate log files

This generates the input data for Adverbl.

* Run Adverbl to generate web content

    adverbl somefile.log > somefile.html

* Profit

    firefox somefile.html

###  Advanced

* Merging multiple qpid-dispatch log files

Adverbl accepts multiple log files names in the command line and
merges the log data according to the router log timestamps.

    adverbl A.log B.log C.log > abc.html

Note that the qpid-dispatch host system clocks for merged log files
must be synchronized to within a few microseconds in order for the
result to be useful. This is easiest to achieve when the routers are
run on the same CPU core on a single system.

Adverbl usually does a decent job merging log files created within a
qpid-dispatch self test.

* Wow, that's a lot of data

Indeed it is. Good luck figuring it out.

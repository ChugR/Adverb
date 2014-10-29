Adverb - a project to distill Wireshark trace data into web pages
that show details of the AMQP protocol.

The data flow starts with a .pcapng file. This can be created by
Wireshark or some other network capture tool. This file captures
the binary AMQP traffic of interest.

Next the data is processed by tshark (terminal shark) to produce
a .pdml file, which is like .xml for protocol data.

Finally the pdml is processed by a script that emits javascript html
that a browser displays.

In its current form Adverb is set up to be a cgi-bin web service
and consists of three files:

  scripts/html/adverb.html   - The server web form
  scripts/cgi-bin/adverb.sh  - Bash script to process form data:
                                * use tshark to generate pdml
                                * run adverb.py to generate html
  scripts/adverb.py          - Python code to generate html from pdml

An example web page is available to demonstrate the output.

  example/dispatch-router-test.pcapng.html

  Load this file into your browser to see a real-world dispatch router
  test in progress. Highlights include:

  * Dozens of connections identified by host address:port pairs.
  * Each connection shows the number of collected network frames.
  * Connections are highlighted in color to help identify them.
  * Each connections's frames may be shown or hidden independently.
  * Six or seven hunderd AMQP frames are captured.
  * Each frame has:
    - Expand buttons for high and low levels of detail.
    - The relative time stamp of the packet in microseconds.
    - The frame number in the original .pcapng capture file.
    - The host:port pair for the connection. Originating host is highlighted.
    - The performatives or methods for the frame each with extra details.
  * A legend describing the display details.

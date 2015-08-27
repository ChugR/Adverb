#  Adverb - distill AMQP net trace into web page

Wireshark is a great tool for capturing and viewing network traces. When it comes to AMQP traces, however, it's difficult to make sense of the larger picture of the protocol operation. All of the details are there but the general flow of AMQP connection and link activity has to be pieced together with a lot of clicks in Wireshark.

Welcome to Adverb. Adverb is tuned to AMQP and helpfully summarizes AMQP protocol activity on an interactive web page. An Adverb web page is laid out with:

* Page controls
* Connection data display controls
* AMQP Frames
* Decode legend and notes

For instance, this [simple example](http://htmlpreview.github.io/?https://github.com/ChugR/Adverb/blob/master/example/helloworld.html) illustrates some of Adverb's basic capabilities.

## Data Flow

Adverb can be used as a web server or as a stand-alone CLI process. The data flow for both cases is the same:

#### Before running Adverb
* Start with a .pcapng file. This can be created by
Wireshark or some other network capture tool. This file holds
the binary AMQP traffic of interest.

#### Work Adverb performs

* Process the capture file with *tshark* (terminal shark) to produce
a .pdml file, which is like .xml for protocol data.

* Process the pdml file with a script that emits javascript html
that a browser displays.

The web pages are indexed and metadata provides high level views of what's going on.

## As a Web Server

As a cgi-bin web service Adverb consists of three files:

*  scripts/html/adverb.html   - The server web form
*  scripts/cgi-bin/adverb.sh  - Bash script to process form data:
 * use tshark to generate pdml
 * run adverb.py to generate html
* scripts/adverb.py          - Python code to generate html from pdml. This is Adverb's real business logic.

The web service is convenient for doing small, quick traces.

* Run Wireshark; capture test traffic; save the .pcapng file.
* Open the web server page.
 * Browse to the saved .pcapng file
 * Press *Upload*
* View the distilled trace file in your browser.

An advantage of the Web Service is that the processing is done on a server system with late and great Wireshark versions. The client system does not need Wireshark installed at all other than to generate the capture file.

A drawback of the Web Service is the size of the files involved and pushing them through the web interface. A modest trace file of 12,000 frames may be 3.5 Mbytes. The resulting html file may be 54 Mbytes. Even with a fast server and network the download may time out and finish with an error.

## As a CLI process

If your local system has Wireshark installed then you are good to go. 

* Run Wireshark; capture test traffic; save the .pcapng file. This is the same as with the server.
* Run scripts/adverb-cli/adverb-cli.py including the path to the .pcapng file as arg1.
* The .html file is generated locally and can be opened as a file.

## Example

An [example](http://htmlpreview.github.io/?https://github.com/ChugR/Adverb/blob/master/example/helloworld.html) is included. It is a trace of a simple HelloWorld staged for tutorial purposes. Take a look.

## TODO:

* The scripts run on Fedora Linux and have some issues running on Windows.
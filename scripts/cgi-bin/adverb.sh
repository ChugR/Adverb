#!/bin/bash -ex
#
# Version 2.3
set +o errexit

if [ "$REQUEST_METHOD" = "POST" ]; then
    if [ "$CONTENT_LENGTH" -gt 0 ]; then
	# create workspace
	workdir=$(mktemp -d)

	# web form data -> user's input
	cat - > $workdir/user.orig

	# extract incoming file name
	ufname=`head -n 5 $workdir/user.orig | grep --binary-files=text filename | awk '{print $4}' | sed 's/filename="//; s/"//'`

	# local working file name
	fname=user.pcapng

	# Extract alternate decode ports and create selectors list
	portlist=`tail -n 6 $workdir/user.orig | head -n 1 | tr -d '\r'`
	selectors=""
	if [ -n "$portlist" ]; then
	    for s in $portlist
	    do
		if [ -n "$s" ]; then
		    selectors="$selectors -d tcp.port==$s,amqp"
		fi
	    done
	fi
	
        # Extract user note
        usernote=`tail -n 2 $workdir/user.orig | head -n 1 | tr -d '\r'`

	# user's input -> .pcapng
	tail -n +5 $workdir/user.orig | head -n -9 > $workdir/$fname-0
	fsize=$(stat --print="%s" $workdir/$fname-0)
	dd if=$workdir/$fname-0 of=$workdir/$fname bs=1 skip=0 count=$((fsize-2))

	# .pcapng -> .pdml
	cd adverb/bin
	./tshark -2 -r $workdir/$fname $selectors -T pdml > $workdir/user.pdml 2>&1
	if [ "$?" -ne "0" ]; then
	    echo "Status: 500 Internal Server Error"
	    echo "Content-Type: text/plain"
	    echo
	    echo "Tshark utility error processing $ufname"
	    echo
	    cat $workdir/user.pdml
	    exit
	fi

	# .pdml -> .html
	#xsltproc --stringparam userFileName $ufname ../scripts/adverb.xsl $workdir/user.pdml > $workdir/user.html 2>&1
        ../scripts/adverb.py $workdir/user.pdml "$ufname" "$portlist"  "$usernote" > $workdir/user.html 2>&1
	if [ "$?" -ne "0" ]; then
	    echo "Status: 500 Internal Server Error"
	    echo "Content-Type: text/plain"
	    echo
	    echo "python utility error processing $ufname"
	    echo
	    cat $workdir/user.html
	    exit
	fi

	# .html -> user
	echo "Content-Type: text/html"
	echo
	cat $workdir/user.html

	# clean up
	rm -rf $workdir
    else
        echo "Content-Type: text/plain"
        echo 
	echo "Error: no content"
    fi
else
    echo "Content-Type: text/plain"
    echo 
    echo "Error: expected to receive POST but received $REQUEST_METHOD"
fi



#!/bin/bash
# submenu

#get script path here
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
OPENJKPATH="$HOME/openjk"
MBIIPATH="$OPENJKPATH/MBII"
MACHINE_TYPE=`uname -m`

		cd $SCRIPTPATH

		sudo rm -f /usr/bin/mbii 2> /dev/null
		sudo ln -s $SCRIPTPATH/mbii.py /usr/bin/mbii
		sudo chmod +x /usr/bin/mbii

                unlink $HOME/.local/share/
		mkdir -p $HOME/.local/share/
		ln -s $HOME/openjk $HOME/.local/share/

                mkdir -p $HOME/openjk/log

		# Copies Binaries so you can run openjk.i386 or mbiided.i386 as your engine
		sudo cp $HOME/openjk/mbiided.i386 /usr/bin/

		sudo chmod +755 /usr/bin/mbiided.i386

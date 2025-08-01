#!/usr/bin/env bash

# Updater requires .NET Core 3.1 and should be placed in the game directory.
# Customize variables below as necessary.

# directory where base and MBII folder reside (AKA GameData on clients)
gamedir="/home/mb2/jamp"
# server startup script in $gamedir
startscript="start.sh"
# server stop script in $gamedir
stopscript="stop.sh"

read -p "Stop all servers and update MBII?" -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # stop servers
    sh $gamedir/$stopscript

    # download newer files
    cd $gamedir
	dotnet MBII_CommandLine_Update_XPlatform.dll

	read -p "Is your engine OpenJK based?" -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
		cd $gamedir/MBII
        mv -f jampgamei386.so jampgamei386.jamp.so
        cp jampgamei386.nopp.so jampgamei386.so
    fi

    # start servers
    sh $gamedir/$startscript
    
    echo "***** Done! *****"
else
	echo "Aborting"
fi
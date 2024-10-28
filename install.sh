#!/bin/bash
# submenu

#get script path here
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
OPENJKPATH="$HOME/openjk"
MBIIPATH="$OPENJKPATH/MBII"
MACHINE_TYPE=`uname -m`

cd $SCRIPTPATH

debian () {
  local PS3=$'\nPlease enter sub option: '
  local options=("Dependancies" "Python Tools" "Python2" "MBII Server" "RTVRTM" "Dotnet" "MBII Updater" "Update MBII" "Back to main menu")
  local opt
  select opt in "${options[@]}"
  do
      case $opt in
          "Dependancies")
	if [ ${MACHINE_TYPE} == 'x86_64' ]; then
		sudo dpkg --add-architecture i386
                sudo apt-get update
		sudo apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 zlib1g:i386 curl:i386 lib32z1 build-essential cmake gcc-multilib g++-multilib libjpeg-dev:i386 libpng-dev:i386 zlib1g-dev:i386 libcurl4:i386
	else
                sudo apt-get update
		sudo apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 zlib1g:i386 curl:i386 lib32z1 build-essential cmake gcc-multilib g++-multilib libjpeg-dev:i386 libpng-dev:i386 zlib1g-dev:i386 libcurl4:i386 
	fi
		debian;
              ;;
          "Python Tools")
		sudo apt-get update
		sudo apt-get install -y net-tools
		sudo apt-get install -y fping
		sudo apt-get install -y python3
		sudo apt-get install -y nano
		sudo apt-get install -y python3-pip
		sudo apt-get install -y unzip
		pip3 install watchgod --break-system-packages
		pip3 install tailer --break-system-packages
		pip3 install six --break-system-packages
		pip3 install psutil --break-system-packages
		pip3 install PTable --break-system-packages
		pip3 install ConfigParser --break-system-packages
		pip3 install pysqlite3 --break-system-packages
		pip3 install flask --break-system-packages
		pip3 install flask_httpauth --break-system-packages
		pip3 install discord.py --break-system-packages
		pip3 install prettytable --break-system-packages
		debian;
		;;
          "Python2")
		sudo apt-get update
		sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
	if [ ! -r ~/.pyenv/ ]
			then
    		git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    		git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
    		echo '
	# pyenv
		export PYENV_ROOT="$HOME/.pyenv"
		export PATH="$PYENV_ROOT/bin:$PATH"
	if command -v pyenv 1>/dev/null 2>&1; then
    		eval "$(pyenv init -)"
    		eval "$(pyenv virtualenv-init -)" # Enable auto-activation of virtualenvs
	fi' >> ~/.bashrc
    		source ~/.bashrc
    		exec "$SHELL"
	fi
		pyenv install 2.7.18 -s -v
		pyenv local 2.7.18
		debian;
              ;;
          "MBII Server")
 	if [ -d $MBIIPATH ]; then
		clear;
       		sleep 2
	else
        	clear;
        	sleep 2

        #Download file lists, get the latest
		wget -O MBII.zip https://www.moddb.com/downloads/mirror/269567/130/322caa7bdb18fe3ed9645724f169b0c6/?referer=https%3A%2F%2Fwww.moddb.com%2Fmods%2Fmovie-battles-ii%2Fdownloads
		
       	unzip -o MBII.zip -d $OPENJKPATH
		rm MBII.zip
		cd $MBIIPATH
	
		mv -f jampgamei386.so jampgamei386.jamp.so
		cp jampgamei386.nopp.so jampgamei386.so

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

		sudo chmod 755 /usr/bin/mbiided.i386		
	fi
                debian;
              ;;
          "RTVRTM")
		cd $SCRIPTPATH
		
		cp rtvrtm.py $OPENJKPATH/  
		chmod +x $OPENJKPATH/rtvrtm.py
                debian
              ;;
          "Dotnet")
		sudo apt-get install software-properties-common
                sudo apt-get update
		sudo add-apt-repository ppa:dotnet/backports
                sudo apt-get install -y apt-transport-https dotnet-sdk-6.0
                debian;
              ;;
          "MBII Updater")
                wget https://www.moviebattles.org/download/MBII_CLI_Updater.zip
                unzip -o MBII_CLI_Updater.zip -d $OPENJKPATH
                rm MBII_CLI_Updater.zip
                debian;
              ;;
          "Update MBII")
                cd $OPENJKPATH
                dotnet MBII_CommandLine_Update_XPlatform.dll

                mv -f jampgamei386.so jampgamei386.jamp.so
                cp jampgamei386.nopp.so jampgamei386.so
                debian;
              ;;
          "Back to main menu")
              main;
              ;;
          *) echo "invalid option $REPLY";;
      esac
  done
}

ubuntu () {
  local PS3=$'\nPlease enter sub option: '
  local options=("Dependancies" "Python Tools" "Python2" "MBII Server" "RTVRTM" "Dotnet" "MBII Updater" "Update MBII" "Back to main menu")
  local opt
  select opt in "${options[@]}"
  do
      case $opt in
          "Dependancies")
	if [ ${MACHINE_TYPE} == 'x86_64' ]; then
		sudo dpkg --add-architecture i386
                sudo apt-get update
		sudo apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 zlib1g:i386 curl:i386 lib32z1 build-essential cmake gcc-multilib g++-multilib libjpeg-dev:i386 libpng-dev:i386 zlib1g-dev:i386 libcurl4:i386
	else
                sudo apt-get update
		sudo apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 zlib1g:i386 curl:i386 lib32z1 build-essential cmake gcc-multilib g++-multilib libjpeg-dev:i386 libpng-dev:i386 zlib1g-dev:i386 libcurl4:i386 
	fi
            ubuntu;
              ;;
          "Python Tools")
		sudo apt-get update
		sudo apt-get install -y net-tools
		sudo apt-get install -y fping
		sudo apt-get install -y python3
		sudo apt-get install -y nano
		sudo apt-get install -y python3-pip
		sudo apt-get install -y unzip
		pip3 install watchgod --break-system-packages
		pip3 install tailer --break-system-packages
		pip3 install six --break-system-packages
		pip3 install psutil --break-system-packages
		pip3 install PTable --break-system-packages
		pip3 install ConfigParser --break-system-packages
		pip3 install pysqlite3 --break-system-packages
		pip3 install flask --break-system-packages
		pip3 install flask_httpauth --break-system-packages
		pip3 install discord.py --break-system-packages
		pip3 install prettytable --break-system-packages
            ubuntu;
              ;;
          "Python2")
		sudo apt-get update
		sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
	if [ ! -r ~/.pyenv/ ]
			then
    		git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    		git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
    		echo '
	# pyenv
		export PYENV_ROOT="$HOME/.pyenv"
		export PATH="$PYENV_ROOT/bin:$PATH"
	if command -v pyenv 1>/dev/null 2>&1; then
    		eval "$(pyenv init -)"
    		eval "$(pyenv virtualenv-init -)" # Enable auto-activation of virtualenvs
	fi' >> ~/.bashrc
    		source ~/.bashrc
    		exec "$SHELL"
	fi
		pyenv install 2.7.18 -s -v
		pyenv local 2.7.18
            ubuntu;
		;;
          "MBII Server")
 	if [ -d $MBIIPATH ]; then
		clear;
       		sleep 2
	else
        	clear;
        	sleep 2

        #Download file lists, get the latest
		wget -O MBII.zip https://www.moddb.com/downloads/mirror/269567/130/322caa7bdb18fe3ed9645724f169b0c6/?referer=https%3A%2F%2Fwww.moddb.com%2Fmods%2Fmovie-battles-ii%2Fdownloads
		
       	unzip -o MBII.zip -d $OPENJKPATH
		rm MBII.zip
		cd $MBIIPATH
	
		mv -f jampgamei386.so jampgamei386.jamp.so
		cp jampgamei386.nopp.so jampgamei386.so

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

		sudo chmod 755 /usr/bin/mbiided.i386			
	fi
		ubuntu;
              ;;
          "RTVRTM")
		cd $SCRIPTPATH
		
		cp rtvrtm.py $OPENJKPATH/  
		chmod +x $OPENJKPATH/rtvrtm.py
            ubuntu;
              ;;
          "Dotnet")
		sudo apt-get install software-properties-common
                sudo apt-get update
		sudo add-apt-repository ppa:dotnet/backports
                sudo apt-get install -y apt-transport-https dotnet-sdk-6.0
            ubuntu;
              ;;
          "MBII Updater")
                wget https://www.moviebattles.org/download/MBII_CLI_Updater.zip
                unzip -o MBII_CLI_Updater.zip -d $OPENJKPATH
                rm MBII_CLI_Updater.zip
            ubuntu;
              ;;
          "Update MBII")
                cd $OPENJKPATH
                dotnet MBII_CommandLine_Update_XPlatform.dll

                cd $MBIIPATH
                mv -f jampgamei386.so jampgamei386.jamp.so
                cp jampgamei386.nopp.so jampgamei386.so
            ubuntu;
              ;;
          "Back to main menu")
              main;
              ;;
          *) echo "invalid option $REPLY";;
      esac
  done
}

main () {
local PS3=$'\nEnter a number and press enter: '
local options=("Debian" "Ubuntu" "Quit")
local opt
select opt in "${options[@]}"
do
    case $opt in
        "Debian")
            debian
            ;;
        "Ubuntu")
            ubuntu
            ;;
        "Quit")
            exit
            ;;
        *) echo "invalid option $REPLY";;
    esac
done
}


# main menu
echo "*************************************************"
echo " 	   Moviebattles II EZ Installer Tool           "
echo "        	  Interactive Menu                     "
echo "*************************************************"
echo ""
echo "		Press a number to install 	       "

PS3=$'\nEnter a number and press enter: '
options=("Debian" "Ubuntu" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Debian")
            debian
            ;;
        "Ubuntu")
            ubuntu
            ;;
        "Quit")
            exit
            ;;
        *) echo "invalid option $REPLY";;
    esac
done

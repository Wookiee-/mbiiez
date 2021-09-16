!#/bin/sh

#get script path
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
OPENJKPATH="/opt/openjk"
MBIIPATH="$OPENJKPATH/MBII"
MACHINE_TYPE=`uname -m`

cd $SCRIPTPATH

if [ "$EUID" -ne 0 ]
  then echo "Installation requires root. Please run installation as root"
  ##exit
fi

show_menu(){
    normal=`echo "\033[m"`
    menu=`echo "\033[36m"` #Blue
    number=`echo "\033[33m"` #yellow
    admin=`echo "\033[32m"` #green
    bgred=`echo "\033[41m"`
    fgred=`echo "\033[31m"`
    printf "\n${menu}*************************************************${normal}\n"
    printf "${menu} 	 Moviebattles II EZ Server Updater		\n"
    printf "${menu}*************************************************${normal}\n\n"
    printf "${menu}**${number} 1)${menu} Install Dependancies${normal}\n"
    printf "${menu}**${number} 2)${menu} Install MBII Server Updater${normal}\n"
    printf "${menu}**${number} 3)${menu} Update MBII Server${normal}\n"
    printf "\n${menu}*************************************************${normal}\n"
    printf "Please enter a menu option and enter or ${fgred}x to exit. ${normal}"
    read opt
}

option_picked(){
    msgcolor=`echo "\033[01;31m"` # bold red
    normal=`echo "\033[00;00m"` # normal white
    message=${@:-"${normal}Error: No message passed"}
    printf "${msgcolor}${message}${normal}\n"
}



clear
show_menu
while [ $opt != '' ]
    do
    if [ $opt = '' ]; then
      exit;
    else
      case $opt in
        1) clear;
            option_picked "\n${menu} Installing Dependancies...${normal}\n";
                wget https://packages.microsoft.com/config/ubuntu/21.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
                dpkg -i packages-microsoft-prod.deb
                rm packages-microsoft-prod.deb


                apt-get update
                apt-get install -y apt-transport-https
                apt-get install -y dotnet-sdk-5.0
                apt-get install -y dotnet-sdk-3.1

	   clear;
           show_menu;
        ;;
        2) clear;
            option_picked "\n${menu} Installing MBII Server Updater...${normal}\n";
		wget https://www.moviebattles.org/download/MBII_CLI_Updater.zip
		unzip -o MBII_CLI_Updater.zip -d ./updater
		rm MBII_CLI_Updater.zip

	   clear;
           show_menu;
        ;;
        3) clear;
            option_picked "\n${menu} Updating MBII Server...${normal}\n";
                cd $OPENJKPATH
                dotnet $SCRIPTPATH/updater/MBII_CommandLine_Update_XPlatform.dll

                cd $MBIIPATH
	        mv -f jampgamei386.so jampgamei386.jamp.so
	        cp jampgamei386.nopp.so jampgamei386.so

           clear;
           show_menu;
        ;;
        x)exit;
        ;;
        \n)exit;
        ;;
        *)clear;
            option_picked "Pick an option from the menu";
            show_menu;
        ;;
      esac
    fi
done
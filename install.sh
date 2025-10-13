#!/bin/bash
# Moviebattles II EZ Installer Tool - Single Level Menu

# Get script path
SCRIPT=$(readlink -f $0)
SCRIPTPATH=$(dirname $SCRIPT)
OPENJKPATH="$HOME/openjk"
MBIIPATH="$OPENJKPATH/MBII"
MACHINE_TYPE=$(uname -m)

cd $SCRIPTPATH

install_dependencies() {
    sudo dpkg --add-architecture i386
    sudo apt-get update
    sudo apt-get install -y libc6:i386 lib32z1 libstdc++6:i386 libcurl4t64:i386 
}

install_python_tools() {
    sudo apt-get update
    sudo apt-get install -y net-tools fping python3 python3-pip unzip
    pip3 install --user watchgod tailer six psutil PTable ConfigParser flask flask_httpauth discord.py prettytable --break-system-packages
}

setup_pyenv() {
    sudo apt-get update
    sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev \
        libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

    if [ ! -r ~/.pyenv/ ]; then
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
    pyenv global 2.7.18
}

setup_rtvrtm() {
    cp rtvrtm.py $OPENJKPATH/
    chmod +x $OPENJKPATH/rtvrtm.py
}

setup_links() {
    sudo rm -f /usr/bin/mbii 2> /dev/null
    sudo ln -s $SCRIPTPATH/mbii.py /usr/bin/mbii
    sudo chmod +x /usr/bin/mbii

    unlink $HOME/.local/share/openjk
    mkdir -p $HOME/.local/share/
    ln -s $HOME/openjk $HOME/.local/share/

    wget https://github.com/Wookiee-/OpenJK/releases/download/R20/mbiided.i386
    chmod +x mbiided.i386
    sudo cp mbiided.i386 /usr/bin 
}

install_dotnet() {
    wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
    chmod +x ./dotnet-install.sh
    ./dotnet-install.sh --channel 6.0

#    echo "export DOTNET_ROOT=$HOME/.dotnet" >> ~/.bashrc
#    echo "export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools" >> ~/.bashrc

#    source ~/.bashrc
}

install_mbii_updater() {
    cd $SCRIPTPATH/update

    wget https://www.moviebattles.org/download/MBII_CLI_Updater.zip
    unzip *.zip

    cp *.exe $OPENJKPATH
    cp *.dll $OPENJKPATH
    cp *.json $OPENJKPATH
}

update_mbii() {
    cd $OPENJKPATH

    export DOTNET_ROOT=$HOME/.dotnet  
    export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools


    dotnet MBII_CommandLine_Update_XPlatform.dll

    cd $MBIIPATH
    mv -f jampgamei386.so jampgamei386.jamp.so
    cp jampgamei386.nopp.so jampgamei386.so
}

# Main menu
while true; do
    clear
    echo "*************************************************"
    echo "      Moviebattles II EZ Installer Tool          "
    echo "            Interactive Menu                     "
    echo "*************************************************"
    echo ""
    echo "Select an option to install/configure:"

    PS3=$'\nEnter your choice (1-9) or 10 to quit: '
    options=(
        "Install Dependencies"
        "Setup Pyenv"
        "Install Python Tools"
        "Setup RTVRTM"
        "Setup Links"
        "Install Dotnet"
        "Install MBII Updater"
        "Update MBII"
        "Show Current Paths"
        "Quit"
    )

    select opt in "${options[@]}"; do
        case $REPLY in
            1) install_dependencies; break ;;
            2) setup_pyenv; break ;;
            3) install_python_tools; break ;;
            4) setup_rtvrtm; break ;;
            5) setup_links; break ;;
            6) install_dotnet; break ;;
            7) install_mbii_updater; break ;;
            8) update_mbii; break ;;
            9)
                echo "Current paths:"
                echo "Script path: $SCRIPTPATH"
                echo "OpenJK path: $OPENJKPATH"
                echo "MBII path: $MBIIPATH"
                read -p "Press enter to continue..."
                break
                ;;
            10) exit 0 ;;
            *) echo "Invalid option. Try again."; continue ;;
        esac
    done
done

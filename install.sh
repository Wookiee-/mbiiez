#!/bin/bash
# Moviebattles II EZ Installer Tool - Enhanced Interactive Menu

# Colors
RED='\u001b[31m'
GREEN='\u001b[32m'
YELLOW='\u001b[33m'
BLUE='\u001b[34m'
MAGENTA='\u001b[35m'
CYAN='\u001b[36m'
WHITE='\u001b[37m'
BOLD='\u001b[1m'
RESET='\u001b[0m'

# Box drawing characters
HORIZONTAL='\u2500'
VERTICAL='\u2502'
TOP_LEFT='\u250c'
TOP_RIGHT='\u2510'
BOTTOM_LEFT='\u2514'
BOTTOM_RIGHT='\u2518'
CROSS='\u253c'
T_RIGHT='\u251c'
T_LEFT='\u2524'
T_DOWN='\u252c'
T_UP='\u2564'

# Get script path
SCRIPT=$(readlink -f $0)
SCRIPTPATH=$(dirname $SCRIPT)
OPENJKPATH=~/openjk
MBIIPATH=$OPENJKPATH/MBII
MACHINE_TYPE=$(uname -m)

cd $SCRIPTPATH

# Print centered text
center_text() {
    local text=$1
    local width=50
    local padding=$(( (width - ${#text}) / 2 ))
    printf '%*s%s%*s\n' $padding '' 1 '' $padding ''
}

# Print box header
print_box_header() {
    local title=$1
    local width=50
    echo -ne ${CYAN}
    echo -n '    '
    echo -n -e $TOP_LEFT
    printf '%*s' $width ''
    echo -n -e $TOP_RIGHT
    echo
    echo -n '    '
    echo -n -e $VERTICAL
    local title_padding=$(( (width - ${#title}) / 2 ))
    local title_spaces=$(( width - ${#title} - title_padding ))
    printf '%*s%s%*s' $title_padding '' 1 '' $title_spaces ''
    echo -n -e $VERTICAL
    echo
    echo -n '    '
    echo -n -e $T_RIGHT
    printf '%*s' $width ''
    echo -n -e $T_LEFT
    echo -ne ${RESET}
}

# Print box line
print_box_line() {
    local width=50
    echo -ne ${CYAN}
    echo -n '    '
    echo -n -e $VERTICAL
    printf '%*s' $width ''
    echo -n -e $VERTICAL
    echo
    echo -ne ${RESET}
}

# Print box footer
print_box_footer() {
    local width=50
    echo -ne ${CYAN}
    echo -n '    '
    echo -n -e $BOTTOM_LEFT
    printf '%*s' $width ''
    echo -n -e $BOTTOM_RIGHT
    echo
    echo -ne ${RESET}
}

# Status message (green success)
status_ok() {
    echo -ne ${GREEN}'    [OK] '${RESET}$1${RESET}'\n'
}

# Status message (yellow warning)
status_warn() {
    echo -ne ${YELLOW}'    [WARN] '${RESET}$1${RESET}'\n'
}

# Status message (red error)
status_error() {
    echo -ne ${RED}'    [ERROR] '${RESET}$1${RESET}'\n'
}

# Info message (cyan)
info_msg() {
    echo -ne ${CYAN}'    [INFO] '${RESET}$1${RESET}'\n'
}

# Progress message (magenta)
progress_msg() {
    echo -ne ${MAGENTA}'    [....] '${RESET}$1${RESET}
}

# Complete progress message
complete_progress() {
    echo -ne '\r    [ DONE ] '${RESET}$1${RESET}'\n'
}

# Check if command exists
command_exists() {
    command -v $1 >/dev/null 2>&1
}

# Check if path exists
path_exists() {
    [ -e $1 ] 2>/dev/null
}

# Install dependencies
install_dependencies() {
    clear
    print_box_header 'Installing System Dependencies'
    echo
    info_msg 'Adding i386 architecture support...'
    progress_msg 'Running: sudo dpkg --add-architecture i386'
    sudo dpkg --add-architecture i386 2>/dev/null
    if [ $? -eq 0 ]; then
        complete_progress 'Added i386 architecture'
    else
        status_error 'Failed to add i386 architecture'
        read -p '    Press enter to continue...'
        return 1
    fi

    info_msg 'Updating package lists...'
    progress_msg 'Running: sudo apt-get update'
    sudo apt-get update -qq 2>/dev/null
    if [ $? -eq 0 ]; then
        complete_progress 'Updated package lists'
    else
        status_error 'Failed to update package lists'
        read -p '    Press enter to continue...'
        return 1
    fi

    info_msg 'Installing packages: libc6:i386 lib32z1 libstdc++6:i386 libcurl4t64:i386 libjemalloc2:i386 sqlite3'
    progress_msg 'Running: sudo apt-get install -y ...'
    sudo apt-get install -y libc6:i386 lib32z1 libstdc++6:i386 libcurl4t64:i386 libjemalloc2:i386 sqlite3 2>/dev/null
    if [ $? -eq 0 ]; then
        complete_progress 'Installed all system dependencies'
    else
        status_error 'Failed to install some packages'
        read -p '    Press enter to continue...'
        return 1
    fi

    echo
    status_ok 'System dependencies installed successfully!'
    echo
    read -p '    Press enter to continue...'
}

# Install Python tools
install_python_tools() {
    clear
    print_box_header 'Installing Python Tools'
    echo

    # Check for python3
    if command_exists python3; then
        status_ok 'Python 3 found: ' $(python3 --version 2>&1)
    else
        status_error 'Python 3 not found - please run Install Dependencies first'
        echo
        read -p '    Press enter to continue...'
        return 1
    fi

    info_msg 'Updating package lists...'
    sudo apt-get update -qq 2>/dev/null

    info_msg 'Installing: net-tools fping python3 python3-pip unzip'
    progress_msg 'Running: sudo apt-get install -y ...'
    sudo apt-get install -y net-tools fping python3 python3-pip unzip 2>/dev/null
    if [ $? -eq 0 ]; then
        complete_progress 'Base Python tools installed'
    else
        status_error 'Failed to install base Python tools'
        read -p '    Press enter to continue...'
        return 1
    fi

    info_msg 'Installing Python packages: watchgod, tailer, six, psutil, prettytable, urllib3, flask, flask_httpauth, flask-socketio, discord.py'
    progress_msg 'Running: pip3 install --user ...'
    pip3 install --user watchgod tailer six psutil prettytable urllib3 flask flask_httpauth flask-socketio discord.py --break-system-packages 2>/dev/null
    if [ $? -eq 0 ]; then
        complete_progress 'Python packages installed'
    else
        status_warn 'Some Python packages may have failed - continuing anyway'
    fi

    echo
    status_ok 'Python tools installed successfully!'
    echo
    read -p '    Press enter to continue...'
}

# Setup RTVRTM
setup_rtvrtm() {
    clear
    print_box_header 'Setting up RTVRTM'
    echo

    if [ ! -f rtvrtm.py ]; then
        status_error 'rtvrtm.py not found in current directory'
        echo
        read -p '    Press enter to continue...'
        return 1
    fi

    info_msg 'Checking OpenJK directory...'
    if [ ! -d $OPENJKPATH ]; then
        status_warn 'OpenJK path does not exist: $OPENJKPATH'
        info_msg 'Creating OpenJK directory...'
        mkdir -p $OPENJKPATH
    else
        status_ok 'OpenJK directory found'
    fi

    info_msg 'Copying rtvrtm.py to $OPENJKPATH/'
    cp rtvrtm.py $OPENJKPATH/
    chmod +x $OPENJKPATH/rtvrtm.py
    if [ $? -eq 0 ]; then
        complete_progress 'rtvrtm.py copied and made executable'
        status_ok 'RTVRTM setup complete'
    else
        status_error 'Failed to copy rtvrtm.py'
        read -p '    Press enter to continue...'
        return 1
    fi

    echo
    read -p '    Press enter to continue...'
}

# Setup links
setup_links() {
    clear
    print_box_header 'Setting Up Links and MBII'
    echo

    info_msg 'Creating mbii symlink in /usr/bin'
    sudo rm -f /usr/bin/mbii 2>/dev/null
    sudo ln -s $SCRIPTPATH/mbii.py /usr/bin/mbii
    sudo chmod +x /usr/bin/mbii
    if [ -L /usr/bin/mbii ]; then
        status_ok '/usr/bin/mbii symlink created'
    else
        status_error 'Failed to create /usr/bin/mbii symlink'
    fi

    info_msg 'Creating openjk symlink in ~/.local/share/'
    unlink ~/.local/share/openjk 2>/dev/null
    mkdir -p ~/.local/share/
    ln -s $HOME/openjk ~/.local/share/
    if [ -L ~/.local/share/openjk ]; then
        status_ok 'openjk symlink created'
    else
        status_error 'Failed to create openjk symlink'
    fi

    info_msg 'Downloading mbiided.i386...'
    if [ -f mbiided.i386 ]; then
        status_ok 'mbiided.i386 already exists'
    else
        wget -q https://github.com/Wookiee-/OpenJK/releases/download/R20/mbiided.i386
        if [ $? -eq 0 ]; then
            status_ok 'Downloaded mbiided.i386'
        else
            status_error 'Failed to download mbiided.i386'
        fi
    fi

    chmod +x mbiided.i386 2>/dev/null
    sudo cp mbiided.i386 /usr/bin 2>/dev/null
    if [ -f /usr/bin/mbiided.i386 ]; then
        status_ok 'mbiided.i386 installed to /usr/bin'
    else
        status_error 'Failed to install mbiided.i386 to /usr/bin'
    fi

    echo
    read -p '    Press enter to continue...'
}

# Install dotnet
install_dotnet() {
    clear
    print_box_header 'Installing .NET SDK'
    echo

    if [ -d $HOME/.dotnet ]; then
        status_ok '.NET SDK already installed'
    else
        info_msg 'Downloading dotnet-install.sh...'
        wget -q https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
        if [ $? -ne 0 ]; then
            status_error 'Failed to download dotnet-install.sh'
            read -p '    Press enter to continue...'
            return 1
        fi

        chmod +x ./dotnet-install.sh
        info_msg 'Installing .NET SDK 6.0...'
        progress_msg 'This may take a few minutes...'
        ./dotnet-install.sh --channel 6.0 2>/dev/null
        if [ $? -eq 0 ]; then
            complete_progress '.NET SDK installed'
            status_ok '.NET SDK 6.0 installed successfully'
        else
            status_error 'Failed to install .NET SDK'
            read -p '    Press enter to continue...'
            return 1
        fi
    fi

    echo
    read -p '    Press enter to continue...'
}

# Install MBII Updater
install_mbii_updater() {
    clear
    print_box_header 'Installing MBII Updater'
    echo

    if [ ! -d $SCRIPTPATH/update ]; then
        mkdir -p $SCRIPTPATH/update
    fi

    cd $SCRIPTPATH/update

    info_msg 'Downloading MBII_CLI_Updater.zip...'
    if [ -f MBII_CLI_Updater.zip ]; then
        status_ok 'Updater zip already exists'
    else
        wget -q https://www.moviebattles.org/download/MBII_CLI_Updater.zip
        if [ $? -ne 0 ]; then
            status_error 'Failed to download MBII_CLI_Updater.zip'
            read -p '    Press enter to continue...'
            return 1
        fi
        status_ok 'Downloaded MBII_CLI_Updater.zip'
    fi

    info_msg 'Extracting updater files...'
    unzip -o *.zip 2>/dev/null
    if [ $? -eq 0 ]; then
        status_ok 'Extracted updater files'
    else
        status_error 'Failed to extract updater files'
        read -p '    Press enter to continue...'
        return 1
    fi

    cd $SCRIPTPATH

    info_msg 'Copying updater files to OpenJK directory...'
    if [ -d $OPENJKPATH ]; then
        cp $SCRIPTPATH/update/*.exe $OPENJKPATH/ 2>/dev/null
        cp $SCRIPTPATH/update/*.dll $OPENJKPATH/ 2>/dev/null
        cp $SCRIPTPATH/update/*.json $OPENJKPATH/ 2>/dev/null
        status_ok 'Updater files copied to $OPENJKPATH/'
    else
        status_warn 'OpenJK directory not found - skipping file copy'
    fi

    echo
    status_ok 'MBII Updater installed!'
    echo
    read -p '    Press enter to continue...'
}

# Update MBII
update_mbii() {
    clear
    print_box_header 'Updating MBII'
    echo

    if [ ! -d $OPENJKPATH ]; then
        status_error 'OpenJK directory not found: $OPENJKPATH'
        echo
        read -p '    Press enter to continue...'
        return 1
    fi

    if [ ! -f $HOME/.dotnet/dotnet ]; then
        status_error '.NET SDK not found - please run Install Dotnet first'
        echo
        read -p '    Press enter to continue...'
        return 1
    fi

    cd $OPENJKPATH

    export DOTNET_ROOT=$HOME/.dotnet
    export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools

    info_msg 'Running MBII Command Line Updater...'
    progress_msg 'This may take a minute...'
    dotnet MBII_CommandLine_Update_XPlatform.dll 2>/dev/null
    if [ $? -eq 0 ]; then
        complete_progress 'MBII update completed'
    else
        status_error 'MBII update failed'
        read -p '    Press enter to continue...'
        return 1
    fi

    if [ -d $MBIIPATH ]; then
        info_msg 'Applying game patch files...'
        cd $MBIIPATH
        mv -f jampgamei386.so jampgamei386.jamp.so 2>/dev/null
        cp jampgamei386.nopp.so jampgamei386.so 2>/dev/null
        status_ok 'Game patch applied'
    fi

    cd $SCRIPTPATH
    echo
    status_ok 'MBII update complete!'
    echo
    read -p '    Press enter to continue...'
}

# Show status
show_status() {
    clear
    print_box_header 'Installation Status'
    echo    echo -e "    \${CYAN}Path Information:\${RESET}"
    echo -e "    \${WHITE}  Script path: \${GREEN}$SCRIPTPATH\${RESET}"
    echo -e "    \${WHITE}  OpenJK path: \${GREEN}$OPENJKPATH\${RESET}"
    echo -e "    \${WHITE}  MBII path:   \${GREEN}$MBIIPATH\${RESET}"
    echo
    echo -e "    \${CYAN}Installed Components:\${RESET}"

    # Check system packages
    if dpkg -l libc6:i386 2>/dev/null | grep -q ii; then
        status_ok 'System dependencies (i386)'
    else
        status_warn 'System dependencies (i386) - not installed'
    fi

    # Check Python 3
    if command_exists python3; then
        status_ok "Python 3: $(python3 --version 2>&1)"
    else
        status_warn 'Python 3 - not found'
    fi

    # Check pip packages
    if pip3 show watchgod >/dev/null 2>&1; then
        status_ok 'Python packages (watchgod, etc.)'
    else
        status_warn 'Python packages - not installed'
    fi

    # Check rtvrtm.py
    if [ -f $OPENJKPATH/rtvrtm.py ]; then
        status_ok 'RTVRTM installed'
    else
        status_warn 'RTVRTM - not installed'
    fi

    # Check mbii symlink
    if [ -L /usr/bin/mbii ]; then
        status_ok 'mbii symlink'
    else
        status_warn 'mbii symlink - not created'
    fi

    # Check .NET
    if [ -d $HOME/.dotnet ]; then
        status_ok '.NET SDK installed'
    else
        status_warn '.NET SDK - not installed'
    fi

    # Check mbiided
    if [ -f /usr/bin/mbiided.i386 ]; then
        status_ok 'mbiided.i386 installed'
    else
        status_warn 'mbiided.i386 - not installed'
    fi

    echo
    read -p '    Press enter to continue...'
}

# Run all (quick install)
run_all() {
    clear
    print_box_header 'Running Full Installation'
    echo

    status_warn 'This will run: Dependencies -> Python Tools -> Links -> Dotnet'
    echo
    read -p '    Press Enter to continue or Ctrl+C to cancel...'

    install_dependencies
    install_python_tools
    setup_links
    install_dotnet

    clear
    print_box_header 'Full Installation Complete'
    echo
    status_ok 'All core components installed!'
    echo
    read -p '    Press enter to continue...'
}

# Main menu
main_menu() {
    while true; do
        clear
        echo -e ${CYAN}
        cat << 'EOF'

    ╔══════════════════════════════════════════════════╗
    ║                                                  ║
    ║        MovieBattles II EZ Installer Tool         ║
    ║              Enhanced Interactive Menu           ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝

EOF
        echo -e ${WHITE}'                   Main Menu'
        echo -e ${CYAN}'    ════════════════════════════════════'${RESET}
        echo
        echo -e '    '${GREEN}'1.'${WHITE}' Install System Dependencies'
        echo -e '    '${GREEN}'2.'${WHITE}' Install Python Tools'
        echo -e '    '${GREEN}'3.'${WHITE}' Setup RTVRTM'
        echo -e '    '${GREEN}'4.'${WHITE}' Setup Links and MBII'
        echo -e '    '${GREEN}'5.'${WHITE}' Install .NET SDK'
        echo -e '    '${GREEN}'6.'${WHITE}' Install MBII Updater'
        echo -e '    '${GREEN}'7.'${WHITE}' Update MBII'
        echo -e '    '${GREEN}'8.'${WHITE}' Show Installation Status'
        echo -e '    '${GREEN}'9.'${WHITE}' Quick Install (Run 1-4, 5)'
        echo
        echo -e '    '${RED}'0.'${WHITE}' Quit'
        echo
        echo -ne ${CYAN}'    ════════════════════════════════════'${RESET}
        echo
        echo -ne ${WHITE}'    Enter your choice [0-9]: '${RESET}

        read choice
        echo

        case $choice in
            1) install_dependencies ;;
            2) install_python_tools ;;
            3) setup_rtvrtm ;;
            4) setup_links ;;
            5) install_dotnet ;;
            6) install_mbii_updater ;;
            7) update_mbii ;;
            8) show_status ;;
            9) run_all ;;
            0) echo -e ${GREEN}'    Goodbye! Happy gaming!'${RESET}; exit 0 ;;
            *) echo -e ${RED}'    Invalid option. Please try again.'${RESET}; sleep 1 ;;
        esac
    done
}

# Run main menu
main_menu
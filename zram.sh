#!/bin/bash

# Zram Installer for Jedi Academy Game Servers
# Targets: Debian/Ubuntu based systems

echo "Starting Zram Installation..."

# 1. Install necessary utilities
sudo apt update
sudo apt install -y zram-tools util-linux

# 2. Configure zram-tools
# We set SIZE to 50% of total RAM, which is safe for a 2GB VPS.
# We set ALGO to lz4 for maximum speed (minimal stuttering).
echo "Configuring /etc/default/zramswap..."
sudo bash -c 'cat << CONFIG > /etc/default/zramswap
ALGO=lz4
PERCENT=50
PRIORITY=100
CONFIG'

# 3. Configure sysctl for aggressive swapping
# Forces the OS to use zram before touching the disk.
echo "Configuring sysctl parameters..."
sudo bash -c 'cat << SYSCTL > /etc/sysctl.d/99-zram.conf
vm.swappiness=100
vm.vfs_cache_pressure=100
SYSCTL'

# 4. Restart services
echo "Restarting services..."
sudo systemctl restart zramswap
sudo sysctl --system

echo "Installation Complete!"
echo "Check status with: zramctl"
#!/bin/bash

# 1. Load the BBR module
echo "Loading TCP BBR module..."
sudo modprobe tcp_bbr
echo "tcp_bbr" | sudo tee /etc/modules-load.d/bbr.conf

# 2. Apply "End Game" Network & Buffer Optimizations
cat <<SYSCTL | sudo tee /etc/sysctl.d/99-server-optimizer.conf
# Enable BBR Congestion Control
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr

# --- UDP & RECEIVE BUFFER FIXES ---
# Increase Max Socket Buffers to 32MB (Fixes the "11093 receive buffer errors")
net.core.rmem_max=33554432
net.core.wmem_max=33554432

# Increase Default Buffers to 2MB (Gives every player a larger starting "lane")
net.core.rmem_default=2097152
net.core.wmem_default=2097152

# How many packets the kernel can process in one 'interrupt' (Default is 300)
# Increasing this to 600 helps clear the 32MB buffer faster
net.core.netdev_budget = 600

# Total time the CPU can spend on network interrupts per slice
net.core.netdev_budget_usecs = 8000

# Increase the 'Backlog' queue (the line outside the mailbox)
# This is crucial for 30+ player bursts
net.core.netdev_max_backlog = 10000

# Scalable UDP Memory limits (min, pressure, max)
net.ipv4.udp_mem=768432 1024576 1536864
# Ensure minimum UDP buffer per-socket is high enough for MB2 snapshots
net.ipv4.udp_rmem_min=16384
net.ipv4.udp_wmem_min=16384
SYSCTL

# 3. Apply the changes
echo "Applying network changes..."
sudo sysctl --system

# 4. Final Verification
echo "---------------------------------------"
CC=$(sysctl net.ipv4.tcp_congestion_control | awk '{print $3}')
RMEM=$(sysctl net.core.rmem_max | awk '{print $3}')
if [ "$CC" == "bbr" ] && [ "$RMEM" == "33554432" ]; then
    echo -e "\e[32mSUCCESS: BBR Active & Buffers Expanded (32MB).\e[0m"
else
    echo -e "\e[31mCHECK CONFIG: Settings may not have applied fully.\e[0m"
fi
echo "---------------------------------------"
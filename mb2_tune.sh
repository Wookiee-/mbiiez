#!/bin/bash

# =======================================================
# Tuned MB2 VDS Optimizer - Networking & Limits Only
# Target: 2GB RAM / 4 Instances (Movie Battles II)
# =======================================================

echo "-------------------------------------------------------"
echo " MB2 VDS Optimizer: Networking Profile (No Zram)"
echo "-------------------------------------------------------"

# 1. Conservative thresholds for IP Fragmentation
# Prevents kernel from hogging RAM for packet reassembly
# High: 64MB, Low: 48MB (Reduced from original)
sudo sysctl -w net.ipv4.ipfrag_high_thresh=67108864
sudo sysctl -w net.ipv4.ipfrag_low_thresh=50331648
sudo sysctl -w net.ipv4.ipfrag_time=60

# 2. Optimized Network Buffers
# Reduced from original 25MB to 12MB. Saves ~100MB RAM total
# for 4 instances. Crucial for 2GB VPS.
sudo sysctl -w net.core.rmem_max=12582912
sudo sysctl -w net.core.wmem_max=12582912
sudo sysctl -w net.core.netdev_max_backlog=2000

# 3. Security & Stability
sudo sysctl -w net.ipv4.tcp_syncookies=1

# 4. Update Ulimit for mbiiez
echo "[*] Checking and updating mbiiez user limits..."
CURRENT_ULIMIT=$(su - mbiiez -c "ulimit -Sn")

if [ "$CURRENT_ULIMIT" -lt 65535 ]; then
    echo "[!] WARNING: mbiiez ulimit is $CURRENT_ULIMIT."
    echo "[!] Ensure /etc/security/limits.conf is updated."
else
    echo "[✓] mbiiez ulimit is healthy (65535)"
fi

# Apply current session limit
sudo ulimit -n 65535
echo "[✓] Current session ulimit is $(ulimit -n)"

# 5. Make it permanent
CONF_FILE="/etc/sysctl.d/99-mb2-performance.conf"
echo "[*] Writing permanent configuration to $CONF_FILE"
cat <<EOF | sudo tee $CONF_FILE > /dev/null
# MB2 Performance Tuning - Networking Profile
net.ipv4.ipfrag_high_thresh = 67108864
net.ipv4.ipfrag_low_thresh = 50331648
net.ipv4.ipfrag_time = 60
net.core.rmem_max = 12582912
net.core.wmem_max = 12582912
net.core.netdev_max_backlog = 2000
net.ipv4.tcp_syncookies = 1
EOF

# Apply immediately
sudo sysctl -p

echo "-------------------------------------------------------"
echo " Networking Optimizer Complete."
echo "-------------------------------------------------------"
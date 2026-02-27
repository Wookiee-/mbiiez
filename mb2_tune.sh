#!/bin/bash

# Configuration: The Aggressive "Movie Battles II" Profile
HIGH_THRESH=134217728  # 128MB
LOW_THRESH=100663296   # 96MB

echo "-------------------------------------------------------"
echo " MB2 VDS Optimizer: Aggressive Frag patience"
echo "-------------------------------------------------------"

# 1. Apply High Thresh FIRST to avoid "Invalid Argument"
echo "[*] Raising memory ceiling..."
sudo sysctl -w net.ipv4.ipfrag_high_thresh=$HIGH_THRESH

# 2. Now apply the rest
echo "[*] Setting cleanup floor and timeout..."
sudo sysctl -w net.ipv4.ipfrag_low_thresh=$LOW_THRESH
sudo sysctl -w net.ipv4.ipfrag_time=120
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.wmem_max=26214400
sudo sysctl -w net.core.netdev_max_backlog=5000

# 3. Check and Update Ulimit for mbiiez
echo "[*] Checking and updating mbiiez user limits..."
LIMITS_FILE="/etc/security/limits.conf"

# Check if limits are already applied to avoid duplicates
if ! grep -q "mbiiez soft nofile 65535" "$LIMITS_FILE"; then
    echo "[*] Adding limits to $LIMITS_FILE..."
    echo -e "mbiiez soft nofile 65535\nmbiiez hard nofile 65535" | sudo tee -a "$LIMITS_FILE" > /dev/null
else
    echo "[✓] Limits already present in $LIMITS_FILE."
fi

# Apply current session limit for the check
sudo ulimit -n 65535
CURRENT_ULIMIT=$(ulimit -n)
echo "[✓] Current session ulimit is $CURRENT_ULIMIT"

# 4. Make it permanent for reboots
CONF_FILE="/etc/sysctl.d/99-mb2-performance.conf"

# Use 'tee' to create or update the configuration file safely
if [ ! -f "$CONF_FILE" ]; then
    echo "[*] Creating permanent configuration file at $CONF_FILE"
    cat <<EOF | sudo tee $CONF_FILE > /dev/null
net.ipv4.ipfrag_high_thresh = $HIGH_THRESH
net.ipv4.ipfrag_low_thresh = $LOW_THRESH
net.ipv4.ipfrag_time = 120
net.core.rmem_max = 26214400
net.core.wmem_max = 26214400
net.core.netdev_max_backlog = 5000
EOF
else
    echo "[✓] Configuration file $CONF_FILE already exists, skipping creation."
fi

echo "-------------------------------------------------------"
echo " Final Verification:"
sysctl net.ipv4.ipfrag_high_thresh net.ipv4.ipfrag_low_thresh
echo "-------------------------------------------------------"

sudo sysctl -p
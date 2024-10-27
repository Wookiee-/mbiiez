#!/bin/bash

apt update
apt install -y git

useradd -m mbiiez
usermod -aG sudo mbiiez
usermod -s /bin/bash mbiiez
passwd mbiiez

echo ''
echo 'You may now log into mbiiez via ssh'
echo ''

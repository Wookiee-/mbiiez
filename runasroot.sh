#!/bin/bash

sudo useradd -m mbiiez
sudo usermod -aG sudo mbiiez
sudo usermod -s /bin/bash mbiiez
sudo passwd mbiiez

echo 'You may now log into mbiiez via ssh'

#!/bin/sh

# Start koreader's SSH server without starting koreader
# https://github.com/koreader/koreader/blob/f793c6a36c2254cc28808fba6f5fe0ab0baf0f08/plugins/SSH.koplugin/main.lua

cd /mnt/us/koreader && ./dropbear -E -R -p3333 -P /tmp/dropbear_mike.pid
iptables -A INPUT -p tcp --dport 3333 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --sport 3333 -m conntrack --ctstate ESTABLISHED -j ACCEPT
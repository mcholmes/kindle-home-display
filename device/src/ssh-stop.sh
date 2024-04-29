#!/bin/sh

# https://github.com/koreader/koreader/blob/f793c6a36c2254cc28808fba6f5fe0ab0baf0f08/plugins/SSH.koplugin/main.lua
# shellcheck disable=SC2002
cat /tmp/dropbear_mike.pid | xargs kill
rm /tmp/dropbear_mike.pid
iptables -D INPUT -p tcp --dport 3333 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -D OUTPUT -p tcp --sport 3333 -m conntrack --ctstate ESTABLISHED -j ACCEPT
#!/bin/bash
set -e
ip link show pan0 &>/dev/null || ip link add name pan0 type bridge
ip addr show pan0 | grep -q 192.168.60.1 || ip addr add 192.168.60.1/24 dev pan0
ip link set pan0 up

#!/bin/bash
# Dong goi Bat-WinRM-ConsoleSystem.msi tu assets/windows/bat-winrm.{ps1,wxs} (can wixl: apt install wixl)
# Dung: tools/dong-goi-winrm-msi.sh <phien-ban> <thu-muc-ra>
set -e
VER=${1:-1.0.0}; RA=$(realpath "${2:-.}")
NGUON=$(dirname "$(realpath "$0")")/../src/consolesystem/assets/windows
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
cp "$NGUON/bat-winrm.ps1" "$T/"
sed "s/@VER@/$VER/" "$NGUON/bat-winrm.wxs" > "$T/wr.wxs"
(cd "$T" && wixl -a x64 -o out.msi wr.wxs)
cp "$T/out.msi" "$RA/Bat-WinRM-ConsoleSystem.msi"
sha256sum "$RA/Bat-WinRM-ConsoleSystem.msi"

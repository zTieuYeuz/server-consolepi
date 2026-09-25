#!/bin/bash
# ===================================================================
# CHI DE TEST: phong thi nghiem PXE hoan toan TACH BIET (network namespace),
# khong dung toi mang that cua may build.
# ===================================================================
#   "LAN"  = bridge br0 trong netns lan
#   "Router cong ty" = dnsmasq DHCP 192.168.110.1 trong netns cty (chi khi
#                      che do mang_co_dhcp - tai hien dung loi that 25/09/2026)
#   "Pi"   = dnsmasq voi FILE CAU HINH DO CHINH CODE sinh ra (ui/pxe.py) +
#            HTTP phuc vu menu.ipxe do pxemenu.sinh_script() sinh ra
#   "May khach" = QEMU boot mang (BIOS: iPXE ROM cua e1000; UEFI: OVMF)
#
#   bash pxe-lab.sh <mang_co_dhcp|mang_khong_dhcp|truc_tiep> <bios|uefi> <thu_muc_vao>
# thu_muc_vao can co: <kieu>.conf, <kieu>.ipxe, boot/ (ca 3 sinh bang
# sinh-cau-hinh.py - boot/ = file boot kem san + _pxe/<kich ban>/).
# Chi kiem den buoc may khach TAI dung file cua kich ban (khong co boot.wim
# that); chay tron WinPE xem wimboot-lab.sh, cai that xem pi-that.sh. Ket qua + anh man hinh: <thu_muc_vao>/kq-<kieu>-<fw>/
K=$1; FW=$2; D=${3:-/tmp/pxl}; R=$D/kq-$K-$FW; rm -rf $R; mkdir -p $R
for f in $K.conf $K.ipxe boot/undionly.kpxe boot/snponly-shim.efi boot/ipxe.efi; do [ -f $D/$f ] || { echo "THIEU $D/$f"; exit 1; }; done
for f in cty.pid pi.pid http.pid q.pid; do [ -f $D/$f ] && kill $(cat $D/$f) 2>/dev/null; rm -f $D/$f; done
sleep 1
for n in lan pi cty; do ip netns del $n 2>/dev/null; done
ip netns add lan; ip netns add pi; ip netns add cty
ip -n lan link add br0 type bridge; ip -n lan link set br0 up
ip link add c0 netns cty type veth peer name c0b netns lan
ip link add p0 netns pi type veth peer name p0b netns lan
for x in c0b p0b; do ip -n lan link set $x master br0; ip -n lan link set $x up; done
ip -n cty link set c0 up; ip -n pi link set p0 up; ip -n pi link set lo up
if [ "$K" = mang_co_dhcp ]; then
  ip -n cty addr add 192.168.110.1/24 dev c0; ip -n pi addr add 192.168.110.14/24 dev p0
  cat > $D/cty.conf <<EOF
interface=c0
bind-interfaces
port=0
dhcp-range=192.168.110.30,192.168.110.40,255.255.255.0,1h
dhcp-option=3,192.168.110.1
log-facility=$R/cty.log
EOF
  ip netns exec cty dnsmasq -C $D/cty.conf --pid-file=$D/cty.pid
else
  ip -n pi addr add 192.168.98.1/24 dev p0     # KHONG co DHCP nao khac
fi
rm -rf $D/www $D/tftp; mkdir -p $D/www/deployos/pxeboot $D/tftp
cp $D/boot/undionly.kpxe $D/boot/snponly-shim.efi $D/boot/ipxe.efi $D/boot/snponly.efi $D/tftp/
cp -r $D/boot/. $D/www/deployos/pxeboot/
cp $D/$K.ipxe $D/www/deployos/pxeboot/menu.ipxe
sed -e "s/^interface=eth0/interface=p0/" -e "s#^tftp-root=.*#tftp-root=$D/tftp#" \
    -e "/^except-interface/d" $D/$K.conf > $R/dnsmasq.conf
echo "log-facility=$R/dnsmasq.log" >> $R/dnsmasq.conf
ip netns exec pi dnsmasq -C $R/dnsmasq.conf --pid-file=$D/pi.pid || { echo DNSMASQ_LOI; exit 1; }
ip netns exec pi sh -c "cd $D/www && python3 -m http.server 80 > $R/http.log 2>&1 & echo \$! > $D/http.pid"
EXTRA=""
if [ "$FW" = uefi ]; then
  cp /usr/share/OVMF/OVMF_VARS_4M.fd $D/vars.fd
  EXTRA="-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=$D/vars.fd"
fi
ip netns exec lan ip tuntap add tap0 mode tap 2>/dev/null
ip -n lan link set tap0 master br0; ip -n lan link set tap0 up
rm -f $D/mon.sock
ip netns exec lan qemu-system-x86_64 -m 512 -display none -vga std -boot n $EXTRA \
  -netdev tap,id=n0,ifname=tap0,script=no,downscript=no \
  -device e1000,netdev=n0,mac=00:0c:29:80:13:cd,bootindex=1 \
  -monitor unix:$D/mon.sock,server,nowait -pidfile $D/q.pid -daemonize
m(){ echo "$1" | socat - UNIX-CONNECT:$D/mon.sock >/dev/null; }
chup(){ m "screendump $R/$1.ppm"; sleep 1; }
for i in $(seq 1 120); do grep -q "GET /deployos/pxeboot/menu.ipxe" $R/http.log 2>/dev/null && break; sleep 2; done
sleep 8; chup 1-menu
m "sendkey up"; sleep 3; m "sendkey ret"; sleep 6; chup 2-install-windows
m "sendkey down"; sleep 4; m "sendkey ret"; sleep 15; chup 3-chon-kich-ban-2
echo "== $K $FW"; grep -o '"GET [^"]*"' $R/http.log | sort | uniq -c
kill $(cat $D/q.pid) 2>/dev/null

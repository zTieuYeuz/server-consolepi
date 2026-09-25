#!/bin/bash
# cho-xong.sh <fw> "<ten may> · <dau IP>"   (may build) - cho trang Tien trinh bao xong, tat dung cach, doc ket qua
FW=$1; MAY=$2; cd /build/test
for i in $(seq 1 150); do
  bash may-chu-iso.sh ssh "curl -s -H X-ConsolePi-Local:1 http://127.0.0.1:8880/api/tiendo/data" | MAY=$MAY python3 -c "
import sys,json,re,html,os
t=html.unescape(re.sub(r'<[^>]+>',' ',json.load(sys.stdin)['html'])); t=re.sub(r'\s+',' ',t)
# Moi ban ghi ket thuc bang nut 'Xoá bản ghi' - xet TUNG ban ghi, khong de
# regex vuot sang ban ghi cu cung ten (da bat nham 1 lan).
ok=any(r.strip().startswith(os.environ['MAY']) and re.search(r'(đã xong|xong, \d+ lỗi)', r) for r in t.split('Xoá bản ghi'))
sys.exit(0 if ok else 1)" && break
  sleep 30
done
echo "cho $((i/2)) phut"; sleep 150
bash may-chu-iso.sh khach $FW tatdep; systemctl stop chup-lab-$FW
bash may-chu-iso.sh khach $FW xem

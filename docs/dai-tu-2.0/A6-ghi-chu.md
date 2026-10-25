# A6 - releases/ + current + console-system-apply (25/10/2026)

- `ui/phathanh.py` (stdlib): tao_ban (cay nguon -> /opt/console-system/releases/<ver>, chi doc, RELEASE.json ma bam), chuyen_ban (current nguyen tu),
  ban_truoc/lui, don_ban_cu (giu 3 + dang dung + ban lui), kiem_ban, ap_dung (file he thong -> /etc: so bam, sao luu etc-*, nginx -t/testparm
  truoc khi nap, loi thi tra ve; CHI cap nhat file DA CO tren may), nhap_khau_cu (/opt/console-pi thu muc that -> lien ket, thu muc cu giu .cu-*).
- `/opt/console-pi` van la TEN CU nhung la lien ket toi /opt/console-system/current -> don vi systemd, script, nginx khong phai doi duong dan.
- Trang thai chay (captures, tftp, backups thiet bi, ifthen-rules) chuyen ve du lieu: duongdan.py + dichuyen.ANH_XA + don vi tftp. Bo nho dem
  bien dich ra /var/cache/console-system/pycache (don vi dashboard).
- Lenh: `scripts/console-system-release.py cai --nguon CAY | ds | kiem | lui | don`, `scripts/console-system-apply.py [--thu]`.
- install.sh / tools/cap-nhat-pi.sh / uninstall.sh / iso/dung-cay-build.sh dung co che nay o bo cuc moi (bo cuc cu: nhu truoc).
Thu that tren .30: nhap khau thu muc that -> lien ket, nang cap 1.9.5 -> 1.9.5-2, lui, tien lai: 96 trang giong het moi buoc; kiem ma bam nguyen ven.
Loi tim ra khi thu: dich vu bi dung luc nhap khau khong duoc bat lai (da sua + test); root van ghi duoc vao ban 'chi doc' (chi chan nguoi thuong).
CHUA: ISO (dung-cay-build.sh moi chi mo phong rieng doan dung ban + lien ket tuong doi), tra_ve_thu_muc_cu tren may that, Pi .14.

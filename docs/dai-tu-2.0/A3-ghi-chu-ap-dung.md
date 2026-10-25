# A3 - chuyen sang bo cuc /var/lib/console-system (trang thai 24/10/2026)

Da co (nhanh v2, CHUA ap dung len may nao):
- `ui/dichuyen.py`: dua_ve_bo_cuc_moi / kiem_bo_cuc_moi / hoan_tac_bo_cuc; lenh `scripts/dichuyen.py bo-cuc-moi|kiem-bo-cuc|hoantac-bo-cuc`.
- `ui/duongdan.py`: tu nhan biet bo cuc (dau `.bo-cuc-moi` trong thu muc goc). Chua co dau = chay y het 1.9.5.
- Thu tren ban sao du lieu that cua .30 (27 file): ma bam khop, ban cu nguyen ven, trang web giong het, CA/khoa doc duoc.

CHUA lam (can truoc khi ap dung len may that):
1. install.sh / uninstall.sh / cap-nhat-pi.sh / tools/sao-luu-sang-may-build.sh con duong dan cu (PRESERVE, KHOA_SAMBA, config.json...).
2. src/scripts/kiosk-start.sh, iso/includes/console-system-lan-dau (KHOA=/var/lib/console-pi/samba-deploy.key), config/smb.conf, nginx, systemd: doc/ghi file theo cho cu.
3. src/scripts/phien-chay.py, bt-auto-agent.py (tien trinh doc lap, chua dung duongdan).
4. deploy/ va storage/ o bo cuc moi la LIEN KET toi thu muc cu (khong chep nhieu GB); chuyen han o buoc sau.
5. Samba share / nginx root van tro /var/lib/console-pi/deploy (hop le nho lien ket).
Ap dung that: dung dich vu -> `dichuyen.py bo-cuc-moi` -> `kiem-bo-cuc` -> khoi dong lai; hoan tac = `hoantac-bo-cuc` (thu muc moi doi ten, khong mat).

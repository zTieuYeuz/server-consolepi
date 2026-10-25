# A4 - bo cai va script dung bo cuc moi (24/10/2026)

Khong doi ten dich vu/thu muc (`console-pi`) - viec do de rieng, chua duoc duyet. Chi cap nhat de dung bo cuc du lieu moi.

- `src/scripts/duong-dan.sh` (CS_*): shell tuong ung ui/duongdan.py. Chua co dau `.bo-cuc-moi` = y het 1.9.5.
- `src/scripts/chon-bo-cuc.sh` (`chon_bo_cuc`): install.sh goi. May moi -> tao bo cuc moi; may co du lieu cu -> chep + kiem bam,
  loi thi GIU bo cuc cu va cai dat van tiep tuc. `CS_KHONG_DOI_BO_CUC=1` ep giu bo cuc cu.
- config/smb.conf, config/nginx-console-pi.conf viet theo bo cuc MOI; install.sh / cap-nhat-pi.sh doi ve duong dan thuc te khi o bo cuc cu
  (test: ra DUNG noi dung 1.9.5).
- Da sua: install.sh, uninstall.sh, tools/cap-nhat-pi.sh, tools/sao-luu-sang-may-build.sh, tools/thu-phan-mem.sh, wifi-fallback.sh,
  selftest.sh, kiosk-start.sh, phien-chay.py, iso/hooks/0100, iso/includes/console-system-lan-dau + kiosk-ve, iso/dung-cay-build.sh.

CHUA kiem tren may that / ISO:
- install.sh chay tron (can root + apt): moi kiem cac manh tach roi (tests/test_bo_cuc_shell.py) + `bash -n` + shellcheck -S error.
- Cac script ISO (hook, lan-dau) chua dung ISO; phai thu trong VM UEFI khi dung ISO 2.0.
- Sau khi chuyen, /opt/console-pi/config.json... ban cu van nam do (khong xoa) nhung chuong trinh khong doc nua.
- deploy/ va storage/ o bo cuc moi van la lien ket toi /var/lib/console-pi/{deploy,storage} (chuyen han o buoc sau).

# B3 - go vong import / tach dich vu dung chung (25/10/2026)

Do bang `tools/do-do-thi-import.py` (canh top-level + canh trong ham). Truoc B3: 61 canh vi pham luat phu thuoc giua cac goi. Sau: 3 canh no ky thuat + 2 "goc lap rap".
Vong import luc nap: chi con mau blueprint cua nettools (`from . import nettools_bp`), khong co vong trong ui/consolesystem.

Dich vu keo ra khoi tinh nang (ten ham giu nguyen, noi goi cu van dung qua re-export / cau noi ui/):
| Tu | Ve | Noi dung |
|---|---|---|
| features/logs/errlog | core/errlog | nhat ky loi/thao tac; ngu canh yeu cau do tang web dang ky (`dat_ngu_canh`) -> core khong import flask |
| features/network/phancung | core/phancung | chon card mang (nettools, layout, health, pxe, deployos dung chung) |
| features/software_deploy/tk_dulieu | core/tk_dulieu | kho may/tai khoan/lich/kich ban dung chung software_deploy + uem |
| deploy_os/wol (chuan_mac, goi_tin, card_mang, gui) | core/magic_packet | gui goi tin Wake-on-LAN |
| network/remote (da_cai, co_token, dang_chay, hang so) | integrations/cloudflare | trang thai Cloudflare Tunnel cho layout |
| software_deploy/tk_dongco (tao_token, tra_token, _TOKEN) | core/token_tai | token tai file 1 lan (web.auth khong phai import tk_dongco) |
| terminal (load_config, save_config, get_term_credential) | core/cauhinh | config.json |
| deployos (APPS_DIR, SCRIPTS_DIR... EXT_SCRIPT) | core/duongdan | hang so thu muc deploy |
| pxe.dang_bat | core/duongdan.pxe_dang_bat | PXE dang chay? |
| tk_trang.CSS | web/css_tk | CSS dung chung tk + uem |
| tk_dongco (dong co WinRM) | integrations/tk_dongco | uem + software_deploy cung dung |

Luat + trach nhiem: tests/test_kien_truc.py (core/integrations khong import ngoai, core khong flask, khong vong, phu thuoc dung luat; `NO_KY_THUAT` chi duoc giam).
No ky thuat con lai (B4): tk_trang->deployos va tk_dongco->deployos (danh muc phan mem/ung dung nam trong deployos 6.8k dong), tk_dongco->uem_agent_goi (kho goi MSI agent).
Goc lap rap (duoc import tinh nang khac, co chu y): features.settings.settings, web.home.
Luu y test: hang so thu muc deploy nay o duongdan nen test patch `duongdan.APPS_DIR` (them vao thu-uem.py), khong chi `deployos.APPS_DIR`.

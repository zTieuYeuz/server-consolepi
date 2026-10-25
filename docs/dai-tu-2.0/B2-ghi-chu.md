# B2 - chuyen file vao cau truc goi moi (25/10/2026)

DI CHUYEN THUAN TUY: khong doi ten module, khong doi logic. Moi module `ui/<ten>.py` da `git mv` vao goi moi; tai `ui/<ten>.py` con CAU NOI
(`sys.modules[ten cu] = module moi` => CUNG MOT doi tuong, patch/trang thai/`from ui import <ten>` nhu cu). Import tuong doi trong module da doi thanh `from ui import ...`
(se doi sang ten moi o buoc go cau noi). Dong dau tien truoc import dau dang ky ten cu tro toi chinh module (chong vong import). `consolesystem/web` va
`consolesystem/features` nap `ui` truoc nen import bang ten MOI truoc cung an toan. Tai nguyen di kem ma (branding, pxe-boot, ui/agent_bin, ui/goi-driver.json, novnc)
tim qua `core/duongdan.py` (GOC_MA, DIR_*), khong theo vi tri file. Cong cu: `tools/chuyen-b2.py` (ANH_XA ben duoi). Kiem: tests/test_cau_noi.py (63 module x 2 thu tu import).

| Nhom | Goi | Module |
|---|---|---|
| core | `core` | duongdan, dichuyen, phathanh |
| web | `web` | layout, auth, gioithieu, docs, ph_icons, home, health |
| deploy_os | `features/deploy_os` | deployos, unattend, pxe, pxemenu, isotach, goidriver, doodia, lichsu, tiendo, datten, tenmay, khotrungtam, winperieng, wol, sansang, gopy, fontinfo |
| software_deploy | `features/software_deploy` | tk_dulieu, tk_dongco, tk_trang |
| uem | `features/uem` | uem_agent, uem_agent_cs, uem_agent_goi, uem_agent_trang, uem_baocao, uem_buoc, uem_dulieu, uem_ketnoi, uem_pki, uem_profiles, uem_trang, uem_trang_b, uem_trienkhai, uem_vnc, uem_winget |
| network | `features/network` | network, phancung, direct, remote |
| terminal | `features/terminal` | terminal, ssh, commands, soanlenh, phien |
| power | `features/power` | power, entertainment |
| files | `features/files` | storage, baotri |
| logs | `features/logs` | logs, errlog |
| settings | `features/settings` | settings |
| backup | `features/backup` | saoluu |

Chua lam (de cho B3/B4...): tach file lon (deployos 6853 dong, unattend 4012...), go vong import, tinh nang khong import cheo nhau, templates/static.
Moi nhom da kiem: hop dong 333 route + 96 trang + golden 48 file khop tung byte + 113 test.

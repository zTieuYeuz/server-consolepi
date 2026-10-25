# B4 - tach deployos.py va unattend.py (25/10/2026)

Di chuyen NGUYEN VAN (khong sua logic) bang cong cu tu dong, moi buoc deu chay lai toan bo lưới an toàn:
- `tools/tach-module.py`: tach khoi cap cao (ham/hang) thanh module nho theo SPEC (nhom theo dong + `ep_nhom`), kiem vong phu thuoc giua cac module moi, nguon van RE-EXPORT moi ten (moi noi goi cu `ui.deployos.x` / `ui.unattend.x` chay nhu truoc).
- `tools/tach-register.py`: tach ham `register_deployos(app)` (4.501 dong, 71 route, 40 ham long) theo tien to duong dan; ham tro giup duoc nang len cap module (dedent KHONG dong vao chuoi nhieu dong); dung boi >=2 cum -> `dosui_chung`.

| Truoc | Sau |
|---|---|
| deployos.py 6.853 dong | deployos.py 317 dong (facade) + dos_hangso, dos_chung, dos_phanmem, dos_font, dos_os, dos_driver, dos_kichban, dos_tomtat, dos_giaodien (cap cao) + dosui_{chung,tiendo,kichban,caidat,os,driver,kho,ungdung,o_dia,font,console} (route, moi cum co `register_<cum>(app)`) |
| unattend.py 4.012 dong | unattend.py 227 dong (facade) + un_{hangso,xml,kiemtra,tientrinh,baocao,chonodia,deploycmd,tuychon,goapp_font,offline,iso,nhung} |

Kiem chung: 333 route + 96 trang + golden 48 file (unattend/deploy.cmd/... KHOP TUNG BYTE) + 121 test + **tests/hop-dong/hanh-vi.json: 75 tuong tac that (3 wizard den luu kich ban, tao/xoa os/ung dung/font/driver, tai len, xoa...) cho KET QUA GIONG HET ban truoc B4** (so bang `git worktree` cua commit 595887d bang `tools/so-sanh-hanh-vi.py`).
Con lai: `dosui_kichban.py` 1.5k dong (wizard: _noi_dung_buoc 726 dong...) va `dosui_kho.py` 750 dong con lon - tach tiep o B6 cung viec dua HTML/CSS/JS ra templates/static. no ky thuat: danh muc phan mem (dos_phanmem) van duoc tk_trang/tk_dongco goi qua `ui.deployos` (xem tests/test_kien_truc.py).

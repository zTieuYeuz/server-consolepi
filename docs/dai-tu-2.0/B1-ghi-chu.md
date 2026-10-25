# B1 - consolesystem/core (25/10/2026)

Goi moi `src/consolesystem/` (ui/ va nettools/ GIU NGUYEN ten va vi tri; chuyen dan o B2). Co trong ban phat hanh (phathanh.MUC_MA).
- `core/esc.py`: 12 ban `_esc` (4 hanh vi khac nhau + 3 ban long) -> 5 ham co ten: esc, esc_none, esc_html, esc_xml, esc_html_rong. Moi module import
  `... as _esc` nen giu nguyen ten goi. Test so khop hanh vi ban cu tren 11 gia tri.
- `core/store.py`: KhoJson (ghi tam+fsync+doi ten+fsync thu muc; .bak la LIEN KET CUNG nen khong ton dung luong; doc file hong -> khoi phuc .bak hoac giu
  `.hong-<gio>`, canh_bao(), KHONG tra rong roi ghi de; loi IO that -> LoiDuLieu). ghi_nguyen_tu cho file le.
- `core/cauhinh.py`: config.json 0600 qua KhoJson (mot doi tuong cho moi duong dan). terminal.load_config/save_config dung no.
- `core/lenh.py`: chay(list, timeout) -> Ket(rc,out,err), het gio=124, khong co lenh=127, khong nem ngoai le; chuoi bi cam. Chua thay 80 cho subprocess (B7).
- `core/nhatky.py`: logger [ten] LEVEL noi dung ra stderr (journald).
- tk_dulieu.Kho ke thua KhoJson (cung giao dien doc/ghi/sua) => sua loi "Kho tra rong khi file hong" (da gap that 23/10).
- A5: goi sao luu bo qua `.bak`, `.hong-*` (lien ket cung lam tarfile ghi thanh LNKTYPE, goi se bi tu choi).

Thu that tren .30 (ban 1.9.5-3): 96 trang giong het, ban phat hanh nguyen ven, .bak sinh ra tren du lieu that (may.json.bak) khi agent bao cao.
Con lai cua B1: SQLite (B1b) cho du lieu lon; chua co UI hien canh_bao() (se lam o B6); chua gom `_chay`/co_kich_thuoc lap ngoai _esc.

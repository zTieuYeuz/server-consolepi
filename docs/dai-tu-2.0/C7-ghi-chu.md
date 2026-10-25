# C7 - kiem thu toan dien he thong cap nhat (25/10/2026)

Tong hop: **thu that tren .30** (xem C2-C5-ghi-chu.md) + **test tu dong** (tests/test_capnhat.py 45 tan cong, test_nangcap.py ma tran chen loi/mat dien, test_chongsua_khoa.py, test_c7_tinh_huong.py).

| Tinh huong | Noi kiem | Ket qua mong doi |
|---|---|---|
| Mat mang / kho tat luc kiem tra | test_c7 `kho_tat...`, test_nangcap | Ghi loi `kho`, thu lai sau ~1 gio, khong cho nang cap |
| Kho tat giua luc tai | test_c7, `mat_dien_giua_luc_tai_goi` | That bai gon; tai TIEP bang Range khi co lai |
| Mat dien giua luc cai/migration/doi ban/khoi dong lai/hoan tac | ma tran moi diem ghi + .30 (kill -9 + phuc-hoi) | Ve trang thai an toan, `current` luon tro ban hop le |
| Day o dia (tai / giai nen / sao luu) | test_c7 ENOSPC x3 | That bai gon, khong de thu muc do, thu lai duoc |
| Goi gia / cu / sai khoa / bi sua 1 byte / ghep khoi | test_capnhat | Chan o buoc chu ky, truoc khi giai ma |
| Nhay coc phien ban | test_c7 `bo_qua_phien_ban`, test_nangcap | Khong co `ban_ke_tiep` -> khong cho nang cap |
| Khong phai admin | test_c7 `khong_dang_nhap` (moi route /cap-nhat*, /khoa-may) | Chuyen /login |
| Bam dup / hai bo chay cung luc | test_c7 | Lan hai bi chan ("dang co mot lan khac chay"), migration chay dung 1 lan |
| PXE dang chay | test_nangcap | Chan, chi cho phep khi xac nhan chap nhan nguy co |
| Kho tat | nt | nt |
| Dong ho may lech (-3,+3,+8 ngay) | test_c7 | Loi "Dong ho may lech ... gio" co huong dan; trong dung sai van chay |
| Chuong trinh bi sua | test_chongsua_khoa | Chan nang cap; ha cap van duoc |
| Khoa/mo khoa | test_chongsua_khoa | Xem C6-ghi-chu.md |

Chua lam duoc (can anh): thu voi KHOA THAT va kho .34 that; thu tren Pi (arm64) va may amd64 khac; mo phong qua Cloudflare (header CF-Connecting-IP) bang kho that.

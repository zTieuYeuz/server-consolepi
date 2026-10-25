# C8 - Thu that bang KHOA THAT + kho .34 that (25/10/2026)

- Kho .34 nang len ma moi (truoc do chay dung commit 28b9618): sao luu DB (integrity ok, 23 may) + ma + khoa kho trong /var/backups/kho-console-pi (moc 20261025-0731); thu migration tren BAN SAO DB; chuyen ban; smoke test. Quay lai: chep /root/app.py.truoc-capnhat2 de len src/app.py, xoa capnhat.py, restart.
- Nap tai lieu tin cay that (so_hieu 2, het han 23/04/2027) + goi 2.0.1 kenh THU-NGHIEM (chi LAN) bang nap-ban.py chay duoi www-data.
- .30: cai 2.0.0 (nhung khoa goc THAT) -> tu dang ky kho, nhan khoa_may -> hoi kho qua LAN (kho_url http://192.168.110.34) -> nang cap 2.0.0 -> 2.0.1 bang goi do chu ky khoa phat-hanh THAT: kiem chu ky, giai ma, doi chieu 390 file, migration, doi ban, khoi dong lai, suc khoe: XONG. nguyenven = ok (390 file). Ha cap 2.0.1 -> 2.0.0: XONG. Sau do tra .30 ve ban 1.9.5 cua repo, don cau hinh/trang thai thu.
- Qua Cloudflare, kenh thu-nghiem bi tu choi 403 dung thiet ke.
- Con trong kho: goi 2.0.1 kenh thu-nghiem (vo hai: chi may LAN thay). Co the xoa bang bang cn_ban neu muon.
- Luu y sao luu kho: thu muc `capnhat/` (co master.key) nam trong /var/lib/kho-console-pi - kiem backup tu dong 05:00 co gom thu muc nay.

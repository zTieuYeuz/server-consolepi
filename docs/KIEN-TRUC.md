# Kien truc Console System 2.0

## Cac tang (chi duoc import XUONG, tu tren xuong)
```
src/app.py                      composition: dang ky blueprint, khoi dong
consolesystem/web/              khung trang (layout), dang nhap (auth), trang chu (home), health
consolesystem/features/<ten>/   MOI tinh nang mot goi: deploy_os, uem, network, terminal, settings, backup, updates, logs, files, ...
consolesystem/integrations/     noi voi ben ngoai: kho trung tam (tk_dongco, kho_capnhat), Cloudflare
consolesystem/core/             KHONG biet flask/web/tinh nang: duong dan, store (JSON/SQLite), lenh, nhat ky, migration, sao luu, ban phat hanh, capnhat/
nettools/                       cong cu mang (blueprint rieng, chi import core, web)
ui/                             CAU NOI cu (alias sang consolesystem.* de import cu va 'ui.xxx' van chay)
```
Luat duoc **test tu dong**: `tests/test_kien_truc.py` (core khong import flask/web; khong vong import; web/features chi import tang duoi; no ky thuat chi GIAM) va `tools/importlinter.ini` (import-linter). Ngoai le co ten: 3 "goc lap rap" (features.settings.settings, web.home, features.updates.thuc_te).

## Du lieu va ban phat hanh
- `/var/lib/console-system/{config,secrets,pki,data,deploy,storage,backups,updates}` (+ `.bo-cuc-moi`). Du lieu nho = JSON nguyen tu (`core/store.KhoJson`: ghi tam + fsync + doi ten, giu `.bak`, khong am tham tra rong khi file hong); du lieu lon = SQLite `data/console.db` (`KhoSqlite`).
- `/opt/console-system/releases/<ban>` chi-doc + symlink `current`; `/opt/console-pi` tro vao `current` (tuong thich cu).
- Migration du lieu co so phien ban: `core/dichuyen.py` (sao luu, chay thu tren ban sao, hoan tac).
- Sao luu/khoi phuc: `core/../features/backup/saoluu.py` (goi .tar.gz + manifest sha256).

## He thong cap nhat (Phan C)
`core/capnhat/`: `khoa` (Ed25519 3 vai tro + tai lieu tin cay) -> `goi` (.cspkg: ky + AES-256-GCM tung khoi) -> `danhmuc` (ky, het han ngan) -> `may` (hoi kho, trang thai) -> `nangcap` (may trang thai ben vung: kiem > sao luu > tai > cai > migration > doi ban > khoi dong lai > suc khoe > hoan tat, tu hoan tac, phuc hoi sau mat dien) -> `nguyenven` (bang bam da ky) -> `khoa_lenh` (khoa/mo khoa may). UI: `features/updates/`. Kho: repo `kho-console-pi/src/capnhat.py`. Xem `docs/dai-tu-2.0/C*-ghi-chu.md`.

## Luoi an toan khi sua ma
`tests/hop-dong/routes.txt` (hop dong route), `trang.txt` (96 trang), `tests/golden/` (48 file sinh ra khop tung byte), `hanh-vi.json` (75 tuong tac), pytest (`tools/ci.sh`). Doi co CHU DICH thi chay lai `tools/xuat-route.py`, `tools/xuat-trang.py`, `tools/golden.py` va giai thich trong commit.

## Them mot tinh nang moi
1. Tao `consolesystem/features/<ten>/` voi `register_<ten>(app)`; logic dua vao `core` neu dung chung, khong import tinh nang khac.
2. Du lieu: `KhoJson`/`KhoSqlite`, duong dan lay tu `core/duongdan.py` (khong ghi cung `/var/lib/...`).
3. Lenh he thong: `core/lenh.chay([...], timeout=...)` (luon co timeout); loi nuot: `core/nhatky.bo_qua(e)`, KHONG `except: pass`.
4. Dang ky trong `ui/__init__.py`, chay `tools/xuat-route.py` + `tools/ci.sh`.

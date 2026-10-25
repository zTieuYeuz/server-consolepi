# B7 + B8 + B9 (25/10/2026)

## B7 - xu ly loi / lenh he thong
- 67 cho `except Exception: pass` (tren 82; con lai: errlog, 3 script doc lap) -> `except Exception as _loi: _bo_qua(_loi)` (`core/nhatky.bo_qua`): HANH VI GIU NGUYEN (van nuot) nhung ghi 1 dong canh bao/10 phut/diem goi vao journald (`[consolesystem.bo-qua] ... bo qua loi X: ...`). Ruff S110 xanh.
- 13 `subprocess.run/call` thieu `timeout` (nginx -t, systemctl reload/restart trong uem_pki; script apply/saoluu/release) -> da them timeout. Test chan hoi quy: `tests/test_kien_truc.py::test_moi_subprocess_run_co_timeout` (ngoai le co ten: phien terminal tuong tac).
- `core/lenh.chay` da co (timeout, rc 124/127, khong nem ngoai le); 168 cho goi `subprocess` rai rac CHUA gop het vao do (moi cho co xu ly loi rieng, doi hang loat co nguy co; se gop khi dung toi tung tinh nang). Test: `tests/test_core.py` (het gio, khong co lenh, check, bo_qua rate-limit).
- Viec nen (thread) : van la `threading.Thread(daemon=True)` tai cho (chua co bo chay viec chung) - ghi nhan, khong doi o day.

## B8 - ten / tai lieu
- Giu ten tieng Viet khong dau (chua co duyet doi sang tieng Anh). Moi module deu co docstring (132/132, quet tu dong).
- Moi: `docs/KIEN-TRUC.md`, `docs/TU-DIEN.md`, `docs/MODULES.md` (tu sinh bang `tools/tao-tai-lieu-module.py`).

## B9 - cong chat luong
- `ruff.toml` (E9, F, S110; ghi ro cac luat tam tat: F401 vi cau noi re-export, F841/F811 ghi nhan no ky thuat), `tools/importlinter.ini` (core khong phu thuoc web/features/integrations/flask), `tools/ci.sh` (ruff + import-linter + cu phap Python 3.11 + bandit + pytest + do phu; `tools/ci.sh nhanh` bo pytest). Ket qua lan chay dau: **CI XANH**, do phu `core/` = 77% (nguong 70%).
- Chua lam: pip-audit/khoa phien ban phu thuoc (`requirements.lock`): can mang va chon phien ban tren Pi that - de anh duyet.

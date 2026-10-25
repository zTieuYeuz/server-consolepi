# B6 - tai nguyen HTML/CSS/JS/PowerShell ra khoi ma Python (25/10/2026)

Cach lam: **di chuyen thuan tuy**, dau ra KHONG doi. `tools/tach-tai-nguyen.py` tim hang so chuoi cap module >= 40 dong (`NAME = """..."""`), ghi nguyen van ra `src/consolesystem/assets/<module>.<NAME>.<css|js|html|ps1|cs>` va thay bang `NAME = _taisan.doc("...")` (`core/taisan.py`, doc nhi phan -> utf-8, nap 1 lan luc import).
Ket qua: 37 hang so (~420 KB) — layout.py BASE_CSS (594 dong), uem_agent_cs SOURCE (ma C# agent 1.037 dong), phien.py JS/TRANG, commands.py, 16 mau HTML cua nettools, script PowerShell cua trinh cai... Ma Python ngan lai, CSS/JS/PowerShell/C# xem va sua duoc bang cong cu rieng.
Kiem: pytest day du (281 pass) gom hop dong route + 96 trang + golden 48 file + 75 hanh vi; ban phat hanh chua du 37 file (`kiem_ban` = []); Python 3.11 sach; thu that tren .30 (ban 1.9.5-2): cac trang tra 200, khong co dong loi trong journald.

Chua lam (co chu y): chuoi nam TRONG ham hoac la f-string (tron du lieu dong) — de chuyen sang Jinja2 `templates/` can viet lai tung trang va chup anh trinh duyet truoc/sau; rui ro cao so voi loi ich, de lai khi co duyet. Thu muc `static/` giu nguyen.

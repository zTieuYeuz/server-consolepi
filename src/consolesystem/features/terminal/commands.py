# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Thu vien lenh (yeu cau so 6)

Luu cac tap lenh hay dung, them/sua/xoa duoc qua web. Tu day co the:
  - Gui thang vao Terminal dang mo (qua tmux send-keys)
  - Copy sang tab SSH de sua (doi IP/ten) roi chay hang loat

File luu: /opt/console-pi/command-library.json  (giu nguyen khi cai dat lai)
"""
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.commands"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json
import os
import subprocess
import time

from flask import request

from ui.layout import render_page

# Duong dan du lieu tap trung - xem ui/duongdan.py
from ui.duongdan import FILE_THU_VIEN_LENH as LIB_FILE
from consolesystem.core.esc import esc as _esc

# 5 tap lenh co ban hay dung nhat khi lam viec voi switch Cisco
DEFAULT_LIBRARY = [
    {
        "name": "Xem thông tin cơ bản switch",
        "desc": "Kiểm tra model, IOS version, uptime, số serial",
        "tags": "cisco, xem",
        "commands": "show version\nshow inventory\nshow env all",
    },
    {
        "name": "Xem trạng thái tất cả cổng",
        "desc": "Cổng nào up/down, tốc độ, duplex, VLAN đang gán",
        "tags": "cisco, xem, port",
        "commands": "show ip interface brief\nshow interfaces status\nshow interfaces description",
    },
    {
        "name": "Xem VLAN và bảng MAC",
        "desc": "Danh sách VLAN, cổng nào thuộc VLAN nào, MAC đang học được",
        "tags": "cisco, xem, vlan",
        "commands": "show vlan brief\nshow mac address-table\nshow interfaces trunk",
    },
    {
        "name": "Gán VLAN cho 1 cổng (access)",
        "desc": "SỬA lại tên cổng và số VLAN trước khi chạy",
        "tags": "cisco, cau hinh, vlan",
        "commands": ("interface GigabitEthernet0/1\n"
                     " description Cau hinh boi Console Pi\n"
                     " switchport mode access\n"
                     " switchport access vlan 10\n"
                     " no shutdown"),
    },
    {
        "name": "Cấu hình IP quản lý + SSH",
        "desc": "SỬA lại IP/subnet/gateway/domain trước khi chạy",
        "tags": "cisco, cấu hình, quản lý",
        "commands": ("interface Vlan1\n"
                     " ip address 192.168.1.10 255.255.255.0\n"
                     " no shutdown\n"
                     "exit\n"
                     "ip default-gateway 192.168.1.1\n"
                     "ip domain-name local.lan\n"
                     "crypto key generate rsa modulus 2048\n"
                     "ip ssh version 2\n"
                     "line vty 0 4\n"
                     " transport input ssh\n"
                     " login local"),
    },
]


def load_library():
    """Doc thu vien. Lan dau chua co file thi tao san 5 tap lenh mau."""
    try:
        with open(LIB_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except FileNotFoundError:
        save_library(DEFAULT_LIBRARY)
        return list(DEFAULT_LIBRARY)
    except Exception as _loi:
        _bo_qua(_loi)
    return []


def save_library(items):
    try:
        with open(LIB_FILE, "w") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def add_item(name, desc, tags, commands):
    items = load_library()
    items.append({"name": name, "desc": desc, "tags": tags, "commands": commands})
    return save_library(items)


def update_item(index, name, desc, tags, commands):
    items = load_library()
    if 0 <= index < len(items):
        items[index] = {"name": name, "desc": desc, "tags": tags, "commands": commands}
        return save_library(items)
    return False


def delete_item(index):
    items = load_library()
    if 0 <= index < len(items):
        items.pop(index)
        return save_library(items)
    return False


def send_to_tmux(session_name, text, press_enter=False):
    """
    Dan tap lenh vao phien tmux dang chay (terminal tren web).

    Dung "bracketed paste" cua tmux (paste-buffer -p) thay vi send-keys:
      - send-keys se lam cac dong DINH LIEN nhau thanh 1 dong vo nghia
      - bracketed paste giu nguyen xuong dong, va shell (bash >= 4.4) hieu
        day la van ban dan vao nen KHONG tu chay - nguoi dung xem lai roi
        moi tu bam Enter. Dung y do "sua xong xac nhan moi chay".
    """
    import tempfile

    try:
        has = subprocess.run(["tmux", "has-session", "-t", session_name],
                             capture_output=True, timeout=5)
        if has.returncode != 0:
            return False, (f"Chưa có phiên terminal '{session_name}'. "
                           f"Mở tab Terminal trước rồi bấm lại.")

        buf_name = "consolepi-lib"
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(text.rstrip("\n"))
            tmp = f.name
        try:
            subprocess.run(["tmux", "load-buffer", "-b", buf_name, tmp],
                           capture_output=True, timeout=5)
            subprocess.run(["tmux", "paste-buffer", "-p", "-b", buf_name,
                            "-t", session_name],
                           capture_output=True, timeout=5)
            if press_enter:
                subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"],
                               capture_output=True, timeout=5)
        finally:
            os.unlink(tmp)

        n = len([l for l in text.splitlines() if l.strip()])
        if press_enter:
            return True, f"Đã dán và chạy {n} lệnh trong terminal."
        # Loi nhan trung tinh: ham nay duoc goi ca tu trang Thu vien lenh lan
        # tu trang SSH (khung terminal nam ngay tren cung trang), nen khong
        # noi cung "mo tab Terminal" nua.
        return True, (f"Đã dán {n} lệnh vào khung terminal (CHƯA chạy). "
                      f"Đọc lại lần cuối rồi bấm Enter trong khung terminal để chạy.")
    except FileNotFoundError:
        return False, "Chưa cài tmux trên máy."
    except Exception as e:
        return False, f"Lỗi: {e}"


def _chup_man_hinh_tmux(session_name):
    try:
        r = subprocess.run(["tmux", "capture-pane", "-p", "-t", session_name],
                           capture_output=True, text=True, timeout=5)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


# Cac "vo" shell tren may - dan vao day thi an toan de dan ca khoi
VO_SHELL = {"bash", "sh", "zsh", "dash", "fish", "ash", "ksh", "tmux"}


def _lenh_dang_chay(session_name):
    """Chuong trinh dang chay trong phien tmux: 'bash', 'ssh', 'microcom'..."""
    try:
        r = subprocess.run(["tmux", "display-message", "-p", "-t", session_name,
                            "#{pane_current_command}"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def dan_thong_minh(session_name, text):
    """
    Dan tap lenh, TU CHON cach dan cho dung voi thu dang o trong terminal.

    Hai cach dan co diem manh nguoc nhau, chon nham la hong:
      - Dang o SHELL cua Pi (bash): dan ca khoi kieu "bracketed paste" -
        moi dong nam yen tai dau nhac, KHONG dong nao chay cho den khi nguoi
        dung tu bam Enter. An toan nhat cho mot shell quyen root.
      - Dang SSH/console VAO THIET BI MANG: khong the dan ca khoi vi CLI
        thiet bi khong co dieu khien luong -> roi mat ky tu dau dong. Phai
        gui tung dong va cho thiet bi in xong.

    Nho `tmux display-message #{pane_current_command}` biet duoc dang chay
    'bash' hay 'ssh'/'microcom', nen khong phai bat nguoi dung tu chon.
    """
    lenh = (_lenh_dang_chay(session_name) or "").lower()

    if lenh in VO_SHELL:
        ok, msg = send_to_tmux(session_name, text)
        if ok:
            msg = f"Đang ở dòng lệnh '{lenh}' nên dán cả khối - CHƯA dòng nào chạy. " + msg
        return ok, msg

    ok, msg = dan_tung_dong_vao_tmux(session_name, text)
    if ok and lenh:
        msg = f"Terminal đang chạy '{lenh}' (thiết bị ngoài) nên gửi từng dòng. " + msg
    return ok, msg


def _dong_cuoi_man_hinh(text):
    dong = [l.rstrip() for l in (text or "").splitlines() if l.strip()]
    return dong[-1] if dong else ""


def _giong_dau_nhac(dong):
    """
    Dong nay co giong dau nhac dang cho go lenh khong?

    Switch/router: "Switch#", "Switch>", "Switch(config-if)#".
    May Linux:     "... $" hoac "... #".
    KHONG tinh dau ":" la dau nhac - do thuong la dau nhac MAT KHAU, gui lenh
    vao do la sai cho.
    """
    d = (dong or "").rstrip()
    return d.endswith("#") or d.endswith(">") or d.endswith("$")


def _cho_thiet_bi_in_xong(session_name, im_lang_giay=0.5,
                          im_lang_khong_dau_nhac=2.5, cho_toi_da=25.0):
    """
    Doi cho toi khi thiet bi IN XONG va THUC SU san sang nhan lenh tiep theo.

    VI SAO KHONG cho mot khoang co dinh: lenh "show version" tren switch that
    in ra hang tram dong, mat vai giay. Cho co dinh 0.18s roi ban dong ke
    tiep thi thiet bi VAN DANG IN, chua doc kip dau vao -> mat ky tu dau dong
    (loi that: "show inventory" thanh "how inventory").

    Dieu kien coi la san sang - phai du CA HAI:
      1. Man hinh khong doi trong `im_lang_giay`
      2. Dong cuoi GIONG DAU NHAC (ket thuc bang # > $)
    Chi "im lang" thoi la CHUA DU: thiet bi cham co the ngung giua chung 1
    nhip roi in tiep, hoac dang dung o "--More--" cho bam phim - ca hai deu
    khong phai la da xong. Neu im lang lau (`im_lang_khong_dau_nhac`) ma van
    khong thay dau nhac thi cung tra ve, de khong ket lai voi nhung thiet bi
    co dau nhac la.

    LOI THAT DA GAP NGAY TRONG HAM NAY: ban dau chi kiem tra "--More--" khi
    man hinh CO THAY DOI. Nhung thiet bi dung o "--More--" thi man hinh dung
    im -> bi cham nham la "da in xong" -> gui dong ke tiep, va ky tu dau tien
    cua dong do bi thiet bi an luon lam PHIM BAM de sang trang. Ket qua dung
    y het loi cu: mat 1 ky tu dau dong. Nay kiem tra "--More--" o MOI vong.
    """
    het_han = time.time() + cho_toi_da
    truoc = _chup_man_hinh_tmux(session_name)
    lan_doi_cuoi = time.time()

    while time.time() < het_han:
        time.sleep(0.15)
        hien = _chup_man_hinh_tmux(session_name)
        cuoi = _dong_cuoi_man_hinh(hien)

        # Kiem tra o MOI vong, khong phu thuoc man hinh co doi hay khong
        if "--more--" in cuoi.lower():
            subprocess.run(["tmux", "send-keys", "-t", session_name, "Space"],
                           capture_output=True, timeout=5)
            truoc = hien
            lan_doi_cuoi = time.time()
            continue

        if hien != truoc:
            truoc = hien
            lan_doi_cuoi = time.time()
            continue

        im_lang = time.time() - lan_doi_cuoi
        if im_lang >= im_lang_giay and _giong_dau_nhac(cuoi):
            return True
        if im_lang >= im_lang_khong_dau_nhac:
            return True

    return False


def dan_tung_dong_vao_tmux(session_name, text, tre_giay=0.25, toi_da_dong=120):
    """
    Dan tap lenh vao phien tmux nhung GUI TUNG DONG, co giai lao giua cac dong.

    VI SAO KHONG dung send_to_tmux() o day: ham do bắn ca khoi van ban ra 1
    luot. Voi bash thi khong sao, nhung voi THIET BI MANG THAT (switch/router
    qua SSH hoac cong console) thi CLI khong co dieu khien luong - trong luc
    thiet bi con dang xu ly + echo lai dong truoc, cac ky tu dau cua dong ke
    tiep bi ROI MAT.

    LOI THAT DA GAP (2 vong):
      1. Ban ca khoi ra 1 luot -> "show interfaces trunk" thanh "how
         interfaces trunk".
      2. Sua thanh cho CO DINH 0.18s giua cac dong -> VAN MAT CHU, vi
         "show version" tren switch that in ra hang tram dong mat vai giay,
         0.18s la qua ngan, thiet bi con dang in thi dong sau da toi.
    Nen bay gio KHONG cho theo thoi gian co dinh nua ma CHO DEN KHI THIET BI
    IN XONG (man hinh im lang) roi moi gui dong tiep - dung nhip cua tung
    thiet bi, thiet bi cham cach may cung khong mat chu.

    KHONG bam Enter o DONG CUOI: cac dong truoc no thi thiet bi mang coi
    xuong dong = Enter nen se chay, rieng dong cuoi de nguyen cho nguoi dung
    doc lai lan cuoi roi tu bam - giu dung nguyen tac "xem roi moi chay".
    """
    dong = [d for d in text.rstrip("\n").split("\n")]
    if not dong or not any(d.strip() for d in dong):
        return False, "Không có nội dung để dán."
    if len(dong) > toi_da_dong:
        return False, (f"Tập lệnh có {len(dong)} dòng, vượt quá {toi_da_dong} dòng cho 1 lần dán. "
                       f"Chia nhỏ ra dán làm nhiều lần cho an toàn.")

    try:
        has = subprocess.run(["tmux", "has-session", "-t", session_name],
                             capture_output=True, timeout=5)
        if has.returncode != 0:
            return False, (f"Chưa có phiên terminal '{session_name}'. "
                           f"Mở khung terminal trước rồi bấm lại.")

        han_chot = time.time() + 180          # tran tong: khong treo mai mai
        da_gui = 0
        cham_gio = False

        for i, d in enumerate(dong):
            if time.time() > han_chot:
                cham_gio = True
                break

            # -l = gui NGUYEN VAN, khong dich cac chuoi trung ten phim
            # (vi du dong lenh co chu "Space" hay "Enter") thanh phim bam.
            subprocess.run(["tmux", "send-keys", "-l", "-t", session_name, d],
                           capture_output=True, timeout=5)
            da_gui += 1

            if i < len(dong) - 1:
                subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"],
                               capture_output=True, timeout=5)
                # Cho THIET BI in xong roi moi gui dong ke tiep (khong phai
                # cho mot khoang co dinh - xem giai thich o tren).
                _cho_thiet_bi_in_xong(session_name)
                # Nghi them 1 nhip ngan: vai thiet bi in xong dau nhac roi
                # van con ban vai chuc ms truoc khi doc duoc dau vao.
                time.sleep(tre_giay)
    except FileNotFoundError:
        return False, "Chưa cài tmux trên máy."
    except Exception as e:
        return False, f"Lỗi: {e}"

    if cham_gio:
        return False, (f"Đã gửi {da_gui}/{len(dong)} dòng rồi phải dừng vì quá 3 phút - "
                       f"thiết bị phản hồi quá chậm hoặc đang kẹt. Kiểm tra khung terminal, "
                       f"dán phần còn lại sau.")

    n = len([d for d in dong if d.strip()])
    if len(dong) == 1:
        return True, "Đã dán vào khung terminal (CHƯA chạy) - bấm Enter trong terminal để chạy."
    return True, (f"Đã dán {n} lệnh: gửi từng dòng, mỗi dòng đều CHỜ THIẾT BỊ IN XONG mới "
                  f"gửi dòng tiếp nên không bị rơi mất chữ. Dòng CUỐI chưa bấm Enter - "
                  f"đọc lại rồi tự bấm để chạy.")




# ---------------------------------------------------------------------------
# GIAO DIEN THU VIEN LENH (lam lai 22/10/2026 theo yeu cau anh Thoai: "de nhin, de them, thuc te").
#
# Truoc day: luoi the, moi the dai ca man hinh, nut xep chong len nhau, form them nam gap sau cung
# danh sach. Nay: DANH SACH ben trai (tim + loc the) / CHI TIET ben phai (xem, sua, them ngay tai cho),
# nhin mot man hinh la thay het va chon duoc ngay.
#   - Du lieu day xuong trang bang mot khoi JSON, JS ve giao dien bang createElement/textContent
#     (khong dung innerHTML voi du lieu nguoi dung -> khong the chen ma).
#   - Cac duong POST cu (/commands/add|update|delete|send) giu nguyen, chi them tham so `chon`
#     de sau khi luu van dang xem dung tap lenh do.
#   - Cho can dien khi dung viet {{ten}} (phien.py da hieu cu phap nay) - hien noi bat trong khoi lenh.
# ---------------------------------------------------------------------------
LIB_CSS = _taisan.doc("features/terminal/commands.LIB_CSS.css")

LIB_JS = _taisan.doc("features/terminal/commands.LIB_JS.html")


def render_library_page(msg="", ok=True, edit_index=None, chon=None):
    items = load_library()
    du_lieu = {
        "items": [{"i": i, "name": str(it.get("name") or ""), "desc": str(it.get("desc") or ""),
                   "tags": str(it.get("tags") or ""), "commands": str(it.get("commands") or "")}
                  for i, it in enumerate(items)],
        "msg": msg or "", "ok": bool(ok),
        "chon": chon if (chon is not None and 0 <= chon < len(items)) else None,
        "edit": edit_index if (edit_index is not None and 0 <= edit_index < len(items)) else None,
    }
    # </ trong JSON co the dong the script som: thay bang <\/ (JSON van hop le)
    nhung = json.dumps(du_lieu, ensure_ascii=False).replace("</", "<\\/")
    tim_icon = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 4a7 7 0 100 14 7 7 0 000-14zM20 20l-4-4"/></svg>')
    body = f"""
    {LIB_CSS}
    <div class="tv">
      <aside class="tv-ds">
        <div class="tv-tim">
          <div class="tv-o">{tim_icon}
            <input type="text" id="tv-tim" placeholder="Tìm tập lệnh" autocomplete="off">
            <button type="button" id="tv-xoa" aria-label="Xóa ô tìm">&#10005;</button>
          </div>
          <button type="button" class="tv-moi" id="tv-moi">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>Thêm mới</button>
        </div>
        <div class="tv-the" id="tv-the"></div>
        <div class="tv-dem" id="tv-dem"></div>
        <ul class="tv-list" id="tv-list"></ul>
      </aside>
      <section class="tv-vo"><div class="tv-ct" id="tv-ct"></div></section>
    </div>
    <script id="tv-data" type="application/json">{nhung}</script>
    {LIB_JS}"""

    return render_page(body, active="/commands", title="Thư viện lệnh",
                       subtitle="Lưu sẵn các tập lệnh hay dùng, sửa được trước khi chạy")


def register_commands(app, tmux_session="consolepi-local"):
    @app.route("/commands")
    def commands_page():
        edit = request.args.get("edit")
        edit_index = int(edit) if (edit or "").isdigit() else None
        chon = request.args.get("chon")
        return render_library_page(edit_index=edit_index, chon=int(chon) if (chon or "").isdigit() else None)

    @app.route("/commands/add", methods=["POST"])
    def commands_add():
        f = request.form
        if not (f.get("name") or "").strip() or not (f.get("commands") or "").strip():
            return render_library_page(msg="Thiếu tên hoặc nội dung lệnh.", ok=False)
        add_item(f.get("name").strip(), f.get("desc", "").strip(),
                 f.get("tags", "").strip(), f.get("commands"))
        return render_library_page(msg=f"Đã thêm '{f.get('name')}'.", ok=True, chon=len(load_library()) - 1)

    @app.route("/commands/update", methods=["POST"])
    def commands_update():
        f = request.form
        idx = int(f.get("index", -1) or -1)
        if update_item(idx, f.get("name", "").strip(), f.get("desc", "").strip(),
                       f.get("tags", "").strip(), f.get("commands", "")):
            return render_library_page(msg="Đã lưu thay đổi.", ok=True, chon=idx)
        return render_library_page(msg="Không tìm thấy tập lệnh để sửa.", ok=False)

    @app.route("/commands/delete", methods=["POST"])
    def commands_delete():
        idx = int(request.form.get("index", -1) or -1)
        if delete_item(idx):
            return render_library_page(msg="Đã xóa tập lệnh.", ok=True)
        return render_library_page(msg="Không tìm thấy tập lệnh.", ok=False)

    @app.route("/commands/send", methods=["POST"])
    def commands_send():
        idx = int(request.form.get("index", -1) or -1)
        items = load_library()
        if not (0 <= idx < len(items)):
            return render_library_page(msg="Không tìm thấy tập lệnh.", ok=False)
        # Dung dan_thong_minh (khong phai send_to_tmux thang) - LOI THAT SUYT
        # LAP LAI: neu nguoi dung dang mo Terminal roi tu SSH vao 1 thiet bi
        # mang tu trong do (khong qua o soan cua tab SSH), roi quay lai
        # Thu vien lenh bam "Gui vao Terminal", ban cu se dan CA KHOI vao
        # thang thiet bi do -> dung y het loi "roi mat ky tu dau dong" da
        # sua o cho khac. dan_thong_minh() tu nhan biet dung o shell hay
        # dang o thiet bi ngoai va chon cach dan phu hop, bat ke vao tu
        # duong nao.
        ok, msg = dan_thong_minh(tmux_session, items[idx].get("commands", ""))
        return render_library_page(msg=msg, ok=ok, chon=idx)

    return app

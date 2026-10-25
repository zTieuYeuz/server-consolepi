# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Thu vien lenh (yeu cau so 6)

Luu cac tap lenh hay dung, them/sua/xoa duoc qua web. Tu day co the:
  - Gui thang vao Terminal dang mo (qua tmux send-keys)
  - Copy sang tab SSH de sua (doi IP/ten) roi chay hang loat

File luu: /opt/console-pi/command-library.json  (giu nguyen khi cai dat lai)
"""
import json
import os
import subprocess
import time

from flask import request

from .layout import render_page

# Duong dan du lieu tap trung - xem ui/duongdan.py
from .duongdan import FILE_THU_VIEN_LENH as LIB_FILE
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
    except Exception:
        pass
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
LIB_CSS = """
<style>
.tv { display:grid; grid-template-columns:minmax(300px,380px) minmax(0,1fr); gap:18px; align-items:start; }
.tv-ds { position:sticky; top:12px; display:flex; flex-direction:column; gap:12px; max-height:calc(100vh - 120px); }
.tv-tim { display:flex; gap:8px; }
.tv-o { position:relative; flex:1; min-width:0; }
.tv-o svg { position:absolute; left:12px; top:50%; width:18px; height:18px; transform:translateY(-50%);
            stroke:var(--chu-mo2); fill:none; stroke-width:1.7; stroke-linecap:round; stroke-linejoin:round; pointer-events:none; }
.tv-o input { width:100%; max-width:none; padding-left:38px; padding-right:38px; height:44px; margin:0; }
.tv-o button { position:absolute; right:6px; top:50%; transform:translateY(-50%); width:32px; height:32px; min-height:32px;
               padding:0; border-radius:8px; background:transparent; border:0; color:var(--chu-mo); cursor:pointer; display:none; }
.tv-o button:hover { background:var(--hang-nen); color:var(--chu); }
.tv-moi { height:44px; padding:0 16px; border-radius:8px; border:0; cursor:pointer; background:var(--nhan);
          color:var(--chu-tren-nhan); font:600 14.5px var(--chu-font); display:inline-flex; align-items:center; gap:7px;
          white-space:nowrap; transition:transform .5s var(--muot), filter .3s var(--muot); }
.tv-moi:hover { filter:brightness(1.08); } .tv-moi:active { transform:scale(.97); }
.tv-moi svg, .tv-nut svg { width:17px; height:17px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
.tv-the { display:flex; gap:6px; flex-wrap:wrap; }
.tv-the button { background:transparent; border:1px solid var(--vien-ro); color:var(--chu-mo); border-radius:99px;
                 padding:0 12px; height:32px; min-height:32px; font:500 13px var(--chu-font); cursor:pointer;
                 transition:background .35s var(--muot), color .35s var(--muot), border-color .35s var(--muot); }
.tv-the button:hover { color:var(--chu); border-color:var(--chu-mo2); }
.tv-the button.on { background:var(--nhan-mo); color:var(--nhan); border-color:var(--nhan); }
.tv-the button small { opacity:.7; margin-left:5px; font-size:11.5px; }
.tv-dem { color:var(--chu-mo2); font-size:12.5px; margin:-2px 2px 0; }
.tv-list { list-style:none; margin:0; padding:0; overflow:auto; border:1px solid var(--vien); border-radius:var(--bo);
           background:var(--the); scrollbar-width:thin; }
.tv-list li { margin:0; }
.tv-list li + li button { border-top:1px solid var(--vien); }
.tv-list button { width:100%; text-align:left; background:transparent; border:0; color:var(--chu); cursor:pointer;
                  padding:13px 16px 13px 18px; min-height:62px; display:grid; grid-template-columns:1fr auto; gap:2px 12px;
                  position:relative; font-family:var(--chu-font); border-radius:0; transition:background .3s var(--muot); }
.tv-list button:hover { background:var(--hang-hover); }
.tv-list button.on { background:var(--nhan-mo); }
.tv-list button.on::before { content:""; position:absolute; left:0; top:10px; bottom:10px; width:3px; border-radius:0 3px 3px 0; background:var(--nhan); }
.tv-list b { font-size:14.5px; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tv-list em { font-style:normal; font-size:12.5px; color:var(--chu-mo2); align-self:center; }
.tv-list small { grid-column:1 / -1; color:var(--chu-mo); font-size:12.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tv-list mark { background:var(--vang-mo); color:var(--vang); border-radius:3px; padding:0 1px; }
.tv-trong { padding:26px 18px; color:var(--chu-mo); font-size:14px; text-align:center; }
.tv-vo { background:var(--the-noi); border:1px solid var(--vien); border-radius:var(--bo); padding:6px; min-width:0; }
.tv-ct { background:var(--the); border-radius:calc(var(--bo) - 6px); padding:24px 26px 26px; min-height:360px; }
.tv-ct h2 { margin:0 0 6px; font-size:22px; letter-spacing:-.02em; }
.tv-mo-ta { color:var(--chu-mo); font-size:14.5px; line-height:1.5; margin:0 0 14px; }
.tv-tag { display:flex; gap:6px; flex-wrap:wrap; margin:0 0 18px; }
.tv-tag span { background:var(--nhan-mo); color:var(--nhan); border-radius:99px; padding:3px 11px; font-size:12.5px; font-weight:500; }
.tv-nut-hang { display:flex; gap:8px; flex-wrap:wrap; margin:0 0 18px; }
.tv-nut { height:44px; min-height:44px; padding:0 15px; border-radius:8px; cursor:pointer; text-decoration:none;
          font:550 14px var(--chu-font); display:inline-flex; align-items:center; gap:7px; border:1px solid var(--vien-ro);
          background:transparent; color:var(--chu); transition:transform .5s var(--muot), background .3s var(--muot), border-color .3s var(--muot); }
.tv-nut:hover { background:var(--hang-nen); border-color:var(--chu-mo2); color:var(--chu); }
.tv-nut:active { transform:scale(.97); }
.tv-nut.chinh { background:var(--nhan); border-color:var(--nhan); color:var(--chu-tren-nhan); }
.tv-nut.chinh:hover { filter:brightness(1.08); background:var(--nhan); color:var(--chu-tren-nhan); }
.tv-nut.nguy { color:var(--do); border-color:var(--do-mo); }
.tv-nut.nguy:hover { background:var(--do-mo); border-color:var(--do); color:var(--do); }
.tv-ma { display:flex; justify-content:space-between; align-items:center; color:var(--chu-mo2); font-size:12.5px; margin:0 0 8px; }
.tv-code { margin:0; background:var(--pre-nen); border:1px solid var(--vien); border-radius:10px; overflow:auto; max-height:46vh;
           font:13.5px/1.65 var(--mono); color:var(--pre-chu); counter-reset:d; }
.tv-code div { display:flex; padding:0 14px 0 0; white-space:pre; }
.tv-code div:first-child { padding-top:12px; } .tv-code div:last-child { padding-bottom:12px; }
.tv-code div::before { counter-increment:d; content:counter(d); flex:0 0 42px; text-align:right; padding-right:14px; color:var(--chu-mo2); opacity:.6; user-select:none; }
.tv-code i { font-style:normal; background:var(--vang-mo); color:var(--vang); border-radius:4px; padding:0 3px; }
.tv-goi { color:var(--chu-mo); font-size:13px; margin:12px 0 0; line-height:1.55; }
.tv-goi i { font-style:normal; background:var(--vang-mo); color:var(--vang); border-radius:4px; padding:0 3px; font-family:var(--mono); }
.tv-f label { display:block; font-size:13px; font-weight:600; color:var(--chu-mo); margin:16px 0 6px; }
.tv-f label:first-of-type { margin-top:0; }
.tv-f input[type=text], .tv-f textarea { width:100%; max-width:none; margin:0; }
.tv-f textarea { font:13.5px/1.6 var(--mono); min-height:230px; resize:vertical; tab-size:2; }
.tv-f .ghi { color:var(--chu-mo2); font-size:12.5px; margin:6px 0 0; line-height:1.5; }
.tv-f .ghi i { font-style:normal; font-family:var(--mono); background:var(--vang-mo); color:var(--vang); border-radius:4px; padding:0 3px; }
.tv-goiy { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
.tv-goiy button { background:transparent; border:1px dashed var(--vien-ro); color:var(--chu-mo); border-radius:99px; padding:0 11px;
                  height:30px; min-height:30px; font:500 12.5px var(--chu-font); cursor:pointer; }
.tv-goiy button:hover { color:var(--nhan); border-color:var(--nhan); }
.tv-mau { display:flex; gap:8px; align-items:center; flex-wrap:wrap; padding:12px 14px; border:1px dashed var(--vien-ro);
          border-radius:10px; margin:0 0 20px; color:var(--chu-mo); font-size:13.5px; }
.tv-mau button { background:var(--hang-nen); border:1px solid var(--vien-ro); color:var(--chu); border-radius:8px; height:34px;
                 min-height:34px; padding:0 12px; font:500 13px var(--chu-font); cursor:pointer; }
.tv-mau button:hover { border-color:var(--nhan); color:var(--nhan); }
.tv-rong { text-align:center; padding:60px 20px; color:var(--chu-mo); }
.tv-rong h2 { color:var(--chu); }
.tv-thongbao { margin:0 0 16px; padding:12px 16px; border-radius:10px; font-size:14px; line-height:1.5; border:1px solid; }
.tv-thongbao.ok { background:var(--xanh-mo); color:var(--msg-ok); border-color:rgba(67,212,146,.35); }
.tv-thongbao.loi { background:var(--do-mo); color:var(--msg-err); border-color:rgba(239,107,107,.4); }
.tv-ct { animation:tv-vao .6s var(--muot) both; }
@keyframes tv-vao { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }
@media (prefers-reduced-motion:reduce) { .tv-ct { animation:none; } }
@media (max-width:900px) {
  .tv { grid-template-columns:1fr; }
  .tv-ds { position:static; max-height:none; }
  .tv-list { max-height:300px; }
  .tv-ct { padding:18px 16px 20px; }
}
</style>
"""

LIB_JS = """
<script>
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("tv-data").textContent);
  var ITEMS = D.items;            // [{i, name, desc, tags, commands}] - i = chi so that trong file
  var NS = "http://www.w3.org/2000/svg";
  var q = "", the = "", chon = null;
  var $ = function (id) { return document.getElementById(id); };

  var ICON = {
    plus: "M12 5v14M5 12h14", search: "M11 4a7 7 0 100 14 7 7 0 000-14zM20 20l-4-4", x: "M6 6l12 12M18 6L6 18",
    send: "M4 12l16-8-6 16-3-7z", link: "M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1",
    copy: "M9 9h11v11H9zM5 15V4h11", edit: "M4 20h4L19 9l-4-4L4 16zM13 7l4 4", trash: "M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13",
    dup: "M8 8h12v12H8zM4 16V4h12", save: "M5 3h11l3 3v15H5zM8 3v5h7V3M8 21v-7h8v7"
  };
  function icon(n) {
    var s = document.createElementNS(NS, "svg"); s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("aria-hidden", "true");
    var p = document.createElementNS(NS, "path"); p.setAttribute("d", ICON[n]); s.appendChild(p); return s;
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e;
  }
  function bo(s) {   // bo dau de tim khong can go dau
    return (s || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").replace(/đ/g, "d");
  }
  function cacThe(it) { return (it.tags || "").split(",").map(function (t) { return t.trim(); }).filter(Boolean); }
  function soLenh(it) { return (it.commands || "").split("\\n").filter(function (l) { return l.trim(); }).length; }
  function khop(it) {
    if (the && cacThe(it).map(bo).indexOf(the) < 0) return false;
    if (!q) return true;
    return bo([it.name, it.desc, it.tags, it.commands].join(" ")).indexOf(q) >= 0;
  }
  // to sang tu khoa dang tim trong ten (khong dung innerHTML)
  function toSang(node, text) {
    var k = q ? bo(text).indexOf(q) : -1;
    if (k < 0) { node.textContent = text; return; }
    node.appendChild(document.createTextNode(text.slice(0, k)));
    node.appendChild(el("mark", null, text.slice(k, k + q.length)));
    node.appendChild(document.createTextNode(text.slice(k + q.length)));
  }

  // ---------------------------------------------------------------- danh sach ben trai
  function veThe() {
    var dem = {}, ten = {};
    ITEMS.forEach(function (it) { cacThe(it).forEach(function (t) { var k = bo(t); dem[k] = (dem[k] || 0) + 1; ten[k] = ten[k] || t; }); });
    var h = $("tv-the"); h.textContent = "";
    var tatca = el("button", the ? "" : "on", "Tất cả"); tatca.type = "button";
    tatca.onclick = function () { the = ""; ve(); }; h.appendChild(tatca);
    Object.keys(dem).sort().forEach(function (k) {
      var b = el("button", the === k ? "on" : "", ten[k]); b.type = "button";
      b.appendChild(el("small", null, String(dem[k])));
      b.onclick = function () { the = (the === k) ? "" : k; ve(); };
      h.appendChild(b);
    });
  }
  function veDs() {
    var ul = $("tv-list"); ul.textContent = "";
    var hien = ITEMS.filter(khop).sort(function (a, b) { return a.name.localeCompare(b.name, "vi"); });
    $("tv-dem").textContent = hien.length + " / " + ITEMS.length + " tập lệnh";
    if (!hien.length) {
      ul.appendChild(el("li", "tv-trong", ITEMS.length ? "Không có tập lệnh nào khớp. Thử từ khóa ngắn hơn hoặc bỏ lọc thẻ." : "Thư viện đang trống."));
      return;
    }
    hien.forEach(function (it) {
      var li = el("li"), b = el("button", chon === it.i ? "on" : ""); b.type = "button";
      var t = el("b"); toSang(t, it.name); b.appendChild(t);
      b.appendChild(el("em", null, soLenh(it) + " lệnh"));
      if (it.desc) b.appendChild(el("small", null, it.desc));
      b.onclick = function () { xem(it.i); };
      li.appendChild(b); ul.appendChild(li);
    });
  }
  function ve() { veThe(); veDs(); $("tv-xoa").style.display = q ? "block" : "none"; }

  // ---------------------------------------------------------------- phan chi tiet
  function postForm(action, fields) {
    var f = el("form"); f.method = "POST"; f.action = action; f.style.display = "none";
    Object.keys(fields).forEach(function (k) { var i = el("input"); i.type = "hidden"; i.name = k; i.value = fields[k]; f.appendChild(i); });
    document.body.appendChild(f); f.submit();
  }
  function sao(text) {
    function du() { var t = el("textarea"); t.value = text; t.style.position = "fixed"; t.style.opacity = "0"; document.body.appendChild(t); t.select();
      try { document.execCommand("copy"); } catch (e) {} document.body.removeChild(t); }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).catch(du); else du();
  }
  function nutBam(cls, ic, nhan, fn, tag) {
    var b = el(tag || "button", "tv-nut " + (cls || "")); if (!tag) b.type = "button";
    b.appendChild(icon(ic)); b.appendChild(document.createTextNode(nhan)); if (fn) b.onclick = fn; return b;
  }
  function khungChiTiet() { var c = $("tv-ct"); var m = c.cloneNode(false); c.parentNode.replaceChild(m, c); return m; }
  function thongBao(ct) {
    if (!D.msg) return; ct.appendChild(el("div", "tv-thongbao " + (D.ok ? "ok" : "loi"), D.msg)); D.msg = "";
  }
  function hash(i) { try { history.replaceState(null, "", i == null ? location.pathname : "#" + i); } catch (e) {} }

  function xem(i) {
    chon = i; var it = ITEMS.filter(function (x) { return x.i === i; })[0]; hash(i); veDs();
    var ct = khungChiTiet(); if (!it) { rong(); return; }
    thongBao(ct);
    ct.appendChild(el("h2", null, it.name));
    if (it.desc) ct.appendChild(el("p", "tv-mo-ta", it.desc));
    var tg = cacThe(it);
    if (tg.length) { var t = el("div", "tv-tag"); tg.forEach(function (x) { t.appendChild(el("span", null, x)); }); ct.appendChild(t); }
    var h = el("div", "tv-nut-hang");
    h.appendChild(nutBam("chinh", "send", "Gửi vào Terminal", function () { postForm("/commands/send", { index: i, chon: i }); }));
    var lk = nutBam("", "link", "Dùng trong Phiên kết nối", null, "a"); lk.href = "/phien?lenh=" + i; h.appendChild(lk);
    var cp = nutBam("", "copy", "Sao chép", function () { sao(it.commands); cp.lastChild.textContent = "Đã chép"; setTimeout(function () { cp.lastChild.textContent = "Sao chép"; }, 1600); });
    h.appendChild(cp);
    h.appendChild(nutBam("", "edit", "Sửa", function () { sua(i); }));
    h.appendChild(nutBam("", "dup", "Nhân bản", function () { moi({ name: it.name + " (bản sao)", desc: it.desc, tags: it.tags, commands: it.commands }); }));
    h.appendChild(nutBam("nguy", "trash", "Xóa", function () { if (confirm("Xóa tập lệnh \\"" + it.name + "\\"?")) postForm("/commands/delete", { index: i }); }));
    ct.appendChild(h);
    var ma = el("div", "tv-ma"); ma.appendChild(el("span", null, soLenh(it) + " lệnh")); ct.appendChild(ma);
    var pre = el("div", "tv-code"), coBien = false;
    it.commands.replace(/\\r/g, "").split("\\n").forEach(function (dong) {
      var d = el("div"); var re = /\\{\\{[^{}]+\\}\\}/g, k = 0, m;
      if (!dong) d.appendChild(document.createTextNode(" "));
      while ((m = re.exec(dong))) {
        coBien = true; d.appendChild(document.createTextNode(dong.slice(k, m.index))); d.appendChild(el("i", null, m[0])); k = m.index + m[0].length;
      }
      if (dong) d.appendChild(document.createTextNode(dong.slice(k)));
      pre.appendChild(d);
    });
    ct.appendChild(pre);
    var g = el("p", "tv-goi");
    if (coBien) { g.appendChild(document.createTextNode("Chỗ tô vàng như ")); g.appendChild(el("i", null, "{{ten}}")); g.appendChild(document.createTextNode(" là chỗ cần điền: mở bằng ")); g.appendChild(el("b", null, "Dùng trong Phiên kết nối")); g.appendChild(document.createTextNode(" thì có ô nhập để điền rồi mới gửi. ")); }
    g.appendChild(document.createTextNode("Gửi vào Terminal chỉ dán lệnh, không tự bấm Enter ở dòng cuối: đọc lại rồi tự chạy."));
    ct.appendChild(g);
  }

  var MAU = [
    { ten: "Cisco: gán VLAN cho 1 cổng", name: "Gán VLAN cho cổng", desc: "Điền tên cổng và số VLAN khi dùng", tags: "cisco, vlan",
      commands: "interface {{cổng}}\\n switchport mode access\\n switchport access vlan {{vlan}}\\n no shutdown" },
    { ten: "Linux: kiểm tra mạng", name: "Kiểm tra mạng Linux", desc: "Địa chỉ, đường đi, ping thử một máy", tags: "linux, mạng",
      commands: "ip -br addr\\nip route\\nping -c 3 {{địa chỉ}}" },
    { ten: "Windows: thông tin máy", name: "Thông tin máy Windows", desc: "Tên máy, địa chỉ mạng, phiên bản", tags: "windows, xem",
      commands: "hostname\\nipconfig /all\\nsysteminfo" }
  ];

  function bieuMau(it, laSua) {
    var ct = khungChiTiet(); thongBao(ct);
    ct.appendChild(el("h2", null, laSua ? "Sửa tập lệnh" : "Thêm tập lệnh mới"));
    ct.appendChild(el("p", "tv-mo-ta", laSua ? "Sửa xong bấm Lưu, thay đổi có hiệu lực ngay." : "Điền tên và các lệnh là đủ, mô tả và thẻ để sau cũng được."));
    var f = el("form", "tv-f"); f.method = "POST"; f.action = laSua ? "/commands/update" : "/commands/add";
    if (laSua) { var ix = el("input"); ix.type = "hidden"; ix.name = "index"; ix.value = it.i; f.appendChild(ix); }
    var o = {};
    function truong(nhan, ten, thuoc, ghiChu) {
      var l = el("label", null, nhan); l.setAttribute("for", "tv-" + ten); f.appendChild(l);
      var e = el(thuoc.t || "input"); if (!thuoc.t) e.type = "text"; e.name = ten; e.id = "tv-" + ten; e.value = it[ten] || "";
      if (thuoc.ph) e.placeholder = thuoc.ph; if (thuoc.req) e.required = true; if (thuoc.rows) e.rows = thuoc.rows;
      f.appendChild(e); o[ten] = e; if (ghiChu) f.appendChild(ghiChu); return e;
    }
    if (!laSua) {
      var mau = el("div", "tv-mau"); mau.appendChild(el("span", null, "Bắt đầu nhanh từ mẫu:"));
      MAU.forEach(function (m) { var b = el("button", null, m.ten); b.type = "button";
        b.onclick = function () { ["name", "desc", "tags", "commands"].forEach(function (k) { o[k].value = m[k]; }); dem(); }; mau.appendChild(b); });
      ct.appendChild(mau);
    }
    truong("Tên tập lệnh", "name", { req: true, ph: "Ví dụ: Gán VLAN cho 1 cổng" });
    truong("Mô tả ngắn", "desc", { ph: "Ghi rõ chỗ nào cần sửa trước khi chạy" });
    var gy = el("div", "tv-goiy");
    var tg = truong("Thẻ, cách nhau bằng dấu phẩy (để lọc nhanh bên trái)", "tags", { ph: "cisco, vlan" }, gy);
    var co = {}; ITEMS.forEach(function (x) { cacThe(x).forEach(function (t) { co[t] = 1; }); });
    Object.keys(co).sort().slice(0, 12).forEach(function (t) {
      var b = el("button", null, "+ " + t); b.type = "button";
      b.onclick = function () { var c = cacThe({ tags: tg.value }); if (c.map(bo).indexOf(bo(t)) < 0) c.push(t); tg.value = c.join(", "); }; gy.appendChild(b);
    });
    var gc = el("p", "ghi"); gc.appendChild(document.createTextNode("Mỗi dòng một lệnh. Chỗ cần điền khi dùng thì viết dạng "));
    gc.appendChild(el("i", null, "{{tên}}")); gc.appendChild(document.createTextNode(", ví dụ ")); gc.appendChild(el("i", null, "interface {{cổng}}"));
    gc.appendChild(document.createTextNode(". "));
    var dm = el("span"); gc.appendChild(dm);
    var ta = truong("Các lệnh", "commands", { t: "textarea", req: true, ph: "show version\\nshow ip interface brief" }, gc);
    function dem() { var n = ta.value.split("\\n").filter(function (l) { return l.trim(); }).length; dm.textContent = n ? n + " lệnh." : ""; }
    ta.addEventListener("input", dem); dem();
    ta.addEventListener("keydown", function (e) {      // Tab chen 2 dau cach thay vi nhay khoi o
      if (e.key === "Tab" && !e.shiftKey) { e.preventDefault(); var s = ta.selectionStart; ta.value = ta.value.slice(0, s) + "  " + ta.value.slice(ta.selectionEnd); ta.selectionStart = ta.selectionEnd = s + 2; }
    });
    var h = el("div", "tv-nut-hang"); h.style.marginTop = "20px";
    var ok = el("button", "tv-nut chinh"); ok.type = "submit"; ok.appendChild(icon("save")); ok.appendChild(document.createTextNode(laSua ? "Lưu thay đổi" : "Thêm vào thư viện")); h.appendChild(ok);
    var hu = nutBam("", "x", "Hủy", function () { if (laSua) xem(it.i); else if (chon != null) xem(chon); else rong(); }); h.appendChild(hu);
    f.appendChild(h); ct.appendChild(f);
    o.name.focus();
  }
  function sua(i) { chon = i; hash(i); veDs(); bieuMau(ITEMS.filter(function (x) { return x.i === i; })[0], true); }
  function moi(goc) { chon = null; hash(null); veDs(); bieuMau(goc || { name: "", desc: "", tags: "", commands: "" }, false); }
  function rong() {
    var ct = khungChiTiet(); thongBao(ct);
    var r = el("div", "tv-rong"); r.appendChild(el("h2", null, ITEMS.length ? "Chọn một tập lệnh bên trái" : "Thư viện đang trống"));
    r.appendChild(el("p", null, ITEMS.length ? "Hoặc bấm Thêm mới để lưu một tập lệnh của bạn." : "Bấm Thêm mới để lưu tập lệnh đầu tiên."));
    ct.appendChild(r);
  }

  $("tv-tim").addEventListener("input", function (e) { q = bo(e.target.value.trim()); ve(); });
  $("tv-xoa").addEventListener("click", function () { $("tv-tim").value = ""; q = ""; ve(); $("tv-tim").focus(); });
  $("tv-moi").addEventListener("click", function () { moi(); });
  ve();
  var h0 = (location.hash || "").replace("#", "");
  if (D.edit != null) sua(D.edit);
  else if (D.chon != null && ITEMS.some(function (x) { return x.i === D.chon; })) xem(D.chon);
  else if (/^\\d+$/.test(h0) && ITEMS.some(function (x) { return x.i === +h0; })) xem(+h0);
  else if (D.msg) rong();
  else if (ITEMS.length) xem(ITEMS.slice().sort(function (a, b) { return a.name.localeCompare(b.name, "vi"); })[0].i);
  else moi();
})();
</script>
"""


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

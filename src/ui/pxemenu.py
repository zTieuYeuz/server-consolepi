"""
Console Pi - MENU PXE: may khach boot qua mang thay menu de TU CHON kich ban.

VI SAO (anh Thoai 24/09/2026, "Buoc A"): truoc day PXE chi phuc vu DUNG 1
kich ban - kich ban vua bam "Dung" tren web. Muon cai may khac bang kich
ban khac thi phai quay lai web bam "Dung" kich ban do (dung lai anh dia
~1 phut). Kieu MDT thi nguoc lai: ky thuat vien dung TAI MAY chon.

MENU 2 TANG (anh Thoai 24/09/2026: "neu nhu la kich ban de lua chon thi co
1 cai a lua chon lam gi" - ban dau phai tick tung kich ban vao menu, tick
1 cai thi menu chi co 1 muc, vo nghia):
  Menu chinh:  1. Win PE (chua co - lam sau, hien san cho biet)
               2. Install Windows  >  TAT CA kich ban Windows dang co
               Khoi dong o cung / Khoi dong lai

CACH LAM - dung lai nguyen duong da kiem chung, khong viet lai:
  - Moi kich ban Windows (du thong tin) duoc dung 1 ANH DIA RIENG bang
    CHINH ham cua nut "Dung" (unattend.dung_dia_gpt_tu_dong) voi cau hinh
    nap Y HET nut "Dung" (deployos.cauhinh_tu_kichban). Ten file
    "_menu-<ten kich ban>.img": dau "_" de trang "Tai nguyen > File boot"
    khong liet ke (xem deployos._liet_ke), duoi .img nam trong danh sach
    route /deployos/pxeboot/ duoc phep phuc vu.
  - menu.ipxe (file iPXE tai DUNG 1 lan dau moi lan boot, xem pxe.py) doi
    tu 1 dong `sanboot` thanh 1 MENU cua chinh iPXE (lenh menu/item/choose).
    Muc mac dinh chay sau N giay neu khong ai bam - giu duoc che do "cam
    vao la tu cai" cho phong may.
  - Anh dia chi dung lai khi THAT SU can: "dau van tay" (noi dung kich ban
    + dia chi Pi + boot.wim + phien ban ma sinh script) khop thi dung lai
    anh cu. Moi anh vai tram MB, dung mat ~1 phut - dung lai het moi lan
    bat PXE thi rat cham.

GIOI HAN THAT:
  - Menu chu (iPXE chay TRUOC Windows, chi co man hinh chu, khong co dau
    tieng Viet, chon bang phim mui ten + Enter).
  - Moi muc dung CHE DO MANG cua kich ban dang "Dung" (dnsmasq chi chay 1
    che do mot luc) - dia chi Pi nhet vao anh dia la dia chi cua che do do.
  - Chi kich ban Windows (Linux van dung duong cu, chua co menu).
"""
import hashlib
import json
import os
import re
import unicodedata

from . import deployos as _d

FILE_CAUHINH = os.path.join(_d.DEPLOY_DIR, "menu-pxe.json")
TIEN_TO_ANH = "_menu-"
CHO_TOI_DA = 300          # giay
MAC_DINH = {"bat": False, "cho_giay": 10, "mac_dinh": "kichban"}


# ---------------------------------------------------------------- cau hinh
def doc_cauhinh():
    c = dict(MAC_DINH)
    try:
        with open(FILE_CAUHINH, encoding="utf-8") as f:
            c.update({k: v for k, v in json.load(f).items() if k in MAC_DINH})
    except (OSError, ValueError):
        pass
    try:
        c["cho_giay"] = max(0, min(CHO_TOI_DA, int(c["cho_giay"])))
    except (TypeError, ValueError):
        c["cho_giay"] = MAC_DINH["cho_giay"]
    if c["mac_dinh"] not in ("kichban", "odia"):
        c["mac_dinh"] = "kichban"
    c["bat"] = bool(c["bat"])
    return c


def luu_cauhinh(bat, cho_giay, mac_dinh):
    try:
        cho = max(0, min(CHO_TOI_DA, int(cho_giay)))
    except (TypeError, ValueError):
        return False, "Số giây chờ không hợp lệ."
    if mac_dinh not in ("kichban", "odia"):
        return False, "Mục mặc định không hợp lệ."
    try:
        os.makedirs(os.path.dirname(FILE_CAUHINH), exist_ok=True)
        with open(FILE_CAUHINH, "w", encoding="utf-8") as f:
            json.dump({"bat": bool(bat), "cho_giay": cho, "mac_dinh": mac_dinh},
                      f, ensure_ascii=False, indent=1)
    except OSError as e:
        return False, f"Không lưu được: {e}"
    return True, "Đã lưu cài đặt menu PXE."


def kichban_windows():
    """TAT CA kich ban Windows (khong can tick nua), theo thu tu ten."""
    return [k for k in _d.danh_sach_kichban() if k.get("os_ho") == "windows"]


def thieu_cua(kb, kieu_boot=None):
    """Nhung gi kich ban con thieu de dung duoc anh dia (rong = du)."""
    d = _d.cauhinh_tu_kichban(kb)
    if kieu_boot:
        d["kieu_boot"] = kieu_boot
    return _d.thieu_gi(d)


# ------------------------------------------------------------ anh dia rieng
def ten_anh(ten_file_kichban):
    goc = ten_file_kichban[:-5] if ten_file_kichban.endswith(".json") else ten_file_kichban
    # Ten nay nam trong URL cua lenh sanboot - chi giu ky tu an toan cho URL
    # (ten_an_toan con cho phep dau cach, dau cach se lam gay lenh iPXE).
    return TIEN_TO_ANH + re.sub(r"[^A-Za-z0-9._-]", "_", goc)[:120] + ".img"


def _dau_van_tay(kb, dia_chi_pi):
    """
    Thay doi BAT KY thu gi lam anh dia khac di thi dau van tay phai khac:
    noi dung kich ban, dia chi Pi nhet vao anh, boot.wim cua OS do, va ma
    nguon sinh script (cap nhat Console Pi -> dung lai cho chac).
    """
    from . import unattend as _u
    h = hashlib.sha256()
    kb_sach = {k: v for k, v in kb.items() if not k.startswith("_")}
    h.update(json.dumps(kb_sach, sort_keys=True, ensure_ascii=False).encode())
    h.update(dia_chi_pi.encode())
    for p in (_d.duong_boot_wim(kb.get("os_id", "")), _u.__file__, __file__):
        try:
            st = os.stat(p)
            h.update(f"{p}:{st.st_size}:{int(st.st_mtime)}".encode())
        except OSError:
            h.update(f"{p}:khong-co".encode())
    return h.hexdigest()[:16]


def _con_trong_mb():
    try:
        st = os.statvfs(_d.BOOT_DIR)
        return st.f_bavail * st.f_frsize // (1024 * 1024)
    except OSError:
        return 0


def dung_anh_menu(dia_chi_pi, kieu_boot, ten_kichban_dang_dung=""):
    """
    Dung (hoac dung lai neu da cu) anh dia cho moi kich ban Windows, tru
    kich ban dang "Dung" (no da co anh chinh). Xoa anh cua kich ban da xoa. Tra ve danh sach dong ket qua de hien cho nguoi dung.
    """
    from . import unattend as _u
    ket_qua = []
    can_giu = set()
    for kb in kichban_windows():
        ten = kb.get("ten_kichban", kb["_file"])
        if ten_kichban_dang_dung and ten == ten_kichban_dang_dung:
            continue
        d = _d.cauhinh_tu_kichban(kb)
        # Moi muc dung che do mang cua kich ban dang Dung - xem GIOI HAN.
        d["kieu_boot"] = kieu_boot
        thieu = _d.thieu_gi(d)
        if thieu:
            ket_qua.append(f'"{ten}": bỏ qua - ' + ", ".join(thieu) + ".")
            continue
        anh = ten_anh(kb["_file"])
        can_giu.add(anh)
        dau = _dau_van_tay(kb, dia_chi_pi)
        cu = _u.doc_dau_kichban(anh)
        if (cu and cu.get("dau_van_tay") == dau
                and os.path.isfile(os.path.join(_d.BOOT_DIR, anh))):
            ket_qua.append(f'"{ten}": ảnh đĩa vẫn đúng, dùng lại.')
            continue
        # Moi anh ~ kich thuoc boot.wim + file boot. Doi 1.5 lan + 300MB
        # cho chac (co ca file tam trong luc dung).
        try:
            can_mb = os.path.getsize(_d.duong_boot_wim(kb.get("os_id", ""))) * 3 // 2 // (1024 * 1024) + 300
        except OSError:
            can_mb = 1200
        if _con_trong_mb() < can_mb:
            ket_qua.append(f'"{ten}": KHÔNG dựng được - ổ đĩa còn {_con_trong_mb()} MB, '
                           f'cần khoảng {can_mb} MB.')
            can_giu.discard(anh)
            continue
        ok, msg = _u.dung_dia_gpt_tu_dong(d, dia_chi_pi, ten_dia=anh,
                                          dau_them={"dau_van_tay": dau})
        ket_qua.append(f'"{ten}": ' + ("đã dựng ảnh đĩa." if ok else f"LỖI - {msg}"))
        if not ok:
            can_giu.discard(anh)
    # Don anh cua kich ban da xoa / khong con la Windows - moi anh vai tram MB.
    try:
        for n in os.listdir(_d.BOOT_DIR):
            if n.startswith(TIEN_TO_ANH) and n.endswith(".img") and n not in can_giu:
                for x in (n, n + ".json"):
                    try:
                        os.remove(os.path.join(_d.BOOT_DIR, x))
                    except OSError:
                        pass
    except OSError:
        pass
    return ket_qua


# ---------------------------------------------------------------- menu iPXE
def _chu_ipxe(s, dai=60):
    """
    Chu cho menu iPXE: iPXE chi ve duoc ASCII -> bo dau tieng Viet; bo ky
    tu dac biet cua iPXE ($ { } ...) de ten kich ban khong the chen lenh.
    """
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z0-9 .,_()+:/-]", " ", s)
    s = re.sub(r" +", " ", s).strip()
    return s[:dai] or "(khong ten)"


def muc_menu(kb_dang_dung):
    """
    Danh sach (nhan, file anh) theo DUNG thu tu hien trong menu - dung cho
    ca script iPXE lan phan xem truoc tren web.
    kb_dang_dung: dict dau vet anh chinh (unattend.doc_dau_kichban()).
    """
    from . import unattend as _u
    muc = []
    if kb_dang_dung is not None and _u.co_san_dia_gpt_tu_dong():
        muc.append((kb_dang_dung.get("ten_kichban") or "Kich ban dang dung",
                    _u.TEN_DIA_GPT_TU_DONG))
    ten_dang_dung = (kb_dang_dung or {}).get("ten_kichban")
    for kb in kichban_windows():
        ten = kb.get("ten_kichban", kb["_file"])
        anh = ten_anh(kb["_file"])
        if ten == ten_dang_dung:
            continue
        if os.path.isfile(os.path.join(_d.BOOT_DIR, anh)):
            muc.append((ten, anh))
    return muc


def sinh_script(goc):
    """
    Script iPXE menu 2 tang. goc = http://<dia chi Pi>/deployos/pxeboot

    Menu chinh -> "Install Windows" -> menu con liet ke kich ban. Mac dinh
    "kich ban dang Dung" thi CA 2 tang cung dem nguoc (phong may: khong ai
    bam van tu cai kich ban dang Dung); mac dinh "o cung" thi menu con cho
    nguoi bam. Esc o menu con = quay lai menu chinh, o menu chinh = o cung.
    """
    from . import unattend as _u
    c = doc_cauhinh()
    muc = muc_menu(_u.doc_dau_kichban())
    tu_cai = c["mac_dinh"] == "kichban" and bool(muc)
    # --timeout tinh bang mili giay; 0 giay = cho mai den khi co nguoi bam.
    cho = f"--timeout {c['cho_giay'] * 1000} " if c["cho_giay"] > 0 else ""
    dong = ["#!ipxe", ":menu",
            "menu Console System - Cai dat qua mang",
            "item --gap -- Chon bang phim mui ten + Enter:",
            "item --gap -- ",
            # iPXE "gap" = dong chu KHONG chon duoc - WinPE chua co (lam sau).
            "item --gap -- 1. Win PE (chua co - sap ra mat)",
            f"item win 2. Install Windows > ({len(muc)} kich ban)",
            "item --gap -- ",
            "item odia Khoi dong o cung (KHONG cai gi)",
            "item lai Khoi dong lai may",
            f"choose {cho}--default {'win' if tu_cai else 'odia'} chon || goto odia",
            "goto ${chon}", "",
            ":win",
            "menu Install Windows - chon kich ban cai dat"]
    if not muc:
        dong.append("item --gap -- (Chua co kich ban Windows nao dung duoc)")
    for i, (nhan, _anh) in enumerate(muc):
        dong.append(f"item kb{i} {_chu_ipxe(nhan)}")
    dong += ["item --gap -- ",
             "item menu < Quay lai menu chinh"]
    # Menu con: chi dem nguoc khi dang o che do tu cai.
    cho_con = cho if tu_cai else ""
    dong += [f"choose {cho_con}--default {'kb0' if muc else 'menu'} chon || goto menu",
             "goto ${chon}", ""]
    for i, (nhan, anh) in enumerate(muc):
        dong += [f":kb{i}",
                 f"echo Dang nap: {_chu_ipxe(nhan)}",
                 f"sanboot --no-describe {goc}/{anh} || goto loi", ""]
    dong += [":odia",
             "echo Khoi dong tu o cung...",
             "exit", "",
             ":lai",
             "reboot", "",
             ":loi",
             "echo LOI: khong nap duoc anh dia cai dat tu Console System.",
             "prompt Bam phim bat ky de quay lai menu...",
             "goto win", ""]
    return "\n".join(dong)


def menu_dang_dung():
    """True neu menu dang bat VA co it nhat 1 muc de chon."""
    from . import unattend as _u
    return doc_cauhinh()["bat"] and _u.co_san_dia_gpt_tu_dong()


# ------------------------------------------------------------------- web
def _xem_truoc(c, muc):
    """Ve lai 2 man hinh menu may khach se thay (cung chu voi sinh_script)."""
    tu_cai = c["mac_dinh"] == "kichban" and bool(muc)
    # iPXE gop nhieu dau cach thanh 1 -> xem truoc cung khong can can cot.
    chinh = ["  Console System - Cai dat qua mang", "",
             "    Chon bang phim mui ten + Enter:", "",
             "    1. Win PE (chua co - sap ra mat)",
             ("  > " if tu_cai else "    ") +
             f"2. Install Windows > ({len(muc)} kich ban)", "",
             ("    " if tu_cai else "  > ") + "Khoi dong o cung (KHONG cai gi)",
             "    Khoi dong lai may"]
    con = ["  Install Windows - chon kich ban cai dat", ""]
    if not muc:
        con.append("    (Chua co kich ban Windows nao dung duoc)")
    for i, (nhan, _a) in enumerate(muc):
        con.append(("  > " if i == 0 else "    ") + _chu_ipxe(nhan))
    con += ["", ("  > " if not muc else "    ") + "< Quay lai menu chinh"]
    if c["cho_giay"]:
        chinh += ["", f"  (tu chon muc > sau {c['cho_giay']} giay)"]
        if tu_cai:
            con += ["", f"  (tu chon muc > sau {c['cho_giay']} giay)"]
    return "\n".join(chinh), "\n".join(con)


def khoi_cai_dat_html(esc):
    """Hop cai dat menu + xem truoc menu may khach se thay (trang Kich ban)."""
    from . import unattend as _u
    c = doc_cauhinh()
    muc = muc_menu(_u.doc_dau_kichban())
    so_win = len(kichban_windows())
    man_chinh, man_con = _xem_truoc(c, muc)
    if not c["bat"]:
        tinh_trang = ('<div class="msg warn" style="margin-top:0;">Menu đang '
                      '<strong>TẮT</strong> &mdash; máy khách boot qua mạng vào '
                      'thẳng kịch bản đang "Dùng", không hỏi gì.</div>')
    elif not muc:
        tinh_trang = ('<div class="msg warn" style="margin-top:0;">Menu đang bật '
                      'nhưng chưa có mục nào: bấm "Dùng" một kịch bản Windows '
                      'để bật PXE.</div>')
    else:
        tinh_trang = (f'<div class="msg ok" style="margin-top:0;">Menu đang '
                      f'<strong>BẬT</strong> &mdash; "Install Windows" có '
                      f'{len(muc)} kịch bản để chọn.</div>')
    chk = "checked" if c["bat"] else ""
    md_kb = "checked" if c["mac_dinh"] == "kichban" else ""
    md_od = "checked" if c["mac_dinh"] == "odia" else ""
    kieu_pre = ("background:#000;color:#ddd;padding:12px;border-radius:6px;"
                "overflow-x:auto;font-size:13px;line-height:1.5;margin:6px 0 12px;")
    return f"""
    <div class="card">
      <h3>Menu khi máy khách khởi động qua mạng</h3>
      {tinh_trang}
      <p style="color:#8b93a1;font-size:13.5px;margin:8px 0 12px;">
        Bật menu thì máy khách thấy menu để <strong>tự chọn tại máy</strong>
        (kiểu MDT): <strong>1. Win PE</strong> (sắp có) và <strong>2. Install
        Windows</strong> &mdash; vào mục 2 sẽ thấy <strong>tất cả kịch bản
        Windows</strong> đang có (hiện có {so_win}), không cần chọn từng cái.
        Mỗi kịch bản cần một ảnh đĩa riêng (vài trăm MB) &mdash; lần đầu dựng
        mất khoảng 1 phút mỗi cái, các lần sau chỉ dựng lại cái nào đã sửa.
        Tất cả dùng chế độ mạng của kịch bản đang "Dùng".</p>
      <form method="POST" action="/deployos/menu-pxe/luu">
        <label style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
          <input type="checkbox" name="bat" value="1" {chk}>
          Bật menu chọn kịch bản</label>
        <label style="display:block;margin-bottom:10px;">Tự chọn mục mặc định sau
          <input type="number" name="cho_giay" min="0" max="{CHO_TOI_DA}"
                 value="{c['cho_giay']}" style="width:80px;"> giây
          <small style="color:#8b93a1;">(0 = chờ mãi đến khi có người bấm)</small></label>
        <div style="margin-bottom:12px;">Mục mặc định:
          <label style="margin-left:10px;"><input type="radio" name="mac_dinh"
            value="kichban" {md_kb}> Kịch bản đang "Dùng" (tự cài &mdash; phòng máy)</label>
          <label style="margin-left:10px;"><input type="radio" name="mac_dinh"
            value="odia" {md_od}> Khởi động ổ cứng (an toàn &mdash; không ai bấm thì
            không cài gì)</label>
        </div>
        <button type="submit" data-busy="Đang cập nhật menu... có thể mất vài phút">
          Lưu cài đặt menu</button>
      </form>
      <details style="margin-top:14px;">
        <summary>Xem trước màn hình máy khách</summary>
        <div style="color:#8b93a1;font-size:13px;margin-top:10px;">Menu chính:</div>
        <pre style="{kieu_pre}">{esc(man_chinh)}</pre>
        <div style="color:#8b93a1;font-size:13px;">Sau khi chọn "2. Install Windows":</div>
        <pre style="{kieu_pre}">{esc(man_con)}</pre>
      </details>
    </div>"""


def trang_thai_html(k, esc):
    """Cot "Menu PXE" cua bang kich ban: kich ban nay co hien trong menu khong."""
    if k.get("os_ho") != "windows":
        return '<small style="color:#8b93a1;">chỉ Windows</small>'
    thieu = thieu_cua(k)
    if thieu:
        return (f'<small style="color:#f59e0b;">thiếu: '
                f'{esc(", ".join(thieu))}</small>')
    return '<small style="color:#4CAF50;">&#10003; Có trong menu</small>'

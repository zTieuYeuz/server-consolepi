# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""RustDesk phia quan ly may tram: cai client RustDesk len may qua agent/WinRM va liet ke may/ID/mat khau. Logic may chu: integrations/rustdesk_may_chu.py."""
import os
import re
import threading
import time
import uuid

from flask import Response, jsonify, request, send_file, session

from consolesystem.features.uem import uem_dieukhien as DK
from consolesystem.core.nhatky import bo_qua as _bo_qua
from consolesystem.integrations import rustdesk_giam_sat as GS
from consolesystem.integrations import rustdesk_may_chu as RD
from ui import tk_dulieu as DL
from ui import uem_dulieu as UD
from ui import uem_agent as UA


def cai_client_may(m):
    """Cai qua agent/WinRM, kem May chu ID / chuyen tiep / Key. Tra (ok, thong_diep, id)."""
    return RD.cai_va_ghi(lambda sc: DK._chay(m, sc), m["id"])


def bang_dieu_khien():
    """Du lieu cho buoc 5: moi may (co ID RustDesk hoac co agent), trang thai, + cac ID da dang ky voi may chu nhung chua gan vao may nao."""
    cfg = RD.doc_cfg()
    ds_may = DL.MAY.doc()
    may = []
    for m in ds_may:
        ban = cfg["may"].get(m["id"]) or {}
        co_ag = bool(UA.co_agent(m))
        if m.get("an") or not (ban.get("id") or co_ag):
            continue
        may.append({"mid": m["id"], "ten": m.get("ten") or m["ip"], "ip": m["ip"], "id": ban.get("id", ""), "mk": ban.get("mk", ""), "agent": co_ag,
                    "online": bool(UA.con_song(m)) if co_ag else None, "dong_bo": bool(ban.get("dong_bo", True)) or not cfg.get("mk_chung")})
    da_gan = {v.get("id") for v in cfg["may"].values() if v.get("id")}
    ip_ten = {m["ip"]: (m.get("ten") or m["ip"]) for m in ds_may}
    ten_hoa = {(m.get("ten") or "").upper(): (m.get("ten") or m["ip"]) for m in ds_may if m.get("ten")}
    chua = []
    for x in RD.thiet_bi():
        if x["id"] in da_gan:
            continue
        t = GS.thong_tin_id(x["id"])
        goi_y = ten_hoa.get((t.get("ten") or "").upper()) or ip_ten.get(x["ip"], "")   # cung ten may Windows -> goi y gan
        chua.append({"id": x["id"], "ip": x["ip"], "tao": x["tao"], "goi_y": goi_y, "ten_may": t.get("ten", ""), "nguoi": t.get("nguoi", ""),
                     "hdh": t.get("hdh", ""), "ban": t.get("ban", ""), "online": t["online"],
                     "nhip": time.strftime("%d/%m %H:%M", time.localtime(t["luc_nhip"])) if t["luc_nhip"] else ""})
    return {"may": may, "chua_gan": chua, "che_do": GS.cai_dat()["che_do"], "tat_ca": [{"mid": m["id"], "ten": m.get("ten") or m["ip"]} for m in ds_may if not m.get("an")]}


def register_uem_rustdesk(app):
    from consolesystem.features.uem.uem_dieukhien import may_theo_id
    from ui.uem_trang import chuyen

    @app.route("/uem/may/<mid>/rustdesk/luu", methods=["POST"])
    def uem_rustdesk_luu(mid):
        m = may_theo_id(mid)
        i, mk = (request.form.get("id") or "").replace(" ", ""), (request.form.get("mk") or "").strip()
        if not re.fullmatch(r"\d{6,12}", i) or not re.fullmatch(r"[A-Za-z0-9!@#$%^&*._\-]{4,64}", mk):
            return chuyen(f"/uem/may/{mid}/tu-xa", "ID phải là 6 đến 12 chữ số; mật khẩu 4 đến 64 ký tự (chữ, số, ký hiệu thường).", False)
        cfg = RD.doc_cfg()
        cfg["may"][m["id"]] = {"id": i, "mk": mk, "luc": int(time.time()), "dong_bo": (not cfg.get("mk_chung")) or mk == cfg.get("mk_chung")}
        RD.luu_cfg(cfg)
        if cfg.get("mk_chung") and mk != cfg["mk_chung"]:
            dong_bo({m["id"]})
        return chuyen(f"/uem/may/{mid}/tu-xa", "Đã lưu ID và mật khẩu RustDesk của máy.")

    @app.route("/rustdesk/api/thiet-bi")
    def rustdesk_api_dev():
        cfg = RD.doc_cfg()
        ds_may = DL.MAY.doc()
        ten = {m["id"]: (m.get("ten") or m["ip"]) for m in ds_may}
        agent = [{"id": m["id"], "ten": m.get("ten") or m["ip"], "ip": m["ip"], "online": UA.con_song(m)} for m in ds_may if UA.co_agent(m) and not m.get("an")]
        may = [{"ten": ten.get(k, k), "id": v.get("id", ""), "mk": v.get("mk", ""), "dong_bo": bool(v.get("dong_bo", True)) or not cfg.get("mk_chung"),
                "loi": v.get("loi", "")} for k, v in cfg["may"].items()]
        theo_id = {v.get("id"): ten.get(k, "") for k, v in cfg["may"].items() if v.get("id")}
        theo_ip = {m["ip"]: (m.get("ten") or "") for m in ds_may}
        ds = [dict(x, ten=theo_id.get(x["id"]) or theo_ip.get(x["ip"], "")) for x in RD.thiet_bi()]   # ten may: theo ID da ghi, khong thi theo IP
        return jsonify({"ds": ds, "may": may, "agent": agent, "mk_chung": cfg.get("mk_chung", ""), "dong_bo": dict(_DONG_BO)})

    @app.route("/rustdesk/api/bang")
    def rustdesk_api_bang():
        return jsonify(bang_dieu_khien())

    @app.route("/rustdesk/api/ket-noi", methods=["POST"])
    def rustdesk_api_ket_noi():
        j = request.get_json(silent=True) or {}
        return jsonify(bat_dau_ket_noi(str(j.get("mid", "")), session.get("user") or "Quản trị viên tại màn hình Console"))

    @app.route("/rustdesk/api/ket-noi/<ma>")
    def rustdesk_api_ket_noi_tt(ma):
        with _KHOA_KN:
            v = _KET_NOI.get(ma)
            return jsonify(dict(v) if v else {"xong": True, "ok": False, "tb": "Không tìm thấy yêu cầu (có thể Console vừa khởi động lại)."})

    @app.route("/rustdesk/api/cai-dat", methods=["GET", "POST"])
    def rustdesk_api_cai_dat():
        if request.method == "POST":
            j = request.get_json(silent=True) or {}
            ok, kq = GS.luu_cai_dat(str(j.get("che_do", "")), bool(j.get("ghi_hinh")), j.get("ghi_hinh_gb"))
            if not ok:
                return jsonify({"ok": False, "tb": kq})
            tb = "Đã lưu cài đặt."
            if kq:                                               # bat/tat ghi hinh: file cai moi + day xuong may da cai
                tb += " " + RD.cap_nhat_kho()[1]
                tb += " Đang áp dụng ghi hình xuống các máy có agent..." if ap_cau_hinh() else " Đang có việc khác chạy, bấm Áp dụng ở bước 4 sau."
            return jsonify({"ok": True, "tb": tb})
        return jsonify(tt_cai_dat())

    @app.route("/rustdesk/api/lich-su")
    def rustdesk_api_lich_su():
        return jsonify({"ds": lich_su_day_du()})

    @app.route("/rustdesk/ghi-hinh/<mid>/<ten>")
    def rustdesk_ghi_hinh_xem(mid, ten):
        f = GS.duong_ghi_hinh(mid, ten)
        if not f:
            return Response("Không có bản ghi này (có thể đã bị xóa do vượt dung lượng).", status=404, mimetype="text/plain; charset=utf-8")
        return send_file(f, mimetype="video/webm" if ten.endswith(".webm") else "video/mp4", conditional=True,
                         as_attachment=request.args.get("tai") == "1", download_name=ten)

    @app.route("/rustdesk/api/ghi-hinh/xoa", methods=["POST"])
    def rustdesk_api_ghi_hinh_xoa():
        j = request.get_json(silent=True) or {}
        f = GS.duong_ghi_hinh(str(j.get("mid", "")), str(j.get("ten", "")))
        if not f:
            return jsonify({"ok": False, "tb": "Không có bản ghi này."})
        os.remove(f)
        return jsonify({"ok": True, "tb": "Đã xóa bản ghi."})

    @app.route("/rustdesk/api/gan", methods=["POST"])
    def rustdesk_api_gan():
        j = request.get_json(silent=True) or {}
        i, mid = str(j.get("id", "")), str(j.get("mid", ""))
        if not any(x["id"] == i for x in RD.thiet_bi()) or not any(x["id"] == mid for x in DL.MAY.doc()):
            return jsonify({"ok": False, "tb": "ID hoặc máy không hợp lệ."})
        RD.ghi_may(mid, i)
        return jsonify({"ok": True, "tb": "Đã gắn ID %s vào máy." % i})

    @app.route("/rustdesk/api/kiem-tra", methods=["POST"])
    def rustdesk_api_kiem_tra():
        m = next((x for x in DL.MAY.doc() if x["id"] == str((request.get_json(silent=True) or {}).get("mid", ""))), None)
        if not m or not UA.co_agent(m):
            return jsonify({"ok": False, "tb": "Chỉ kiểm tra được máy có agent."})
        ok, kq = kiem_tra_may(m)
        return jsonify({"ok": ok, "kq": kq if ok else None, "tb": "" if ok else kq})

    @app.route("/rustdesk/api/mat-khau", methods=["POST"])
    def rustdesk_api_mk():
        ok, tb = RD.dat_mk_chung(str((request.get_json(silent=True) or {}).get("mk", "")))
        if ok:
            dong_bo()
        return jsonify({"ok": ok, "tb": tb})

    @app.route("/rustdesk/api/ap-cau-hinh", methods=["POST"])
    def rustdesk_api_ap_cau_hinh():
        return jsonify({"ok": ap_cau_hinh(), "tb": "Đang áp dụng..."})

    @app.route("/rustdesk/api/dong-bo", methods=["POST"])
    def rustdesk_api_dong_bo():
        if not RD.mk_chung():
            return jsonify({"ok": False, "tb": "Chưa đặt mật khẩu chung."})
        return jsonify({"ok": dong_bo(), "tb": "Đang đồng bộ..."})

    @app.route("/rustdesk/api/cai-client", methods=["POST"])
    def rustdesk_api_cai_client():
        ids = (request.get_json(silent=True) or {}).get("may") or []
        kq = []
        for m in DL.MAY.doc():
            if m["id"] in ids:
                ok, tb, _id = cai_client_may(m)
                kq.append({"ten": m.get("ten") or m["ip"], "ok": ok, "tb": tb})
        return jsonify({"ok": True, "kq": kq})

    GS.dang_ky_thong_bao(thong_bao_may)
    khoi_dong_bo_lap()


PS_KIEM_TRA = r"""$rd = Join-Path $env:ProgramFiles 'RustDesk\rustdesk.exe'
if (-not (Test-Path $rd)) { 'RDK=CHUA_CAI'; return }
$v = (Get-Item $rd).VersionInfo.ProductVersion
$s = Get-Service RustDesk -ErrorAction SilentlyContinue
$f = 'C:\Windows\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\config\RustDesk2.toml'
$t = if (Test-Path $f) { Get-Content $f -Raw } else { '' }
$ms = [regex]::Match($t, "(?m)^custom-rendezvous-server = '([^']*)'").Groups[1].Value
$mr = [regex]::Match($t, "(?m)^relay-server = '([^']*)'").Groups[1].Value
$md = [regex]::Match($t, "(?m)^allow-auto-record-incoming = '([^']*)'").Groups[1].Value
'RDK=OK|' + $v + '|' + $(if ($s) { [string]$s.Status } else { 'KHONG_CO_DICH_VU' }) + '|' + $ms + '|' + $mr + '|' + $md + '|' + ((& $rd --get-id | Out-String).Trim())"""


def kiem_tra_may(m):
    """Doc trang thai RustDesk tren may qua agent/WinRM. (ok, {ban, dich_vu, may_chu, relay, ghi_hinh, id, dung_may_chu} hoac thong_diep loi)."""
    ok, out = DK._chay(m, PS_KIEM_TRA)
    if not ok:
        return False, out[-200:]
    mm = re.search(r"RDK=(CHUA_CAI|OK\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|(\d*))", out or "")
    if not mm:
        return False, "Không đọc được kết quả từ máy."
    if mm.group(1) == "CHUA_CAI":
        return True, {"cai": False}
    dc = RD.dia_chi()
    return True, {"cai": True, "ban": mm.group(2), "dich_vu": mm.group(3), "may_chu": mm.group(4), "relay": mm.group(5), "ghi_hinh": mm.group(6) == "Y", "id": mm.group(7),
                  "dung_may_chu": mm.group(4) == dc["id"] and mm.group(5) == dc["relay"]}


_DONG_BO = {"dang": False, "tb": ""}


def _dong_bo_nen(chi=None):
    """Day mat khau chung xuong cac may (qua agent/WinRM) chua dong bo. Chay nen, ghi ket qua tung may."""
    try:
        mk = RD.mk_chung()
        if not mk:
            return
        ds = {m["id"]: m for m in DL.MAY.doc()}
        ok_n = loi_n = 0
        for mid, v in list(RD.doc_cfg()["may"].items()):
            if (chi and mid not in chi) or (v.get("dong_bo") and v.get("mk") == mk) or mid not in ds:
                continue
            ok, out = DK._chay(ds[mid], RD.script_dat_mk(mk))
            d = RD.doc_cfg()
            if mid in d["may"]:
                if ok and "RUSTDESK_MK_OK" in (out or ""):
                    d["may"][mid].update(mk=mk, dong_bo=True, loi="")
                    ok_n += 1
                else:
                    d["may"][mid].update(dong_bo=False, loi=(out or "")[-120:])
                    loi_n += 1
                RD.luu_cfg(d)
        _DONG_BO["tb"] = "Đồng bộ xong: %d máy thành công, %d máy chưa được (máy tắt hoặc mất agent, bấm Đồng bộ lại sau)." % (ok_n, loi_n)
    finally:
        _DONG_BO["dang"] = False


def _ap_cau_hinh_nen():
    """Day May chu ID / chuyen tiep + khoa xuong MOI may co agent (qua agent/WinRM): may co RustDesk thi doi, may chua cai thi bo qua.
    May tim thay ID thi them vao danh sach RustDesk (mat khau de trong cho toi khi dat mat khau chung / nhap tay)."""
    try:
        sc = RD.script_cau_hinh()
        ok_n = loi_n = bo_qua = 0
        for m in DL.MAY.doc():
            if m.get("an") or not UA.co_agent(m):
                continue
            ok, out = DK._chay(m, sc)
            out = out or ""
            if ok and "RUSTDESK_CHUA_CAI" in out:
                bo_qua += 1
            elif ok and "RUSTDESK_CFG_OK" in out:
                ok_n += 1
                i = re.search(r"RUSTDESK_ID=(\d{6,12})", out)
                if i:
                    d = RD.doc_cfg()
                    if m["id"] not in d["may"]:
                        d["may"][m["id"]] = {"id": i.group(1), "mk": "", "luc": int(time.time()), "dong_bo": not d.get("mk_chung")}
                        RD.luu_cfg(d)
            else:
                loi_n += 1
        _DONG_BO["tb"] = ("Áp dụng địa chỉ máy chủ xong: %d máy đã đổi, %d máy chưa cài RustDesk (bỏ qua), %d máy lỗi (tắt hoặc mất agent). "
                          "Máy đã đổi cần mở lại ứng dụng RustDesk." % (ok_n, bo_qua, loi_n))
    except RuntimeError as e:
        _DONG_BO["tb"] = str(e)
    finally:
        _DONG_BO["dang"] = False


def ap_cau_hinh():
    if _DONG_BO["dang"]:
        return False
    _DONG_BO.update(dang=True, tb="Đang áp dụng địa chỉ máy chủ xuống các máy...")
    import threading
    threading.Thread(target=_ap_cau_hinh_nen, daemon=True, name="rustdesk-ap-cau-hinh").start()
    return True


def dong_bo(chi=None):
    if _DONG_BO["dang"]:
        return False
    _DONG_BO.update(dang=True, tb="Đang áp dụng mật khẩu xuống các máy...")
    import threading
    threading.Thread(target=_dong_bo_nen, args=(chi,), daemon=True, name="rustdesk-dong-bo").start()
    return True


def khoi_tu_xa(m):
    """The 'Dieu khien bang RustDesk' cho tab Ho tro tu xa cua may: ID + mat khau da luu, nut mo ung dung RustDesk tren may nguoi quan tri."""
    from consolesystem.core.esc import esc_html as _e
    ban = (RD.doc_cfg().get("may") or {}).get(m["id"])
    st = RD.trang_thai()
    if not st["da_cai"]:
        return ('<div class="card"><h3>Điều khiển bằng RustDesk</h3><p class="tk-ghi">Chưa cài máy chủ RustDesk. Vào <a href="/rustdesk">RustDesk</a> để cài, rồi cài client lên máy này.</p></div>')
    if not ban:
        goi_y = next((x["id"] for x in RD.thiet_bi() if x["ip"] == m.get("ip")), "")      # ID cua may da dang ky voi may chu tu cung dia chi IP
        return ('<div class="card"><h3>Điều khiển bằng RustDesk</h3><p class="tk-ghi">Máy này chưa có ID RustDesk trong Console System. Cách 1: vào <a href="/rustdesk">RustDesk</a>, '
                'chọn máy rồi bấm <b>Cài lên máy đã chọn</b> (máy phải có agent), hoặc cài file <b>Cai-RustDesk-ConsoleSystem.msi</b> bằng Triển khai phần mềm (ID tự ghi vào đây). Cách 2: máy đã cài file .msi bằng tay (trỏ về máy chủ <b>' + _e(st["dia_chi"]["id"]) + '</b>): nhập ID (xem trong RustDesk trên máy đó) và mật khẩu chung:</p>'
                f'<form method="POST" action="/uem/may/{m["id"]}/rustdesk/luu" class="tk-hang"><input type="text" name="id" value="' + _e(goi_y) + '" placeholder="ID RustDesk (số)" required style="max-width:200px;margin:0;">'
                '<input type="text" name="mk" value="' + _e(RD.mk_chung()) + '" placeholder="Mật khẩu cố định" required autocomplete="off" style="max-width:220px;margin:0;"><button class="tk-nut chinh" type="submit">Lưu</button></form></div>')
    i, mk = _e(ban["id"]), _e(ban["mk"])
    return (f'<div class="card"><h3>Điều khiển bằng RustDesk</h3>'
            f'<p class="tk-ghi">RustDesk không chạy trong trình duyệt (khác VNC phía trên): bấm nút để mở <b>ứng dụng RustDesk đã cài trên máy của anh</b> và kết nối thẳng xuống máy này. '
            f'Máy anh đang ngồi cần RustDesk trỏ về máy chủ <b>{_e(st["dia_chi"]["id"])}</b>: tải và chạy <a href="/rustdesk/Cai-RustDesk-ConsoleSystem.msi">file cài RustDesk</a> một lần là xong.</p>'
            f'<div class="uem-2"><div>ID: <span class="rd-k" style="font-family:monospace;user-select:all;">{i}</span></div><div>Mật khẩu: <span style="font-family:monospace;user-select:all;">{mk}</span></div></div>'
            f'<div class="tk-hang" style="margin-top:10px;"><a class="tk-nut chinh" href="rustdesk://connection/new/{i}?password={mk}">Mở RustDesk và kết nối</a>'
            f'<a class="tk-nut" href="/rustdesk">Trang RustDesk (khóa, tải client)</a></div></div>')


# ------------------------------------------------------------------ ket noi theo che do (thong bao / xin phep 5 phut)
_KET_NOI = {}                     # ma -> {xong, ok, tb, url, luc}
_KHOA_KN = threading.Lock()


def _ps_chuoi(x):
    return "'" + str(x).replace("'", "''") + "'"


def ps_thong_bao(noi_dung, giay=60):
    """Hien thong bao (nut OK, khong cho) giua man hinh phien dang dang nhap - chay bang SYSTEM qua agent/WinRM."""
    return ("$sig = '[DllImport(\"wtsapi32.dll\", CharSet = CharSet.Unicode)] public static extern bool WTSSendMessage(IntPtr h, int sid, string t, int tl, string m, int ml, int s, int to, out int r, bool w); "
            "[DllImport(\"kernel32.dll\")] public static extern uint WTSGetActiveConsoleSessionId();'\n"
            "Add-Type -MemberDefinition $sig -Name W -Namespace CsRd -ErrorAction SilentlyContinue\n"
            "$sid = [CsRd.W]::WTSGetActiveConsoleSessionId()\nif ($sid -eq 4294967295) { 'TB_KHONG_PHIEN'; return }\n"
            "$t = 'Console System'\n$m = %s\n$r = 0\n"
            "$ok = [CsRd.W]::WTSSendMessage([IntPtr]::Zero, [int]$sid, $t, $t.Length * 2, $m, $m.Length * 2, 0x40 -bor 0x40000, %d, [ref]$r, $false)\n"
            "if ($ok) { 'TB_OK' } else { 'TB_LOI' }" % (_ps_chuoi(noi_dung), int(giay)))


def _may_theo_rid(rid):
    cfg = RD.doc_cfg()
    mid = next((k for k, v in cfg["may"].items() if v.get("id") == str(rid)), None)
    return next((m for m in DL.MAY.doc() if m["id"] == mid), None) if mid else None


def thong_bao_may(rid, noi_dung):
    """Goi tu giam sat (che do thong bao): co ket noi RustDesk da xac thuc vao may co ID rid."""
    m = _may_theo_rid(rid)
    if not m or not UA.co_agent(m) or not UA.con_song(m):
        return False
    ok, out = DK._chay(m, ps_thong_bao(noi_dung))
    return ok and "TB_OK" in (out or "")


def _ghi_console(m, rid, nguoi, kq):
    GS.ghi_su_kien(loai="console", rid=rid, mid=m["id"], ten_may=m.get("ten") or m["ip"], nguoi=nguoi, kq=kq)


def bat_dau_ket_noi(mid, nguoi):
    """Nut Ket noi o buoc 5. Che do thong bao: tra ngay lien ket rustdesk://. Che do xin phep: hien hop Co/Khong tren may (cho toi 5 phut),
    tra ma de trang hoi tien do; dong y thi may chu cho phep ket noi moi trong 5 phut, khong thi moi ket noi bi ngat."""
    m = next((x for x in DL.MAY.doc() if x["id"] == mid), None)
    ban = (RD.doc_cfg()["may"].get(m["id"]) if m else None) or {}
    if not m or not ban.get("id"):
        return {"ok": False, "xong": True, "tb": "Máy này chưa có ID RustDesk."}
    rid, url = ban["id"], "rustdesk://connection/new/%s?password=%s" % (ban["id"], ban.get("mk", ""))
    if GS.cai_dat()["che_do"] == "thong_bao":
        GS.dat_cho_ten(rid, nguoi)
        _ghi_console(m, rid, nguoi, "Mở kết nối")
        UD.ghi_tac_vu(m["id"], "tu_xa", "Mở điều khiển từ xa (RustDesk)", True, "ID %s, người: %s" % (rid, nguoi))
        return {"ok": True, "xong": True, "url": url, "tb": "Đang mở RustDesk. Máy đó sẽ hiện thông báo có người đang kết nối."}
    if not UA.co_agent(m) or not UA.con_song(m):
        return {"ok": False, "xong": True, "tb": "Chế độ Xin phép cần máy có agent đang online để hiện hộp xin phép. Máy này đang offline hoặc không có agent."}
    ma = uuid.uuid4().hex[:12]
    with _KHOA_KN:
        for k in [k for k, v in _KET_NOI.items() if time.time() - v["luc"] > 3600]:
            _KET_NOI.pop(k, None)
        _KET_NOI[ma] = {"xong": False, "ok": False, "tb": "Đang chờ người dùng trên máy %s xác nhận (tối đa 5 phút)..." % (m.get("ten") or m["ip"]), "url": "", "luc": time.time(), "ma": ma}
    threading.Thread(target=_xin_phep_nen, args=(ma, m, rid, url, nguoi), daemon=True, name="rustdesk-xin-phep").start()
    return {"ok": True, "xong": False, "ma": ma, "tb": _KET_NOI[ma]["tb"]}


def _xin_phep_nen(ma, m, rid, url, nguoi):
    loi = {"TU_CHOI": "Người dùng đã từ chối.", "HET_GIO": "Người dùng không xác nhận trong 5 phút, đã hủy.",
           "KHONG_CO_PHIEN": "Máy không có ai đăng nhập (không hiện được hộp xin phép), đã hủy."}
    try:
        kq = UA.hoi_phep(m["id"], "%s (quản trị Console System) xin quyền kết nối vào máy tính của bạn bằng RustDesk để hỗ trợ.\n\n"
                         "Bấm Yes (Có) để cho phép, No (Không) để từ chối. Sau 5 phút không trả lời sẽ tự từ chối." % nguoi, GS.CHO_DUYET_GIAY)
    except Exception as e:                    # mat agent giua chung
        kq, loi["LOI"] = "LOI", "Không hỏi được máy: %s" % e
    if kq == "CHO_PHEP":
        GS.dat_duyet(rid, nguoi)
        tb, ok = "Người dùng đã đồng ý. Đang mở RustDesk (có 5 phút để bắt đầu kết nối).", True
    else:
        tb, ok = loi.get(kq, "Kết quả không rõ: %s" % kq), False
    _ghi_console(m, rid, nguoi, "Đồng ý" if ok else tb)
    UD.ghi_tac_vu(m["id"], "tu_xa", "Xin phép điều khiển từ xa (RustDesk)", ok, "%s: %s" % (nguoi, tb))
    with _KHOA_KN:
        _KET_NOI[ma].update(xong=True, ok=ok, tb=tb, url=url if ok else "")


def tt_cai_dat():
    cd = GS.cai_dat()
    ds = GS.ds_ghi_hinh()
    try:
        st = os.statvfs(RD._goc() if os.path.isdir(RD._goc()) else "/")
        trong = st.f_bavail * st.f_frsize
    except OSError:
        trong = 0
    nhip = GS.trang_thai_nhip()
    rids = {v.get("id") for v in RD.doc_cfg()["may"].values() if v.get("id")}
    return dict(cd, may_chu_api=GS.tt_may_chu(), cong_api_ngoai=RD.dia_chi()["cong_id"] - 2, host=RD.dia_chi()["id"].split(":")[0],
                nhip_gan=sum(1 for k, v in nhip.items() if v["cach"] < 120), tong_may=len(rids),
                ghi_hinh_so=len(ds), ghi_hinh_dung=sum(x["kich_thuoc"] for x in ds), dia_trong=trong, thu_ghi={"luc": _THU.get("luc", 0), "tb": _THU.get("tb", "")})


def lich_su_day_du():
    """Lich su ket noi + lien ket ban ghi hinh (moi ban ghi vao 1 phien cung may bat dau gan nhat)."""
    cfg = RD.doc_cfg()
    ds_may = {m["id"]: (m.get("ten") or m["ip"]) for m in DL.MAY.doc()}
    ten = {v.get("id"): ds_may.get(k, "") for k, v in cfg["may"].items() if v.get("id")}
    mid_theo_rid = {v.get("id"): k for k, v in cfg["may"].items() if v.get("id")}
    ghi = GS.ds_ghi_hinh()
    ra = GS.lich_su(ten)
    for p in ra:
        p["ghi_hinh"] = []
    phien = [p for p in ra if p["loai"] != "Yêu cầu từ Console" and mid_theo_rid.get(p["rid"])]
    for x in ghi:                 # moi ban ghi chi gan vao DUNG 1 phien: cung may, bat dau gan nhat (ten file mang gio bat dau phien, lech vai giay)
        bd = _luc_ten_ghi(x["ten"])
        if not bd:
            continue
        hop = [p for p in phien if mid_theo_rid[p["rid"]] == x["mid"] and p["bat_dau"] - 15 <= bd <= (p["ket_thuc"] or time.time()) + 15]
        if hop:
            min(hop, key=lambda p: abs(p["bat_dau"] - bd))["ghi_hinh"].append({"mid": x["mid"], "ten": x["ten"], "kich_thuoc": x["kich_thuoc"]})
    return ra


def _luc_ten_ghi(ten):
    """incoming_<id>_YYYYmmddHHMMSSfff_display0_vp9.webm -> epoch (gio may khach, coi nhu cung mui gio voi Console)."""
    mm = re.search(r"_(\d{14})\d{3}_", ten)
    if not mm:
        return None
    try:
        return time.mktime(time.strptime(mm.group(1), "%Y%m%d%H%M%S"))
    except ValueError:
        return None


# ------------------------------------------------------------------ thu ban ghi hinh tu may ve Console (vong nen)
THU_MUC_GHI_MAY = r"C:\ProgramData\RustDesk\recording"
PS_DS_GHI = r"""$d = '%s'
if (Test-Path $d) { Get-ChildItem $d -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddSeconds(-90) -and $_.Length -gt 0 } | ForEach-Object { 'GHI=' + $_.Name + '|' + $_.Length } }
'GHI_XONG'""" % THU_MUC_GHI_MAY
_THU = {"luc": 0, "tb": ""}
_BAT_DAU = {"co": False}


def thu_ghi_hinh_may(m):
    """Lay cac ban ghi da xong tren 1 may (agent) ve Console, kiem kich thuoc roi xoa tren may. Tra so file da lay."""
    ok, out = DK._chay(m, PS_DS_GHI)
    if not ok or "GHI_XONG" not in (out or ""):
        return 0
    dich_dir = os.path.join(GS.thu_muc_ghi_hinh(), m["id"])
    os.makedirs(dich_dir, mode=0o700, exist_ok=True)
    n = 0
    for ten, kt in re.findall(r"GHI=([^|\r\n]+)\|(\d+)", out):
        kt = int(kt)
        if not GS.MAU_TEP_GHI.fullmatch(ten):
            continue
        if kt > UA.TOI_DA_TEP:
            _THU["tb"] = "Bản ghi %s trên máy %s lớn hơn 2 GB, không lấy về được (vẫn nằm trên máy, thư mục %s)." % (ten, m.get("ten") or m["ip"], THU_MUC_GHI_MAY)
            continue
        st = os.statvfs(dich_dir)
        if st.f_bavail * st.f_frsize < kt + 2 * 1024 ** 3:
            _THU["tb"] = "Ổ đĩa Console System sắp đầy, tạm dừng lấy bản ghi hình."
            break
        dich, tam = os.path.join(dich_dir, ten), os.path.join(dich_dir, "." + ten + ".tai")
        try:
            UA.Client(m["id"]).fetch(THU_MUC_GHI_MAY + "\\" + ten, tam)
            if os.path.getsize(tam) != kt:
                raise RuntimeError("kích thước không khớp")
            os.replace(tam, dich)
        except Exception as e:                        # loi mang / agent: giu file tren may, lan sau lay lai
            _bo_qua(e)
            try:
                os.remove(tam)
            except OSError:
                pass
            continue
        DK._chay(m, "Remove-Item -LiteralPath %s -Force" % _ps_chuoi(THU_MUC_GHI_MAY + "\\" + ten))
        n += 1
    return n


def _tick():
    GS.khoi_dong()
    now = time.time()
    if now - _THU.get("don", 0) > 86400:
        GS.don_lich_su()
        _THU["don"] = now
    if not GS.cai_dat()["ghi_hinh"]:
        return
    cfg = RD.doc_cfg()
    tong, quet_het = 0, now - _THU.get("quet", 0) > 1800             # 30 phut hoi moi may 1 lan, con lai chi hoi may vua co ket noi
    co_phien = GS.lay_may_co_phien() | _THU.pop("cho", set())
    if quet_het:
        _THU["quet"] = now
    for m in DL.MAY.doc():
        rid = (cfg["may"].get(m["id"]) or {}).get("id")
        if m.get("an") or not rid or not UA.co_agent(m) or not (quet_het or rid in co_phien):
            continue
        if not UA.con_song(m):
            _THU.setdefault("cho", set()).add(rid)                     # may vua tat: lan sau hoi lai
            continue
        try:
            tong += thu_ghi_hinh_may(m)
        except Exception as e:
            _bo_qua(e)
    xoa = GS.don_ghi_hinh()
    _THU.update(luc=int(now), tb="Lần lấy gần nhất: %d bản ghi mới%s." % (tong, (", xóa %d bản cũ cho vừa dung lượng" % xoa) if xoa else ""))


def khoi_dong_bo_lap():
    if _BAT_DAU["co"]:
        return
    _BAT_DAU["co"] = True

    def vong():
        time.sleep(15)
        while True:
            try:
                _tick()
            except Exception as _loi:
                _bo_qua(_loi)
            time.sleep(120)
    threading.Thread(target=vong, daemon=True, name="rustdesk-giam-sat").start()

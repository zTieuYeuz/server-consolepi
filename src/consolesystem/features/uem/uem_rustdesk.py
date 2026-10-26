# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""RustDesk phia quan ly may tram: cai client RustDesk len may qua agent/WinRM va liet ke may/ID/mat khau. Logic may chu: integrations/rustdesk_may_chu.py."""
import re
import secrets
import time

from flask import jsonify, request

from consolesystem.features.uem import uem_dieukhien as DK
from consolesystem.integrations import rustdesk_may_chu as RD
from ui import tk_dulieu as DL
from ui import uem_agent as UA


def cai_client_may(m):
    """Cai qua agent/WinRM. Tra (ok, thong_diep, id)."""
    cfg = RD.doc_cfg()
    ban = cfg["may"].get(m["id"]) or {}
    mk = RD.mk_chung() or ban.get("mk") or secrets.token_hex(6)
    try:
        sc = RD.script_client(mk)
    except RuntimeError as e:
        return False, str(e), ""
    ok, out = DK._chay(m, sc)
    ma = re.search(r"RUSTDESK_ID=(\d{6,12})", out or "")
    if not ok or not ma:
        return False, (out or "Không lấy được ID RustDesk.")[-400:], ""
    cfg = RD.doc_cfg()
    cfg["may"][m["id"]] = {"id": ma.group(1), "mk": mk, "luc": int(time.time()), "dong_bo": True}
    RD.luu_cfg(cfg)
    return True, "Đã cài RustDesk, ID %s." % ma.group(1), ma.group(1)



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
        return jsonify({"ds": RD.thiet_bi(), "may": may, "agent": agent, "mk_chung": cfg.get("mk_chung", ""), "dong_bo": dict(_DONG_BO)})

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
    """Day dia chi may chu + khoa + WebSocket xuong MOI may co agent (qua agent/WinRM): may co RustDesk thi doi, may chua cai thi bo qua.
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
                'chọn máy rồi bấm <b>Cài lên máy đã chọn</b> (máy phải có agent). Cách 2: anh đã tự cài RustDesk trên máy này (trỏ về máy chủ <b>' + _e(st["host_hieu_luc"]) + '</b>) thì nhập ID và mật khẩu vào đây:</p>'
                f'<form method="POST" action="/uem/may/{m["id"]}/rustdesk/luu" class="tk-hang"><input type="text" name="id" value="' + _e(goi_y) + '" placeholder="ID RustDesk (số)" required style="max-width:200px;margin:0;">'
                '<input type="text" name="mk" placeholder="Mật khẩu cố định" required autocomplete="off" style="max-width:220px;margin:0;"><button class="tk-nut chinh" type="submit">Lưu</button></form></div>')
    i, mk = _e(ban["id"]), _e(ban["mk"])
    return (f'<div class="card"><h3>Điều khiển bằng RustDesk</h3>'
            f'<p class="tk-ghi">RustDesk không chạy trong trình duyệt (khác VNC phía trên): bấm nút để mở <b>ứng dụng RustDesk đã cài trên máy của anh</b> và kết nối thẳng xuống máy này. '
            f'Cần cài RustDesk client trên máy đang ngồi và trỏ về máy chủ <b>{_e(st["host_hieu_luc"])}</b> (Cài đặt, Mạng, ID/Relay server, dán key ở trang RustDesk).</p>'
            f'<div class="uem-2"><div>ID: <span class="rd-k" style="font-family:monospace;user-select:all;">{i}</span></div><div>Mật khẩu: <span style="font-family:monospace;user-select:all;">{mk}</span></div></div>'
            f'<div class="tk-hang" style="margin-top:10px;"><a class="tk-nut chinh" href="rustdesk://connection/new/{i}?password={mk}">Mở RustDesk và kết nối</a>'
            f'<a class="tk-nut" href="/rustdesk">Trang RustDesk (khóa, tải client)</a></div></div>')

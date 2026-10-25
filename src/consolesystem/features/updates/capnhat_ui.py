# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Tab CAP NHAT (C3/C4/C5): trang thai + nut Kiem tra ngay, thong tin ban moi, xac nhan (mien tru + go chu), tien do truc tiep, ha cap, lich su,
cai dat kenh. Logic nang cap o core/capnhat/nangcap.py, bo nang cap chay tach rieng (don vi systemd). Tai khoan dang nhap duoc dung tab nay
(may chi co tai khoan quan tri).
"""
import hashlib
import json
import random
import threading
import time

from flask import jsonify, redirect, request

from consolesystem.core import duongdan as DD
from consolesystem.core.capnhat import may as M
from consolesystem.core.capnhat import nangcap as N
from consolesystem.core.esc import esc
from consolesystem.web.layout import render_page

from consolesystem.features.updates import thuc_te as T

DIEU_KHOAN = """\
1. Cap nhat Console System thay doi chuong trinh dang chay tren may nay va CO THE KHOI DONG LAI cac dich vu (ke ca trang web quan ly). Trong luc do viec
   cai Windows qua mang (PXE), tai file, quet mang... dang chay co the BI GIAN DOAN hoac LOI.
2. He thong tu sao luu cau hinh truoc khi nang cap va tu hoan tac neu co loi; tuy nhien KHONG co phan mem nao dam bao tuyet doi. Ban co trach nhiem
   sao luu rieng du lieu quan trong (kho phan mem, anh he dieu hanh, cau hinh may chu) truoc khi cap nhat.
3. Goi cap nhat duoc ky so va ma hoa; he thong chi cai goi hop le tu nha phat hanh, tung ban mot theo thu tu, va kiem lai tung file sau khi cai.
4. Phan mem duoc cung cap theo hien trang. Nha phat hanh khong chiu trach nhiem ve thiet hai gian tiep hay mat du lieu do ban khong sao luu hoac do
   thay doi trai phep ma nguon/he thong cap nhat.
5. Tinh nang cap nhat co the bi chan neu phat hien chuong trinh bi sua doi trai phep (xem muc Chong chinh sua).
"""
GO_XAC_NHAN = "CAP NHAT"
GO_HA_CAP = "HA CAP"
_cache_chuong = {"luc": 0, "co": False}


def _hash_dieu_khoan():
    return hashlib.sha256(DIEU_KHOAN.encode()).hexdigest()[:16]


def da_dong_y_dieu_khoan(moi):
    return M.cau_hinh(moi).get("dieu_khoan") == _hash_dieu_khoan()


def _gio(ts):
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(ts)) if ts else "-"


def _the(tieu_de, nd, mau=""):
    return '<div class="card"%s><h3>%s</h3>%s</div>' % (' style="border-color:%s"' % mau if mau else "", tieu_de, nd)


def _form_nut(duong, nhan, cls="gray", an=None):
    an_html = "".join('<input type="hidden" name="%s" value="%s">' % (k, esc(v)) for k, v in (an or {}).items())
    return '<form method="POST" action="%s" style="display:inline">%s<button class="%s">%s</button></form>' % (duong, an_html, cls, nhan)


def _trang_dieu_khoan():
    nd = ('<p>Truoc khi dung chuc nang Cap nhat, vui long doc va dong y:</p><pre style="white-space:pre-wrap;background:rgba(0,0,0,.2);padding:12px;border-radius:8px">%s</pre>'
          '<form method="POST" action="/cap-nhat/dong-y"><label><input type="checkbox" name="dong_y" value="1" required> Toi da doc va dong y voi dieu khoan tren</label><br><br>'
          '<button class="blue">Dong y va tiep tuc</button></form>') % esc(DIEU_KHOAN)
    return render_page(_the("Dieu khoan su dung chuc nang Cap nhat", nd), active="/cap-nhat", title="Cập nhật", subtitle="Điều khoản")


def _khoi_tien_do(job):
    if not job:
        return ""
    buoc = N.BUOC_NANG_CAP if job["loai"] == "nang-cap" else N.BUOC_HA_CAP
    ten = {"kiem": "Kiểm tra điều kiện", "sao-luu": "Sao lưu cấu hình", "tai": "Tải gói", "cai": "Kiểm chữ ký, giải mã, giải nén, đối chiếu từng file",
           "migration": "Chuyển đổi dữ liệu", "doi-ban": "Đổi bản", "khoi-dong-lai": "Khởi động lại dịch vụ", "suc-khoe": "Kiểm tra sức khỏe",
           "khoi-phuc-du-lieu": "Khôi phục dữ liệu", "hoan-tat": "Hoàn tất", "hoan-tac": "ĐANG HOÀN TÁC"}
    hien = job.get("buoc")
    li = ""
    for b in buoc:
        da = buoc.index(b) < (buoc.index(hien) if hien in buoc else len(buoc))
        cls = "✔" if da or job["trang_thai"] == "xong" else ("➜" if b == hien else "·")
        li += "<li>%s %s</li>" % (cls, ten.get(b, b))
    mau = {"xong": "#4ADE80", "da-hoan-tac": "#FBBF24", "that-bai": "#F87171", "can-xu-ly-tay": "#F87171", "da-huy": "#9CA3AF"}.get(job["trang_thai"], "#38BDF8")
    nk = "".join("<div><small>%s</small> %s</div>" % (_gio(x["luc"]), esc(x["noi_dung"])) for x in (job.get("nhat_ky") or [])[-12:])
    tt = {"dang-chay": "ĐANG CHẠY - đừng tắt máy", "xong": "XONG", "da-hoan-tac": "ĐÃ HOÀN TÁC về bản cũ", "that-bai": "THẤT BẠI (chưa đụng vào hệ thống)",
          "can-xu-ly-tay": "CẦN XỬ LÝ TAY", "da-huy": "ĐÃ HỦY"}.get(job["trang_thai"], job["trang_thai"])
    ly = '<p><b>%s</b></p>' % esc(job["ly_do"]) if job.get("ly_do") else ""
    nut_huy = _form_nut("/cap-nhat/huy", "Hủy", "gray") if job["trang_thai"] == "dang-chay" and job["loai"] == "nang-cap" and hien in ("kiem", "sao-luu", "tai", "cai") else ""
    tu_tai = '<script>(function(){function t(){fetch("/cap-nhat/tien-do").then(r=>r.json()).then(j=>{if(j.trang_thai&&j.trang_thai!="dang-chay"||(j.buoc!="%s"))location.reload();else setTimeout(t,2000)}).catch(()=>setTimeout(t,3000))}setTimeout(t,2000)})()</script>' % esc(hien) \
        if job["trang_thai"] == "dang-chay" else ""
    return _the("%s %s → %s: %s" % ("Nâng cấp" if job["loai"] == "nang-cap" else "Hạ cấp", esc(job["tu"]), esc(job["den"]), tt),
                '<ul style="list-style:none;padding:0">%s</ul>%s<div style="font-size:12px;opacity:.8">%s</div>%s%s' % (li, ly, nk, nut_huy, tu_tai), mau)


def _khoi_trang_thai(moi, ts, cur, cfg):
    dong = ["<tr><td>Phiên bản đang chạy</td><td><b>%s</b> (số phát hành %s, %s)</td></tr>" % (esc(cur["phien_ban"]), cur["so_phat_hanh"], esc(cur["kien_truc"])),
            "<tr><td>Kênh</td><td>%s</td></tr>" % ("Ổn định" if cfg["kenh"] == "on-dinh" else "<b>Thử nghiệm</b> (chỉ qua mạng LAN)"),
            "<tr><td>Kiểm tra lần cuối</td><td>%s</td></tr>" % _gio(ts.get("hoi_luc")),
            "<tr><td>Danh mục hết hạn</td><td>%s</td></tr>" % _gio(ts.get("danh_muc_het_han"))]
    loi = ""
    if ts.get("loi"):
        mau = "#F87171" if ts.get("loai_loi") == "an-ninh" else "#FBBF24"
        loi = '<div class="msg err" style="border-color:%s">%s</div>' % (mau, esc(ts["loi"]))
    nut = _form_nut("/cap-nhat/kiem-tra", "Kiểm tra ngay", "blue")
    return _the("Cập nhật Console System", "<table>%s</table>%s<p>%s</p>" % ("".join(dong), loi, nut))


def _khoi_ban_moi(moi, ts, cur, job_chay):
    ban, moi_nhat = ts.get("ban_ke_tiep"), ts.get("ban_moi_nhat")
    if not ts.get("co_ban_moi") or ts.get("loi"):
        return _the("Phiên bản", "<p>Bạn đang dùng bản mới nhất%s.</p>" % ("" if not ts.get("loi") else " (chưa xác nhận được vì lần kiểm tra gần nhất bị lỗi)"))
    if not ban:
        return _the("Có bản mới %s" % esc(moi_nhat["phien_ban"] if moi_nhat else ""),
                    "<p>Phải nâng cấp tuần tự: cần qua bản trung gian trước. Hiện chưa có bản trung gian khả dụng cho máy này.</p>", "#FBBF24")
    chan, canh_bao, _b = N.kiem_dieu_kien_nang_cap(moi)
    chan_html = "".join("<li>%s</li>" % esc(c) for c in chan)
    pxe = any("PXE" in c for c in chan)
    form = ""
    if not job_chay:
        bo_pxe = ('<label style="color:#FBBF24"><input type="checkbox" name="bo_qua_pxe" value="1"> Tôi hiểu PXE đang chạy và chấp nhận nguy cơ lỗi cho máy đang cài</label><br>' if pxe else "")
        form = ('<details><summary class="btn blue">Cập nhật lên %(v)s…</summary><form method="POST" action="/cap-nhat/bat-dau" style="margin-top:12px">'
                '<p><b>Trước khi tiếp tục:</b> hệ thống tự sao lưu cấu hình, nâng cấp tự động và <b>tự hoàn tác nếu lỗi</b>; dịch vụ sẽ KHỞI ĐỘNG LẠI.</p>'
                '<pre style="white-space:pre-wrap;font-size:12px">%(dk)s</pre>'
                '<label><input type="checkbox" name="da_sao_luu" value="1" required> Tôi đã sao lưu dữ liệu và máy chủ quan trọng và đồng ý điều khoản trên</label><br>%(pxe)s'
                '<label>Gõ <b>%(go)s</b> để xác nhận: <input name="xac_nhan" autocomplete="off" required></label> <button class="blue">Bắt đầu cập nhật</button></form></details>') \
            % {"v": esc(ban["phien_ban"]), "dk": esc(DIEU_KHOAN), "pxe": bo_pxe, "go": GO_XAC_NHAN}
    ghi = '<p><b>Có gì mới:</b> %s</p>' % esc(ban.get("ghi_chu") or "(không có ghi chú)")
    return _the("Có bản mới: %s" % esc(ban["phien_ban"]), ghi + ("<ul style='color:#F87171'>%s</ul>" % chan_html if chan_html and not job_chay else "") + (form if not chan or pxe else ""),
                "#38BDF8")


def _khoi_ha_cap(moi, job_chay):
    chan, canh_bao, dich = N.kiem_dieu_kien_ha_cap(moi, {})
    if not dich or job_chay:
        return ""
    lydo = "".join("<li>%s</li>" % esc(c) for c in chan)
    if chan:
        return _the("Hạ cấp", "<p>Không thể hạ cấp lúc này:</p><ul>%s</ul>" % lydo)
    return _the("Hạ cấp về %s" % esc(dich["phien_ban"]),
                ('<details><summary class="btn gray">Hạ cấp…</summary><form method="POST" action="/cap-nhat/ha-cap" style="margin-top:12px">'
                 '<div class="msg warn">%s</div><label><input type="checkbox" name="khoi_phuc_du_lieu" value="1" checked> Khôi phục dữ liệu về lúc trước khi nâng cấp '
                 '(bỏ chọn nếu muốn giữ dữ liệu hiện tại và dữ liệu tương thích)</label><br>'
                 '<label>Gõ <b>%s</b>: <input name="xac_nhan" autocomplete="off" required></label> <button class="gray">Hạ cấp</button></form></details>') %
                ("<br>".join(esc(c) for c in canh_bao) or "Trạng thái hiện tại được sao lưu trước khi hạ cấp.", GO_HA_CAP))


def _khoi_cai_dat(cfg):
    return _the("Cài đặt cập nhật",
                ('<form method="POST" action="/cap-nhat/cai-dat"><label>Kênh: <select name="kenh"><option value="on-dinh"%s>Ổn định</option>'
                 '<option value="thu-nghiem"%s>Thử nghiệm (chỉ qua mạng LAN, có thể chưa ổn định)</option></select></label><br>'
                 '<label><input type="checkbox" name="hoi_dinh_ky" value="1"%s> Tự kiểm tra bản mới mỗi 24 giờ</label><br><button class="gray">Lưu</button></form>')
                % (" selected" if cfg["kenh"] == "on-dinh" else "", " selected" if cfg["kenh"] == "thu-nghiem" else "", " checked" if cfg["hoi_dinh_ky"] else ""))


def _khoi_lich_su(moi):
    ds = N.lich_su(moi)[-10:][::-1]
    if not ds:
        return ""
    return _the("Lịch sử", "<table>%s</table>" % "".join("<tr><td>%s</td><td>%s</td><td>%s → %s</td><td>%s</td></tr>" % (
        _gio(x.get("bat_dau")), "Nâng cấp" if x.get("loai") == "nang-cap" else "Hạ cấp", esc(x.get("tu")), esc(x.get("den")), esc(x.get("trang_thai"))) for x in ds))


def register_capnhat(app):
    def _moi():
        return T.moi_thuc()

    @app.route("/cap-nhat")
    def trang_cap_nhat(msg="", ok=True):
        moi = _moi()
        if not da_dong_y_dieu_khoan(moi):
            return _trang_dieu_khoan()
        try:
            cur, ts, cfg = M.hien_tai(moi), M.trang_thai(moi), M.cau_hinh(moi)
        except M.LoiCapNhat as e:
            return render_page(_the("Cập nhật", '<div class="msg err">%s</div>' % esc(str(e))), active="/cap-nhat", title="Cập nhật")
        job = N.doc_job(moi)
        chay = bool(job and job.get("trang_thai") == "dang-chay")
        thong_bao = ('<div class="msg %s">%s</div>' % ("ok" if ok else "err", esc(msg))) if msg else ""
        body = thong_bao + _khoi_tien_do(T.mo_ta_job(job) if job and (chay or time.time() - (job.get("ket_thuc") or 0) < 86400) else None) + _khoi_trang_thai(moi, ts, cur, cfg) \
            + _khoi_ban_moi(moi, ts, cur, chay) + _khoi_ha_cap(moi, chay) + _khoi_cai_dat(cfg) + _khoi_lich_su(moi)
        return render_page(body, active="/cap-nhat", title="Cập nhật", subtitle="Phiên bản và nâng cấp")

    @app.route("/cap-nhat/dong-y", methods=["POST"])
    def cap_nhat_dong_y():
        if request.form.get("dong_y") == "1":
            M.luu_cau_hinh(_moi(), dieu_khoan=_hash_dieu_khoan(), dong_y_luc=int(time.time()))
        return redirect("/cap-nhat")

    @app.route("/cap-nhat/kiem-tra", methods=["POST"])
    def cap_nhat_kiem_tra():
        M.kiem_tra(_moi(), bat_buoc=True)
        return redirect("/cap-nhat")

    @app.route("/cap-nhat/cai-dat", methods=["POST"])
    def cap_nhat_cai_dat():
        try:
            M.luu_cau_hinh(_moi(), kenh=request.form.get("kenh", "on-dinh"), hoi_dinh_ky=request.form.get("hoi_dinh_ky") == "1")
        except M.LoiCapNhat:
            pass
        return redirect("/cap-nhat")

    def _khoi_dong(ham_bat_dau, tuy_chon, go_dung):
        moi = _moi()
        if request.form.get("xac_nhan", "").strip().upper() != go_dung:
            return trang_cap_nhat("Chưa gõ đúng chữ xác nhận.", False)
        try:
            ham_bat_dau(moi, tuy_chon)
        except N.LoiNangCap as e:
            return trang_cap_nhat(str(e), False)
        T.khoi_chay_bo_nang_cap()
        return redirect("/cap-nhat")

    @app.route("/cap-nhat/bat-dau", methods=["POST"])
    def cap_nhat_bat_dau():
        if request.form.get("da_sao_luu") != "1":
            return trang_cap_nhat("Cần xác nhận đã sao lưu dữ liệu và đồng ý điều khoản.", False)
        return _khoi_dong(N.bat_dau_nang_cap, {"bo_qua_pxe": request.form.get("bo_qua_pxe") == "1"}, GO_XAC_NHAN)

    @app.route("/cap-nhat/ha-cap", methods=["POST"])
    def cap_nhat_ha_cap():
        return _khoi_dong(N.bat_dau_ha_cap, {"khoi_phuc_du_lieu": request.form.get("khoi_phuc_du_lieu") == "1"}, GO_HA_CAP)

    @app.route("/cap-nhat/huy", methods=["POST"])
    def cap_nhat_huy():
        N.huy(_moi())
        return redirect("/cap-nhat")

    @app.route("/cap-nhat/tien-do")
    def cap_nhat_tien_do():
        j = N.doc_job(_moi())
        return jsonify(T.mo_ta_job(j) or {})

    def vong_kiem_tra_nen():
        time.sleep(random.randint(60, 300))
        while True:
            try:
                moi = _moi()
                if M.den_han_hoi(moi) and moi.kho is not None:
                    M.kiem_tra(moi)
            except Exception as e:                                   # luong nen khong duoc chet vi mot lan loi
                print("[cap-nhat] loi kiem tra dinh ky: %s: %s" % (type(e).__name__, e), flush=True)
            time.sleep(900)
    threading.Thread(target=vong_kiem_tra_nen, daemon=True, name="cap-nhat-kiem-tra").start()

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

from flask import Response, jsonify, redirect, request, session

from consolesystem.core import duongdan as DD
from consolesystem.core.capnhat import may as M
from consolesystem.core.capnhat import nangcap as N
from consolesystem.core.capnhat import khoa_lenh as KL
from consolesystem.core.capnhat import nguyenven as NV
from consolesystem.core.esc import esc
from consolesystem.web import auth as _auth
from consolesystem.web.layout import render_page

from consolesystem.features.updates import thuc_te as T

DIEU_KHOAN = """\
1. Cập nhật Console System thay đổi chương trình đang chạy trên máy này, KHỞI ĐỘNG LẠI các dịch vụ (kể cả trang web quản lý) và sau đó cần
   khởi động lại máy. Trong lúc đó việc cài Windows qua mạng (PXE), tải file, quét mạng... đang chạy có thể BỊ GIÁN ĐOẠN hoặc LỖI.
2. Hệ thống tự sao lưu cấu hình trước khi nâng cấp và tự hoàn tác nếu có lỗi; tuy nhiên KHÔNG có phần mềm nào bảo đảm tuyệt đối. Bạn có trách
   nhiệm tự sao lưu dữ liệu quan trọng (kho phần mềm, ảnh hệ điều hành, cấu hình máy chủ) trước khi cập nhật.
3. Gói cập nhật được ký số và mã hóa; hệ thống chỉ cài gói hợp lệ từ nhà phát hành, từng bản một theo thứ tự, và kiểm lại từng file sau khi cài.
4. Phần mềm được cung cấp theo hiện trạng. Nhà phát hành không chịu trách nhiệm về thiệt hại gián tiếp hay mất dữ liệu do bạn không sao lưu hoặc do
   thay đổi trái phép mã nguồn / hệ thống cập nhật.
5. Tính năng cập nhật có thể bị chặn nếu phát hiện chương trình bị sửa đổi trái phép (xem mục Chống chỉnh sửa). Đây là lớp phát hiện thay đổi, không
   chống được người đã có quyền root trên máy.
6. KHÓA MÁY: nếu máy bị nghi ngờ (ví dụ chương trình bị sửa, máy thất lạc/bị sao chép), CHỦ HỆ THỐNG có thể ký một lệnh khóa; máy nhận lệnh thì mã hóa
   các bí mật NHỎ (khóa phiên web, token kho, khóa Samba...) và chỉ mở lại khi nhập MÃ MỞ KHÓA do chủ hệ thống giữ. Lệnh chỉ có hiệu lực khi có chữ
   ký hợp lệ, đúng máy, còn hạn; không ai (kể cả kho) mở khóa từ xa. Mất mã mở khóa = mất các bí mật đã khóa, nên hãy giữ mã ở nơi an toàn.
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
    nd = ('<p>Trước khi dùng chức năng Cập nhật, vui lòng đọc và đồng ý:</p><pre style="white-space:pre-wrap;background:rgba(0,0,0,.2);padding:12px;border-radius:8px">%s</pre>'
          '<form method="POST" action="/cap-nhat/dong-y"><label><input type="checkbox" name="dong_y" value="1" required> Tôi đã đọc và đồng ý với điều khoản trên</label><br><br>'
          '<button class="blue">Đồng ý và tiếp tục</button></form>') % esc(DIEU_KHOAN)
    return render_page(_the("Điều khoản sử dụng chức năng Cập nhật", nd), active="/cap-nhat", title="Cập nhật", subtitle="Điều khoản")


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
                '<p><b>Bước 1 - tải bản sao lưu về máy của bạn</b> (hệ thống cũng tự sao lưu cấu hình, nhưng nên giữ thêm một bản bên ngoài): '
                '<a class="btn gray" href="/settings/sao-luu">Tải sao lưu cấu hình</a> <a class="btn gray" href="/settings/sao-luu?che_do=toanbo">Tải sao lưu toàn bộ (kèm kho, ảnh Windows)</a></p>'
                '<label><input type="checkbox" name="da_sao_luu" value="1" required> Tôi đã sao lưu dữ liệu và máy chủ quan trọng và đồng ý điều khoản trên</label><br>%(pxe)s'
                '<label>Mật khẩu tài khoản quản trị của bạn: <input type="password" name="mat_khau" autocomplete="current-password" required></label><br>'
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
                 '<label>Mật khẩu tài khoản quản trị: <input type="password" name="mat_khau" autocomplete="current-password" required></label><br>'
                 '<label>Gõ <b>%s</b>: <input name="xac_nhan" autocomplete="off" required></label> <button class="gray">Hạ cấp</button></form></details>') %
                ("<br>".join(esc(c) for c in canh_bao) or "Trạng thái hiện tại được sao lưu trước khi hạ cấp.", GO_HA_CAP))


def _thoi_diem_khoi_dong():
    try:
        with open("/proc/uptime") as f:
            return time.time() - float(f.read().split()[0])
    except (OSError, ValueError):
        return 0


def _can_khoi_dong_lai(moi, job):
    """Nang/ha cap xong ma may CHUA khoi dong lai tu luc do (goi khai can_khoi_dong_lai, mac dinh co) -> nhac khoi dong lai (hoi truoc)."""
    if not job or job.get("trang_thai") != "xong" or not job.get("ket_thuc"):
        return False
    if job.get("loai") == "nang-cap" and (job.get("manifest") or {}).get("can_khoi_dong_lai") is False:
        return False
    return _thoi_diem_khoi_dong() < job["ket_thuc"]


def _khoi_khoi_dong_lai(moi, job):
    if not _can_khoi_dong_lai(moi, job):
        return ""
    return _the("Cần khởi động lại máy",
                "<p>Đã %s lên bản <b>%s</b>. Để hoàn tất, hãy <b>khởi động lại máy</b> (máy khách đang cài Windows qua PXE sẽ bị gián đoạn).</p>%s"
                % ("nâng cấp" if job.get("loai") == "nang-cap" else "hạ cấp", esc(job.get("den", "")),
                   '<form method="POST" action="/cap-nhat/khoi-dong-lai-may" onsubmit="return confirm(this.dataset.hoi);" data-hoi="Khởi động lại máy Console System ngay bây giờ?">'
                   '<button class="blue">Khởi động lại máy ngay</button></form>'), "#FBBF24")


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


def _khoi_nguyen_ven(moi):
    kq = NV.doc_ket_qua(moi) or {}
    tt = kq.get("trang_thai")
    if not tt:
        return ""
    nhan = {"ok": ("Nguyên vẹn", "var(--ok,#2a2)"), "chua-ky": ("Chưa có chữ ký để đối chiếu", ""), "lech": ("BỊ SỬA ĐỔI", "#c33"),
            "khong-xac-minh": ("Chưa xác minh lại được chữ ký", "#c90")}.get(tt, (tt, ""))
    nd = "<p><b>%s</b> — bản %s, kiểm lúc %s.</p>" % (nhan[0], esc(kq.get("ban") or "-"), _gio(kq.get("luc")))
    if kq.get("ly_do"):
        nd += "<p>%s</p>" % esc(kq["ly_do"])
    if kq.get("lech"):
        nd += "<ul>%s</ul>" % "".join("<li>%s</li>" % esc(x) for x in kq["lech"][:10])
    return _the("Chống chỉnh sửa", nd, nhan[1])


def register_capnhat(app):
    def _moi():
        return T.moi_thuc()

    @app.before_request
    def _chi_quan_tri():
        if not request.path.startswith("/cap-nhat") or _auth.la_quan_tri():
            return None
        if not session.get("user"):
            return redirect("/login")
        return Response(render_page(_the("Cập nhật", "<p>Chức năng Cập nhật chỉ dành cho <b>tài khoản quản trị</b> (thuộc nhóm sudo của máy). "
                                                     "Đăng xuất rồi đăng nhập bằng tài khoản quản trị.</p>"), active="/cap-nhat", title="Cập nhật"),
                        status=403, mimetype="text/html")

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
        body = thong_bao + _khoi_khoi_dong_lai(moi, job) + _khoi_tien_do(T.mo_ta_job(job) if job and (chay or time.time() - (job.get("ket_thuc") or 0) < 86400) else None) + _khoi_trang_thai(moi, ts, cur, cfg) \
            + _khoi_nguyen_ven(moi) + _khoi_ban_moi(moi, ts, cur, chay) + _khoi_ha_cap(moi, chay) + _khoi_cai_dat(cfg) + _khoi_lich_su(moi)
        return render_page(body, active="/cap-nhat", title="Cập nhật", subtitle="Phiên bản và nâng cấp")

    @app.route("/cap-nhat/dong-y", methods=["POST"])
    def cap_nhat_dong_y():
        if request.form.get("dong_y") == "1":
            M.luu_cau_hinh(_moi(), dieu_khoan=_hash_dieu_khoan(), dong_y_luc=int(time.time()))
        return redirect("/cap-nhat")

    @app.route("/cap-nhat/kiem-tra", methods=["POST"])
    def cap_nhat_kiem_tra():
        moi = _moi()
        NV.kiem_va_ghi(moi, moi.kho.bao_cao if moi.kho is not None else None)
        M.kiem_tra(moi, bat_buoc=True)
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
        ok_mk, _tb = _auth.check_login(session.get("user", ""), request.form.get("mat_khau", ""))
        if not ok_mk:
            return trang_cap_nhat("Mật khẩu tài khoản quản trị không đúng.", False)
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

    @app.route("/cap-nhat/khoi-dong-lai-may", methods=["POST"])
    def cap_nhat_khoi_dong_lai_may():
        moi = _moi()
        if not _can_khoi_dong_lai(moi, N.doc_job(moi)):
            return redirect("/cap-nhat")
        if N.dang_chay(moi):
            return trang_cap_nhat("Đang có một lần nâng cấp/hạ cấp chạy, chưa khởi động lại được.", False)
        T.khoi_dong_lai_may()
        return render_page(_the("Đang khởi động lại máy", "<p>Máy đang khởi động lại. Chờ khoảng 1-2 phút rồi tải lại trang.</p>"), active="/cap-nhat", title="Cập nhật")

    @app.route("/cap-nhat/huy", methods=["POST"])
    def cap_nhat_huy():
        N.huy(_moi())
        return redirect("/cap-nhat")

    @app.route("/cap-nhat/tien-do")
    def cap_nhat_tien_do():
        j = N.doc_job(_moi())
        return jsonify(T.mo_ta_job(j) or {})

    # ---- C6: man hinh MAY BI KHOA (chi chan nguoi da dang nhap; /healthz, /static, agent va PXE khong bi dong vao)
    nho_khoa = {"luc": 0.0, "co": False}

    def _dang_khoa():
        t = time.time()
        if t - nho_khoa["luc"] > 2:
            try:
                nho_khoa["co"] = KL.dang_khoa(_moi())
            except Exception:
                nho_khoa["co"] = False
            nho_khoa["luc"] = t
        return nho_khoa["co"]

    def _trang_khoa(msg=""):
        nd = ('<div class="msg err">%s</div>' % esc(msg)) if msg else ""
        nd += ("<p>Máy này đã bị <b>KHÓA</b> theo lệnh đã ký của chủ hệ thống. Các bí mật nhỏ (khóa phiên, token kho, khóa Samba...) đã được mã hóa; "
               "chỉ <b>mã mở khóa</b> do chủ hệ thống giữ mới giải được.</p>"
               '<form method="POST" action="/khoa-may"><input name="ma" placeholder="XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX" size="48" autocomplete="off" autofocus> '
               '<button class="green">Mở khóa</button></form>')
        return Response(render_page(_the("Máy bị khóa", nd, "#c33"), active="/khoa-may", title="Máy bị khóa"), status=423, mimetype="text/html")

    @app.before_request
    def _cong_khoa_may():
        if request.path in ("/khoa-may", "/healthz") or request.path.startswith("/static") or not (session.get("user") or _auth._is_local_screen()):
            return None
        return _trang_khoa() if _dang_khoa() else None

    @app.route("/khoa-may", methods=["GET", "POST"])
    def khoa_may_trang():
        moi = _moi()
        if not KL.dang_khoa(moi):
            return redirect("/")
        if request.method == "POST":
            try:
                n = KL.mo_khoa(moi, request.form.get("ma", ""))
            except KL.LoiKhoaLenh as e:
                return _trang_khoa(str(e))
            nho_khoa["luc"] = 0.0
            return redirect("/cap-nhat?mo=%d" % n)
        return _trang_khoa()

    try:                                                     # mat dien luc dang khoa -> hoan tat viec xoa ban ro
        KL.hoan_tat_khoa(_moi())
    except Exception as e:
        print("[cap-nhat] loi hoan tat khoa: %s" % e, flush=True)

    def vong_kiem_tra_nen():
        time.sleep(random.randint(60, 300))
        lan_nguyen_ven = 0.0
        while True:
            try:
                moi = _moi()
                if time.time() - lan_nguyen_ven > 6 * 3600:
                    lan_nguyen_ven = time.time()
                    NV.kiem_va_ghi(moi, moi.kho.bao_cao if moi.kho is not None else None)
                if M.den_han_hoi(moi) and moi.kho is not None:
                    M.kiem_tra(moi)
            except Exception as e:                                   # luong nen khong duoc chet vi mot lan loi
                print("[cap-nhat] loi kiem tra dinh ky: %s: %s" % (type(e).__name__, e), flush=True)
            time.sleep(900)
    threading.Thread(target=vong_kiem_tra_nen, daemon=True, name="cap-nhat-kiem-tra").start()

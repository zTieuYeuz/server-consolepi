# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Trang NGUOI DUNG va VAI TRO (RBAC 2.0.7 buoc 1). Chi Quan tri (root/sudo) vao duoc. Che do GHI NHAN: vai tro CHUA chan gi, chi cho thay truoc
route nao se bi tu choi khi bat chan (buoc 2, cho anh duyet)."""
import time
from html import escape as _e

from flask import redirect, request

from consolesystem.core import rbac as RB
from consolesystem.web.auth import la_quan_tri
from ui.layout import render_page


def _tu_choi():
    return render_page('<div class="msg err">Chỉ tài khoản quản trị (nhóm sudo) vào được trang này.</div>', active="/nguoi-dung", title="Người dùng"), 403


def _trang(msg="", ok=True):
    ds = RB.danh_sach()
    hang = ""
    for ten, v in sorted(ds.items()):
        hang += ('<tr><td>%s</td><td>%s</td><td><form method="POST" action="/nguoi-dung/xoa"><input type="hidden" name="ten" value="%s">'
                 '<button class="gray small">Bỏ vai trò</button></form></td></tr>' % (_e(ten), _e(RB.VAI_TRO.get(v["vai_tro"], v["vai_tro"])), _e(ten)))
    opts = "".join('<option value="%s">%s</option>' % (k, _e(n)) for k, n in RB.VAI_TRO.items())
    sk = RB.su_kien_gan_day()
    nk = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td><code>%s %s</code></td><td>%s</td></tr>" % (
        time.strftime("%H:%M:%S", time.localtime(x["luc"])), _e(x["nguoi"]), _e(x["vai_tro"]), _e(x["method"]), _e(x["path"]), _e(x["ly_do"])) for x in reversed(sk[-20:]))
    body = ((('<div class="msg %s">%s</div>' % ("ok" if ok else "err", _e(msg))) if msg else "") +
            '<div class="card"><h3>Chế độ ghi nhận</h3><p>Phân quyền đang ở <b>chế độ ghi nhận</b>: vai trò dưới đây <b>chưa chặn</b> thao tác nào; mọi người đăng nhập vẫn dùng như trước. '
            'Bảng cuối trang cho thấy trước những yêu cầu SẼ bị từ chối khi bật chặn. Tài khoản root và nhóm sudo luôn là <b>Quản trị</b> (không bị hạ vai trò, không tự khóa mình ra ngoài). '
            'Lỡ gán sai: trên Pi chạy <code>sudo python3 /opt/console-pi/scripts/rbac-reset.py</code> để về mặc định.</p></div>'
            '<div class="card"><h3>Người dùng đã gán vai trò</h3>' +
            ('<table><tr><th>Tài khoản</th><th>Vai trò</th><th></th></tr>%s</table>' % hang if hang else '<p class="tk-ghi">Chưa gán vai trò nào (tài khoản sudo tự là Quản trị).</p>') +
            '<form method="POST" action="/nguoi-dung/luu" class="row" style="align-items:flex-end;margin-top:12px;">'
            '<div><label style="margin-top:0;">Tài khoản Linux</label><input type="text" name="ten" required placeholder="vd nhanvien" style="max-width:200px;"></div>'
            '<div><label style="margin-top:0;">Vai trò</label><select name="vai_tro">%s</select></div><div><button type="submit">Lưu vai trò</button></div></form></div>' % opts +
            '<div class="card"><h3>Sẽ bị từ chối khi bật chặn (20 gần nhất)</h3>' +
            ('<table><tr><th>Giờ</th><th>Người</th><th>Vai trò</th><th>Yêu cầu</th><th>Lý do</th></tr>%s</table>' % nk if nk else '<p class="tk-ghi">Chưa có yêu cầu nào sẽ bị từ chối.</p>') + '</div>')
    return render_page(body, active="/nguoi-dung", title="Người dùng", subtitle="Vai trò và quyền")


def register_rbac(app):
    @app.route("/nguoi-dung")
    def nguoi_dung_trang():
        from flask import session
        return _trang() if la_quan_tri(session.get("user")) else _tu_choi()

    @app.route("/nguoi-dung/luu", methods=["POST"])
    def nguoi_dung_luu():
        from flask import session
        if not la_quan_tri(session.get("user")):
            return _tu_choi()
        ten = (request.form.get("ten") or "").strip()
        import pwd
        try:
            pwd.getpwnam(ten)
        except KeyError:
            return _trang("Không có tài khoản Linux tên “%s”." % ten, False)
        try:
            RB.dat_vai_tro(ten, request.form.get("vai_tro", ""))
        except ValueError as e:
            return _trang(str(e), False)
        try:
            from consolesystem.core.errlog import ghi_thao_tac
            ghi_thao_tac("Gán vai trò %s cho %s" % (request.form.get("vai_tro"), ten), "", nguoi=session.get("user"))
        except Exception as e:
            print("[rbac] khong ghi duoc nhat ky: %s" % type(e).__name__, flush=True)
        return redirect("/nguoi-dung")

    @app.route("/nguoi-dung/xoa", methods=["POST"])
    def nguoi_dung_xoa():
        from flask import session
        if not la_quan_tri(session.get("user")):
            return _tu_choi()
        RB.xoa((request.form.get("ten") or "").strip())
        return redirect("/nguoi-dung")

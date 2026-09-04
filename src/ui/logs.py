"""
Console Pi - Trang xem Nhat ky loi (yeu cau: "phai co he thong log lai ghi
lai tat ca nhung loi, nhieu khi can check thi sao")

Gom 2 nguon vao 1 cho de khong phai nho nhieu lenh:
  1. Loi Python KHONG DUOC BAT trong dashboard (tu errlog.ghi_loi(), duoc
     goi tu app.py moi khi co unhandled exception).
  2. Canh bao/loi tu journal cua tung dich vu chinh (bt-agent, tunnel,
     nginx...) - cung mot du lieu ma `journalctl -u <dich vu>` cho ra,
     nhung khong can nho ten lenh hay go vao Terminal.

Trang nay CHI DOC, khong xoa/sua gi ca - an toan de xem bat cu luc nao.
"""
from flask import request

from .layout import render_page
from .errlog import LOG_FILE, DICH_VU_CAN_THEO_DOI, doc_nhat_ky, doc_journal_dich_vu


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def register_logs(app):
    @app.route("/logs")
    def logs_page():
        tab = request.args.get("tab", "loi")

        noi_dung_loi = doc_nhat_ky(300)
        khoi_loi = f"""
        <div class="card" style="padding:0;overflow:hidden;">
          <pre style="margin:0;max-height:65vh;overflow:auto;padding:14px;">{_esc(noi_dung_loi) or '(chua co loi nao duoc ghi lai - tot!)'}</pre>
        </div>"""

        # Tab dich vu: 1 nut cho moi dich vu, bam vao moi tai du lieu (thay vi
        # tai het TAT CA journal cua moi dich vu ngay khi vao trang - vua
        # nhanh vua do tai cho Pi).
        dv_chon = request.args.get("dv", DICH_VU_CAN_THEO_DOI[0])
        if dv_chon not in DICH_VU_CAN_THEO_DOI:
            dv_chon = DICH_VU_CAN_THEO_DOI[0]
        nut_dv = "".join(
            f'<a class="btn {"blue" if d == dv_chon else "gray"} small" '
            f'href="/logs?tab=dichvu&dv={d}">{_esc(d)}</a>'
            for d in DICH_VU_CAN_THEO_DOI
        )
        noi_dung_dv = doc_journal_dich_vu(dv_chon, 60)
        khoi_dv = f"""
        <div class="row" style="margin-bottom:10px;">{nut_dv}</div>
        <div class="card" style="padding:0;overflow:hidden;">
          <pre style="margin:0;max-height:60vh;overflow:auto;padding:14px;">{_esc(noi_dung_dv)}</pre>
        </div>"""

        dang_loi = tab != "dichvu"
        body = f"""
        <div class="row" style="margin-bottom:14px;">
          <a class="btn {"blue" if dang_loi else "gray"}" href="/logs?tab=loi">📋 Loi ung dung</a>
          <a class="btn {"blue" if not dang_loi else "gray"}" href="/logs?tab=dichvu&dv={dv_chon}">⚙️ Canh bao dich vu</a>
          <a class="btn gray" href="/logs?tab={tab}&dv={dv_chon}">🔄 Lam moi</a>
        </div>

        {'<div class="msg info">File: <code>' + _esc(LOG_FILE) + '</code> - tu dong xoay vong, khong lam day the nho. '
         'Chi ghi loi THAT SU (unhandled exception), khong ghi cac loi da duoc cong cu tu bao (vd "khong ket noi duoc") - '
         'nhung loi do da hien ngay tren man hinh luc do roi.</div>' if dang_loi else ''}

        {khoi_loi if dang_loi else khoi_dv}
        """

        return render_page(body, active="/logs", title="Nhat ky loi",
                           subtitle="Xem lai loi da xay ra - khong can nho lenh journalctl")

    return app

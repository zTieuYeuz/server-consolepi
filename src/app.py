#!/usr/bin/env python3
"""
Console Pi - Dashboard web

File nay chi LAP RAP: tao app Flask roi gan cac nhom chuc nang.
    ui/        - giao dien: Tong quan, WiFi, Bluetooth, Terminal, SSH,
                 Thu vien lenh, Cai dat, Tai lieu, dang nhap
    nettools/  - 9 cong cu chan doan mang (port tu netool.io Pro2)

KIEN TRUC MANG:
    trinh duyet -> nginx :80 -> Flask 127.0.0.1:5000   (giao dien)
                             -> ttyd 127.0.0.1:801x    (terminal, WebSocket)

Flask KHONG mo ra mang truc tiep nua - nginx dung truoc. Ly do: trinh duyet
cam iframe khac origin hien hop thoai nhap mat khau, nen terminal chay cong
rieng se luon loi. Qua nginx thi moi thu chung cong 80, cung origin, va
terminal dung luon phien dang nhap cua dashboard.

Chay duoi quyen root (systemd khong khai User=) vi can raw socket cho cac
cong cu bat goi tin va quyen sua cau hinh mang.
"""
import sys
from urllib.parse import urlparse

sys.path.insert(0, "/opt/console-pi")

from flask import Flask, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix

from nettools import nettools_bp, register_no_cache_json, register_vkeyboard
from ui import register_all

app = Flask(__name__)

# Doc IP that cua nguoi dung tu header nginx dat.
# Neu khong co buoc nay, MOI request deu thay la 127.0.0.1 (vi nginx dung
# tren cung may) -> ngoai le "man hinh tai cho khong can dang nhap" se ap
# dung cho ca nguoi tu mang vao = mat het bao mat.
# An toan vi Flask chi lang nghe 127.0.0.1, khong ai ngoai nginx goi duoc.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.register_blueprint(nettools_bp)
register_all(app)
register_vkeyboard(app)
register_no_cache_json(app)


@app.errorhandler(405)
def _loi_sai_phuong_thuc(e):
    """
    LOI THAT DA GAP: rat nhieu route POST (bt-connect, bt-unpair, wifi-*,
    bt-scan...) hien trang HTML thang ra sau khi xu ly xong, KHONG chuyen
    huong. Vi vay dia chi tren trinh duyet VAN DUNG NGUYEN o duong dan POST
    do sau khi bam nut. Tren man hinh cam ung, chi can cu chi keo xuong lam
    moi (pull-to-refresh) la trinh duyet gui lai dung request do nhung bang
    GET - Flask tu choi (route chi cho POST), Werkzeug hien trang loi trang
    boc xau xi "Method Not Allowed", lam nguoi dung tuong ca dashboard bi vo
    (da gap dung tinh huong nay: man hinh Pi "trang boc" sau khi thu ket noi
    Bluetooth).

    Sua tan goc (doi tat ca route POST sang chuyen huong sau khi xu ly) la
    thay doi lon dung vao rat nhieu file, rui ro cao. Cach nay an toan hon:
    bat loi 405 O TOAN APP, dua nguoi dung VE LAI TRANG TRUOC DO (Referer)
    thay vi hien trang loi. Hanh dong that su da chay xong tu lan POST that
    truoc do; lan GET nham chi la du gay, khong can bao gi them.
    """
    dich = "/"
    try:
        p = urlparse(request.referrer or "")
        # Chi tin duong dan CUNG GOC (khong netloc, hoac netloc trung host
        # hien tai) - tranh bi dan huong sang trang la neu Referer bi gia.
        if p.path and (not p.netloc or p.netloc == request.host):
            dich = p.path
    except Exception:
        pass
    return redirect(dich)


@app.errorhandler(Exception)
def _ghi_loi_toan_cuc(e):
    """
    Ghi MOI loi Python khong duoc bat (unhandled exception) vao nhat ky
    tap trung truoc khi tra loi 500 binh thuong cho trinh duyet - xem
    trang /logs.

    VI SAO CAN: truoc day 1 loi bat ngo trong bat ky route nao chi hien 1
    trang loi chung chung roi BIEN MAT khong con dau vet - ngoai hien truong
    (cong ty, mang la, khong co ai de hoi ngay) khong con cach nao biet
    chuyen gi da xay ra. Nay moi loi deu duoc ghi lai kem traceback day du,
    xem lai duoc bat cu luc nao qua /logs, khong can nho lenh journalctl.

    LOI THAT DA GAP KHI VIET HAM NAY (bat duoc truoc khi trien khai, khong
    phai sau khi hong that): ban dau ham nay "ghi log roi raise lai nguyen
    van loi" voi y dinh "chi them, khong doi hanh vi". NHUNG Flask goi
    @app.errorhandler(Exception) o HAI CHO khac nhau - mot lan trong luc
    dispatch (handle_user_exception), MOT LAN NUA o tang WSGI cuoi cung
    (handle_exception, khi khong con noi nao bat duoc nua). raise lai o
    LAN GOI THU HAI se thoat hang ra NGOAI CA TANG WSGI - khong con la loi
    Python o trong app nua ma la loi ơ tang server, ket qua la TRINH DUYET
    NHAN DUOC KET NOI BI NGAT thay vi trang loi 500 binh thuong (da kiem
    chung that qua HTTP that truoc khi sua, khong doan mo). Neu trien khai
    ban dau do thi MOI loi khong duoc bat trong toan bo dashboard se lam
    nguoi dung thay trang trang/mat ket noi thay vi trang loi ro rang - te
    hon ca truoc khi co tinh nang ghi log nay.

    Sua: KHONG raise lai o CA HAI nhanh. Nhanh HTTPException (404, 403...)
    cung KHONG duoc raise - da kiem chung that: raise lai o day khien Flask
    coi day la loi khong xu ly duoc, bien 1 loi 404 binh thuong thanh 500 -
    tra ve `e.get_response()` moi giu dung nguyen ma trang thai va noi dung
    goc cua loi HTTP do (405 van do handler rieng ben tren xu ly truoc vi
    Flask uu tien handler dang ky cho DUNG ma trang thai hon la handler
    dang ky cho Exception noi chung).
    """
    from werkzeug.exceptions import HTTPException, InternalServerError
    if isinstance(e, HTTPException):
        return e.get_response()
    try:
        from ui.errlog import ghi_loi
        ghi_loi(request.path, f"{type(e).__name__}: {e}", ngoai_le=e)
    except Exception:
        pass
    return InternalServerError().get_response()


if __name__ == "__main__":
    # threaded=True: cac cong cu quet mang co the block vai giay,
    # khong duoc de treo ca dashboard
    app.run(host="127.0.0.1", port=5000, threaded=True)

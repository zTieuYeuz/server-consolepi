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

sys.path.insert(0, "/opt/console-pi")

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from nettools import nettools_bp, register_vkeyboard
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


if __name__ == "__main__":
    # threaded=True: cac cong cu quet mang co the block vai giay,
    # khong duoc de treo ca dashboard
    app.run(host="127.0.0.1", port=5000, threaded=True)

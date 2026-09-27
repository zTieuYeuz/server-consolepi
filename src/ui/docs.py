# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console System - trang "Tai lieu" tren may.

27/09/2026: toan bo tai lieu (truoc day ~1700 dong nam ngay trong may) da
chuyen len trang huong dan truc tuyen (console-docs) thanh 2 phan: huong dan
su dung + "Tai lieu ky thuat" (da loc chi tiet nhay cam). Tren may chi con
trang nay: gioi thieu + loi vao tung muc cua trang huong dan.

(c) 2026 zTieuYeuz - Console System
"""
from .layout import render_page
from .gioithieu import khoi_gioi_thieu, CSS_GIOI_THIEU, TRANG_TAI_LIEU

MUC = [
    ("Bắt đầu nhanh", "bat-dau-nhanh", "Cắm điện, vào giao diện, dùng ngay"),
    ("Lần đầu sử dụng", "lan-dau-su-dung", "Đăng nhập, các mục trong menu"),
    ("Mạng, WiFi và AP", "mang-wifi", "Kết nối WiFi, phát sóng, giả MAC"),
    ("Console và SSH", "console-ssh", "Phiên kết nối, thư viện lệnh"),
    ("Công cụ mạng", "network-tools", "Kiểm tra cổng, quét, MTU, DNS, TLS…"),
    ("Cài Windows qua mạng", "deployment-os", "Deployment OS, kịch bản, PXE"),
    ("Bảo trì và nhật ký", "bao-tri", "Nguồn điện, dung lượng, sao lưu, nhật ký"),
    ("Xử lý sự cố", "su-co", "Lỗi hay gặp và cách xử lý"),
    ("Tài liệu kỹ thuật", "ky-thuat", "Cách hoạt động bên trong, giới hạn, sự cố thật"),
]

CSS = CSS_GIOI_THIEU + """
.tl-luoi{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px;}
.tl-luoi a{display:block;padding:13px 15px;border:1px solid var(--vien);border-radius:10px;background:var(--the);}
.tl-luoi a:hover{border-color:var(--nhan);}
.tl-luoi b{display:block;color:var(--chu);margin-bottom:3px;} .tl-luoi small{color:var(--chu-mo);}
"""


def register_docs(app):
    @app.route("/docs")
    def docs_page():
        o = "".join(
            f'<a href="{TRANG_TAI_LIEU}/{ma}.html" target="_blank" rel="noopener">'
            f'<b>{ten}</b><small>{mo_ta}</small></a>' for ten, ma, mo_ta in MUC)
        body = f"""
        {khoi_gioi_thieu()}
        <h2>Mở nhanh từng mục hướng dẫn</h2>
        <div class="tl-luoi">{o}</div>
        """
        return render_page(body, active="/docs", title="Tài liệu",
                           subtitle="Hướng dẫn sử dụng và tài liệu kỹ thuật nằm trên trang hướng dẫn trực tuyến",
                           extra_css=CSS)

    return app

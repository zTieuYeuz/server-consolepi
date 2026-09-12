"""
Console Pi - Tab rieng: Tắt máy / Khởi động lại

Tach rieng khoi Tong quan theo yeu cau thuc te: may nay thuong duoc gan
vao vo RasPad (SunFounder). Nut "Tắt máy" o day CHI tat duoc he dieu hanh
tren module Raspberry Pi - no khong the va se khong bao gio tat duoc
man hinh/mach nguon rieng cua vo RasPad, vi hai ly do da kiem tra that
tren chinh may nay (khong doan):

  1. I2C dang bi TAT trong /boot/firmware/config.txt (dtparam=i2c_arm=on
     dang bi comment) - khong co /dev/i2c-1 nen du RasPad co chip quan ly
     nguon rieng qua I2C thi phan mem tren Pi cung khong doc/ghi duoc.
  2. Khong tim thay bat ky driver kernel, dtoverlay, hay dich vu he thong
     nao mang ten raspad/sunfounder tren may nay (da grep toan bo
     systemd unit files + dmesg + lsmod).

=> Ket luan trung thuc: KHONG phat hien duoc kenh dieu khien nguon nao
   cua rieng vo RasPad tu phia phan mem. Vo RasPad (it nhat la ban dang
   dung) dieu khien nguon toan bo bang cong tac/nut vat ly rieng, tach
   biet voi he dieu hanh cua Pi. Neu sau nay gan them mach quan ly nguon
   that (vi du bat lai i2c_arm va do thay chip that qua i2cdetect), quay
   lai sua ham nay - KHONG duoc bao "da tat duoc RasPad" khi chua do
   duoc phan cung that.
"""
from .layout import render_page
from . import health
from .home import power_msg_html, _esc


def register_power(app):

    @app.route("/power")
    def power_page():
        h = health.snapshot()
        power_msg = power_msg_html(h)

        body = f"""
        <h2>Trạng thái nguồn</h2>
        <table>
          <tr><td style="width:190px;">Nguồn điện (Pi)</td><td>{power_msg}</td></tr>
        </table>

        <h2>Tắt máy / Khởi động lại (module Raspberry Pi)</h2>
        <div class="row" style="gap:10px;margin-top:13px;flex-wrap:wrap;">
          <form method="POST" action="/power/reboot"
                onsubmit="return confirm('Khoi dong lai Console Pi ngay bay gio?\\n\\nMoi phien console dang mo se bi dong.');">
            <button type="submit" class="gray" data-busy="Đang khởi động lại...">🔄 Khoi dong lai</button>
          </form>
          <form method="POST" action="/power/poweroff"
                onsubmit="return confirm('TAT HAN Console Pi?\\n\\nBat lai phai cam dien truc tiep - khong bat tu xa duoc.');">
            <button type="submit" class="red" data-busy="Đang tắt máy...">🛑 Tat may</button>
          </form>
        </div>
        <p style="color:#8b93a1;font-size:13px;margin-top:10px;">
          Luôn tắt máy bằng nút này trước khi rút điện, tránh hỏng thẻ nhớ.
          Đợi đến khi đèn xanh (ACT) trên board Pi ngừng nhấp nháy rồi mới rút điện.
        </p>

        <h2>Cắm vỏ RasPad có tắt "hoàn toàn" được không?</h2>
        <div class="msg warn" style="line-height:1.6;">
          <strong>Không thể tắt màn hình/mạch nguồn của vỏ RasPad từ trang này.</strong><br>
          Đã kiểm tra thật trên chính máy: I2C đang bị tắt trong cấu hình boot
          (không có <code>/dev/i2c-1</code>), và không tìm thấy driver/dịch vụ
          nào của RasPad/SunFounder trên hệ thống - nên không có đường nào để
          phần mềm trên Pi nói chuyện với mạch nguồn riêng của vỏ.
          <br><br>
          Theo thiết kế của RasPad, vỏ này dùng <strong>công tắc nguồn vật lý</strong>
          (thường ở cạnh vỏ) để cấp/ngắt điện cho toàn bộ cụm màn hình + Pi -
          đây là cách DUY NHẤT để tắt hoàn toàn hiện tại. Quy trình đúng:
          <ol style="margin:8px 0 0 18px;">
            <li>Bam "🛑 Tat may" ở trên, đợi đèn ACT trên Pi ngừng nhấp nháy (Pi đã tắt hẳn).</li>
            <li>Sau do gat công tắc nguồn vật lý cua vo RasPad de cat dien man hinh.</li>
          </ol>
        </div>"""
        return render_page(body, active="/power", title="Nguồn điện",
                           subtitle="Tắt máy / khởi động lại module Raspberry Pi")

    @app.route("/power/<what>", methods=["POST"])
    def power_route(what):
        ok, msg = health.power_action(what)
        color = "ok" if ok else "err"
        # Trang tinh, khong tu chuyen huong: may sap tat/khoi dong lai nen
        # moi request tiep theo se that bai va nguoi dung tuong co loi.
        body = f"""
        <div class="msg {color}" style="font-size:15px;">{_esc(msg)}</div>
        <p style="margin-top:15px;"><a class="btn" href="/power">Về trang Nguồn điện</a></p>"""
        return render_page(body, active="/power", title="Nguon",
                           subtitle="Lệnh đã được gửi tới hệ thống"), (200 if ok else 400)

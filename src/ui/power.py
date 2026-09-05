"""
Console Pi - Tab rieng: Tat may / Khoi dong lai

Tach rieng khoi Tong quan theo yeu cau thuc te: may nay thuong duoc gan
vao vo RasPad (SunFounder). Nut "Tat may" o day CHI tat duoc he dieu hanh
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
        <h2>Trang thai nguon</h2>
        <table>
          <tr><td style="width:190px;">Nguon dien (Pi)</td><td>{power_msg}</td></tr>
        </table>

        <h2>Tat may / Khoi dong lai (module Raspberry Pi)</h2>
        <div class="row" style="gap:10px;margin-top:13px;flex-wrap:wrap;">
          <form method="POST" action="/power/reboot"
                onsubmit="return confirm('Khoi dong lai Console Pi ngay bay gio?\\n\\nMoi phien console dang mo se bi dong.');">
            <button type="submit" class="gray" data-busy="Dang khoi dong lai...">🔄 Khoi dong lai</button>
          </form>
          <form method="POST" action="/power/poweroff"
                onsubmit="return confirm('TAT HAN Console Pi?\\n\\nBat lai phai cam dien truc tiep - khong bat tu xa duoc.');">
            <button type="submit" class="red" data-busy="Dang tat may...">🛑 Tat may</button>
          </form>
        </div>
        <p style="color:#8b93a1;font-size:13px;margin-top:10px;">
          Luon tat may bang nut nay truoc khi rut dien, tranh hong the nho.
          Doi den khi den xanh (ACT) tren board Pi ngung nhap nhay roi moi rut dien.
        </p>

        <h2>Cam vo RasPad co tat "hoan toan" duoc khong?</h2>
        <div class="msg warn" style="line-height:1.6;">
          <strong>Khong the tat man hinh/mach nguon cua vo RasPad tu trang nay.</strong><br>
          Da kiem tra that tren chinh may: I2C dang bi tat trong cau hinh boot
          (khong co <code>/dev/i2c-1</code>), va khong tim thay driver/dich vu
          nao cua RasPad/SunFounder tren he thong - nen khong co duong nao de
          phan mem tren Pi noi chuyen voi mach nguon rieng cua vo.
          <br><br>
          Theo thiet ke cua RasPad, vo nay dung <strong>cong tac nguon vat ly</strong>
          (thuong o canh vo) de cap/ngat dien cho toan bo cum man hinh + Pi -
          day la cach DUY NHAT de tat hoan toan hien tai. Quy trinh dung:
          <ol style="margin:8px 0 0 18px;">
            <li>Bam "🛑 Tat may" o tren, doi den ACT tren Pi ngung nhap nhay (Pi da tat han).</li>
            <li>Sau do gat cong tac nguon vat ly cua vo RasPad de cat dien man hinh.</li>
          </ol>
        </div>"""
        return render_page(body, active="/power", title="Nguon dien",
                           subtitle="Tat may / khoi dong lai module Raspberry Pi")

    @app.route("/power/<what>", methods=["POST"])
    def power_route(what):
        ok, msg = health.power_action(what)
        color = "ok" if ok else "err"
        # Trang tinh, khong tu chuyen huong: may sap tat/khoi dong lai nen
        # moi request tiep theo se that bai va nguoi dung tuong co loi.
        body = f"""
        <div class="msg {color}" style="font-size:15px;">{_esc(msg)}</div>
        <p style="margin-top:15px;"><a class="btn" href="/power">Ve trang Nguon dien</a></p>"""
        return render_page(body, active="/power", title="Nguon",
                           subtitle="Lenh da duoc gui toi he thong"), (200 if ok else 400)

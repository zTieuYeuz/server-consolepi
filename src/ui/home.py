"""
Console Pi - Trang Tong quan (yeu cau so 2 va 4)

Bo cuc uu tien nhung gi dan network can nhin dau tien:
  1. Cac cong console dang cam (viec chinh cua thiet bi nay)
  2. Trang thai mang chi tiet tung card
  3. Tinh trang cac dich vu
"""
import glob
import os
import re
import subprocess

from flask import request

from .layout import render_page
from . import health

BASE_TTYD_PORT = 8001
NAMES_FILE = "/opt/console-pi/port-names.json"

SERVICES = [
    ("console-pi-dashboard", "Dashboard web"),
    ("console-pi-term-local", "Terminal tại chỗ"),
    ("console-pi-term-ssh", "Terminal SSH"),
    ("lldpd", "LLDP/CDP discovery"),
    ("bluetooth", "Bluetooth"),
    ("bt-nap", "Bluetooth PAN"),
    ("wifi-fallback.timer", "Tự chuyển WiFi/AP"),
    ("console-pi-kiosk", "Màn hình cảm ứng"),
]


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def power_msg_html(h):
    """Dung chung giua Tong quan va tab Nguon dien (dung 1 nguon logic)."""
    th = h["throttle"]
    if th is None:
        return ('<span style="color:#8b93a1;">Không đọc được (máy này '
                'khong phai Raspberry Pi)</span>')
    if th["now"]:
        return ('<span style="color:#ff6b6b;">⛔ ' +
                _esc(", ".join(th["now"])) +
                ' - DANG xay ra. Doi nguon/cap sac tot hon ngay.</span>')
    if th["past"]:
        return ('<span style="color:#ffb74d;">⚠️ ' +
                _esc(", ".join(th["past"])) +
                ' - da tung xay ra ke tu luc bat may. Nguon dang o ranh gioi.</span>')
    return '<span style="color:#6ee7a0;">🟢 Nguon on dinh, khong sut ap</span>'


def load_names():
    import json
    try:
        with open(NAMES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def console_port_for(devname):
    """
    Cong web cho 1 thiet bi serial. Hai ho thiet bi dung dai cong rieng de
    khong dam nhau:
        ttyUSB0..3 -> 8001..8004   (cap FTDI / Prolific / CH340 thong thuong)
        ttyACM0..3 -> 8005..8008   (cap Cisco USB Console, thiet bi CDC-ACM)

    Cong thuc nay phai KHOP voi scripts/ttyd-one.sh va bang map trong
    config/nginx-console-pi.conf - lech mot cho la console khong mo duoc.
    """
    m = re.search(r"(\d+)$", devname)
    idx = int(m.group(1)) if m else 0
    base = 8005 if devname.startswith("ttyACM") else BASE_TTYD_PORT
    return base + idx


def chip_of(devname):
    """
    Ten chip/hang cua cap console, doc tu /dev/serial/by-id.
    Giup phan biet khi cam nhieu cap cung luc (vd 'Cisco' vs 'FTDI').
    """
    try:
        for link in glob.glob("/dev/serial/by-id/*"):
            if os.path.basename(os.path.realpath(link)) == devname:
                name = os.path.basename(link)
                # usb-FTDI_FT232R_USB_UART_A9WUI6D2-if00-port0 -> FTDI FT232R
                name = name.replace("usb-", "").split("-if")[0]
                parts = name.split("_")
                return " ".join(parts[:3])[:34]
    except Exception:
        pass
    return ""


def get_ports():
    """
    Tim moi cong console dang cam.

    Quet CA HAI ho thiet bi:
      /dev/ttyUSB*  - cap dung chip chuyen doi (FTDI, Prolific, CH340...)
      /dev/ttyACM*  - thiet bi CDC-ACM, vi du cap console micro-USB cua Cisco
                      (thiet bi tu trinh dien la USB device)

    Truoc day chi quet ttyUSB* nen cap Cisco micro-USB cam vao khong hien -
    kernel co nhan (tao /dev/ttyACM0) nhung dashboard bo sot.
    """
    names = load_names()
    out = []
    for dev in sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")):
        devname = os.path.basename(dev)
        out.append({
            "devname": devname,
            "name": names.get(devname, ""),
            "port": console_port_for(devname),
            "chip": chip_of(devname),
        })
    return out


def service_states(names):
    """
    Hoi trang thai NHIEU dich vu bang MOT lenh.
    Truoc day goi rieng tung cai (8 lan spawn tien trinh moi lan tai trang) -
    tren Pi doi thap rat cham. systemctl is-active nhan nhieu ten cung luc.
    """
    try:
        r = subprocess.run(["systemctl", "is-active"] + list(names),
                           capture_output=True, text=True, timeout=6)
        lines = r.stdout.split()
        if len(lines) == len(names):
            return dict(zip(names, lines))
    except Exception:
        pass
    return {n: "unknown" for n in names}


def iface_detail(name):
    """Thong tin chi tiet 1 interface cho bang trang chu."""
    info = {"name": name, "ip": "", "mac": "", "state": "?", "speed": "", "extra": ""}
    try:
        with open(f"/sys/class/net/{name}/operstate") as f:
            info["state"] = f.read().strip()
    except Exception:
        return None      # interface khong ton tai
    try:
        with open(f"/sys/class/net/{name}/address") as f:
            info["mac"] = f.read().strip()
    except Exception:
        pass
    # Doc IP tu /proc/net/route + lenh ip chi khi can.
    # Uu tien /sys va /proc vi khong phai spawn tien trinh - nhanh hon nhieu
    # tren Pi doi thap (Pi 3 / Zero).
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", name],
                             capture_output=True, text=True, timeout=4).stdout
        for tok in out.split():
            if "/" in tok and tok.count(".") == 3:
                info["ip"] = tok
                break
    except Exception:
        pass
    try:
        with open(f"/sys/class/net/{name}/speed") as f:
            s = f.read().strip()
            if s and s != "-1":
                info["speed"] = f"{s} Mbps"
    except Exception:
        pass
    return info


def _thanh(phan_tram, nguong_vang=75, nguong_do=90):
    """
    Thanh mau truc quan cho mot chi so phan tram.

    Nhin con so "78%" thi phai doc va nghi; nhin thanh mau thi biet ngay
    dang o muc nao - quan trong khi dang cam may giua hien truong va chi
    liec nhanh mot cai.
    """
    p = max(0, min(100, int(phan_tram or 0)))
    mau = "#6ee7a0" if p < nguong_vang else ("#ffb74d" if p < nguong_do else "#ff6b6b")
    return (f'<div style="background:#2c3036;border-radius:5px;height:8px;'
            f'overflow:hidden;margin-top:5px;max-width:230px;">'
            f'<div style="width:{p}%;height:100%;background:{mau};"></div></div>')


def _bang_suc_khoe(h, power_msg):
    """
    Bang "Suc khoe thiet bi" - dung RIENG mot ham (khong viet thang trong
    trang) vi duoc dung o HAI cho: luc dung trang lan dau, va moi 10 giay
    khi /api/suckhoe tra ve de cap nhat tai cho. Viet 2 ban se lech nhau.
    """
    temp = h.get("temp")
    temp_color = ("#6ee7a0" if (temp or 0) < 65
                  else ("#ffb74d" if (temp or 0) < 80 else "#ff6b6b"))
    mem_u, mem_t, mem_p = h.get("mem", (0, 0, 0))
    dk_u, dk_t, dk_p = h.get("disk", (0, 0, 0))
    cpu = h.get("cpu")

    if cpu is None:
        # Lan do dau tien chua co moc so sanh - xem cpu_percent() trong
        # ui/health.py. Sau 10 giay se co so that.
        o_cpu = '<span style="color:#8b93a1;">đang đo...</span>'
    else:
        mau = "#6ee7a0" if cpu < 75 else ("#ffb74d" if cpu < 90 else "#ff6b6b")
        o_cpu = (f'<span style="color:{mau};font-weight:600;">{cpu}%</span>'
                 + _thanh(cpu))

    return f"""
        <table>
          <tr><td style="width:190px;">Nguồn điện</td><td>{power_msg}</td></tr>
          <tr><td>CPU đang dùng</td><td>{o_cpu}</td></tr>
          <tr><td>Bộ nhớ (RAM)</td>
              <td>{mem_u} / {mem_t} MB &nbsp;<strong>{mem_p}%</strong>
                  {_thanh(mem_p)}</td></tr>
          <tr><td>Nhiệt độ CPU</td>
              <td><span style="color:{temp_color};font-weight:600;">
                  {temp if temp is not None else '?'} &deg;C</span></td></tr>
          <tr><td>Thời gian chạy</td><td>{h.get('uptime', '?')}</td></tr>
          <tr><td>Tải hệ thống</td>
              <td><code>{h.get('load', '?')}</code>
                  <span style="color:#8b93a1;font-size:12px;">(1 / 5 / 15 phút)</span></td></tr>
          <tr><td>Đĩa</td><td>{dk_u} / {dk_t} GB &nbsp;<strong>{dk_p}%</strong>
                  {_thanh(dk_p, 80, 92)}</td></tr>
        </table>"""


def register_home(app):
    @app.route("/")
    def home():
        host = request.host.split(":")[0]
        ports = get_ports()

        # --- Cong console ---
        if ports:
            rows = ""
            for p in ports:
                rows += f"""
                <tr>
                  <td><code>{p['devname']}</code>
                      {f'<br><small style="color:#8b93a1;">{_esc(p["chip"])}</small>' if p.get("chip") else ''}</td>
                  <td>
                    <form method="POST" action="/rename" class="row" style="gap:7px;">
                      <input type="hidden" name="devname" value="{p['devname']}">
                      <input type="text" name="name" value="{_esc(p['name'])}"
                             placeholder="Ví dụ: Switch tầng 3" style="max-width:260px;">
                      <button type="submit" class="gray small">Lưu tên</button>
                    </form>
                  </td>
                  <td><a class="btn" href="/console/{p['devname']}">Mở Console</a></td>
                </tr>"""
            ports_html = f"""
            <table>
              <tr><th style="width:120px;">Cổng</th><th>Tên gợi nhớ</th><th style="width:150px;">Thao tác</th></tr>
              {rows}
            </table>"""
        else:
            ports_html = ('<div class="msg warn">Chưa cắm cáp console nào. '
                          'Cam cap USB-serial (FTDI/Prolific) vao Pi, trang se tu nhan.</div>')

        # --- Mang chi tiet ---
        net_rows = ""
        for ifname, label in (("eth0", "Card LAN"), ("wlan0", "Card WiFi"),
                              ("pan0", "Bluetooth PAN")):
            d = iface_detail(ifname)
            if not d:
                continue
            up = bool(d["ip"])
            net_rows += f"""
            <tr>
              <td><strong>{label}</strong><br><code style="font-size:12px;">{ifname}</code></td>
              <td>{'<code>' + d['ip'] + '</code>' if d['ip'] else '<span style="color:#8b93a1;">chua co IP</span>'}</td>
              <td><code style="font-size:12px;">{d['mac']}</code></td>
              <td>{d['state']}{' &middot; ' + d['speed'] if d['speed'] else ''}</td>
              <td>{'🟢' if up else '⚪'}</td>
            </tr>"""

        # --- Dich vu ---
        states = service_states([s for s, _ in SERVICES])
        svc_rows = ""
        for svc, label in SERVICES:
            st = states.get(svc, "unknown")
            icon = "🟢" if st == "active" else ("⚪" if st in ("inactive", "unknown") else "🔴")
            svc_rows += (f"<tr><td>{label}</td><td><code style='font-size:12px;'>{svc}</code></td>"
                         f"<td>{icon} {st}</td></tr>")


        # --- Suc khoe he thong + nguon ---
        h = health.snapshot()
        power_msg = power_msg_html(h)

        temp = h["temp"]
        temp_color = "#6ee7a0" if (temp or 0) < 65 else ("#ffb74d" if (temp or 0) < 80 else "#ff6b6b")
        mem_u, mem_t, mem_p = h["mem"]
        dk_u, dk_t, dk_p = h["disk"]

        # Khoi suc khoe TU CAP NHAT moi 10 giay (xem /api/suckhoe + doan JS
        # cuoi trang). Chi thay so trong khoi nay, KHONG tai lai ca trang:
        # tai lai ca trang se cuon vot len dau va dong cac bang dang xem -
        # rat kho chiu khi dang theo doi mot chi so.
        health_html = f"""
        <div id="suc-khoe">{_bang_suc_khoe(h, power_msg)}</div>
        <p style="margin-top:10px;"><a class="btn" href="/power">⚡ Tắt máy / Khởi động lại</a></p>
        <script>
        (function() {{
          var o = document.getElementById('suc-khoe');
          if (!o) return;
          function lamMoi() {{
            fetch('/api/suckhoe', {{cache: 'no-store'}})
              .then(function(r) {{ return r.json(); }})
              .then(function(d) {{ if (d && d.html) o.innerHTML = d.html; }})
              .catch(function() {{}});   /* mat mang thi giu so cu, khong bao loi */
          }}
          setInterval(lamMoi, 10000);
          /* Tab bi an (chuyen sang tab khac) thi KHONG do nua - do tiep chi
             ton CPU cua chinh con Pi ma khong ai nhin. Quay lai thi do ngay. */
          document.addEventListener('visibilitychange', function() {{
            if (!document.hidden) lamMoi();
          }});
        }})();
        </script>"""

        body = f"""
        <h2>Cổng console đang cắm</h2>
        {ports_html}

        <h2>Chi tiết mạng</h2>
        <table>
          <tr><th>Giao diện</th><th>Địa chỉ IP</th><th>MAC</th><th>Trạng thái</th><th style="width:50px;"></th></tr>
          {net_rows}
        </table>

        <h2>Sức khỏe thiết bị</h2>
        {health_html}

        <h2>Dịch vụ hệ thống</h2>
        <table>
          <tr><th style="width:220px;">Chức năng</th><th>Dịch vụ</th><th style="width:160px;">Trạng thái</th></tr>
          {svc_rows}
        </table>"""

        return render_page(body, active="/", title="Tổng quan",
                           subtitle="Trạng thái thiết bị và các cổng console")


    @app.route("/api/status")
    def api_status():
        """Du lieu cho thanh trang thai tu cap nhat moi 30 giay."""
        from flask import jsonify
        from .layout import get_status_chips
        return jsonify({"chips": get_status_chips()})

    @app.route("/api/suckhoe")
    def api_suc_khoe():
        """Bang suc khoe da render san - trang Tong quan goi moi 10 giay."""
        from flask import jsonify
        h = health.snapshot()
        return jsonify({"html": _bang_suc_khoe(h, power_msg_html(h))})

    @app.route("/console")
    def console_danh_sach():
        """
        Trang RIENG liet ke cac cong console dang cam.

        VI SAO TACH KHOI "Tong quan": cong console la thu dung NHIEU NHAT
        khi di hien truong (cam cap vao switch/router roi mo console), nhung
        truoc day no nam lot giua trang Tong quan - phai vao Tong quan roi
        cuon qua thanh trang thai, bang dich vu... moi toi. Nay co muc rieng
        trong nhom "Ket noi thiet bi", bam 1 phat la toi.
        """
        ports = get_ports()
        if ports:
            rows = ""
            for p in ports:
                chip = (f'<br><small style="color:#8b93a1;">{_esc(p["chip"])}</small>'
                        if p.get("chip") else "")
                rows += f"""
                <tr>
                  <td><code>{p['devname']}</code>{chip}</td>
                  <td>
                    <form method="POST" action="/rename" class="row" style="gap:7px;">
                      <input type="hidden" name="devname" value="{p['devname']}">
                      <input type="text" name="name" value="{_esc(p['name'])}"
                             placeholder="Ví dụ: Switch tầng 3" style="max-width:260px;">
                      <button type="submit" class="gray small">Lưu tên</button>
                    </form>
                  </td>
                  <td><a class="btn" href="/console/{p['devname']}">Mở Console</a></td>
                </tr>"""
            noi_dung = f"""
            <div class="card">
              <h3>Cổng console đang cắm</h3>
              <table>
                <tr><th style="width:150px;">Cổng</th><th>Tên gợi nhớ</th>
                    <th style="width:150px;">Thao tác</th></tr>
                {rows}
              </table>
              <p style="color:#8b93a1;font-size:13px;margin:12px 0 0;">
                Đặt tên gợi nhớ để lần sau cắm nhiều cáp cùng lúc còn biết cáp
                nào vào thiết bị nào. Tên được nhớ theo cổng.</p>
            </div>"""
        else:
            noi_dung = """
            <div class="card">
              <h3>Cổng console đang cắm</h3>
              <div class="msg warn">Chưa cắm cáp console nào. Cắm cáp USB-serial
                (FTDI / Prolific / CH340) hoặc cáp console micro-USB của Cisco
                vào Pi &mdash; trang này tự nhận, không cần khởi động lại.</div>
            </div>"""
        return render_page(noi_dung, active="/console", title="Console",
                           subtitle="Cổng serial nối tới switch / router")

    @app.route("/console/<devname>")
    def console_view(devname):
        """
        Hien console serial NGAY TRONG dashboard (giu thanh dieu huong).

        Truoc day nut nay mo thang cong 8001 o tab moi. Tren man hinh cam ung
        chay che do kiosk thi khong co thanh trinh duyet -> bam vao la ket luon,
        khong co duong quay lai. Nhung vao iframe thi thanh trai van con.
        """
        import re as _re
        if not _re.fullmatch(r"tty(USB|ACM)\d+", devname or ""):
            return render_page(
                '<div class="msg err">Tên cổng không hợp lệ.</div>'
                '<p><a class="btn" href="/">← Ve trang chu</a></p>',
                active="/", title="Console")

        if not os.path.exists(f"/dev/{devname}"):
            return render_page(
                f'<div class="msg err">Không thấy cổng <code>{devname}</code>. '
                f'Co the cap da bi rut.</div><p><a class="btn" href="/">← Ve trang chu</a></p>',
                active="/", title="Console")

        from .soanlenh import khoi_copy_terminal

        names = load_names()
        label = names.get(devname, "") or devname
        base = f"/term-console/{devname}"

        body = f"""
        <div class="row" style="margin-bottom:11px;">
          <a class="btn gray" href="/">← Ve trang chu</a>
          <a class="btn" href="{base}/">↗ Mo toan man hinh</a>
          <a class="btn blue" href="/nettools/console-backup?dev={devname}">🔌 Sao luu cau hinh</a>
          <span style="color:#8b93a1;font-size:13px;align-self:center;">
            {devname} &middot; 9600 8N1
          </span>
        </div>
        <div class="card" style="padding:0;overflow:hidden;margin-bottom:12px;">
          <iframe src="{base}/" title="Console {devname}"
                  style="width:100%;height:calc(100vh - 330px);min-height:380px;border:0;display:block;background:#000;"></iframe>
        </div>
        {khoi_copy_terminal()}
        <div class="msg info">
          Cham vao khung den de go lenh. Neu dung man hinh cam ung, ban phim ao
          se hien khi cham vao o nhap lieu o cac trang khac - rieng khung console
          nay can ban phim that (cam USB) hoac dung tab Thu vien lenh de dan lenh.
        </div>"""

        html = render_page(body, active="/", title=f"Console: {label}",
                           subtitle="Cổng serial đang mở trong dashboard")
        # Bao cho ban phim ao biet go vao phien tmux nao (xem vkeyboard.js)
        return html.replace("<body>", f'<body data-tmux-session="console-{devname}">', 1)

    return app

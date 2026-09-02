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

BASE_TTYD_PORT = 8001
NAMES_FILE = "/opt/console-pi/port-names.json"

SERVICES = [
    ("console-pi-dashboard", "Dashboard web"),
    ("console-pi-term-local", "Terminal local"),
    ("console-pi-term-ssh", "Terminal SSH"),
    ("lldpd", "LLDP/CDP discovery"),
    ("bluetooth", "Bluetooth"),
    ("bt-nap", "Bluetooth PAN"),
    ("wifi-fallback.timer", "Tu chuyen WiFi/AP"),
    ("console-pi-kiosk", "Man hinh cam ung"),
]


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def load_names():
    import json
    try:
        with open(NAMES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def get_ports():
    names = load_names()
    out = []
    for dev in sorted(glob.glob("/dev/ttyUSB*")):
        devname = os.path.basename(dev)
        m = re.search(r"(\d+)$", devname)
        out.append({
            "devname": devname,
            "name": names.get(devname, ""),
            "port": BASE_TTYD_PORT + (int(m.group(1)) if m else 0),
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
                  <td><code>{p['devname']}</code></td>
                  <td>
                    <form method="POST" action="/rename" class="row" style="gap:7px;">
                      <input type="hidden" name="devname" value="{p['devname']}">
                      <input type="text" name="name" value="{_esc(p['name'])}"
                             placeholder="Vi du: Switch tang 3" style="max-width:260px;">
                      <button type="submit" class="gray small">Luu ten</button>
                    </form>
                  </td>
                  <td><a class="btn" href="/console/{p['devname']}">Mo Console</a></td>
                </tr>"""
            ports_html = f"""
            <table>
              <tr><th style="width:120px;">Cong</th><th>Ten goi nho</th><th style="width:150px;">Thao tac</th></tr>
              {rows}
            </table>"""
        else:
            ports_html = ('<div class="msg warn">Chua cam cap console nao. '
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

        body = f"""
        <h2>Cong console dang cam</h2>
        {ports_html}

        <h2>Chi tiet mang</h2>
        <table>
          <tr><th>Giao dien</th><th>Dia chi IP</th><th>MAC</th><th>Trang thai</th><th style="width:50px;"></th></tr>
          {net_rows}
        </table>

        <h2>Dich vu he thong</h2>
        <table>
          <tr><th style="width:220px;">Chuc nang</th><th>Dich vu</th><th style="width:160px;">Trang thai</th></tr>
          {svc_rows}
        </table>"""

        return render_page(body, active="/", title="Tong quan",
                           subtitle="Trang thai thiet bi va cac cong console")


    @app.route("/api/status")
    def api_status():
        """Du lieu cho thanh trang thai tu cap nhat moi 30 giay."""
        from flask import jsonify
        from .layout import get_status_chips
        return jsonify({"chips": get_status_chips()})

    @app.route("/console/<devname>")
    def console_view(devname):
        """
        Hien console serial NGAY TRONG dashboard (giu thanh dieu huong).

        Truoc day nut nay mo thang cong 8001 o tab moi. Tren man hinh cam ung
        chay che do kiosk thi khong co thanh trinh duyet -> bam vao la ket luon,
        khong co duong quay lai. Nhung vao iframe thi thanh trai van con.
        """
        import re as _re
        if not _re.fullmatch(r"ttyUSB\d+", devname or ""):
            return render_page(
                '<div class="msg err">Ten cong khong hop le.</div>'
                '<p><a class="btn" href="/">← Ve trang chu</a></p>',
                active="/", title="Console")

        names = load_names()
        label = names.get(devname, "") or devname
        base = f"/term-console/{devname}"

        body = f"""
        <div class="row" style="margin-bottom:11px;">
          <a class="btn gray" href="/">← Ve trang chu</a>
          <a class="btn" href="{base}/">↗ Mo toan man hinh</a>
          <span style="color:#8b93a1;font-size:13px;align-self:center;">
            {devname} &middot; 9600 8N1
          </span>
        </div>
        <div class="card" style="padding:0;overflow:hidden;">
          <iframe src="{base}/" title="Console {devname}"
                  style="width:100%;height:600px;border:0;display:block;background:#000;"></iframe>
        </div>
        <div class="msg info">
          Cham vao khung den de go lenh. Neu dung man hinh cam ung, ban phim ao
          se hien khi cham vao o nhap lieu o cac trang khac - rieng khung console
          nay can ban phim that (cam USB) hoac dung tab Thu vien lenh de dan lenh.
        </div>"""

        html = render_page(body, active="/", title=f"Console: {label}",
                           subtitle="Cong serial dang mo trong dashboard")
        # Bao cho ban phim ao biet go vao phien tmux nao (xem vkeyboard.js)
        return html.replace("<body>", f'<body data-tmux-session="console-{devname}">', 1)

    return app

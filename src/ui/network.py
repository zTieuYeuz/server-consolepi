"""
Console Pi - Quan ly WiFi / AP / Bluetooth

Phan LOGIC ben duoi duoc chuyen nguyen ven tu app.py cu (da qua nhieu vong
debug thuc te: race condition voi systemd-networkd, vong doi D-Bus cua NAP,
ngat ket noi truoc khi reset Bluetooth...). CHI thay doi phan hien thi de
dung khung giao dien moi.
"""
import json
import os
import re
import subprocess
import threading
import time

from flask import request, redirect

from .layout import render_page

AP_IP = "192.168.50.1"
FORCE_AP_FLAG = "/opt/console-pi/force-ap.flag"
NAMES_FILE = "/opt/console-pi/port-names.json"
WPA_CONF = "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
NETWORK_BLOCK_RE = re.compile(r"network=\{.*?\}", re.S)

WIFI_STATUS = {"state": "idle", "ssid": None, "msg": "", "ip": None, "saved": False}


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def ap_locked():
    return os.path.exists(FORCE_AP_FLAG)


def get_net_status():
    ip = ""
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", "wlan0"],
                             capture_output=True, text=True, timeout=5).stdout
        for tok in out.split():
            if "/" in tok and tok.count(".") == 3:
                ip = tok.split("/")[0]
                break
    except Exception:
        pass

    ssid, mode = "", "?"
    try:
        info = subprocess.run(["iw", "dev", "wlan0", "info"],
                              capture_output=True, text=True, timeout=5).stdout
        for line in info.splitlines():
            line = line.strip()
            if line.startswith("ssid "):
                ssid = line[5:].strip()
            elif line.startswith("type "):
                mode = line[5:].strip()
    except Exception:
        pass

    if mode == "AP":
        return ("AP", ssid or "ConsolePi", ip or AP_IP)
    if ssid:
        return ("Client", ssid, ip)
    return ("Chua ket noi", "", ip)


# ---------------------------------------------------------------- WiFi
# Ket qua quet WiFi duoc nho lai. Ly do: `iw scan` mat 2-3 giay, neu quet
# moi lan tai trang thi trang WiFi luon cham 3 giay - rat kho chiu, nhat la
# tren Pi doi thap. Gio trang hien ngay, quet chay nen va cap nhat sau.
_SCAN_CACHE = {"ssids": [], "at": 0.0, "running": False}
SCAN_TTL = 45          # giay - du lau de khong quet lien tuc


def scan_wifi(force=False):
    """Tra ve danh sach SSID da nho. KHONG quet o day (tranh lam cham trang)."""
    if force or (time.time() - _SCAN_CACHE["at"] > SCAN_TTL):
        start_scan_async()
    return _SCAN_CACHE["ssids"]


def _do_scan():
    try:
        r = subprocess.run(["iw", "dev", "wlan0", "scan"],
                           capture_output=True, text=True, timeout=25)
        ssids = []
        for line in r.stdout.split("\n"):
            line = line.strip()
            if line.startswith("SSID:"):
                v = line.replace("SSID:", "").strip()
                if v and v not in ssids:
                    ssids.append(v)
        if ssids:
            _SCAN_CACHE["ssids"] = ssids
        _SCAN_CACHE["at"] = time.time()
    except Exception:
        _SCAN_CACHE["at"] = time.time()
    finally:
        _SCAN_CACHE["running"] = False


def start_scan_async():
    """Quet o luong nen de khong chan viec tai trang."""
    if _SCAN_CACHE["running"]:
        return
    _SCAN_CACHE["running"] = True
    threading.Thread(target=_do_scan, daemon=True).start()


def scan_age():
    """Bao nhieu giay truoc da quet - de hien cho nguoi dung biet do moi."""
    if not _SCAN_CACHE["at"]:
        return None
    return int(time.time() - _SCAN_CACHE["at"])


def load_saved_wifi():
    try:
        with open(WPA_CONF) as f:
            content = f.read()
    except Exception:
        return []
    out = []
    for block in NETWORK_BLOCK_RE.findall(content):
        m = re.search(r'ssid="([^"]*)"', block)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def save_wifi_permanently(ssid, password):
    try:
        with open(WPA_CONF) as f:
            content = f.read()
    except Exception:
        return False
    if f'ssid="{ssid}"' in content:
        return False
    with open(WPA_CONF, "a") as f:
        f.write(f'\nnetwork={{\n    ssid="{ssid}"\n    psk="{password}"\n}}\n')
    return True


def delete_saved_wifi(ssid):
    try:
        with open(WPA_CONF) as f:
            content = f.read()
    except Exception:
        return False
    keep, removed = [], False
    for block in NETWORK_BLOCK_RE.findall(content):
        m = re.search(r'ssid="([^"]*)"', block)
        if m and m.group(1) == ssid:
            removed = True
            continue
        keep.append(block)
    if not removed:
        return False
    header = NETWORK_BLOCK_RE.sub("", content).strip()
    with open(WPA_CONF, "w") as f:
        f.write("\n\n".join(p for p in ([header] + keep) if p).rstrip() + "\n")
    return True


def test_wifi_connection(ssid, password):
    conf = (f'ctrl_interface=/var/run/wpa_supplicant\nupdate_config=1\ncountry=VN\n\n'
            f'network={{\n    ssid="{ssid}"\n    psk="{password}"\n}}\n')
    path = "/tmp/wpa_test.conf"
    with open(path, "w") as f:
        f.write(conf)

    subprocess.run(["systemctl", "stop", "hostapd"])
    subprocess.run(["systemctl", "stop", "dnsmasq"])
    subprocess.run(["pkill", "-9", "wpa_supplicant"])
    time.sleep(1)
    subprocess.run(["ip", "addr", "flush", "dev", "wlan0"])
    subprocess.run(["ip", "link", "set", "wlan0", "down"])
    time.sleep(1)
    subprocess.run(["ip", "addr", "flush", "dev", "wlan0"])
    subprocess.run(["ip", "link", "set", "wlan0", "up"])
    time.sleep(2)
    subprocess.run(["wpa_supplicant", "-B", "-i", "wlan0", "-c", path])

    for _ in range(25):
        time.sleep(1)
        r = subprocess.run(["wpa_cli", "-i", "wlan0", "status"],
                           capture_output=True, text=True)
        if "wpa_state=COMPLETED" in r.stdout:
            subprocess.run(["networkctl", "reconfigure", "wlan0"])
            time.sleep(5)
            return True
    return False


def restore_ap_mode():
    subprocess.run(["pkill", "-9", "wpa_supplicant"])
    subprocess.run(["ip", "addr", "flush", "dev", "wlan0"])
    subprocess.run(["ip", "addr", "add", f"{AP_IP}/24", "dev", "wlan0"])
    subprocess.run(["ip", "link", "set", "wlan0", "up"])
    subprocess.run(["systemctl", "start", "hostapd"])
    subprocess.run(["systemctl", "start", "dnsmasq"])
    # Luoi an toan: systemd-networkd tung xoa mat IP nay ngay sau khi carrier len
    for _ in range(4):
        time.sleep(1)
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", "wlan0"],
                             capture_output=True, text=True, timeout=5).stdout
        if AP_IP in out:
            return
    subprocess.run(["ip", "addr", "add", f"{AP_IP}/24", "dev", "wlan0"])


def _switch_worker(ssid, password, do_save):
    """Doi HTTP response bay ve trinh duyet XONG roi moi ha AP."""
    time.sleep(5)
    WIFI_STATUS.update(state="switching", ssid=ssid,
                       msg=f"Dang chuyen sang '{ssid}'...", ip=None, saved=False)
    if test_wifi_connection(ssid, password):
        saved = save_wifi_permanently(ssid, password) if do_save else False
        _, _, ip = get_net_status()
        WIFI_STATUS.update(state="connected", ssid=ssid, ip=ip, saved=saved,
                           msg=f"Da ket noi '{ssid}'" + (" va da luu." if saved else " (khong luu)."))
    else:
        restore_ap_mode()
        WIFI_STATUS.update(state="failed", ssid=ssid, ip=AP_IP, saved=False,
                           msg=f"Ket noi '{ssid}' that bai. Da quay lai AP ConsolePi.")


# ---------------------------------------------------------- Bluetooth
def get_bt_paired_devices():
    try:
        out = subprocess.run(["bluetoothctl", "devices"],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    devs = []
    for line in out.splitlines():
        p = line.split(None, 2)
        if len(p) == 3 and p[0] == "Device":
            devs.append((p[1], p[2]))
    return devs


def bt_reset(forget_devices=False):
    """Ngat ket noi TUNG thiet bi truoc khi restart - ngat dot ngot tung
    lam Windows bi kep radio Bluetooth (da gap thuc te)."""
    for mac, _ in get_bt_paired_devices():
        subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, timeout=10)
    time.sleep(1)
    removed = []
    if forget_devices:
        for mac, name in get_bt_paired_devices():
            subprocess.run(["bluetoothctl", "remove", mac], capture_output=True)
            removed.append(name)
    subprocess.run(["systemctl", "restart", "bluetooth"], timeout=20)
    time.sleep(3)
    subprocess.run(["systemctl", "restart", "bt-pan0"], timeout=15)
    time.sleep(1)
    subprocess.run(["systemctl", "restart", "dnsmasq-bt"], timeout=15)
    time.sleep(2)
    return removed



# --------------------------------------------- Ghep cap thiet bi Bluetooth
def bt_scan(seconds=10):
    """Quet thiet bi Bluetooth xung quanh. Tra ve [(mac, ten)]."""
    try:
        subprocess.run(["bluetoothctl", "--timeout", str(seconds), "scan", "on"],
                       capture_output=True, timeout=seconds + 8)
    except Exception:
        pass
    found = []
    try:
        out = subprocess.run(["bluetoothctl", "devices"],
                             capture_output=True, text=True, timeout=6).stdout
        for line in out.splitlines():
            p = line.split(None, 2)
            if len(p) == 3 and p[0] == "Device":
                found.append((p[1], p[2]))
    except Exception:
        pass
    return found


def bt_device_info(mac):
    """Tra ve dict thong tin 1 thiet bi (Paired/Connected/Trusted/Icon)."""
    info = {"paired": False, "connected": False, "trusted": False, "icon": "", "name": mac}
    try:
        out = subprocess.run(["bluetoothctl", "info", mac],
                             capture_output=True, text=True, timeout=6).stdout
        for line in out.splitlines():
            t = line.strip()
            if t.startswith("Name:"):      info["name"] = t[5:].strip()
            elif t.startswith("Icon:"):    info["icon"] = t[5:].strip()
            elif t.startswith("Paired:"):    info["paired"] = t.endswith("yes")
            elif t.startswith("Connected:"): info["connected"] = t.endswith("yes")
            elif t.startswith("Trusted:"):   info["trusted"] = t.endswith("yes")
    except Exception:
        pass
    return info


def bt_pair(mac):
    """Ghep cap + tin cay + ket noi 1 thiet bi (ban phim, chuot...)."""
    steps = []
    for action in ("pair", "trust", "connect"):
        try:
            r = subprocess.run(["bluetoothctl", action, mac],
                               capture_output=True, text=True, timeout=35)
            out = (r.stdout + r.stderr).strip().splitlines()
            last = out[-1] if out else ""
            good = ("success" in last.lower() or "successful" in last.lower()
                    or "already" in last.lower())
            steps.append((action, good, last[:110]))
            if action == "pair" and not good:
                break        # khong ghep duoc thi khoi lam tiep
        except Exception as e:
            steps.append((action, False, str(e)[:110]))
            break
    ok = all(g for _, g, _ in steps) and len(steps) == 3
    detail = " | ".join(f"{a}: {m}" for a, _, m in steps)
    return ok, detail


def bt_unpair(mac):
    try:
        subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, timeout=12)
        r = subprocess.run(["bluetoothctl", "remove", mac],
                           capture_output=True, text=True, timeout=12)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[:120]
    except Exception as e:
        return False, str(e)[:120]


ICON_MAP = {"input-keyboard": "⌨️", "input-mouse": "🖱️", "computer": "💻",
            "phone": "📱", "audio-card": "🔊", "audio-headset": "🎧"}


# ------------------------------------------------------------- Trang
def _wifi_page(msg="", ok=True):
    mode, ssid, ip = get_net_status()
    saved = load_saved_wifi()
    locked = ap_locked()
    state = WIFI_STATUS.get("state")
    last = WIFI_STATUS.get("msg") if state in ("connected", "failed") else ""

    msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""
    last_html = (f'<div class="msg {"err" if state == "failed" else "ok"}">{_esc(last)}</div>'
                 if last else "")

    ap_card = f"""
    <div class="card">
      <h3>Che do phat song (AP ConsolePi)</h3>
      <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
        {"Dang KHOA o che do AP - Pi se khong tu chuyen sang WiFi." if locked
         else "Pi tu chuyen sang WiFi quen thuoc khi tim thay. Khoa AP de giu nguyen song ConsolePi."}
      </p>
      <form method="POST" action="{'/release-ap' if locked else '/force-ap'}"
            onsubmit="return confirm('{'Go khoa AP?' if locked else 'Bat va KHOA AP ConsolePi? Neu dang ket noi qua WiFi se bi dut - nen lam khi dang cam day LAN.'}');">
        <button type="submit" class="{'gray' if locked else 'blue'}">
          {'🔓 Go khoa AP' if locked else '🔒 Phat AP ConsolePi (khoa)'}
        </button>
      </form>
    </div>"""

    saved_rows = "".join(f"""
      <tr>
        <td>{_esc(s)}{' <span style="color:#4CAF50;font-size:12px;">● dang ket noi</span>' if s == ssid else ''}</td>
        <td><form method="POST" action="/wifi-delete"
                  onsubmit="return confirm('Xoa WiFi {_esc(s)}?');">
              <input type="hidden" name="ssid" value="{_esc(s)}">
              <button type="submit" class="red small">Xoa</button>
            </form></td>
      </tr>""" for s in saved)

    scan_form = ""
    if not locked:
        ssids = scan_wifi()
        age = scan_age()
        opts = "".join(f"<option>{_esc(s)}</option>" for s in ssids)
        if not ssids:
            fresh = "Dang quet lan dau, bam Quet lai sau vai giay..."
        elif age is None:
            fresh = ""
        elif age < 60:
            fresh = f"quet {age} giay truoc"
        else:
            fresh = f"quet {age // 60} phut truoc"
        scan_form = f"""
        <h2>Ket noi WiFi moi</h2>
        <div class="card">
          <form method="POST" action="/wifi-rescan" style="margin-bottom:12px;">
            <button type="submit" class="gray small">🔄 Quet lai</button>
            <span style="color:#8b93a1;font-size:13px;margin-left:9px;">{fresh}</span>
          </form>
          <form method="POST" action="/connect-wifi">
            <label>Chon WiFi ({len(ssids)} mang tim thay)</label>
            <select name="ssid" required>{opts}</select>
            <label>Mat khau</label>
            <input type="password" name="password" required>
            <label style="display:flex;align-items:center;gap:9px;margin-top:13px;">
              <input type="checkbox" name="save" value="1" checked style="width:20px;height:20px;">
              <span>Luu de lan sau tu ket noi</span>
            </label>
            <div class="row" style="margin-top:13px;"><button type="submit">Ket noi</button></div>
          </form>
          <p style="color:#8b93a1;font-size:13px;margin-top:11px;">
            Neu dang xem qua WiFi, ket noi se dut khi Pi chuyen mang. Sau 20-30 giay
            hay noi may vao mang moi roi vao lai <code>http://server-console.local</code>.
          </p>
        </div>"""

    body = f"""
    {msg_html}{last_html}
    <div class="card">
      <h3>Trang thai hien tai</h3>
      <table style="max-width:470px;">
        <tr><th style="width:150px;">Che do</th><td>{mode}</td></tr>
        <tr><th>Mang</th><td>{_esc(ssid) or '-'}</td></tr>
        <tr><th>Dia chi IP</th><td><code>{ip or '-'}</code></td></tr>
      </table>
    </div>
    {ap_card}
    {scan_form}
    <h2>WiFi da luu ({len(saved)})</h2>
    <table><tr><th>SSID</th><th style="width:110px;">Thao tac</th></tr>{saved_rows}</table>
    {'<p style="color:#8b93a1;">Chua luu WiFi nao. Pi se tu phat AP ConsolePi khi khong tim thay mang quen.</p>' if not saved else ''}
    <h2>Them WiFi thu cong</h2>
    <div class="card">
      <p style="color:#8b93a1;font-size:13px;margin:0 0 9px;">
        Chi luu vao danh sach, khong ket noi ngay. Dung khi biet truoc WiFi noi sap den.</p>
      <form method="POST" action="/wifi-add">
        <label>Ten WiFi (SSID)</label><input type="text" name="ssid" required>
        <label>Mat khau</label><input type="password" name="password" required>
        <div class="row" style="margin-top:13px;"><button type="submit">Luu vao danh sach</button></div>
      </form>
    </div>"""

    return render_page(body, active="/wifi", title="WiFi",
                       subtitle="Ket noi mang, quan ly WiFi da luu, che do phat song")


def _bt_page(msg="", ok=True, scanned=None):
    devs = get_bt_paired_devices()
    infos = [(m, bt_device_info(m)) for m, _ in devs]
    msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

    # --- Thiet bi da ghep cap ---
    rows = ""
    for mac, i in infos:
        icon = ICON_MAP.get(i["icon"], "🔗")
        state = ("🟢 dang ket noi" if i["connected"]
                 else ("⚪ da ghep, chua noi" if i["paired"] else "—"))
        rows += f"""
        <tr>
          <td>{icon} <strong>{_esc(i['name'])}</strong><br>
              <code style="font-size:12px;">{_esc(mac)}</code></td>
          <td>{state}</td>
          <td>
            <form method="POST" action="/bt-connect" style="display:inline;">
              <input type="hidden" name="mac" value="{_esc(mac)}">
              <button type="submit" class="small">Ket noi lai</button>
            </form>
            <form method="POST" action="/bt-unpair" style="display:inline;"
                  onsubmit="return confirm('Xoa ghep cap {_esc(i['name'])}?');">
              <input type="hidden" name="mac" value="{_esc(mac)}">
              <button type="submit" class="red small">Xoa</button>
            </form>
          </td>
        </tr>"""

    # --- Ket qua quet (neu vua bam quet) ---
    scan_html = ""
    if scanned is not None:
        paired_macs = {m for m, _ in devs}
        new_rows = ""
        for mac, name in scanned:
            if mac in paired_macs:
                continue
            i = bt_device_info(mac)
            icon = ICON_MAP.get(i["icon"], "🔗")
            new_rows += f"""
            <tr>
              <td>{icon} <strong>{_esc(name)}</strong><br>
                  <code style="font-size:12px;">{_esc(mac)}</code></td>
              <td>{_esc(i['icon']) or 'khong ro loai'}</td>
              <td>
                <form method="POST" action="/bt-pair" style="display:inline;">
                  <input type="hidden" name="mac" value="{_esc(mac)}">
                  <button type="submit" class="blue small">Ghep cap</button>
                </form>
              </td>
            </tr>"""
        scan_html = f"""
        <h2>Thiet bi tim thay ({len([1 for m,_ in scanned if m not in paired_macs])} chua ghep)</h2>
        <table><tr><th>Thiet bi</th><th style="width:150px;">Loai</th>
                   <th style="width:120px;">Thao tac</th></tr>{new_rows}</table>
        {'<p style="color:#8b93a1;">Khong thay thiet bi moi nao. Nho bat che do ghep cap tren ban phim (thuong giu nut Connect vai giay den khi den nhap nhay).</p>' if not new_rows else ''}"""

    body = f"""
    {msg_html}

    <h2>Ghep ban phim / chuot Bluetooth</h2>
    <div class="card">
      <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
        Dung khi man hinh cam ung khong tien go chu. Bat che do ghep cap tren
        ban phim truoc (thuong giu nut cho den khi den nhap nhay), roi bam Quet.
      </p>
      <form method="POST" action="/bt-scan">
        <button type="submit">🔍 Quet thiet bi (10 giay)</button>
      </form>
    </div>
    {scan_html}

    <h2>Thiet bi da ghep cap ({len(devs)})</h2>
    <table><tr><th>Thiet bi</th><th style="width:170px;">Trang thai</th>
               <th style="width:200px;">Thao tac</th></tr>{rows}</table>
    {'<p style="color:#8b93a1;">Chua ghep cap thiet bi nao.</p>' if not devs else ''}

    <h2>Ket noi mang qua Bluetooth (PAN)</h2>
    <div class="card">
      <p style="color:#8b93a1;font-size:13px;margin:0;">
        Ghep may tinh/dien thoai voi ten <strong>ConsolePi</strong>, sau do vao
        <code>http://192.168.60.1</code>. Tren Windows: mo
        <code>devicesandprinters</code> &rarr; chuot phai ConsolePi &rarr;
        <em>Connect using</em> &rarr; <em>Access point</em>.
      </p>
    </div>

    <h2>Khoi dong lai Bluetooth</h2>
    <div class="card">
      <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
        Dung khi khong ghep cap hoac khong ket noi lai duoc.
      </p>
      <form method="POST" action="/bt-reset"
            onsubmit="return confirm('Reset Bluetooth? Cac thiet bi dang noi se bi ngat.');">
        <label style="display:flex;align-items:center;gap:9px;">
          <input type="checkbox" name="forget" value="1" style="width:20px;height:20px;">
          <span>Quen tat ca thiet bi da ghep cap</span>
        </label>
        <div class="row" style="margin-top:13px;">
          <button type="submit" class="gray">🔄 Reset Bluetooth</button>
        </div>
      </form>
    </div>"""

    return render_page(body, active="/bluetooth", title="Bluetooth",
                       subtitle="Ghep ban phim/chuot va ket noi mang du phong")


def register_network(app):
    @app.route("/wifi")
    def wifi_page():
        return _wifi_page()

    @app.route("/bluetooth")
    def bt_page():
        return _bt_page()

    @app.route("/rename", methods=["POST"])
    def rename():
        devname = request.form.get("devname")
        name = request.form.get("name")
        try:
            with open(NAMES_FILE) as f:
                names = json.load(f)
        except Exception:
            names = {}
        names[devname] = name
        with open(NAMES_FILE, "w") as f:
            json.dump(names, f, ensure_ascii=False)
        return redirect("/")

    @app.route("/connect-wifi", methods=["POST"])
    def connect_wifi():
        ssid = request.form.get("ssid")
        password = request.form.get("password")
        do_save = request.form.get("save") == "1"
        if ap_locked():
            return _wifi_page(msg="AP dang bi KHOA. Go khoa truoc khi doi WiFi.", ok=False)
        WIFI_STATUS.update(state="pending", ssid=ssid, msg="Chuan bi chuyen mang...")
        threading.Thread(target=_switch_worker, args=(ssid, password, do_save),
                         daemon=True).start()
        body = f"""
        <div class="msg warn">
          <h3 style="margin:0 0 8px;">Dang chuyen sang '{_esc(ssid)}'</h3>
          <p>Sau 20-30 giay: noi may cua ban vao WiFi <strong>{_esc(ssid)}</strong>
          roi mo lai <a href="http://server-console.local">http://server-console.local</a>.</p>
          <p>Neu that bai, Pi tu bat lai AP <strong>ConsolePi</strong> sau khoang 30 giay.</p>
        </div>
        <p><a class="btn" href="/wifi">← Quay lai trang WiFi</a></p>"""
        return render_page(body, active="/wifi", title="Dang chuyen mang")

    @app.route("/wifi-rescan", methods=["POST"])
    def wifi_rescan():
        start_scan_async()
        time.sleep(3)      # cho quet mot chut de nguoi dung thay ket qua ngay
        return _wifi_page(msg="Dang quet lai. Neu chua thay du, bam Quet lai lan nua.",
                          ok=True)

    @app.route("/wifi-add", methods=["POST"])
    def wifi_add():
        ssid = (request.form.get("ssid") or "").strip()
        pw = request.form.get("password") or ""
        if not ssid:
            return _wifi_page(msg="Ten WiFi khong duoc de trong.", ok=False)
        if len(pw) < 8:
            return _wifi_page(msg="Mat khau WPA2 phai tu 8 ky tu tro len.", ok=False)
        if '"' in ssid or '"' in pw:
            return _wifi_page(msg='Khong duoc chua dau nhay kep (").', ok=False)
        if save_wifi_permanently(ssid, pw):
            return _wifi_page(msg=f"Da luu '{ssid}'.", ok=True)
        return _wifi_page(msg=f"'{ssid}' da co trong danh sach.", ok=False)

    @app.route("/wifi-delete", methods=["POST"])
    def wifi_delete():
        ssid = request.form.get("ssid", "")
        if delete_saved_wifi(ssid):
            return _wifi_page(msg=f"Da xoa '{ssid}'.", ok=True)
        return _wifi_page(msg=f"Khong tim thay '{ssid}'.", ok=False)

    @app.route("/force-ap", methods=["POST"])
    def force_ap():
        with open(FORCE_AP_FLAG, "w") as f:
            f.write("locked\n")

        def worker():
            time.sleep(5)
            restore_ap_mode()
            WIFI_STATUS.update(state="ap_locked", ssid="ConsolePi", ip=AP_IP,
                               msg="Da KHOA che do AP.")
        threading.Thread(target=worker, daemon=True).start()
        body = f"""
        <div class="msg warn">
          <h3 style="margin:0 0 8px;">Dang bat va KHOA AP "ConsolePi"</h3>
          <p>Sau 15-20 giay, noi vao WiFi <strong>ConsolePi</strong> roi mo
          <a href="http://{AP_IP}">http://{AP_IP}</a>.</p>
          <p>Neu dang xem qua WiFi, ket noi se dut. Qua day LAN thi khong anh huong.</p>
        </div>
        <p><a class="btn" href="/wifi">← Trang WiFi</a></p>"""
        return render_page(body, active="/wifi", title="Dang bat AP")

    @app.route("/release-ap", methods=["POST"])
    def release_ap():
        try:
            os.remove(FORCE_AP_FLAG)
        except FileNotFoundError:
            pass

        def worker():
            time.sleep(3)
            subprocess.run(["/opt/console-pi/scripts/wifi-fallback.sh"])
        threading.Thread(target=worker, daemon=True).start()
        return _wifi_page(msg="Da go khoa AP. Pi se quet lai va tu chon WiFi quen thuoc.", ok=True)

    @app.route("/bt-scan", methods=["POST"])
    def bt_scan_route():
        found = bt_scan(10)
        return _bt_page(msg=f"Quet xong, thay {len(found)} thiet bi.",
                        ok=True, scanned=found)

    @app.route("/bt-pair", methods=["POST"])
    def bt_pair_route():
        mac = request.form.get("mac", "")
        ok_p, detail = bt_pair(mac)
        if ok_p:
            return _bt_page(msg=f"Da ghep cap va ket noi {mac}.", ok=True)
        return _bt_page(msg=f"Ghep cap that bai. Chi tiet: {detail}", ok=False)

    @app.route("/bt-connect", methods=["POST"])
    def bt_connect_route():
        mac = request.form.get("mac", "")
        try:
            r = subprocess.run(["bluetoothctl", "connect", mac],
                               capture_output=True, text=True, timeout=25)
            out = (r.stdout + r.stderr).strip().splitlines()
            last = out[-1] if out else ""
            good = "success" in last.lower()
            return _bt_page(msg=(f"Da ket noi {mac}." if good
                                 else f"Khong ket noi duoc: {last[:120]}"), ok=good)
        except Exception as e:
            return _bt_page(msg=f"Loi: {e}", ok=False)

    @app.route("/bt-unpair", methods=["POST"])
    def bt_unpair_route():
        mac = request.form.get("mac", "")
        ok_u, detail = bt_unpair(mac)
        return _bt_page(msg=(f"Da xoa ghep cap {mac}." if ok_u
                             else f"Khong xoa duoc: {detail}"), ok=ok_u)

    @app.route("/bt-reset", methods=["POST"])
    def bt_reset_route():
        forget = request.form.get("forget") == "1"
        removed = bt_reset(forget_devices=forget)
        m = "Da khoi dong lai Bluetooth."
        if forget:
            m += f" Da quen {len(removed)} thiet bi - can ghep cap lai tu dau."
        return _bt_page(msg=m, ok=True)

    @app.route("/wifi-status")
    def wifi_status():
        mode, ssid, ip = get_net_status()
        return {"mode": mode, "ssid": ssid, "ip": ip,
                "switch_state": WIFI_STATUS.get("state"),
                "switch_msg": WIFI_STATUS.get("msg")}

    return app

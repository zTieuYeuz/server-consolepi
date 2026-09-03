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
    """Thong tin 1 thiet bi, kem phan loai (ban phim / may tinh / tai nghe...)."""
    # 'bonded' KHAC 'paired'. BlueZ co the danh dau Paired=yes ma van khong
    # luu duoc khoa lien ket (Bonded=no) - ban ghi ghep cap hong mot nua.
    # Voi ban phim/chuot thi day la loi CHET NGUOI: BlueZ tu choi gan ho so
    # HID ("Rejected connection from !bonded device"), nen thiet bi hien la
    # Connected=yes nhung kernel khong tao /dev/input nao ca -> nguoi dung
    # thay "dang ket noi" ma go khong an gi. Phai doc rieng de bat duoc.
    info = {"paired": False, "bonded": False, "connected": False,
            "trusted": False, "icon": "", "name": mac, "cod": 0, "uuids": []}
    try:
        out = subprocess.run(["bluetoothctl", "info", mac],
                             capture_output=True, text=True, timeout=6).stdout
        for line in out.splitlines():
            t = line.strip()
            if t.startswith("Name:"):      info["name"] = t[5:].strip()
            elif t.startswith("Icon:"):    info["icon"] = t[5:].strip()
            elif t.startswith("Paired:"):    info["paired"] = t.endswith("yes")
            elif t.startswith("Bonded:"):    info["bonded"] = t.endswith("yes")
            elif t.startswith("Connected:"): info["connected"] = t.endswith("yes")
            elif t.startswith("Trusted:"):   info["trusted"] = t.endswith("yes")
            elif t.startswith("Class:"):
                try:
                    info["cod"] = int(t.split()[1], 16)
                except (IndexError, ValueError):
                    pass
            elif t.startswith("UUID:"):
                m = re.search(r"\(([0-9a-fA-F-]{36})\)", t)
                if m:
                    info["uuids"].append(m.group(1))
    except Exception:
        pass
    info["cls"] = classify_bt(info["cod"], info["uuids"], info["icon"])
    return info


BT_STATE_FILE = "/run/console-pi-bt.json"

# Trang thai ghep cap dang chay (chay o luong nen de trang web khong bi treo)
_PAIR = {"running": False, "mac": "", "step": "", "ok": None, "detail": ""}


def bt_agent_state():
    """
    Doc ma so ma agent dang hien (de nguoi dung go len ban phim).
    Agent ghi file nay khi BlueZ hoi ma - xem scripts/bt-auto-agent.py
    """
    try:
        with open(BT_STATE_FILE) as f:
            d = json.load(f)
        # Chi coi la con hieu luc trong 2 phut
        if time.time() - d.get("at", 0) < 120:
            return d
    except Exception:
        pass
    return None


def _thiet_bi_da_thay(mac):
    """Kiem tra BlueZ co dang "biet" thiet bi nay khong (da tung discover)."""
    try:
        out = subprocess.run(["bluetoothctl", "devices"],
                             capture_output=True, text=True, timeout=6).stdout
        return mac.lower() in out.lower()
    except Exception:
        return False


def _pair_worker(mac):
    """Ghep cap o luong nen. Ban phim can nguoi dung go ma nen co the lau."""
    steps = []
    try:
        # Xoa sach ban ghi cu TRUOC KHI ghep. Ly do: BlueZ co the con giu mot
        # ban ghi hong mot nua (Paired=yes nhung khong co khoa lien ket). Khi
        # do lenh `pair` tra ve "Already Paired" va di tiep, nhung ho so HID
        # van bi tu choi vinh vien - ghep bao nhieu lan cung khong khoi.
        # Xoa truoc thi moi lan ghep deu la mot lan ghep that su moi.
        subprocess.run(["bluetoothctl", "remove", mac],
                       capture_output=True, timeout=15)

        # LOI DA GAP THAT (quan trong): sau khi `remove`, BlueZ QUEN HAN thiet
        # bi - no khong con nam trong danh sach "da biet" nua. Goi `pair` ngay
        # sau do that bai tuc khac voi loi "Device ... not available", VI
        # `pair` theo dia chi MAC chi hoat dong voi thiet bi da duoc discover.
        #
        # Rieng ban phim/chuot Bluetooth con co mot dac diem: sau khi bi tu
        # choi ket noi (do chua bonded), no se tu dong thu KET NOI LAI toi
        # dung dia chi Pi nhieu lan - day la "page request" truc tiep, KHONG
        # phai quang ba discover, nen `bluetoothctl scan` thong thuong khong
        # bat duoc no. No CHI hien ra duoc khi nguoi dung bat lai che do ghep
        # cap tren CHINH ban phim (giu nut Connect cho den khi den nhap nhay
        # NHANH - khac voi nhap nhay cham la dang co reconnect binh thuong).
        #
        # Vi vay o day ta quet toi da 20 giay, kiem tra dinh ky xem thiet bi
        # da xuat hien chua, thay vi doi cung mot khoang thoi gian co dinh.
        # GIU QUET CHAY SUOT ca qua trinh ghep cap, khong tat ngay khi vua
        # thay thiet bi.
        #
        # LOI THAT DA GAP: truoc day thay thiet bi la tat quet ngay roi moi
        # `pair`. BlueZ coi thiet bi vua quet duoc ma chua ghep cap la "tam
        # thoi" va XOA khoi danh sach rat nhanh sau khi ngung quet - den luc
        # chay `pair` thi bao thang "Device ... not available" du vai giay
        # truoc con thay ro rang. Da tai hien duoc dung loi nay tren may that.
        # Vi vay dat thoi gian quet du dai (120s) de phu het ca buoc pair/
        # trust/connect, va chi tat quet o khoi finally ben duoi.
        # Cua so quet 150 GIAY, khong phai 20.
        #
        # DAY LA SO DO THAT, khong phai uoc luong: ghep ban phim Samsung cua
        # nguoi dung tren chinh may nay, ban phim mat **116 giay** ke tu luc
        # bat dau quet moi chiu quang ba ra. Cua so cu 20 giay (va ca muc 60
        # giay thu o ban sua truoc) DEU KHONG DU - trang bao "khong tim thay"
        # du ban phim hoan toan binh thuong, va vi dung ngay o buoc quet nen
        # khong de lai dau vet nao trong log de lan ra nguyen nhan.
        #
        # Ly do ban phim lau nhu vay: nguoi dung bam nut tren TRANG WEB truoc,
        # roi moi cam ban phim len giu nut pairing; cong them nhieu ban phim
        # phai giu nut vai giay moi vao che do quang ba.
        TONG_GIAY_QUET = 150
        _PAIR["step"] = "quet"
        subprocess.Popen(["bluetoothctl", "--timeout", "120", "scan", "on"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        thay = False
        for giay in range(TONG_GIAY_QUET):
            time.sleep(1)
            # Hien dem nguoc de nguoi dung biet con bao lau ma bam nut tren
            # ban phim, thay vi ngoi doan.
            _PAIR["step"] = f"quet (con {TONG_GIAY_QUET - giay}s - bam nut ghep cap tren ban phim ngay)"
            if _thiet_bi_da_thay(mac):
                thay = True
                break

        if not thay:
            steps.append(("quet", False,
                          f"Khong tim thay thiet bi sau {TONG_GIAY_QUET}s quet. Ban phim "
                          "gan nhu chac chan CHUA o che do ghep cap: giu nut Connect/"
                          "pairing tren ban phim cho den khi den nhap nhay NHANH (nhap "
                          "nhay cham la dang tim lai may cu, khong phai che do ghep cap), "
                          "roi bam Ghep cap lai ngay. Ban phim chi giu che do nay 1-3 "
                          "phut. Neu van khong thay: thu thay pin."))
        else:
            for action, limit in (("pair", 60), ("trust", 10), ("connect", 25)):
                _PAIR["step"] = action
                r = subprocess.run(["bluetoothctl", action, mac],
                                   capture_output=True, text=True, timeout=limit)
                out = (r.stdout + r.stderr).strip().splitlines()
                last = out[-1] if out else ""
                good = any(k in last.lower() for k in
                           ("success", "successful", "already"))
                steps.append((action, good, last[:120]))
                if action == "pair" and not good:
                    break
    except subprocess.TimeoutExpired:
        steps.append((_PAIR["step"], False,
                      "Qua thoi gian cho - ban phim khong phan hoi hoac chua go ma"))
    except Exception as e:
        steps.append((_PAIR["step"], False, str(e)[:120]))
    finally:
        # Luon tat quet du ghep cap thanh cong hay khong - de quet chay ngam
        # se ton pin va lam nhieu song cho chinh ket noi vua tao.
        try:
            subprocess.run(["bluetoothctl", "scan", "off"],
                           capture_output=True, timeout=8)
        except Exception:
            pass

    _PAIR["ok"] = all(g for _, g, _ in steps) and len(steps) == 4
    _PAIR["detail"] = " | ".join(f"{a}: {m}" for a, _, m in steps)

    # Kiem tra lai bang SU THAT chu khong tin chu "success" cua bluetoothctl:
    # no bao thanh cong ca khi khoa lien ket khong duoc luu. Voi ban phim/chuot
    # ma thieu khoa nay thi BlueZ se tu choi gan ho so HID va thiet bi khong
    # go duoc gi - phai bao ro ngay tai day thay vi de nguoi dung ngoi doan.
    if _PAIR["ok"]:
        sau = bt_device_info(mac)
        if not sau.get("bonded", False):
            _PAIR["ok"] = False
            _PAIR["detail"] += (" | CANH BAO: ghep xong nhung khong luu duoc khoa "
                                "lien ket (Bonded: no). Ban phim se khong go duoc. "
                                "Hay xoa ghep cap tren CHINH BAN PHIM (thuong giu "
                                "nut Connect vai giay cho den khi den nhap nhay) "
                                "roi ghep lai.")
    _PAIR["step"] = "xong"
    _PAIR["running"] = False


def bt_pair_start(mac):
    """Bat dau ghep cap o luong nen, tra ve ngay de trang web khong treo."""
    if _PAIR["running"]:
        return False, "Dang ghep cap thiet bi khac, doi mot chut."
    _PAIR.update(running=True, mac=mac, step="pair", ok=None, detail="")
    threading.Thread(target=_pair_worker, args=(mac,), daemon=True).start()
    return True, ""


def bt_pair_state():
    return dict(_PAIR)


def bt_connect_profile(mac, want=""):
    """
    Ket noi theo DUNG ho so cua thiet bi.

    `bluetoothctl connect` chung chung de that bai voi thiet bi da ho so
    (vd laptop quang cao ca A2DP lan PAN): BlueZ chon dai va bao loi. Voi may
    tinh/dien thoai ta goi thang org.bluez.Network1.Connect(NAP) de lay mang;
    voi ban phim/chuot thi connect binh thuong la dung (ho so HID).

    Chi `trust` khi thiet bi DA BOND that su - khong phai luc nao cung trust.
    khong trust thi lan sau bat len thiet bi khong tu noi lai duoc (kich ban 3
    anh can), NHUNG trust mot thiet bi CHUA bond la co hai: ReconnectUUIDs
    (main.conf) khien BlueZ lien tuc thu ket noi nen tren voi bat ky thiet bi
    trusted nao quang bao HID/PAN - voi thiet bi chua bond, moi lan thu deu
    bi tu choi ("Rejected connection from !bonded device"), tao thanh vong
    lap spam nen VA con co the tranh chap tai nguyen HCI voi mot lan ghep cap
    moi dang co gang thuc hien cung luc. Da gap that: bam "Ket noi" tren
    thiet bi chua bond -> trust bi bat sai -> lan ghep cap lai sau do that
    bai kho hieu vi adapter dang ban doi pho voi cac lan tu-ket-noi nen.
    """
    if not re.fullmatch(r"[0-9A-Fa-f:]{17}", mac or ""):
        return False, "Dia chi MAC khong hop le."

    info = bt_device_info(mac)
    kind = want or info["cls"]["kind"]
    ten = info["name"]

    if not info.get("bonded", False):
        return False, (f"{ten} chua ghep cap that su (thieu khoa lien ket). "
                       "Bam 'Ghep cap lai' thay vi 'Ket noi'.")

    subprocess.run(["bluetoothctl", "trust", mac], capture_output=True, timeout=10)

    if kind == "net":
        try:
            import dbus
            bus = dbus.SystemBus()
            path = "/org/bluez/hci0/dev_" + mac.upper().replace(":", "_")
            net = dbus.Interface(bus.get_object("org.bluez", path), "org.bluez.Network1")
            iface = str(net.Connect("nap"))
            return True, (f"Da ket noi mang Bluetooth voi {ten} qua giao dien "
                          f"{iface}. May do se cap IP cho Pi.")
        except Exception as e:
            detail = str(e).split(":")[-1].strip()[:110]
            return False, (f"Khong noi duoc mang (PAN) voi {ten}: {detail}. "
                           "Tren may do phai bat chia se ket noi qua Bluetooth "
                           "(Windows: Personal Area Network; Mac: Internet Sharing).")

    r = subprocess.run(["bluetoothctl", "connect", mac],
                       capture_output=True, text=True, timeout=25)
    out = (r.stdout + r.stderr).strip().splitlines()
    last = out[-1] if out else ""
    good = "success" in last.lower() or "Connected: yes" in r.stdout
    if good:
        loai = info["cls"]["label"].lower()
        return True, f"Da ket noi {ten} ({loai})."
    return False, f"Khong ket noi duoc {ten}: {last[:120]}"


def bt_unpair(mac):
    try:
        subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, timeout=12)
        r = subprocess.run(["bluetoothctl", "remove", mac],
                           capture_output=True, text=True, timeout=12)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[:120]
    except Exception as e:
        return False, str(e)[:120]



# ---------------------------------------------------------------------------
# Phan loai thiet bi Bluetooth
#
# Truoc day chi dua vao truong `Icon` cua BlueZ voi bang 6 muc, nen laptop,
# iPad, may Mac, dien thoai deu roi vao "khac" va nut "Ket noi" thi goi
# `bluetoothctl connect` chung chung - khong biet nen noi ho so mang (PAN)
# hay ho so ban phim (HID). Do la ly do ghep cap ban phim hay treo.
#
# Class of Device la mot so 24 bit theo chuan Bluetooth:
#   bit 2-7   : minor class (y nghia phu thuoc major)
#   bit 8-12  : major class  <- xac dinh LOAI thiet bi
#   bit 13-23 : service class (co dich vu mang / audio / ... khong)
# ---------------------------------------------------------------------------

MAJOR_CLASSES = {
    0: ("Khong ro", "🔗"),
    1: ("May tinh", "💻"),
    2: ("Dien thoai", "📱"),
    3: ("Thiet bi mang", "🌐"),
    4: ("Am thanh", "🎧"),
    5: ("Ban phim / Chuot", "⌨️"),
    6: ("May anh / May in", "🖨️"),
    7: ("Thiet bi deo", "⌚"),
    8: ("Do choi", "🧸"),
    9: ("Y te", "🩺"),
}

# Minor class khi major = 1 (May tinh) va = 5 (Peripheral)
MINOR_COMPUTER = {1: "May ban", 2: "May chu", 3: "Laptop",
                  4: "Handheld", 5: "Palm", 6: "Wearable"}
MINOR_PHONE = {1: "Dien thoai di dong", 2: "Dien thoai ban",
               3: "Smart phone", 4: "Modem", 5: "ISDN"}

UUID_HID = "00001124-0000-1000-8000-00805f9b34fb"   # Human Interface Device
UUID_NAP = "00001116-0000-1000-8000-00805f9b34fb"   # Network Access Point
UUID_PANU = "00001115-0000-1000-8000-00805f9b34fb"  # PAN User
UUID_A2DP = "0000110b-0000-1000-8000-00805f9b34fb"  # Audio Sink


def classify_bt(cod, uuids=None, icon=""):
    """
    Tra ve {"major", "label", "icon", "kind"} - `kind` la thu ma UI dung de
    quyet dinh hien nut nao: "hid" (ban phim/chuot), "net" (may tinh, dien
    thoai - noi mang qua PAN), "audio", hoac "other".

    Uu tien UUID that su thiet bi quang cao, roi moi den Class of Device,
    cuoi cung moi den Icon cua BlueZ (kem chinh xac nhat).
    """
    uuids = [str(u).lower() for u in (uuids or [])]
    try:
        cod = int(cod or 0)
    except (TypeError, ValueError):
        cod = 0

    major = (cod >> 8) & 0x1F
    minor = (cod >> 2) & 0x3F
    label, emoji = MAJOR_CLASSES.get(major, ("Khong ro", "🔗"))

    if major == 1 and minor in MINOR_COMPUTER:
        label = MINOR_COMPUTER[minor]
    elif major == 2 and minor in MINOR_PHONE:
        label = MINOR_PHONE[minor]
    elif major == 5:
        # bit 6-7 cua minor: 01 = ban phim, 10 = chuot, 11 = ca hai
        kb = minor & 0x10
        ms = minor & 0x20
        if kb and ms:
            label, emoji = "Ban phim + Chuot", "⌨️"
        elif ms:
            label, emoji = "Chuot", "🖱️"
        elif kb:
            label, emoji = "Ban phim", "⌨️"

    # UUID la bang chung manh nhat ve viec thiet bi LAM DUOC gi
    if UUID_HID in uuids:
        kind = "hid"
        if major not in (5,):
            label, emoji = (label or "Thiet bi nhap lieu"), "⌨️"
    elif UUID_NAP in uuids or UUID_PANU in uuids:
        kind = "net"
    elif UUID_A2DP in uuids:
        kind = "audio"
    elif major == 5:
        kind = "hid"
    elif major in (1, 2, 3):
        kind = "net"
    elif major == 4:
        kind = "audio"
    else:
        kind = "other"

    # Khong doc duoc CoD (thiet bi BLE chi quang cao) -> dua vao Icon
    if cod == 0 and icon:
        fallback = {"input-keyboard": ("Ban phim", "⌨️", "hid"),
                    "input-mouse": ("Chuot", "🖱️", "hid"),
                    "computer": ("May tinh", "💻", "net"),
                    "phone": ("Dien thoai", "📱", "net"),
                    "audio-card": ("Loa", "🔊", "audio"),
                    "audio-headset": ("Tai nghe", "🎧", "audio")}
        if icon in fallback:
            label, emoji, kind = fallback[icon]

    return {"major": major, "label": label, "icon": emoji, "kind": kind}


# Giu lai cho code cu chua chuyen sang classify_bt()
ICON_MAP = {"input-keyboard": "⌨️", "input-mouse": "🖱️", "computer": "💻",
            "phone": "📱", "audio-card": "🔊", "audio-headset": "🎧"}



def wifi_disconnect():
    """
    Ngat WiFi mot cach AN TOAN de con noi lai duoc.

    KHONG dung `ip addr flush` tran lan: tren may nay wlan0 do systemd-networkd
    quan ly, xoa dia chi bang tay lam lech trang thai lease. Cach dung la ha
    wpa_supplicant (ca dang unit lan dang -B do wifi-fallback.sh chay), roi bao
    networkd cau hinh lai - mat carrier thi networkd tu bo dia chi.
    """
    subprocess.run(["systemctl", "stop", "wpa_supplicant@wlan0"],
                   capture_output=True, timeout=15)
    subprocess.run(["pkill", "-f", "wpa_supplicant -B -i wlan0"],
                   capture_output=True, timeout=10)
    time.sleep(1)
    subprocess.run(["networkctl", "reconfigure", "wlan0"],
                   capture_output=True, timeout=15)
    return True, ("Da ngat WiFi. Pi se tu danh gia lai trong vong 2 phut: "
                  "thay mang quen thi noi lai, khong thay thi bat AP ConsolePi.")


def client_via_wlan():
    """
    Nguoi dung co dang truy cap QUA chinh WiFi nay khong?
    Neu co, bam ngat WiFi se lam ho mat ket noi - phai canh bao truoc.
    """
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
        ip = ip.split(",")[0].strip()
        _, _, wlan_ip = get_net_status()
        if not ip or not wlan_ip:
            return False
        # Cung 3 octet dau = cung dai mang wlan0
        return ip.rsplit(".", 1)[0] == wlan_ip.rsplit(".", 1)[0]
    except Exception:
        return False


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
            <button type="submit" class="gray small" data-busy="Dang quet WiFi...">🔄 Quet lai</button>
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
            <div class="row" style="margin-top:13px;"><button type="submit" data-busy="Dang ket noi, cho 20-30 giay...">Ket noi</button></div>
          </form>
          <p style="color:#8b93a1;font-size:13px;margin-top:11px;">
            Neu dang xem qua WiFi, ket noi se dut khi Pi chuyen mang. Sau 20-30 giay
            hay noi may vao mang moi roi vao lai <code>http://server-console.local</code>.
          </p>
        </div>"""

    # Nut ngat chi hien khi dang thuc su ket noi WiFi (khong phai che do AP)
    disconnect_html = ""
    if mode == "Client" and ssid:
        warn = ""
        if client_via_wlan():
            warn = ('<div class="msg warn" style="margin:11px 0 0;">⚠️ Ban dang truy cap '
                    'QUA chinh WiFi nay. Ngat se lam mat ket noi cua ban - hay cam day LAN '
                    'hoac noi vao AP ConsolePi truoc.</div>')
        disconnect_html = f"""
        <form method="POST" action="/wifi-disconnect" style="margin-top:12px;"
              onsubmit="return confirm('Ngat ket noi WiFi {_esc(ssid)}?');">
          <button type="submit" class="red" data-busy="Dang ngat...">
            ⏏ Ngat ket noi WiFi
          </button>
          <span style="color:#8b93a1;font-size:13px;margin-left:9px;">
            Khong xoa WiFi da luu. Pi tu danh gia lai sau toi da 2 phut.
          </span>
        </form>{warn}"""

    body = f"""
    {msg_html}{last_html}
    <div class="card">
      <h3>Trang thai hien tai</h3>
      <table style="max-width:470px;">
        <tr><th style="width:150px;">Che do</th><td>{mode}</td></tr>
        <tr><th>Mang</th><td>{_esc(ssid) or '-'}</td></tr>
        <tr><th>Dia chi IP</th><td><code>{ip or '-'}</code></td></tr>
      </table>
      {disconnect_html}
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
        c = i["cls"]

        # Trang thai phai noi DUNG SU THAT. Truong hop nguy hiem nhat la
        # Connected=yes nhung Bonded=no: BlueZ tu choi gan ho so HID nen ban
        # phim khong go duoc gi, ma giao dien cu van hien "dang ket noi" mau
        # xanh -> nguoi dung ngoi cho mai khong hieu tai sao. Da gap that.
        hong_bond = i["connected"] and not i.get("bonded", False)
        if hong_bond:
            state = ('<span style="color:#ff6b6b;">🔴 Noi duoc nhung KHONG dung duoc'
                     '<br><small>Thieu khoa lien ket (Bonded: no) - phai ghep cap lai</small></span>')
        elif i["connected"]:
            state = "🟢 dang ket noi"
        elif i["paired"]:
            state = "⚪ da ghep, chua noi"
        else:
            state = "—"

        # Nut phai khop voi LOAI thiet bi. Ban phim/chuot dung ho so HID;
        # may tinh, dien thoai, iPad dung ho so mang PAN - goi nham thi
        # BlueZ bao loi kho hieu hoac treo.
        if c["kind"] == "net":
            btn = ('<button type="submit" class="small" data-busy="Dang noi mang...">'
                   '🌐 Ket noi mang (PAN)</button>')
            prof = "net"
        elif c["kind"] == "hid":
            btn = ('<button type="submit" class="small" data-busy="Dang noi...">'
                   '⌨️ Ket noi ban phim/chuot</button>')
            prof = "hid"

        # Ban ghi ghep cap hong thi bam "Ket noi" bao nhieu lan cung vo ich -
        # BlueZ se tu choi lai dung cho do. Cach duy nhat la xoa ban ghi roi
        # ghep lai tu dau, nen dua thang nut do ra.
        if hong_bond:
            btn = ('<button type="submit" class="small" '
                   'formaction="/bt-ghep-lai" data-busy="Dang xoa va ghep lai...">'
                   '🔁 Ghep cap lai</button>')
            prof = ""
        else:
            btn = ('<button type="submit" class="small" data-busy="Dang noi...">'
                   'Ket noi lai</button>')
            prof = ""

        rows += f"""
        <tr>
          <td>{c['icon']} <strong>{_esc(i['name'])}</strong><br>
              <code style="font-size:12px;">{_esc(mac)}</code></td>
          <td>{_esc(c['label'])}</td>
          <td>{state}</td>
          <td>
            <form method="POST" action="/bt-connect" style="display:inline;">
              <input type="hidden" name="mac" value="{_esc(mac)}">
              <input type="hidden" name="profile" value="{prof}">
              {btn}
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
            c = i["cls"]
            new_rows += f"""
            <tr>
              <td>{c['icon']} <strong>{_esc(name)}</strong><br>
                  <code style="font-size:12px;">{_esc(mac)}</code></td>
              <td>{_esc(c['label'])}</td>
              <td>
                <form method="POST" action="/bt-pair" style="display:inline;">
                  <input type="hidden" name="mac" value="{_esc(mac)}">
                  <button type="submit" class="blue small" data-busy="Dang ghep...">Ghep cap</button>
                </form>
              </td>
            </tr>"""
        scan_html = f"""
        <h2>Thiet bi tim thay ({len([1 for m,_ in scanned if m not in paired_macs])} chua ghep)</h2>
        <table><tr><th>Thiet bi</th><th style="width:150px;">Loai</th>
                   <th style="width:120px;">Thao tac</th></tr>{new_rows}</table>
        {'<p style="color:#8b93a1;">Khong thay thiet bi moi nao. Nho bat che do ghep cap tren ban phim (thuong giu nut Connect vai giay den khi den nhap nhay).</p>' if not new_rows else ''}"""

    # --- Khoi hien ma so / trang thai ghep cap ---
    ag = bt_agent_state()
    ps = bt_pair_state()
    pair_html = ""

    # "passkey" (ghep cap doi moi) va "pin" (ghep cap kieu cu, Bluetooth 2.x)
    # deu la CUNG MOT VIEC doi voi nguoi dung: go day so nay tren ban phim roi
    # bam Enter. Truoc day chi hien "passkey", con "pin" bi bo qua hoan toan ->
    # ban phim cu doi go ma ma tren man hinh khong hien gi ca, nguoi dung chi
    # thay "dang ghep cap" roi treo den het gio.
    if ag and ag.get("kind") in ("passkey", "pin") and ag.get("go_tren_ban_phim", True):
        kieu_cu = ag.get("kind") == "pin"
        pair_html = f"""
        <div class="card" style="border-left:4px solid #ffd166;background:#2a2519;">
          <h3 style="color:#ffd166;">⌨️ Go ma nay TREN BAN PHIM Bluetooth</h3>
          <div style="font-size:44px;font-weight:700;letter-spacing:9px;
                      font-family:ui-monospace,monospace;color:#fff;
                      text-align:center;padding:14px 0;">{_esc(ag.get('value'))}</div>
          <p style="text-align:center;color:#c9ced6;margin:0;">
            Go day so tren roi bam <strong>Enter</strong> ngay tren ban phim
            <strong>{_esc(ag.get('device'))}</strong>.
          </p>
          <p style="text-align:center;color:#8b93a1;font-size:13px;margin-top:9px;">
            {'Ban phim doi cu (ghep cap kieu PIN) - van go y het nhu tren.'
             if kieu_cu else f"Da go {ag.get('entered', 0)} ky tu"}
            &middot; trang tu lam moi moi 3 giay
          </p>
          <p style="text-align:center;color:#8b93a1;font-size:12px;margin-top:6px;">
            Ban phim chua ket noi van go duoc ma nay - do la cach ghep cap chuan
            (Windows/macOS cung lam y het).
          </p>
        </div>
        <meta http-equiv="refresh" content="3">"""
    elif ag and ag.get("kind") == "pin":
        # Thiet bi khong go duoc (tai nghe/loa cu): chi thong bao, khong bat
        # nguoi dung go gi ca.
        pair_html = f"""
        <div class="card" style="border-left:4px solid #6cb6ff;">
          <h3>Dang dung ma PIN <code style="font-size:20px;">{_esc(ag.get('value'))}</code></h3>
          <p style="color:#8b93a1;margin:0;">Thiet bi <strong>{_esc(ag.get('device'))}</strong>
          khong phai ban phim nen khong go duoc ma. Pi dung ma mac dinh cua nha san xuat.
          Neu that bai, tra cuu ma PIN in tren thiet bi (hay gap: 0000, 1234, 8888).</p>
        </div>
        <meta http-equiv="refresh" content="3">"""
    elif ag and ag.get("kind") == "need-passkey":
        pair_html = f"""
        <div class="msg err">
          <strong>Thiet bi nay doi Pi nhap ma do chinh no hien ra.</strong><br>
          <span style="font-size:13px;">
          <strong>{_esc(ag.get('device'))}</strong> dang cho mot ma so ma no hien tren man
          hinh cua no - Pi khong doc duoc ma do nen buoc nay se that bai. Ban phim/chuot
          thong thuong KHONG dung kieu nay; neu gap, nhieu kha nang thiet bi dang o sai
          che do ghep cap. Tat roi bat lai che do ghep cap tren thiet bi va thu lai.
          </span>
        </div>
        <meta http-equiv="refresh" content="3">"""
    elif ag and ag.get("kind") == "cancelled":
        pair_html = """
        <div class="msg err">Thiet bi da HUY ghep cap giua chung. Thuong do het thoi gian
        cho tren thiet bi, hoac ma go vao bi sai. Bat lai che do ghep cap tren thiet bi
        roi bam Ghep cap lai.</div>"""
    elif ag and ag.get("kind") == "confirm":
        pair_html = f"""
        <div class="card" style="border-left:4px solid #6cb6ff;">
          <h3>Ma xac nhan: <code style="font-size:22px;">{_esc(ag.get('value'))}</code></h3>
          <p style="color:#8b93a1;margin:0;">Doi chieu voi ma hien tren
          <strong>{_esc(ag.get('device'))}</strong> roi bam dong y ben do.</p>
        </div>
        <meta http-equiv="refresh" content="3">"""
    elif ps.get("running"):
        pair_html = f"""
        <div class="card" style="border-left:4px solid #6cb6ff;">
          <h3>⏳ Dang ghep cap {_esc(ps.get('mac'))}</h3>
          <p style="color:#8b93a1;margin:0;">Buoc hien tai: <code>{_esc(ps.get('step'))}</code>.
          Neu la ban phim, hay <strong>bat che do ghep cap tren ban phim</strong>
          (thuong giu nut Connect den khi den nhap nhay) va cho ma so hien ra.</p>
        </div>
        <meta http-equiv="refresh" content="3">"""
    elif ps.get("ok") is False and ps.get("detail"):
        pair_html = f"""
        <div class="msg err">Ghep cap that bai.<br>
        <span style="font-size:13px;">{_esc(ps.get('detail'))}</span></div>"""
    elif ps.get("ok") is True:
        pair_html = '<div class="msg ok">Da ghep cap va ket noi thanh cong.</div>'

    body = f"""
    {msg_html}
    {pair_html}

    <h2>Ghep ban phim / chuot Bluetooth</h2>
    <div class="card">
      <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
        Dung khi man hinh cam ung khong tien go chu.
      </p>
      <ol style="color:#8b93a1;font-size:13px;margin:0 0 12px;padding-left:19px;line-height:1.75;">
        <li>Bat che do ghep cap tren ban phim (thuong giu nut Connect den khi den nhap nhay)</li>
        <li>Bam <strong>Quet thiet bi</strong> ben duoi</li>
        <li>Bam <strong>Ghep cap</strong> o dong ban phim</li>
        <li>Man hinh se hien <strong>6 chu so</strong> - go day so do <strong>tren chinh ban phim
            Bluetooth</strong> roi bam Enter</li>
      </ol>
      <form method="POST" action="/bt-scan">
        <button type="submit" data-busy="Dang quet 10 giay...">🔍 Quet thiet bi</button>
      </form>
    </div>
    {scan_html}

    <h2>Thiet bi da ghep cap ({len(devs)})</h2>
    <table><tr><th>Thiet bi</th><th style="width:150px;">Loai</th>
               <th style="width:160px;">Trang thai</th>
               <th style="width:230px;">Thao tac</th></tr>{rows}</table>
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
          <button type="submit" class="gray" data-busy="Dang khoi dong lai...">🔄 Reset Bluetooth</button>
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

    @app.route("/wifi-disconnect", methods=["POST"])
    def wifi_disconnect_route():
        ok_d, msg = wifi_disconnect()
        return _wifi_page(msg=msg, ok=ok_d)

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
        started, err = bt_pair_start(mac)
        if not started:
            return _bt_page(msg=err, ok=False)
        time.sleep(2)      # cho agent kip sinh ma so de hien ngay
        return _bt_page(msg="Dang ghep cap - lam theo huong dan ben duoi.", ok=True)

    @app.route("/bt-ghep-lai", methods=["POST"])
    def bt_repair_route():
        """
        Xoa sach ban ghi ghep cap roi ghep lai tu dau.

        Dung cho truong hop thiet bi bao Connected nhung Bonded=no: luc do bam
        "Ket noi" bao nhieu lan cung bi BlueZ tu choi ("Rejected connection from
        !bonded device"), chi co xoa han roi ghep lai moi khoi.
        """
        mac = request.form.get("mac", "")
        started, err = bt_pair_start(mac)      # ham nay da tu xoa ban ghi cu
        if not started:
            return _bt_page(msg=err, ok=False)
        time.sleep(2)
        return _bt_page(
            msg=("Da xoa ban ghi cu va dang ghep cap lai. Neu la ban phim, hay "
                 "bat che do ghep cap tren ban phim (thuong giu nut Connect vai "
                 "giay den khi den nhap nhay) roi go ma so hien ben duoi."),
            ok=True)

    @app.route("/bt-connect", methods=["POST"])
    def bt_connect_route():
        mac = request.form.get("mac", "")
        want = request.form.get("profile", "")   # "net" | "hid" | "" (tu doan)
        ok_c, msg = bt_connect_profile(mac, want)
        return _bt_page(msg=msg, ok=ok_c)

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

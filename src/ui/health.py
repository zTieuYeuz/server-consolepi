"""
Console Pi - Suc khoe he thong va nut nguon.

Thay cho "% pin": may nay KHONG co pin nao Pi doc duoc (da do: i2cdetect bao
0x36 nhung doc 6 lan ra 6 gia tri ngau nhien -> nhieu bus, khong phai chip;
khong co HAT EEPROM, khong co UPS tren USB). Pin trong man hinh di dong khong
co duong du lieu toi Pi.

Nen thay vao do hien nhung thu DOC DUOC va quan trong hon voi Pi:
  - Sut ap / qua nhiet (vcgencmd get_throttled) - nguyen nhan pho bien nhat
    lam Pi treo hoac hong the nho, va no bao TRUOC khi hong
  - Nhiet do CPU, tai he thong, RAM, dung luong dia, thoi gian chay

Neu sau nay gan UPS HAT that, chi can bo sung ham doc chip vao BATTERY_READERS.
"""
import os
import re
import subprocess
import time

_CACHE = {"t": 0.0, "data": None}
CACHE_TTL = 3.0

# Tung bit trong vcgencmd get_throttled. Bit 0-3 = dang xay ra NGAY BAY GIO,
# bit 16-19 = da tung xay ra ke tu luc boot.
THROTTLE_BITS = [
    (0,  "Dien ap thap", "now"),
    (1,  "Bi gioi han xung nhip do nhiet", "now"),
    (2,  "Dang bi throttle", "now"),
    (3,  "Cham nguong nhiet do", "now"),
    (16, "Da tung sut ap", "past"),
    (17, "Da tung gioi han xung nhip", "past"),
    (18, "Da tung bi throttle", "past"),
    (19, "Da tung cham nguong nhiet", "past"),
]


def _run(cmd, timeout=4):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def cpu_temp():
    """Doc tu sysfs truoc (nhanh hon nhieu so voi goi vcgencmd)."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        m = re.search(r"([\d.]+)", _run(["vcgencmd", "measure_temp"]))
        return float(m.group(1)) if m else None


def throttle_status():
    """
    Tra ve (ma_hex, [canh bao dang xay ra], [canh bao da tung xay ra]).
    Khong co vcgencmd (may khong phai Pi) thi tra ve None.
    """
    out = _run(["vcgencmd", "get_throttled"])
    m = re.search(r"throttled=0x([0-9a-fA-F]+)", out)
    if not m:
        return None
    val = int(m.group(1), 16)
    now, past = [], []
    for bit, label, when in THROTTLE_BITS:
        if val & (1 << bit):
            (now if when == "now" else past).append(label)
    return {"hex": f"0x{val:x}", "now": now, "past": past}


def core_voltage():
    m = re.search(r"([\d.]+)V", _run(["vcgencmd", "measure_volts"]))
    return float(m.group(1)) if m else None


def uptime_text():
    try:
        with open("/proc/uptime") as f:
            secs = int(float(f.read().split()[0]))
    except Exception:
        return "?"
    d, r = divmod(secs, 86400)
    h, r = divmod(r, 3600)
    mi = r // 60
    if d:
        return f"{d} ngay {h} gio {mi} phut"
    if h:
        return f"{h} gio {mi} phut"
    return f"{mi} phut"


def load_avg():
    try:
        with open("/proc/loadavg") as f:
            p = f.read().split()
        return f"{p[0]} / {p[1]} / {p[2]}"
    except Exception:
        return "?"


def mem_info():
    """Tra ve (da_dung_MB, tong_MB, phan_tram). Dung 'available' cho dung thuc te."""
    try:
        vals = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, v = line.partition(":")
                vals[k] = int(v.split()[0])
        total = vals["MemTotal"] // 1024
        avail = vals.get("MemAvailable", vals["MemFree"]) // 1024
        used = total - avail
        return used, total, round(used * 100 / total)
    except Exception:
        return 0, 0, 0


def disk_info(path="/"):
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize // (1024 ** 3)
        free = st.f_bavail * st.f_frsize // (1024 ** 3)
        used = total - free
        return used, total, (round(used * 100 / total) if total else 0)
    except Exception:
        return 0, 0, 0


# ---------------------------------------------------------------------------
# DOC PIN
#
# May nay hien khong co pin nao doc duoc - da kiem chung: 0 thiet bi trong
# /sys/class/power_supply, UPower bao "battery-missing", lsusb khong co UPS.
# Pin trong man hinh di dong khong co duong du lieu toi Pi (chi HDMI + nguon).
#
# Nen thay vi bia so, code duoi day CHI hien khi co du lieu THAT, va chia
# lam hai muc do an toan:
#
#   Muc 1 - khong rui ro, luon bat: doc tu kernel (/sys/class/power_supply)
#           va UPower. Moi UPS co driver deu hien o day: UPS USB theo chuan
#           HID Power Device, PoE HAT, cac UPS HAT co driver kernel.
#
#   Muc 2 - phai tu bat trong Cai dat: do thang chip do pin qua I2C.
#           KHONG bat san vi do dia chi I2C mu la khong an toan: chinh may
#           nay tung cho ket qua GIA o dia chi 0x36 (doc 6 lan ra 6 gia tri
#           ngau nhien - nhieu bus chu khong phai chip). Neu tin ngay lan doc
#           dau thi dashboard se hien mot con so pin hoan toan bia dat, con
#           te hon la khong hien gi.
# ---------------------------------------------------------------------------

CONFIG_FILE = "/opt/console-pi/config.json"


def _cau_hinh(khoa, mac_dinh=None):
    try:
        import json
        with open(CONFIG_FILE) as f:
            return json.load(f).get(khoa, mac_dinh)
    except Exception:
        return mac_dinh


def pin_tu_kernel():
    """
    Doc /sys/class/power_supply - nguon dang tin cay nhat. Bo qua cac muc
    khong phai pin (bo sac, nguon dien luoi) va cac muc khong bao dung luong.
    """
    base = "/sys/class/power_supply"
    if not os.path.isdir(base):
        return None
    for ten in sorted(os.listdir(base)):
        d = os.path.join(base, ten)

        def doc(f):
            try:
                with open(os.path.join(d, f)) as fh:
                    return fh.read().strip()
            except OSError:
                return ""

        loai = doc("type")
        if loai not in ("Battery", "Ups"):
            continue
        cap = doc("capacity")
        if not cap.isdigit():
            continue
        pct = int(cap)
        if not 0 <= pct <= 100:
            continue
        trang_thai = doc("status") or "Unknown"
        viet = {"Charging": "dang sac", "Discharging": "dang xa",
                "Full": "day", "Not charging": "khong sac",
                "Unknown": "khong ro"}.get(trang_thai, trang_thai)
        v = doc("voltage_now")
        them = f", {int(v)/1_000_000:.2f}V" if v.isdigit() else ""
        return f"{pct}% ({viet}{them}) — {ten}"
    return None


def pin_tu_upower():
    """Du phong: UPower gom nhieu nguon lai, ke ca UPS qua NUT."""
    try:
        r = subprocess.run(
            ["upower", "-i", "/org/freedesktop/UPower/devices/DisplayDevice"],
            capture_output=True, text=True, timeout=6)
    except Exception:
        return None
    out = r.stdout
    if "battery-missing" in out or "power supply:         no" in out:
        return None
    m = re.search(r"percentage:\s+([\d.]+)%", out)
    if not m:
        return None
    pct = float(m.group(1))
    if pct <= 0:
        return None
    tt = re.search(r"state:\s+(\S+)", out)
    return f"{pct:.0f}%" + (f" ({tt.group(1)})" if tt else "")


# Chip do pin hay gap tren UPS HAT cho Pi.
# 'khoang_v' la khoang dien ap HOP LE cua pin Li-ion 1 cell - dung de loai bo
# ket qua rac: nhieu bus se cho ra gia tri ngoai khoang nay.
CHIP_I2C = {
    "max17040": {"dia_chi": 0x36, "mo_ta": "MAX17040/17048 (PiSugar, mot so UPS HAT)"},
    "ina219":   {"dia_chi": 0x40, "mo_ta": "INA219 (Waveshare UPS HAT B/C, Geekworm)"},
    "ina219b":  {"dia_chi": 0x41, "mo_ta": "INA219 dia chi phu"},
    "ina219c":  {"dia_chi": 0x42, "mo_ta": "INA219 dia chi phu"},
    "ina219d":  {"dia_chi": 0x43, "mo_ta": "INA219 dia chi phu"},
}
V_MIN, V_MAX = 2.5, 4.6          # Li-ion 1 cell
DOC_LAP_LAI = 4                  # so lan doc de kiem tra on dinh
LECH_TOI_DA = 0.15               # V - lech hon the nay coi la nhieu


def _doc_max17040(bus, dia_chi):
    """VCELL o thanh ghi 0x02, SOC o 0x04 (big-endian, 2 byte)."""
    raw_v = bus.read_i2c_block_data(dia_chi, 0x02, 2)
    volt = ((raw_v[0] << 4) | (raw_v[1] >> 4)) * 1.25 / 1000.0
    raw_s = bus.read_i2c_block_data(dia_chi, 0x04, 2)
    pct = raw_s[0] + raw_s[1] / 256.0
    return volt, pct


def _doc_ina219(bus, dia_chi):
    """Thanh ghi bus voltage 0x02: 13 bit cao, moi don vi 4mV."""
    raw = bus.read_i2c_block_data(dia_chi, 0x02, 2)
    volt = (((raw[0] << 8) | raw[1]) >> 3) * 0.004
    # INA219 khong tinh % - suy ra tu duong xa Li-ion (3.0V rong, 4.2V day)
    pct = max(0.0, min(100.0, (volt - 3.0) / 1.2 * 100.0))
    return volt, pct


def pin_tu_i2c():
    """
    Chi chay khi nguoi dung tu bat trong Cai dat. Doc nhieu lan va CHI tin
    khi ket qua ON DINH - day chinh la cho phan biet chip that voi nhieu bus.
    """
    if not _cau_hinh("doc_pin_i2c", False):
        return None
    try:
        import smbus2
    except ImportError:
        return None

    for so_bus in (1, 0):
        duong = f"/dev/i2c-{so_bus}"
        if not os.path.exists(duong):
            continue
        try:
            bus = smbus2.SMBus(so_bus)
        except OSError:
            continue
        try:
            for ten, chip in CHIP_I2C.items():
                doc = _doc_max17040 if ten.startswith("max") else _doc_ina219
                lan_doc = []
                try:
                    for _ in range(DOC_LAP_LAI):
                        lan_doc.append(doc(bus, chip["dia_chi"]))
                        time.sleep(0.05)
                except OSError:
                    continue          # dia chi nay khong co gi tra loi

                dien_ap = [v for v, _ in lan_doc]
                # Ba dieu kien PHAI cung dung thi moi tin:
                #   1. moi lan doc deu nam trong khoang dien ap pin that
                #   2. cac lan doc gan nhau (khong nhay lung tung = nhieu)
                #   3. phan tram hop le
                if not all(V_MIN <= v <= V_MAX for v in dien_ap):
                    continue
                if max(dien_ap) - min(dien_ap) > LECH_TOI_DA:
                    continue
                pct = sum(p for _, p in lan_doc) / len(lan_doc)
                if not 0 <= pct <= 100:
                    continue
                volt = sum(dien_ap) / len(dien_ap)
                return f"{pct:.0f}% ({volt:.2f}V) — {chip['mo_ta']}, i2c-{so_bus}"
        finally:
            try:
                bus.close()
            except Exception:
                pass
    return None


# Thu lan luot tu nguon dang tin nhat xuong. Them phan cung UPS moi chi can
# cam vao - neu no co driver kernel thi muc 1 tu thay ngay, khong sua code.
BATTERY_READERS = {
    "kernel": pin_tu_kernel,
    "upower": pin_tu_upower,
    "i2c": pin_tu_i2c,
}


def battery():
    for ten, doc in BATTERY_READERS.items():
        try:
            v = doc()
            if v:
                return v
        except Exception:
            continue
    return None


def snapshot():
    """Toan bo chi so, co bo nho dem ngan de bam F5 lien tuc khong ton CPU."""
    now = time.time()
    if _CACHE["data"] and now - _CACHE["t"] < CACHE_TTL:
        return _CACHE["data"]

    mem_used, mem_total, mem_pct = mem_info()
    disk_used, disk_total, disk_pct = disk_info()
    data = {
        "temp": cpu_temp(),
        "throttle": throttle_status(),
        "volts": core_voltage(),
        "uptime": uptime_text(),
        "load": load_avg(),
        "mem": (mem_used, mem_total, mem_pct),
        "disk": (disk_used, disk_total, disk_pct),
        "battery": battery(),
    }
    _CACHE.update(t=now, data=data)
    return data


def power_action(what):
    """
    Tat may / khoi dong lai. Dung `systemctl --no-block` de HTTP tra loi xong
    truoc khi may thuc su tat - neu khong trinh duyet chi thay 'mat ket noi'
    va nguoi dung khong biet lenh co an khong.
    """
    if what not in ("poweroff", "reboot"):
        return False, "Lenh khong hop le."
    subprocess.Popen(["systemctl", "--no-block", what])
    if what == "poweroff":
        return True, ("Dang tat may. Doi den khi den xanh tren Pi ngung nhap nhay "
                      "roi hay rut dien - rut som co the hong the nho.")
    return True, "Dang khoi dong lai. Trang se song lai sau khoang 40-60 giay."

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


# Cho tuong lai: khi gan UPS HAT that, them ham doc o day va no se tu hien.
# Vi du {"x1200": doc_x1200, "pisugar": doc_pisugar}
BATTERY_READERS = {}


def battery():
    for name, reader in BATTERY_READERS.items():
        try:
            v = reader()
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

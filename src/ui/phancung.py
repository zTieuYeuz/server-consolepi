"""
Console Pi - Nhan biet phan cung: cong mang nao, may gi, nhiet do o dau.

VI SAO CO FILE NAY (yeu cau 19/09/2026: dong Console Pi thanh ban cai chay
duoc tren laptop/may ban):

Toan bo du an dang goi THANG ten "eth0" va "wlan0" - 183 cho trong 34 file.
Dieu do dung tren Raspberry Pi, nhung SAI tren gan nhu moi may khac: Linux
hien dai dat ten cong theo vi tri phan cung, nen tren may ban/laptop no la
"enp3s0", "wlp2s0", tren may ao VMware la "ens192"... Moi may mot khac,
khong the doan.

Kiem chung that: chinh may ao dung de build ban cai co cong ten "ens192".
Neu be nguyen code sang, tab WiFi/AP, Cam thang thiet bi va toan bo
Deployment OS deu hong ngay - khong phai vi logic sai ma vi goi ten mot
cai cong khong ton tai.

CACH LAM: moi noi hoi "cong day cua may nay ten gi" thay vi tu cho la
"eth0". Ham o day tra loi cau hoi do, theo thu tu:

    1. Nguoi dung da chon tay trong Cai dat  -> dung dung cai do
    2. Cong dang CO DAY CAM (carrier=1)      -> dung cai do
    3. Cong that dau tien tim thay           -> dung tam
    4. Khong co gi                           -> tra ve "" (KHONG bia ra
                                                "eth0" de roi loi kho hieu)

Loi ich ngay ca khi khong lam ban cai x86: con Pi co the cam them USB-LAN
(thanh eth1) - truoc day tuyet doi khong dung duoc cong do.
"""

import json
import os

from .duongdan import THU_MUC_DU_LIEU

FILE_CHON_CONG = os.path.join(THU_MUC_DU_LIEU, "cong-mang.json")

DUONG_NET = "/sys/class/net"


def _doc_chon_tay():
    """Cong nguoi dung tu chon trong Cai dat (neu co)."""
    try:
        with open(FILE_CHON_CONG, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def luu_chon_tay(day="", wifi=""):
    """Luu lua chon cua nguoi dung. Chuoi rong = tu dong tim lai."""
    d = _doc_chon_tay()
    if day is not None:
        d["day"] = (day or "").strip()
    if wifi is not None:
        d["wifi"] = (wifi or "").strip()
    try:
        os.makedirs(THU_MUC_DU_LIEU, mode=0o755, exist_ok=True)
        tam = FILE_CHON_CONG + ".tmp"
        with open(tam, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tam, FILE_CHON_CONG)
        return True, "Đã lưu lựa chọn cổng mạng."
    except OSError as e:
        return False, f"Không lưu được: {e}"


def _co_that(ten):
    """
    Cong THAT (co phan cung), khong phai cong ao.

    Bo qua lo, docker0, veth*, bridge ao, tailscale0, pan0... - chung deu
    khong co thu muc 'device' tro toi phan cung that. Neu khong loc, ham
    tu dong chon cong rat de vo phai tailscale0 hoac pan0 cua chinh du an
    nay va lam hong het.
    """
    return os.path.exists(os.path.join(DUONG_NET, ten, "device"))


def _la_wifi(ten):
    return (os.path.exists(os.path.join(DUONG_NET, ten, "wireless")) or
            os.path.exists(os.path.join(DUONG_NET, ten, "phy80211")))


def _co_day_cam(ten):
    """carrier=1 nghia la dang co tin hieu (cam day va dau kia song)."""
    try:
        with open(os.path.join(DUONG_NET, ten, "carrier")) as f:
            return f.read().strip() == "1"
    except OSError:
        return False        # cong dang down thi doc carrier bao loi


def danh_sach_cong():
    """
    Moi cong THAT tren may: [{"ten", "wifi", "co_day", "mac"}].
    Sap xep: cong dang co day len truoc cho de nhin.
    """
    ra = []
    try:
        ten_cac_cong = sorted(os.listdir(DUONG_NET))
    except OSError:
        return ra
    for ten in ten_cac_cong:
        if ten == "lo" or not _co_that(ten):
            continue
        mac = ""
        try:
            with open(os.path.join(DUONG_NET, ten, "address")) as f:
                mac = f.read().strip()
        except OSError:
            pass
        ra.append({"ten": ten, "wifi": _la_wifi(ten),
                   "co_day": _co_day_cam(ten), "mac": mac})
    ra.sort(key=lambda x: (not x["co_day"], x["ten"]))
    return ra


def cong_day():
    """
    Ten cong mang CO DAY dung cho PXE/cam thang/kiem tra cong mang.
    Tra "" neu may khong co cong day nao - noi that thay vi doan bua.
    """
    chon = _doc_chon_tay().get("day", "")
    if chon and os.path.exists(os.path.join(DUONG_NET, chon)):
        return chon
    cac = [c for c in danh_sach_cong() if not c["wifi"]]
    if not cac:
        return ""
    for c in cac:
        if c["co_day"]:
            return c["ten"]
    return cac[0]["ten"]


def cong_wifi():
    """Ten cong WiFi. Tra "" neu may khong co card WiFi."""
    chon = _doc_chon_tay().get("wifi", "")
    if chon and os.path.exists(os.path.join(DUONG_NET, chon)):
        return chon
    cac = [c for c in danh_sach_cong() if c["wifi"]]
    return cac[0]["ten"] if cac else ""


def la_raspberry_pi():
    """
    Dang chay tren Raspberry Pi that hay may thuong?

    Dung de AN cac tinh nang gan chat voi phan cung RasPad (xoay man hinh
    qua /boot/config.txt, nut nguon, Bluetooth PAN) khi chay tren may ban -
    hien ra roi bao loi thi te hon la khong hien.
    """
    try:
        with open("/proc/device-tree/model") as f:
            return "raspberry pi" in f.read().lower()
    except OSError:
        return False


def nhiet_do_cpu():
    """
    Nhiet do CPU (do C) hoac None neu may khong bao.

    Pi co lenh rieng `vcgencmd`; may thuong thi doc /sys/class/thermal.
    Thu ca hai thay vi gia dinh mot cai - khong thi o nhiet do tren trang
    Tong quan se trong tren moi may khong phai Pi.
    """
    import subprocess
    try:
        r = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True,
                           text=True, timeout=5)
        if r.returncode == 0 and "=" in r.stdout:
            return float(r.stdout.split("=")[1].split("'")[0])
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    # May thuong: lay vung nhiet do dau tien doc duoc
    goc = "/sys/class/thermal"
    try:
        for v in sorted(os.listdir(goc)):
            if not v.startswith("thermal_zone"):
                continue
            try:
                with open(os.path.join(goc, v, "temp")) as f:
                    do = int(f.read().strip()) / 1000.0
                if 0 < do < 150:          # loc gia tri vo ly cua vai cam bien
                    return round(do, 1)
            except (OSError, ValueError):
                continue
    except OSError:
        pass
    return None


if __name__ == "__main__":
    print("Raspberry Pi      :", la_raspberry_pi())
    print("Cong day          :", cong_day() or "(khong co)")
    print("Cong WiFi         :", cong_wifi() or "(khong co)")
    print("Nhiet do CPU      :", nhiet_do_cpu())
    print("Tat ca cong that  :")
    for c in danh_sach_cong():
        print(f"   {c['ten']:12} {'WiFi' if c['wifi'] else 'day '} "
              f"{'[co tin hieu]' if c['co_day'] else ''} {c['mac']}")


def o_chon_cong(dang_chon="", chi_day=False):
    """
    Sinh cac the <option> cho o chon cong mang trong cac cong cu.

    VI SAO CAN (anh Thoai 19/09/2026 - chuan bi ban cai chay tren may ban):
    9 cong cu mang deu liet ke CUNG hai dong "eth0" va "wlan0" trong o chon.
    Tren may khac hai ten do khong ton tai -> nguoi dung chi chon duoc cong
    khong co that, cong cu nao cung bao loi. Nay liet ke dung cac cong THAT
    dang co tren may.

    Loi ich them: con Pi cam USB-LAN (thanh eth1) thi cong do gio hien ra
    va chon duoc - truoc day khong co cach nao dung.
    """
    from html import escape
    cac = danh_sach_cong()
    if chi_day:
        cac = [c for c in cac if not c["wifi"]]
    if not cac:
        return '<option value="">(máy không có cổng mạng nào)</option>'
    if not dang_chon:
        dang_chon = cong_day() or (cac[0]["ten"] if cac else "")
    ra = []
    for c in cac:
        mo_ta = "WiFi" if c["wifi"] else "dây"
        if c["co_day"]:
            mo_ta += ", đang có tín hiệu"
        chon = " selected" if c["ten"] == dang_chon else ""
        ra.append(f'<option value="{escape(c["ten"])}"{chon}>'
                  f'{escape(c["ten"])} ({mo_ta})</option>')
    return "".join(ra)


def cong_mac_dinh(uu_tien_day=True):
    """Cong dung lam gia tri mac dinh cho cac o chon trong cong cu mang."""
    if uu_tien_day:
        return cong_day() or cong_wifi() or ""
    return cong_wifi() or cong_day() or ""

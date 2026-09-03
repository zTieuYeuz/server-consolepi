#!/usr/bin/env python3
"""
Console Pi - Agent ghep cap Bluetooth

VI SAO CAN AGENT RIENG: Pi khong co man hinh/ban phim theo kieu may tinh
thong thuong, nen phai tu tra loi cac cau hoi ghep cap cua BlueZ.

KHA NANG DUNG "KeyboardDisplay" (KHONG dung NoInputNoOutput):
  - NoInputNoOutput bat BlueZ dung kieu "Just Works" - dien thoai/laptop
    chap nhan, nhung BAN PHIM Bluetooth thi TU CHOI. Ly do: ban phim go duoc
    mat khau nen chuan HID bat buoc ghep cap co xac thuc. Trieu chung: bam
    ghep cap thi treo mai, log bao "Rejected connection from !bonded device".
  - KeyboardDisplay lo duoc ca hai: hien ma so cho ban phim, va tu xac nhan
    cho dien thoai/laptop.

Ma so can go se duoc ghi ra file de trang web doc va hien len cho nguoi dung.
"""
import json
import os
import secrets
import time

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib

AGENT_PATH = "/consolepi/agent"
AGENT_IFACE = "org.bluez.Agent1"
STATE_FILE = "/run/console-pi-bt.json"


def _log(chuoi):
    """
    Ghi ra journal (`journalctl -u bt-agent`).

    LOI THAT: truoc day agent chi in 1 dong luc khoi dong, khong ghi gi khi
    BlueZ hoi ma. Ghep cap that bai thi khong con dau vet nao de lan ra
    nguyen nhan - phai doan mo. Nay moi buoc deu co dau vet.
    """
    print(chuoi, flush=True)


def _write_state(**kw):
    """Ghi trang thai ghep cap de dashboard doc duoc."""
    data = dict(kw)
    data["at"] = time.time()
    try:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, STATE_FILE)
        os.chmod(STATE_FILE, 0o644)
    except Exception:
        pass


def _clear_state():
    try:
        os.unlink(STATE_FILE)
    except Exception:
        pass


def _dev_name(bus, path):
    """Lay ten thiet bi tu duong dan D-Bus de hien cho de hieu."""
    try:
        props = dbus.Interface(bus.get_object("org.bluez", path),
                               "org.freedesktop.DBus.Properties")
        return str(props.Get("org.bluez.Device1", "Name"))
    except Exception:
        return str(path).split("/")[-1].replace("dev_", "").replace("_", ":")


def _la_ban_phim(bus, path):
    """
    Thiet bi nay co phai BAN PHIM khong? (doc Class of Device cua BlueZ)

    Can biet vi ma PIN kieu cu phai xu ly khac nhau:
      - BAN PHIM go duoc so -> sinh ma NGAU NHIEN roi hien len cho nguoi dung
        go. An toan hon ma co dinh, va van dung cach lam chuan.
      - Tai nghe/loa/bo dam cu -> KHONG go duoc gi, ma PIN cua chung la co
        dinh tu nha may (hau het la 0000). Sinh ma ngau nhien cho nhom nay la
        chac chan ghep that bai.
    Bit theo chuan Bluetooth CoD: major 0x05 = thiet bi ngoai vi, trong do
    bit 6-7 cho biet loai:
        00 = khong ro    01 = ban phim
        10 = chuot       11 = ban phim LIEN chuot/touchpad
    Phai nhan CA 01 VA 11 - loai 11 (ban phim co touchpad roi) rat pho bien
    voi thiet bi cam tay kieu nay. Kiem thu da bat duoc dung loi nay: ban dau
    chi bat 01 nen ban phim lien touchpad bi coi la "khong go duoc" va bi day
    sang nhanh ma co dinh 0000, khong hien ma len de go.
    """
    try:
        props = dbus.Interface(bus.get_object("org.bluez", path),
                               "org.freedesktop.DBus.Properties")
        cls = int(props.Get("org.bluez.Device1", "Class"))
        major = (cls >> 8) & 0x1F
        return major == 0x05 and ((cls >> 6) & 0x03) in (0x01, 0x03)
    except Exception:
        # Thiet bi BLE khong co truong Class. Doan theo ten cho do vay.
        try:
            ten = _dev_name(bus, path).lower()
            return any(t in ten for t in ("keyboard", "keybd", "ban phim", "kb"))
        except Exception:
            return False


class Agent(dbus.service.Object):
    def __init__(self, bus, path):
        super().__init__(bus, path)
        self._bus = bus

    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        _clear_state()

    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        # Cho phep moi dich vu (HID, PAN...) - da ghep cap roi moi toi buoc nay
        return

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        """
        Kieu ghep cap CU (Bluetooth 2.x): BlueZ hoi Pi mot ma PIN, roi nguoi
        dung phai GO CHINH MA DO tren ban phim va bam Enter.

        LOI THAT DA GAP: truoc day ham nay tra ve cung "0000" va chi ghi trang
        thai, nhung TRANG WEB KHONG CO NHANH NAO HIEN ma PIN ra ca (chi hien
        loai "passkey" va "confirm"). Ket qua: ban phim doi go ma, con nguoi
        dung chi thay "dang ghep cap" ma khong he biet phai go gi -> ghep cap
        treo den het gio. Nhin tu ngoai vao dung la "vo ly".

        Nay: ban phim thi sinh ma NGAU NHIEN roi hien len (an toan hon ma co
        dinh); thiet bi khong go duoc (tai nghe/loa cu) thi giu "0000" vi ma
        cua chung co dinh tu nha may, sinh ngau nhien la chac chan hong.
        """
        ten = _dev_name(self._bus, device)
        if _la_ban_phim(self._bus, device):
            pin = f"{secrets.randbelow(1000000):06d}"
            _write_state(kind="pin", value=pin, device=ten, go_tren_ban_phim=True)
            _log(f"RequestPinCode: ban phim '{ten}' -> hien ma {pin} de nguoi dung go")
        else:
            pin = "0000"
            _write_state(kind="pin", value=pin, device=ten, go_tren_ban_phim=False)
            _log(f"RequestPinCode: thiet bi '{ten}' (khong phai ban phim) -> dung ma co dinh 0000")
        return pin

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        # Thiet bi doi PI nhap ma ma CHINH NO dang hien. Pi khong the biet ma
        # do, nen buoc nay chac chan that bai - phai noi that ly do thay vi
        # de nguoi dung ngoi doi vo vong.
        ten = _dev_name(self._bus, device)
        _write_state(kind="need-passkey", value="", device=ten)
        _log(f"RequestPasskey: '{ten}' doi Pi nhap ma do chinh no hien - "
             f"Pi khong doc duoc ma nay, se that bai")
        return dbus.UInt32(0)

    @dbus.service.method(AGENT_IFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        # DAY LA LUONG CUA BAN PHIM: hien ma cho nguoi dung go len ban phim
        ten = _dev_name(self._bus, device)
        _write_state(kind="passkey", value=f"{int(passkey):06d}",
                     entered=int(entered), device=ten, go_tren_ban_phim=True)
        _log(f"DisplayPasskey: '{ten}' -> hien ma {int(passkey):06d} "
             f"(da go {int(entered)} ky tu)")

    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        ten = _dev_name(self._bus, device)
        _write_state(kind="pin", value=str(pincode), device=ten,
                     go_tren_ban_phim=True)
        _log(f"DisplayPinCode: '{ten}' -> hien ma {pincode} de nguoi dung go")

    @dbus.service.method(AGENT_IFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        # Dien thoai/laptop: hien ma de doi chieu, tu dong dong y
        ten = _dev_name(self._bus, device)
        _write_state(kind="confirm", value=f"{int(passkey):06d}", device=ten)
        _log(f"RequestConfirmation: '{ten}' ma {int(passkey):06d} - tu dong dong y")
        return

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        _log(f"RequestAuthorization: '{_dev_name(self._bus, device)}' - tu dong dong y")
        return

    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Cancel(self):
        _write_state(kind="cancelled", value="")
        _log("Cancel: thiet bi huy ghep cap giua chung")


def main():
    _clear_state()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    agent = Agent(bus, AGENT_PATH)
    manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"),
                             "org.bluez.AgentManager1")
    # KeyboardDisplay: hien duoc ma so (cho ban phim) va tu xac nhan (cho
    # dien thoai/laptop). Xem giai thich o dau file.
    manager.RegisterAgent(AGENT_PATH, "KeyboardDisplay")
    manager.RequestDefaultAgent(AGENT_PATH)
    print("Agent da dang ky (KeyboardDisplay)", flush=True)

    GLib.MainLoop().run()


if __name__ == "__main__":
    main()

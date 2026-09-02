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
import time

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib

AGENT_PATH = "/consolepi/agent"
AGENT_IFACE = "org.bluez.Agent1"
STATE_FILE = "/run/console-pi-bt.json"


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
        # Thiet bi cu doi ma PIN co dinh
        pin = "0000"
        _write_state(kind="pin", value=pin, device=_dev_name(self._bus, device))
        return pin

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        # Truong hop hiem: thiet bi hien ma, host phai nhap. Khong biet ma nen
        # tra 0 - se that bai, nhung it gap voi ban phim/chuot thong thuong.
        _write_state(kind="need-passkey", value="",
                     device=_dev_name(self._bus, device))
        return dbus.UInt32(0)

    @dbus.service.method(AGENT_IFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        # DAY LA LUONG CUA BAN PHIM: hien ma cho nguoi dung go len ban phim
        _write_state(kind="passkey", value=f"{int(passkey):06d}",
                     entered=int(entered), device=_dev_name(self._bus, device))

    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        _write_state(kind="pin", value=str(pincode),
                     device=_dev_name(self._bus, device))

    @dbus.service.method(AGENT_IFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        # Dien thoai/laptop: hien ma de doi chieu, tu dong dong y
        _write_state(kind="confirm", value=f"{int(passkey):06d}",
                     device=_dev_name(self._bus, device))
        return

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        return

    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Cancel(self):
        _write_state(kind="cancelled", value="")


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

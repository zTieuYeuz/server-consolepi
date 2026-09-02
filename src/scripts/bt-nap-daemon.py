#!/usr/bin/env python3
"""
Console Pi - Dang ky vai tro NAP (Network Access Point) va GIU dang ky do
song suot doi tien trinh nay.

QUAN TRONG: org.bluez.NetworkServer1.Register() gan voi VONG DOI ket noi
D-Bus cua tien trinh goi no - tien trinh thoat la BlueZ tu dong huy dang
ky NAP ngay lap tuc. Vi vay day PHAI la mot daemon chay mai, khong duoc
la script chay-roi-thoat (oneshot).
"""
import dbus
import dbus.mainloop.glib
from gi.repository import GLib

NAP_UUID = "nap"
BRIDGE = "pan0"


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    server = dbus.Interface(
        bus.get_object("org.bluez", "/org/bluez/hci0"), "org.bluez.NetworkServer1"
    )
    try:
        server.Register(NAP_UUID, BRIDGE)
        print(f"Da dang ky NAP tren bridge {BRIDGE}, giu tien trinh song.", flush=True)
    except dbus.exceptions.DBusException as e:
        if "AlreadyExists" in str(e):
            print("NAP da duoc dang ky (boi tien trinh khac?).", flush=True)
        else:
            raise

    GLib.MainLoop().run()


if __name__ == "__main__":
    main()

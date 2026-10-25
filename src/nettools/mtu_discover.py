# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - MTU / Path MTU Discovery

Tim MTU THAT cua duong truyen toi 1 dia chi, bang cach gui ping mang co
DF (Don't Fragment) voi kich thuoc tang dan/giam dan (tim nhi phan). Neu
mot router giua duong khong the chuyen tiep goi qua kho ma khong duoc phep
phan manh, no se tra ve ICMP "Fragmentation needed" kem theo MTU THAT cua
doan mang do - day la thong tin dang tin cay nhat, dung ngay khong can do
them.

VI SAO CAN CONG CU NAY: MTU bi giam (thuong thay 1492 do PPPoE, ~1436-1400
do VPN/GRE/IPsec) gay ra loai loi rat kho chiu - goi nho (ping, duyet web
co ban) van chay binh thuong, nhung truyen file lon/tai video lai cham hoac
treo hoan toan, vi cac goi lon bi phan manh sai hoac bi loai bo am tham boi
mot thiet bi khong gui ICMP loi (nhieu firewall/middlebox lam vay).

DA KIEM CHUNG TREN MAY THAT (quan trong, giai thich 2 dang loi khac nhau):
  - `ping -M do -s <n>` KHONG co `-I <iface>`: neu he thong co san 1 tuyen
    duong dac biet cho dia chi dich (vi du mot router Wifi cap rieng tuyen
    cho 8.8.8.8 qua interface khac - da gap that o cong cu DHCP test truoc
    day), ket qua bi anh huong boi duong di SAI, khong phai loi MTU that
    cua duong dang muon do. PHAI luon co `-I iface` de ep dung cong.
  - Loi "sendmsg: Message too long" (khong co "Frag needed") xay ra NGAY
    LAP TUC (0ms) khi kich thuoc goi vuot qua MTU cau hinh CUA CHINH
    interface Pi - day la loi cuc bo, khong lien quan gi den mang, va PHAI
    duoc loai tru bang cach kep tran tim kiem theo MTU that cua interface
    (doc tu /sys/class/net/<iface>/mtu) truoc khi bat dau do.
  - Loi "Frag needed and DF set (mtu = X)" la ICMP THAT tu mot router giua
    duong - no NOI THANG mtu dung, dung luon khong can do them.
"""
from consolesystem.core import taisan as _taisan
import random
import re
import subprocess

from flask import request, render_template_string

from . import nettools_bp


def _cong_mac_dinh():
    """Cong mac dinh cho o chon - cong co day that cua may nay (xem
    ui/phancung.py). Truoc day viet cung "eth0" nen chi dung tren Pi."""
    from ui.phancung import cong_mac_dinh
    return cong_mac_dinh()


def _o_chon_cong(dang_chon=""):
    """Cac the <option> liet ke dung cac cong THAT dang co tren may."""
    from ui.phancung import o_chon_cong
    return o_chon_cong(dang_chon)

# Nguong duoi day - bat cu MTU nao duoi day deu coi la hong nang, khong con
# y nghia thuc te (chuan Ethernet toi thieu la 68, nhung thap hon 576 la
# gan nhu chac chan co van de nghiem trong o dau do).
MTU_TOI_THIEU = 68
MTU_TRAN_MAC_DINH = 1500

# MTU tim duoc thap hon 1500 (chuan Ethernet) thi goi y nguyen nhan pho
# bien nhat - giup nguoi dung khong phai tu doan.
GOI_Y_NGUYEN_NHAN = [
    (1492, 1500, "Có thể do PPPoE (ISP dial-up qua Ethernet) - PPPoE trừ đi 8 byte."),
    (1436, 1465, "Có thể do VPN/GRE/IPsec - các giao thức đóng gói này thường trừ 20-64 byte."),
    (1400, 1436, "Khả năng do VPN/tunnel với overhead lớn hơn bình thường."),
    (0,    1400, "MTU rất thấp - kiểm tra cả cấu hình MTU trên chính thiết bị mạng gần Pi."),
]


def _chay(cmd, timeout=6):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", "khong-cai-dat"
    except subprocess.TimeoutExpired:
        return -1, "", "qua-thoi-gian-cho"
    except Exception as e:
        return -1, "", str(e)


def _mtu_cua_interface(iface):
    try:
        with open(f"/sys/class/net/{iface}/mtu") as f:
            return int(f.read().strip())
    except Exception:
        return MTU_TRAN_MAC_DINH


def _thu_mot_kich_thuoc(iface, host, payload, timeout):
    """
    Gui 1 ping DF voi kich thuoc payload cho truoc.
    Tra ve mot trong ba: ("ok", None), ("qua_lon", mtu_that_neu_biet),
    ("khong_ro", None) - truong hop thu ba la mat goi thuong, khong ro
    co phai do MTU hay khong.
    """
    rc, out, err = _chay(
        ["ping", "-M", "do", "-s", str(payload), "-c", "1", "-W", str(timeout),
         "-I", iface, host],
        timeout=timeout + 3,
    )
    toan_bo = out + err

    if "Frag needed and DF set" in toan_bo or "Fragmentation needed" in toan_bo:
        m = re.search(r"mtu\s*=\s*(\d+)", toan_bo)
        return "qua_lon", (int(m.group(1)) if m else None)

    if "sendmsg: Message too long" in toan_bo:
        # Loi cuc bo (vuot MTU cua chinh interface) - khong phai ket qua
        # mang, nhung van coi la "qua lon" de nhi phan tiep tuc dung huong.
        return "qua_lon", None

    if ", 1 received" in toan_bo or "1 packets transmitted, 1 received" in toan_bo:
        return "ok", None

    return "khong_ro", None


def tim_mtu(host, iface=None, timeout=2):
    """
    Tra ve {"ok", "error", "mtu": int|None, "chi_tiet": [...], "canh_bao": str|None,
            "tu_router": bool}

    Nhi phan tim kich thuoc payload lon nhat con di qua duoc voi co DF, kep
    tran theo MTU that cua interface. Neu mot router bao thang MTU qua ICMP
    Frag-needed thi dung ngay ket qua do, khong can do tiep.
    """
    # Bat dau bang chu/so (khong duoc la dau "-"): "host" duoc dua thang vao
    # subprocess dang list (khong shell=True) nen khong the chen lenh shell,
    # nhung neu bat dau bang "-" thi ping co the hieu nham do la MOT CO LENH
    # (vd "--flood" - can quyen root, tien trinh nay chinh la root) thay vi
    # dia chi. Ra soat lai code phat hien, khong phai da gap that.
    if not host or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.\-:]{0,254}", host):
        return {"ok": False, "error": "Địa chỉ/hostname không hợp lệ.", "mtu": None,
                "chi_tiet": [], "canh_bao": None, "tu_router": False}

    mtu_iface = _mtu_cua_interface(iface)
    chi_tiet = []

    # Kiem tra co ket noi duoc toi dich khong (goi nho, khong DF) truoc khi
    # do MTU - neu host khong phan hoi gi ca thi do MTU vo nghia, va phai
    # noi ro nguyen nhan la "khong toi duoc" chu khong phai "MTU rất thấp".
    rc, out, err = _chay(["ping", "-c", "2", "-W", str(timeout), "-I", iface, host],
                         timeout=timeout * 2 + 3)
    if "0 received" in (out + err) or rc != 0 and "received" not in out:
        return {"ok": False,
                "error": f"Không ping tới được {host} qua {iface} - kiểm tra địa chỉ hoặc "
                        "ket noi truoc khi do MTU.",
                "mtu": None, "chi_tiet": [], "canh_bao": None, "tu_router": False}

    thap = MTU_TOI_THIEU - 28   # payload thap nhat coi nhu luon thanh cong
    cao = min(9000, mtu_iface) - 28
    payload_tot_nhat = thap
    tu_router = False
    mtu_tu_icmp = None

    for _buoc in range(16):    # du cho khoang 9000, thuc te ~14 la du
        if thap > cao:
            break
        giua = (thap + cao) // 2

        # Thu lai toi da 2 lan cho MOT kich thuoc truoc khi ket luan - tranh
        # nham lan mat goi thuong (thoang qua) voi gioi han MTU that.
        ket_qua, mtu_bao = None, None
        for _lan in range(2):
            ket_qua, mtu_bao = _thu_mot_kich_thuoc(iface, host, giua, timeout)
            if ket_qua != "khong_ro":
                break

        chi_tiet.append({"payload": giua, "mtu_tuong_ung": giua + 28, "ket_qua": ket_qua})

        if ket_qua == "ok":
            payload_tot_nhat = giua
            thap = giua + 1
        elif ket_qua == "qua_lon":
            if mtu_bao:
                # Router noi thang MTU dung - tin ngay, dung do them.
                mtu_tu_icmp = mtu_bao
                tu_router = True
                break
            cao = giua - 1
        else:
            # "khong_ro" sau 2 lan thu - khong the ket luan chac chan o muc
            # nay, coi nhu gioi han (an toan hon la bao qua lon).
            cao = giua - 1

    mtu_cuoi = mtu_tu_icmp if mtu_tu_icmp else (payload_tot_nhat + 28)

    canh_bao = None
    if mtu_cuoi < MTU_TRAN_MAC_DINH:
        for duoi, tren, mo_ta in GOI_Y_NGUYEN_NHAN:
            if duoi <= mtu_cuoi < tren:
                canh_bao = (f"MTU {mtu_cuoi} thấp hơn chuẩn Ethernet (1500). {mo_ta}")
                break

    return {"ok": True, "error": None, "mtu": mtu_cuoi, "chi_tiet": chi_tiet,
            "canh_bao": canh_bao, "tu_router": tu_router, "mtu_interface": mtu_iface}


MTU_TEMPLATE = _taisan.doc("nettools/mtu_discover.MTU_TEMPLATE.html")


@nettools_bp.route("/nettools/mtu", methods=["GET", "POST"])
def mtu_route():
    host = request.form.get("host", "").strip()
    iface = request.form.get("iface") or _cong_mac_dinh()
    ran = request.method == "POST"
    result = tim_mtu(host, iface=iface) if ran else None
    return render_template_string(MTU_TEMPLATE, o_chon_cong=_o_chon_cong(iface), host=host, iface=iface, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else _cong_mac_dinh()
    host = sys.argv[2] if len(sys.argv) > 2 else "8.8.8.8"
    print(json.dumps(tim_mtu(host, iface=iface), indent=2, ensure_ascii=False))

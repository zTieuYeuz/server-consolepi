# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - ket noi toi "Kho luu tru trung tam" (kho-console-pi), du an
web rieng chay tren may chu rieng cua nha phat trien, xem
Y-tuong-kho-luu-tru-Console-Pi.md.

VI SAO CO MUC NAY: truoc day moi Pi hien truong deu phai tu mang theo /
tu tai rieng tung ban cai VLC, Unikey... Kho trung tam la 1 noi DUY NHAT
luu san cac file do (co kem tham so cai im lang), Pi nao can thi vao tim
va tai thang ve kho cuc bo cua minh (deploy/apps, deploy/scripts) - khong
phai mang USB di khap noi nua.

Day chi la PHAN CLIENT (goi HTTP toi kho, khong tu lam viec luu tru). Kho
that su la 1 du an Flask+SQLite rieng, o repo khac (kho-console-pi).

Xac thuc: kho dung TOKEN rieng cho tung Pi, gui qua header X-Token - KHONG
dung chung voi mat khau dang nhap trang web kho.

26/09/2026 (anh Thoai: "ket noi voi Console Pi 1 cach muot ma" + "lam them
phan OS, nhieu khi ho muon tai OS xuong luon"):
  - KET NOI BANG MA 6 KY TU (ghep_noi): trang kho tao ma, go ma o day, kho
    tra ve token. Khong con chep token 64 ky tu bang man hinh cam ung.
  - TAI O NEN (tai_nen): truoc day tai ngay trong request web - file vai
    tram MB la trinh duyet/nginx het gio, trang trang tron. Nay tai o luong
    rieng, co tien do, dut mang thi tai TIEP tu byte da co (HTTP Range),
    xong thi kiem SHA-256 voi so kho da tinh.
  - HE DIEU HANH: tai ISO ve thu muc cua 1 he dieu hanh moi roi giao cho
    ui/isotach.py tach boot.wim/install.wim - y het nhu tai ISO len bang tay.
"""

import hashlib
import json
import os
import socket
import threading
import time

import requests

from .duongdan import FILE_KHO_TRUNGTAM, bao_dam_thu_muc_du_lieu

TIMEOUT_DANH_SACH = 10
TIMEOUT_TAI = 30
SO_LAN_THU_LAI = 20           # dut mang: thu lai toi da 20 lan (moi lan tai tiep)


def _phien_ban():
    for p in ("/opt/console-pi/VERSION",
              os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                  os.path.abspath(__file__)))), "VERSION")):
        try:
            with open(p) as f:
                return f.read().strip()
        except OSError:
            pass
    return ""


# Cloudflare Access (tuy chon, 27/09/2026): neu chu kho bat Access cho /api/*
# kieu "Service Auth", moi request cua may phai kem cap Service Token. Cap ma
# nay KHONG nam trong ma nguon: may build chep vao anh ISO tu file rieng (xem
# iso/dung-cay-build.sh), hoac dat tay file duoi day (quyen 600). Khong co file
# -> khong gui gi (dung khi kho chi dung Bypass cho /api/*).
FILE_CF_ACCESS = "/var/lib/console-pi/cf-access.json"


def cf_access_headers():
    try:
        with open(FILE_CF_ACCESS, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("client_id") and d.get("client_secret"):
            return {"CF-Access-Client-Id": d["client_id"],
                    "CF-Access-Client-Secret": d["client_secret"]}
    except (OSError, ValueError):
        pass
    return {}


def _headers(cauhinh):
    """Kem ten may + phien ban -> trang kho hien Pi nao dang ket noi."""
    return {"X-Token": cauhinh["token"], "X-Pi-Ten": socket.gethostname(),
            "X-Pi-Phienban": _phien_ban(), **cf_access_headers()}


def chuan_hoa_url(url):
    """Nguoi dung hay go thieu "https://" hoac dan ca duong dan trang con."""
    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    # Chi giu phan goc: https://ten-mien[:cong]
    proto, _, con = url.partition("://")
    return f"{proto}://{con.split('/')[0]}".rstrip("/")


def doc_cauhinh():
    """Tra ve {"url", "token"} neu da cau hinh, nguoc lai None."""
    try:
        with open(FILE_KHO_TRUNGTAM, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("url") and d.get("token"):
            return d
    except (OSError, ValueError):
        pass
    return None


def luu_cauhinh(url, token):
    url = chuan_hoa_url(url)
    token = (token or "").strip()
    if not url or not token:
        return False, "Chưa điền đủ địa chỉ kho và token."
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "Địa chỉ kho phải bắt đầu bằng http:// hoặc https://."
    bao_dam_thu_muc_du_lieu()
    old = os.umask(0o077)
    tam = FILE_KHO_TRUNGTAM + ".tmp"
    try:
        with open(tam, "w", encoding="utf-8") as f:
            json.dump({"url": url, "token": token}, f)
        os.replace(tam, FILE_KHO_TRUNGTAM)
    finally:
        os.umask(old)
    return True, "Đã lưu kết nối tới kho trung tâm."


def xoa_cauhinh():
    try:
        os.remove(FILE_KHO_TRUNGTAM)
    except OSError:
        pass


def ghep_noi(url, ma):
    """
    Ket noi bang MA 6 KY TU. Kiem tra dia chi dung la kho truoc (de bao loi
    ro "sai dia chi" thay vi "sai ma"), roi doi ma lay token va luu lai.
    """
    url = chuan_hoa_url(url)
    ma = "".join(ch for ch in (ma or "") if ch.isalnum()).upper()
    if not url:
        return False, "Chưa điền địa chỉ kho."
    if len(ma) != 6:
        return False, "Mã kết nối gồm đúng 6 ký tự (lấy ở trang kho, mục Kết nối Console Pi)."
    try:
        r = requests.get(f"{url}/api/thong-tin", timeout=TIMEOUT_DANH_SACH,
                         headers=cf_access_headers())
        d = r.json() if r.status_code == 200 else {}
    except (requests.RequestException, ValueError) as e:
        return False, f"Không mở được {url} - kiểm tra lại địa chỉ và mạng ({type(e).__name__})."
    if not d.get("ghep_bang_ma"):
        return False, (f"{url} không phải kho Console Pi, hoặc là kho bản cũ chưa hỗ trợ "
                       f"mã kết nối - dùng ô Token (nâng cao) bên dưới.")
    try:
        r = requests.post(f"{url}/api/ghep-noi", timeout=TIMEOUT_DANH_SACH,
                          headers=cf_access_headers(),
                          json={"ma": ma, "ten_pi": socket.gethostname(),
                                "phien_ban": _phien_ban()})
        d = r.json()
    except (requests.RequestException, ValueError) as e:
        return False, f"Lỗi khi gửi mã: {e}"
    if not d.get("ok"):
        return False, d.get("loi") or f"Kho từ chối (HTTP {r.status_code})."
    ok, msg = luu_cauhinh(url, d["token"])
    return ok, ("Đã kết nối tới kho." if ok else msg)


def danh_sach(cauhinh):
    """Lay toan bo muc dang co tren kho. Tra ve (True, [muc,...]) hoac
    (False, thong_bao_loi_de_hieu)."""
    try:
        r = requests.get(f"{cauhinh['url']}/api/danh-sach",
                         headers=_headers(cauhinh), timeout=TIMEOUT_DANH_SACH)
    except requests.RequestException as e:
        return False, f"Không kết nối được tới kho: {e}"
    if r.status_code in (401, 403):
        return False, "Token không hợp lệ hoặc đã bị thu hồi trên kho."
    if r.status_code != 200:
        return False, f"Kho trả về lỗi HTTP {r.status_code}."
    try:
        d = r.json()
    except ValueError:
        return False, "Kho trả về dữ liệu không hợp lệ."
    if not isinstance(d, dict) or not d.get("ok") or not isinstance(d.get("muc"), list):
        return False, d.get("loi", "Kho trả về dữ liệu không hợp lệ.") if isinstance(d, dict) else "Kho trả về dữ liệu không hợp lệ."
    return True, d["muc"]


def tai_bo_khoi_dong(cauhinh, duong_dich):
    """
    Tai bootmgr + BCD + boot.sdi (zip) kho tu tach tu ISO Windows tren kho - cho WinPE
    rut gon kieu WDS khi may chua co bo Windows nao (xem ui/winperieng._bao_dam_bootmgr).
    (ok, loi).
    """
    try:
        r = requests.get(f"{cauhinh['url']}/api/bo-khoi-dong", headers=_headers(cauhinh),
                         timeout=180)
        if r.status_code != 200:
            try:
                return False, r.json().get("loi") or f"HTTP {r.status_code}"
            except ValueError:
                return False, f"HTTP {r.status_code}"
        with open(duong_dich, "wb") as f:
            f.write(r.content)
        return True, ""
    except requests.RequestException as e:
        return False, f"Không tới được kho ({type(e).__name__})."


def _bam_file(duong, dung=None):
    """SHA-256 cua file (doc khoi 8 MB). dung() True -> huy, tra None."""
    h = hashlib.sha256()
    with open(duong, "rb") as f:
        while True:
            k = f.read(8 * 1024 * 1024)
            if not k:
                break
            h.update(k)
            if dung and dung():
                return None
    return h


def tai_ve(cauhinh, muc_id, duong_dich, sha256="", bao_tien_do=None, dung=None,
           kich_thuoc=0):
    """
    Tai 1 file tu kho ve duong_dich. TAI TIEP duoc: ghi vao
    "<duong_dich>.part"; neu file .part da co (lan truoc dut mang) thi xin
    kho phan con lai bang Range. Dut mang giua chung -> thu lai toi da
    SO_LAN_THU_LAI lan, moi lan tiep tu cho da co. Xong thi kiem SHA-256
    (neu kho da tinh) roi moi doi ten thanh file that.
    bao_tien_do(da, tong): goi dinh ky. dung(): tra True thi huy.

    30/09/2026 (anh Thoai: "lam nhanh nhat co the"):
      - SHA-256 duoc BAM NGAY TRONG LUC TAI (moi khoi ghi ra dia cung dua vao
        bo bam) thay vi doc lai ca file 8 GB lan nua sau khi tai xong - truoc
        day buoc "Dang kiem tra SHA-256" ton them 1-3 phut (the nho Pi cham
        hon nua). Tai tiep tu .part thi bam phan da co 1 lan roi bam tiep.
      - File dich DA CO san, dung kich thuoc va dung SHA-256 -> KHONG tai lai.
    """
    tam = duong_dich + ".part"
    if (kich_thuoc and sha256 and os.path.isfile(duong_dich)
            and os.path.getsize(duong_dich) == kich_thuoc):
        if bao_tien_do:
            bao_tien_do(kich_thuoc, kich_thuoc, "File đã có sẵn trên máy - đang kiểm tra...")
        hh = _bam_file(duong_dich, dung)
        if hh is None:
            return False, "Đã huỷ."
        if hh.hexdigest() == sha256.lower():
            return True, "File đã có sẵn và đúng SHA-256 - không cần tải lại."
    lan_loi = 0
    tong = 0
    bo_bam = hashlib.sha256() if sha256 else None
    da_bam = 0                 # bo_bam dang bao phu bao nhieu byte DAU cua .part
    while True:
        da = os.path.getsize(tam) if os.path.exists(tam) else 0
        if bo_bam is not None and da_bam != da:
            # .part co san tu truoc (tai tiep): bam phan da co 1 lan
            bo_bam, da_bam = hashlib.sha256(), 0
            if da > 0:
                if bao_tien_do:
                    bao_tien_do(da, da, "Đang kiểm tra phần đã tải trước đó...")
                bo_bam = _bam_file(tam, dung)
                if bo_bam is None:
                    return False, "Đã huỷ."
                da_bam = da
        h = _headers(cauhinh)
        if da:
            h["Range"] = f"bytes={da}-"
        try:
            with requests.get(f"{cauhinh['url']}/api/tai/{muc_id}", headers=h,
                              stream=True, timeout=TIMEOUT_TAI) as r:
                if r.status_code in (401, 403):
                    return False, "Token không hợp lệ hoặc đã bị thu hồi trên kho."
                if r.status_code == 416:            # da du byte tu truoc
                    tong = da
                elif r.status_code not in (200, 206):
                    return False, f"Kho trả về lỗi HTTP {r.status_code}."
                else:
                    if r.status_code == 200:        # kho khong tra Range -> tai lai tu dau
                        da = 0
                        tong = int(r.headers.get("Content-Length") or 0)
                        if bo_bam is not None:
                            bo_bam, da_bam = hashlib.sha256(), 0
                    else:
                        tong = da + int(r.headers.get("Content-Length") or 0)
                    moc = time.time()
                    with open(tam, "ab" if da else "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                            if dung and dung():
                                return False, "Đã huỷ."
                            if chunk:
                                f.write(chunk)
                                if bo_bam is not None:
                                    bo_bam.update(chunk)
                                    da_bam += len(chunk)
                                da += len(chunk)
                                if bao_tien_do and time.time() - moc > 0.5:
                                    bao_tien_do(da, tong)
                                    moc = time.time()
            if tong and os.path.getsize(tam) < tong:
                raise requests.ConnectionError("kết nối bị cắt giữa chừng")
            break
        except requests.RequestException as e:
            lan_loi += 1
            if lan_loi > SO_LAN_THU_LAI:
                return False, f"Lỗi khi tải (đã thử lại {SO_LAN_THU_LAI} lần): {e}"
            if bao_tien_do:
                bao_tien_do(os.path.getsize(tam) if os.path.exists(tam) else 0, tong,
                            f"Mất kết nối, thử lại lần {lan_loi}...")
            time.sleep(min(30, 3 * lan_loi))
    if sha256:
        if bo_bam is None or da_bam != os.path.getsize(tam):
            if bao_tien_do:
                bao_tien_do(os.path.getsize(tam), tong, "Đang kiểm tra SHA-256...")
            bo_bam = _bam_file(tam, dung)
            if bo_bam is None:
                return False, "Đã huỷ."
        if bo_bam.hexdigest() != sha256.lower():
            os.remove(tam)
            return False, "File tải về KHÔNG khớp SHA-256 của kho (hỏng trên đường truyền) - đã xoá, tải lại."
    os.replace(tam, duong_dich)
    return True, "Đã tải xong."


# ----------------------------------------------------------- tai o nen
_VIEC = {}                 # muc_id -> trang thai tai
_KHOA = threading.Lock()


def trang_thai_tai():
    with _KHOA:
        return [dict(v) for v in sorted(_VIEC.values(), key=lambda x: -x["bat_dau"])]


def dang_tai(muc_id):
    with _KHOA:
        v = _VIEC.get(muc_id)
        return bool(v and v["dang"])


def _dat(muc_id, **kw):
    with _KHOA:
        _VIEC[muc_id].update(kw)


_CB_HUY = {}               # muc_id -> ham goi NGAY khi bam Huy (vd dung tien trinh tach ISO)


def huy_tai(muc_id):
    """Bam Huy: dat co huy + bao tien trinh dang chay (tach ISO...) dung lai.
    Viec don dep (xoa du lieu da tai) do luong tai tu lam khi thay co huy."""
    with _KHOA:
        v = _VIEC.get(muc_id)
        if not (v and v["dang"]):
            return False
        v["huy"] = True
        v["thong_bao"] = "Đang huỷ và xoá dữ liệu đã tải..."
        cb = _CB_HUY.get(muc_id)
    if cb:
        try:
            cb()
        except Exception:
            pass
    return True


def da_huy(muc_id):
    with _KHOA:
        v = _VIEC.get(muc_id)
        return bool(v and v["huy"])


def xoa_viec_xong():
    with _KHOA:
        for k in [k for k, v in _VIEC.items() if not v["dang"]]:
            del _VIEC[k]


def tai_nen(cauhinh, muc, duong_dich, sau_khi_xong=None, khi_huy=None, don_dep=None):
    """
    Bat dau tai 1 muc o nen. sau_khi_xong(duong_dich) -> (ok, thong_bao):
    buoc tiep theo (ghi tham so cai dat, tach ISO...), chay trong cung luong.
    khi_huy(): goi NGAY khi nguoi dung bam Huy (vd ngat tien trinh tach ISO).
    don_dep(): goi sau khi huy xong de xoa phan con lai rieng cua loai muc nay.
    Tra ve (ok, thong_bao) ngay lap tuc.

    HUY = XOA SACH (anh Thoai 30/09/2026): file dang tai (.part), file da tai
    xong do LAN NAY tao ra, va phan dang lam do deu bi xoa. File da co san
    tu truoc (vd "Tai lai") thi KHONG dung toi.
    """
    muc_id = muc["id"]
    with _KHOA:
        if _VIEC.get(muc_id, {}).get("dang"):
            return False, f'"{muc["ten"]}" đang tải rồi.'
        _VIEC[muc_id] = {"id": muc_id, "ten": muc.get("ten", ""), "loai": muc.get("loai", ""),
                         "da": 0, "tong": int(muc.get("kich_thuoc") or 0), "dang": True,
                         "ok": None, "thong_bao": "Đang bắt đầu...", "bat_dau": time.time(),
                         "toc_do": 0, "huy": False}
        _CB_HUY[muc_id] = khi_huy

    def bao(da, tong, tb=None):
        with _KHOA:
            v = _VIEC[muc_id]
            if v["huy"]:
                return
            g = time.time() - v["bat_dau"]
            v["toc_do"] = int(da / g) if g > 1 else 0
            v["da"], v["tong"] = da, tong or v["tong"]
            v["thong_bao"] = tb or "Đang tải..."

    def don_sach_khi_huy(co_san_truoc):
        try:
            os.remove(duong_dich + ".part")
        except OSError:
            pass
        if not co_san_truoc:
            try:
                os.remove(duong_dich)
            except OSError:
                pass
        if don_dep:
            try:
                don_dep()
            except Exception:
                pass

    def chay():
        co_san_truoc = os.path.exists(duong_dich)
        huy = lambda: _VIEC[muc_id]["huy"]
        ok, tb = tai_ve(cauhinh, muc_id, duong_dich, muc.get("sha256", ""), bao, huy,
                        int(muc.get("kich_thuoc") or 0))
        if ok and sau_khi_xong and not huy():
            _dat(muc_id, thong_bao="Đang xử lý sau khi tải...", da=_VIEC[muc_id]["tong"])
            try:
                ok, tb = sau_khi_xong(duong_dich)
            except Exception as e:          # khong de luong chet im lang
                ok, tb = False, f"Lỗi sau khi tải: {e}"
        if huy():
            don_sach_khi_huy(co_san_truoc)
            ok, tb = False, "Đã huỷ - đã xoá toàn bộ dữ liệu đã tải và đang xử lý."
        _CB_HUY.pop(muc_id, None)
        _dat(muc_id, dang=False, ok=ok, thong_bao=tb)

    threading.Thread(target=chay, daemon=True).start()
    return True, f'Đang tải "{muc["ten"]}" ở nền - xem tiến độ ngay trên trang này.'


# ------------------------------------------------------- tu dang ky may
# 29/09/2026 (anh Thoai: "cu cho ket noi tu do, nhung tren trang kho biet
# may ten gi, IP WAN, seri... de loc ban hang hoac chan; gui thong tin len
# thi ma hoa cang ky cang tot"). Moi may khi co mang tu gui 1 goi thong tin
# len kho mac dinh, nhan token ve - khong can go ma 6 ky tu. May da ket noi
# (ke ca ghep tay) thi moi lan khoi dong gui lai de kho co thong tin moi.
#
# MA HOA DAU-CUOI (them tren HTTPS - HTTPS bi "mo" tai Cloudflare):
#   X25519 (khoa tam moi goi) + HKDF-SHA256 + AES-256-GCM, khoa cong khai
#   cua kho GHIM duoi day (khong lay qua mang -> khong bi thay khoa giua
#   duong). Goi co thoi diem + ma goi ngau nhien chong phat lai. Token tra
#   ve cung ma hoa bang khoa phien -> chi may nay doc duoc. Chi tiet phia
#   kho: kho-console-pi/src/dangky.py.
URL_KHO_MAC_DINH = "https://kho-console.home-server.id.vn"
KHOA_CONG_KHAI_KHO = "KBKZrsAjnPc4SHWUw+vOIQNRkNM+0Ye2K8yNiqAry1E="   # kho: dang-ky-x25519.key
NHAN_GOI = b"ConsoleSystem/dang-ky/v1"


def _doc(p, dai=120):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read().replace("\x00", "").strip()[:dai]
    except OSError:
        return ""


_CHUOI_RONG = {"", "none", "to be filled by o.e.m.", "default string", "not specified",
               "system serial number", "o.e.m.", "not applicable", "0", "0123456789",
               "default", "unknown", "n/a", "chassis serial number"}


def _sach(s):
    return "" if (s or "").strip().lower() in _CHUOI_RONG else (s or "").strip()


def seri_may():
    """Seri phan cung: PC/mini PC doc DMI; Raspberry Pi doc seri chip."""
    for p in ("/sys/class/dmi/id/product_serial", "/sys/class/dmi/id/board_serial",
              "/sys/class/dmi/id/chassis_serial", "/sys/firmware/devicetree/base/serial-number"):
        s = _sach(_doc(p, 64))
        if s:
            return s
    for dong in _doc("/proc/cpuinfo", 100000).splitlines():
        if dong.lower().startswith("serial"):
            return _sach(dong.split(":", 1)[-1])
    return ""


def thong_tin_may():
    """Gom thong tin phan cung/he thong de kho quan ly (khong gom du lieu
    nguoi dung, mat khau hay noi dung gi cua khach)."""
    import platform
    d = {"ten_may": socket.gethostname(), "seri": seri_may(),
         "machine_id": _doc("/etc/machine-id", 64), "phien_ban": _phien_ban(),
         "kien_truc": platform.machine()}
    hang, model = _sach(_doc("/sys/class/dmi/id/sys_vendor")), _sach(_doc("/sys/class/dmi/id/product_name"))
    if not model:
        model = _doc("/sys/firmware/devicetree/base/model")      # Raspberry Pi
        hang = hang or ("Raspberry Pi" if "raspberry" in model.lower() else "")
    d["hang"], d["model"] = hang, model
    d["bo_mach"] = " ".join(x for x in (_sach(_doc("/sys/class/dmi/id/board_vendor")),
                                        _sach(_doc("/sys/class/dmi/id/board_name"))) if x)
    loai = _doc("/sys/class/dmi/id/chassis_type", 4)
    d["loai_may"] = {"3": "Desktop", "4": "Desktop", "6": "Mini Tower", "7": "Tower",
                     "8": "Portable", "9": "Laptop", "10": "Notebook", "13": "All-in-One",
                     "14": "Sub Notebook", "30": "Tablet", "31": "Convertible", "32": "Detachable",
                     "35": "Mini PC", "36": "Stick PC"}.get(loai, "")
    for dong in _doc("/proc/cpuinfo", 200000).splitlines():
        if dong.startswith("model name") and ":" in dong:
            d["cpu"] = dong.split(":", 1)[1].strip()
            break
    if not d.get("cpu"):                     # ARM (Pi): khong co "model name"
        try:
            import subprocess
            for dong in subprocess.run(["lscpu"], capture_output=True, text=True,
                                       timeout=5).stdout.splitlines():
                if dong.startswith("Model name:"):
                    d["cpu"] = dong.split(":", 1)[1].strip()
                    break
        except (OSError, subprocess.SubprocessError):
            pass
    d["so_nhan"] = os.cpu_count() or 0
    try:
        for dong in _doc("/proc/meminfo", 5000).splitlines():
            if dong.startswith("MemTotal:"):
                d["ram_mb"] = int(dong.split()[1]) // 1024
        st = os.statvfs("/")
        d["dia_gb"] = st.f_blocks * st.f_frsize // (1024 ** 3)
    except (OSError, ValueError):
        pass
    for dong in _doc("/etc/os-release", 5000).splitlines():
        if dong.startswith("PRETTY_NAME="):
            d["he_dieu_hanh"] = dong.split("=", 1)[1].strip('"')
    try:
        d["mui_gio"] = os.path.realpath("/etc/localtime").split("zoneinfo/")[-1]
    except OSError:
        pass
    mac, ip_lan = [], []
    try:
        import fcntl
        import struct
        for ten in sorted(os.listdir("/sys/class/net")):
            if ten == "lo" or not os.path.exists(f"/sys/class/net/{ten}/device"):
                continue                     # chi card that, bo cau/ao
            m = _doc(f"/sys/class/net/{ten}/address", 20)
            if m and m != "00:00:00:00:00:00":
                mac.append(f"{ten}={m}")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sk:
                    kq = fcntl.ioctl(sk.fileno(), 0x8915, struct.pack("256s", ten[:15].encode()))
                    ip_lan.append(f"{ten}={socket.inet_ntoa(kq[20:24])}")
            except OSError:
                pass
    except OSError:
        pass
    d["mac"], d["ip_lan"] = mac, ip_lan
    return d


def _ma_hoa_goi(du):
    """Tra (phong_bi dict, khoa_phien). Xem chu thich dau muc."""
    import base64
    import secrets as _sec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey, X25519PublicKey)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    pub_kho = base64.b64decode(KHOA_CONG_KHAI_KHO)
    tam = X25519PrivateKey.generate()
    epk = tam.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    chung = tam.exchange(X25519PublicKey.from_public_bytes(pub_kho))
    k = HKDF(algorithm=hashes.SHA256(), length=32, salt=epk + pub_kho, info=NHAN_GOI).derive(chung)
    n = _sec.token_bytes(12)
    ct = AESGCM(k).encrypt(n, json.dumps(du, ensure_ascii=False).encode(), NHAN_GOI)
    b64 = lambda b: base64.b64encode(b).decode()
    return {"v": 1, "epk": b64(epk), "n": b64(n), "ct": b64(ct)}, k


def _giai_ma_tra_loi(k, d):
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    n, ct = base64.b64decode(d["n"]), base64.b64decode(d["ct"])
    return json.loads(AESGCM(k).decrypt(n, ct, NHAN_GOI + b"/tra-loi"))


def _lech_gio_voi_kho(url):
    """
    So giay can CONG vao dong ho may cho khop gio kho (lay tu header Date).

    LOI THAT 29/09/2026: mini PC cua anh Thoai lech NHANH 7 TIENG (BIOS de
    gio Viet Nam, Linux hieu la gio quoc te; ISO luc do lai thieu NTP) -> kho
    tu choi moi goi dang ky vi "lech qua 5 phut" (chong phat lai). Dong goi
    theo gio cua kho thi dong ho may sai bao nhieu cung ket noi duoc; chong
    phat lai van giu nguyen (ma goi dung 1 lan). Khong lay duoc -> 0.
    """
    try:
        from email.utils import parsedate_to_datetime
        r = requests.get(f"{url}/api/thong-tin", timeout=TIMEOUT_DANH_SACH,
                         headers=cf_access_headers())
        lech = parsedate_to_datetime(r.headers["Date"]).timestamp() - time.time()
        if abs(lech) > 120:
            print(f"[tu-dang-ky-kho] Dong ho may lech {lech / 3600:+.1f} gio so voi kho - "
                  f"dong goi theo gio kho", flush=True)
        return lech
    except Exception:
        return 0


def tu_dang_ky():
    """Gui goi thong tin da ma hoa len kho. Tra (ok, thong_diep)."""
    import secrets as _sec
    cu = doc_cauhinh()
    url = cu["url"] if cu else URL_KHO_MAC_DINH
    du = {"ts": int(time.time() + _lech_gio_voi_kho(url)), "ma_goi": _sec.token_hex(16),
          "token": cu["token"] if cu else "", "may": thong_tin_may()}
    try:
        phong_bi, k = _ma_hoa_goi(du)
        r = requests.post(f"{url}/api/dang-ky", json=phong_bi, timeout=TIMEOUT_DANH_SACH,
                          headers=cf_access_headers())
        d = r.json()
    except (requests.ConnectionError, requests.Timeout):
        return False, "Máy chưa có Internet, hoặc không tới được kho (kiểm tra dây mạng / WiFi)."
    except (requests.RequestException, ValueError) as e:
        return False, f"Chưa gửi được thông tin lên kho ({type(e).__name__})."
    if r.status_code == 404:
        return False, "Kho bản cũ, chưa hỗ trợ tự đăng ký."
    if "ct" not in d:
        return False, d.get("loi") or f"Kho từ chối (HTTP {r.status_code})."
    try:
        kq = _giai_ma_tra_loi(k, d)
    except Exception:
        return False, "Trả lời của kho không giải mã được (sai khoá kho?)."
    if not kq.get("ok"):
        return False, kq.get("loi") or "Kho từ chối."
    if cu and cu.get("token") == kq.get("token") and cu["url"] == url:
        return True, "Đã cập nhật thông tin máy lên kho."
    return luu_cauhinh(url, kq["token"])


_KHOA_DANG_KY = threading.Lock()
LAN_THU_CUOI = {"luc": 0, "ok": False, "msg": ""}


def thu_dang_ky_ngay(cach_toi_thieu=0):
    """Thu tu dang ky ngay (trang Kho trung tam goi khi chua co cau hinh).
    Dung chung khoa voi luong nen -> khong bao gio 2 lan gui cung luc."""
    if cach_toi_thieu and time.time() - LAN_THU_CUOI["luc"] < cach_toi_thieu:
        return LAN_THU_CUOI["ok"], LAN_THU_CUOI["msg"]
    with _KHOA_DANG_KY:
        try:
            ok, msg = tu_dang_ky()
        except Exception as e:
            ok, msg = False, f"{type(e).__name__}: {e}"
        LAN_THU_CUOI.update(luc=time.time(), ok=ok, msg=msg)
    print(f"[tu-dang-ky-kho] {msg}", flush=True)
    return ok, msg


def tu_dang_ky_nen():
    """
    Chay o luong nen ngay khi dashboard khoi dong (xem app.py): khong lam
    cham khoi dong, khong nem loi ra ngoai. May moi cai co the chua co mang
    -> thu lai, gian cach tang dan toi 30 phut, den khi gui duoc thi thoi
    (lan khoi dong sau gui lai de cap nhat IP/phan cung).
    """
    time.sleep(15)          # vua khoi dong: doi card mang nhan IP (tranh 1 lan loi vo ich)
    cho = 20
    while True:
        ok, msg = thu_dang_ky_ngay()
        if ok or "bị chặn" in msg or "bản cũ" in msg:
            return
        # Toi da 2 phut/lan: cam day mang xong la ket noi gan nhu ngay (truoc
        # day gian toi 30 phut - anh Thoai cai may that, cam mang roi van cho).
        time.sleep(cho)
        cho = min(cho * 2, 120)

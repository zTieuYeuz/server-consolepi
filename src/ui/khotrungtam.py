"""
Console Pi - ket noi toi "Kho luu tru trung tam" (kho-console-pi), du an
web rieng chay tren may chu .34, xem
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


def _headers(cauhinh):
    """Kem ten may + phien ban -> trang kho hien Pi nao dang ket noi."""
    return {"X-Token": cauhinh["token"], "X-Pi-Ten": socket.gethostname(),
            "X-Pi-Phienban": _phien_ban()}


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
        r = requests.get(f"{url}/api/thong-tin", timeout=TIMEOUT_DANH_SACH)
        d = r.json() if r.status_code == 200 else {}
    except (requests.RequestException, ValueError) as e:
        return False, f"Không mở được {url} - kiểm tra lại địa chỉ và mạng ({type(e).__name__})."
    if not d.get("ghep_bang_ma"):
        return False, (f"{url} không phải kho Console Pi, hoặc là kho bản cũ chưa hỗ trợ "
                       f"mã kết nối - dùng ô Token (nâng cao) bên dưới.")
    try:
        r = requests.post(f"{url}/api/ghep-noi", timeout=TIMEOUT_DANH_SACH,
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


def tai_ve(cauhinh, muc_id, duong_dich, sha256="", bao_tien_do=None, dung=None):
    """
    Tai 1 file tu kho ve duong_dich. TAI TIEP duoc: ghi vao
    "<duong_dich>.part"; neu file .part da co (lan truoc dut mang) thi xin
    kho phan con lai bang Range. Dut mang giua chung -> thu lai toi da
    SO_LAN_THU_LAI lan, moi lan tiep tu cho da co. Xong thi kiem SHA-256
    (neu kho da tinh) roi moi doi ten thanh file that.
    bao_tien_do(da, tong): goi dinh ky. dung(): tra True thi huy.
    """
    tam = duong_dich + ".part"
    lan_loi = 0
    tong = 0
    while True:
        da = os.path.getsize(tam) if os.path.exists(tam) else 0
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
                    else:
                        tong = da + int(r.headers.get("Content-Length") or 0)
                    moc = time.time()
                    with open(tam, "ab" if da else "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                            if dung and dung():
                                return False, "Đã huỷ."
                            if chunk:
                                f.write(chunk)
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
    if bao_tien_do:
        bao_tien_do(os.path.getsize(tam), tong, "Đang kiểm tra SHA-256...")
    if sha256:
        h = hashlib.sha256()
        with open(tam, "rb") as f:
            while True:
                k = f.read(4 * 1024 * 1024)
                if not k:
                    break
                h.update(k)
        if h.hexdigest() != sha256.lower():
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


def huy_tai(muc_id):
    with _KHOA:
        v = _VIEC.get(muc_id)
        if v and v["dang"]:
            v["huy"] = True
            return True
    return False


def xoa_viec_xong():
    with _KHOA:
        for k in [k for k, v in _VIEC.items() if not v["dang"]]:
            del _VIEC[k]


def tai_nen(cauhinh, muc, duong_dich, sau_khi_xong=None):
    """
    Bat dau tai 1 muc o nen. sau_khi_xong(duong_dich) -> (ok, thong_bao):
    buoc tiep theo (ghi tham so cai dat, tach ISO...), chay trong cung luong.
    Tra ve (ok, thong_bao) ngay lap tuc.
    """
    muc_id = muc["id"]
    with _KHOA:
        if _VIEC.get(muc_id, {}).get("dang"):
            return False, f'"{muc["ten"]}" đang tải rồi.'
        _VIEC[muc_id] = {"id": muc_id, "ten": muc.get("ten", ""), "loai": muc.get("loai", ""),
                         "da": 0, "tong": int(muc.get("kich_thuoc") or 0), "dang": True,
                         "ok": None, "thong_bao": "Đang bắt đầu...", "bat_dau": time.time(),
                         "toc_do": 0, "huy": False}

    def bao(da, tong, tb=None):
        with _KHOA:
            v = _VIEC[muc_id]
            g = time.time() - v["bat_dau"]
            v["toc_do"] = int(da / g) if g > 1 else 0
            v["da"], v["tong"] = da, tong or v["tong"]
            v["thong_bao"] = tb or "Đang tải..."

    def chay():
        ok, tb = tai_ve(cauhinh, muc_id, duong_dich, muc.get("sha256", ""), bao,
                        lambda: _VIEC[muc_id]["huy"])
        if ok and sau_khi_xong:
            _dat(muc_id, thong_bao="Đang xử lý sau khi tải...")
            try:
                ok, tb = sau_khi_xong(duong_dich)
            except Exception as e:          # khong de luong chet im lang
                ok, tb = False, f"Lỗi sau khi tải: {e}"
        _dat(muc_id, dang=False, ok=ok, thong_bao=tb)

    threading.Thread(target=chay, daemon=True).start()
    return True, f'Đang tải "{muc["ten"]}" ở nền - xem tiến độ ngay trên trang này.'

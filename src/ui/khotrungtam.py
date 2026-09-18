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

Xac thuc: kho dung TOKEN rieng cho tung Pi (sinh tu trang quan tri kho,
muc "Token"), gui qua header X-Token - KHONG dung chung voi mat khau dang
nhap trang web kho (dung nguyen tac tach biet nguoi dung web / may goi
API, giong het cach ui/api.py lam voi cac API noi bo cua chinh Console Pi).
"""

import json
import os

import requests

from .duongdan import FILE_KHO_TRUNGTAM, bao_dam_thu_muc_du_lieu

TIMEOUT_DANH_SACH = 10
TIMEOUT_TAI = 30


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
    url = (url or "").strip().rstrip("/")
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


def danh_sach(cauhinh):
    """Lay toan bo muc dang co tren kho. Tra ve (True, [muc,...]) hoac
    (False, thong_bao_loi_de_hieu)."""
    try:
        r = requests.get(f"{cauhinh['url']}/api/danh-sach",
                          headers={"X-Token": cauhinh["token"]},
                          timeout=TIMEOUT_DANH_SACH)
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


def tai_ve(cauhinh, muc_id, duong_dich):
    """
    Tai 1 file tu kho ve duong_dich (duong day du tren dia cua Console Pi).

    Ghi qua "<duong_dich>.part" roi doi ten - dung y het cach moi noi khac
    trong du an tai file len/xuong lam, de neu mat mang giua chung thi chi
    con lai 1 file .part do dang chu khong phai 1 file that bi cut mat
    nam lan trong danh sach that.
    """
    tam = duong_dich + ".part"
    try:
        with requests.get(f"{cauhinh['url']}/api/tai/{muc_id}",
                          headers={"X-Token": cauhinh["token"]},
                          stream=True, timeout=TIMEOUT_TAI) as r:
            if r.status_code in (401, 403):
                return False, "Token không hợp lệ hoặc đã bị thu hồi trên kho."
            if r.status_code != 200:
                return False, f"Kho trả về lỗi HTTP {r.status_code}."
            with open(tam, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        os.replace(tam, duong_dich)
        return True, "Đã tải xong."
    except requests.RequestException as e:
        try:
            os.remove(tam)
        except OSError:
            pass
        return False, f"Lỗi khi tải: {e}"

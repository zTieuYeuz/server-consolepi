# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - Kiem tra chung chi TLS

Xem chi tiet + tinh trang tin cay cua chung chi HTTPS mot giao dien quan
tri (switch/router/iLO/iDRAC). Cac thiet bi nay GAN NHU LUON dung chung chi
tu ky, nen "khong tin cay duoc" la BINH THUONG - cong cu nay khong phai de
bao "sai", ma de nguoi dung THAY RO minh dang tin ai (hay chua tin ai ca),
va phat hien dung khi chung chi da het han that su.

NGUYEN TAC AN TOAN QUAN TRONG NHAT CUA MODULE NAY: khong bao gio duoc hien
banner "hop le" cho mot chung chi CHUA duoc xac thuc. Rat de mac loi la "lay
duoc chung chi thi coi nhu OK" - phai luon phan biet ro "lay duoc de XEM" va
"duoc he thong TIN CAY".

KY THUAT (2 buoc, ca hai deu dung thu vien co san, khong can cai them):
  1. Thu ket noi CHUAN (ssl.create_default_context - kiem tra theo CA store
     he thong + ten mien). Neu thanh cong: chung chi hop le va duoc tin cay.
  2. Neu that bai (SSLCertVerificationError - truong hop THUONG GAP nhat
     voi thiet bi mang), ket noi LAI voi CERT_NONE CHI DE LAY DU LIEU chung
     chi ve xem, KHONG BAO GIO coi day la "hop le". Luu y ky thuat: khi
     verify_mode=CERT_NONE, ham getpeercert() cua module ssl chuan tra ve
     RONG (day la gioi han da biet cua thu vien chuan) - phai lay dang
     nhi phan (getpeercert(binary_form=True)) roi tu phan tich bang thu
     vien `cryptography` (da co san trong du an, dung cho IF/THEN Fernet).
"""
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
import re
import socket
import ssl

from flask import request, render_template_string

from . import nettools_bp


def _phan_tich_cert_tho(der_bytes):
    """Phan tich chung chi dang DER bang cryptography - dung khi CERT_NONE
    lam getpeercert() cua ssl chuan tra ve rong."""
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    return x509.load_der_x509_certificate(der_bytes, default_backend())


def _lay_ten_chung(name):
    """Rut CN tu mot RFC4514 name object cua cryptography, ngan gon de hien."""
    try:
        from cryptography.x509.oid import NameOID
        cn = name.get_attributes_for_oid(NameOID.COMMON_NAME)
        if cn:
            return cn[0].value
    except Exception as _loi:
        _bo_qua(_loi)
    return name.rfc4514_string()


def _cac_ten_thay_the(cert):
    """Lay danh sach Subject Alternative Name (DNS) - dung de kiem tra khop tenmien."""
    try:
        ext = cert.extensions.get_extension_for_class(__import__(
            "cryptography.x509", fromlist=["SubjectAlternativeName"]).SubjectAlternativeName)
        return ext.value.get_values_for_type(
            __import__("cryptography.x509", fromlist=["DNSName"]).DNSName)
    except Exception:
        return []


def kiem_tra_tls(host, port=443, timeout=5):
    """
    Tra ve {"ok", "error", "host", "port", "xac_thuc_duoc": bool,
            "loi_xac_thuc": str|None, "subject": str, "issuer": str,
            "not_before": str, "not_after": str, "ngay_con_lai": int,
            "tu_ky": bool, "khop_ten": bool}
    """
    host = (host or "").strip()
    # Bat dau bang chu/so: tranh truong hop host="-..." bi cong cu khac (neu
    # sau nay co ai goi ham nay roi dua ket qua vao 1 lenh CLI) hieu nham
    # thanh co lenh. Ham nay tu no dung ssl.socket (khong qua subprocess) nen
    # khong co nguy co that ngay bay gio, nhung giu dong quy uoc kiem tra dau
    # vao NHAT QUAN voi cac cong cu khac trong du an la dieu nen lam.
    if not host or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.\-:]{0,254}", host):
        return {"ok": False, "error": "Địa chỉ/hostname không hợp lệ."}
    try:
        port = int(port)
        if not 1 <= port <= 65535:
            raise ValueError
    except (TypeError, ValueError):
        return {"ok": False, "error": "Cổng không hợp lệ."}

    xac_thuc_duoc = False
    loi_xac_thuc = None
    der = None

    # Buoc 1: thu xac thuc CHUAN truoc.
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                der = ssock.getpeercert(binary_form=True)
                xac_thuc_duoc = True
    except ssl.SSLCertVerificationError as e:
        loi_xac_thuc = str(e)
    except (socket.timeout, TimeoutError):
        return {"ok": False, "error": f"Quá thời gian chờ kết nối tới {host}:{port}."}
    except ConnectionRefusedError:
        return {"ok": False, "error": f"Cổng {port} từ chối kết nối - có đúng là cổng HTTPS không?"}
    except socket.gaierror:
        return {"ok": False, "error": f"Không phân giải được địa chỉ '{host}'."}
    except OSError as e:
        return {"ok": False, "error": f"Lỗi kết nối: {e}"}

    # Buoc 2: neu buoc 1 that bai vi ly do XAC THUC (khong phai loi mang),
    # ket noi LAI chi de LAY chung chi ve xem - KHONG bao gio danh dau la
    # da xac thuc.
    if der is None and loi_xac_thuc is not None:
        try:
            ctx2 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx2.check_hostname = False
            ctx2.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with ctx2.wrap_socket(sock, server_hostname=host) as ssock:
                    der = ssock.getpeercert(binary_form=True)
        except Exception as e:
            return {"ok": False, "error": f"Không lấy được chứng chỉ để xem: {e}"}
    elif der is None:
        return {"ok": False, "error": "Không lấy được chứng chỉ (lý do không xác định)."}

    try:
        cert = _phan_tich_cert_tho(der)
    except Exception as e:
        return {"ok": False, "error": f"Không đọc được nội dung chứng chỉ: {e}"}

    subject = _lay_ten_chung(cert.subject)
    issuer = _lay_ten_chung(cert.issuer)
    tu_ky = cert.subject.rfc4514_string() == cert.issuer.rfc4514_string()

    # cryptography >= 42 co not_valid_after_utc (co timezone, dung khuyen
    # nghi). Ban cu hon chi co not_valid_after (naive) - du phong ca hai.
    from datetime import datetime, timezone
    if hasattr(cert, "not_valid_after_utc"):
        het_han = cert.not_valid_after_utc
        bat_dau = cert.not_valid_before_utc
        bay_gio = datetime.now(timezone.utc)
    else:
        het_han = cert.not_valid_after
        bat_dau = cert.not_valid_before
        bay_gio = datetime.utcnow()
    ngay_con_lai = (het_han - bay_gio).days

    ten_thay_the = _cac_ten_thay_the(cert)
    ten_de_so = host.lower()
    khop_ten = (ten_de_so == subject.lower() or
               any(t.lower() == ten_de_so or
                   (t.startswith("*.") and ten_de_so.endswith(t[1:].lower()))
                   for t in ten_thay_the))

    return {
        "ok": True, "error": None, "host": host, "port": port,
        "xac_thuc_duoc": xac_thuc_duoc, "loi_xac_thuc": loi_xac_thuc,
        "subject": subject, "issuer": issuer,
        "not_before": bat_dau.strftime("%Y-%m-%d"), "not_after": het_han.strftime("%Y-%m-%d"),
        "ngay_con_lai": ngay_con_lai, "tu_ky": tu_ky, "khop_ten": khop_ten,
        "ten_thay_the": ten_thay_the,
    }


TLS_TEMPLATE = _taisan.doc("nettools/tls_check.TLS_TEMPLATE.html")


@nettools_bp.route("/nettools/tls-check", methods=["GET", "POST"])
def tls_check_route():
    host = request.form.get("host", "").strip()
    port = request.form.get("port", "443").strip()
    ran = request.method == "POST"
    result = kiem_tra_tls(host, port=port) if ran else None
    return render_template_string(TLS_TEMPLATE, host=host, port=port, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    host = sys.argv[1] if len(sys.argv) > 1 else "github.com"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 443
    print(json.dumps(kiem_tra_tls(host, port=port), indent=2, ensure_ascii=False))

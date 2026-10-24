# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - HA TANG KHOA CONG KHAI (PKI) cho agent, de agent noi chuyen bang mTLS nhu agent cua OpenUEM:
  * CA rieng cua Console System (RSA 2048, 10 nam) - agent GHIM chung (khong tin CA cua he dieu hanh, khong tin ai khac).
  * Chung chi may chu (SAN = moi dia chi IP + ten may cua Console System) cho cong 8443 cua nginx.
  * Chung chi KHACH rieng tung agent (CN=cs-agent-<ma may>, 2 nam): nginx bat buoc co chung chi nay moi cho vao /uem/agent/*.
    Thu hoi = xoa so serial luu trong ban ghi may (nginx van chap nhan chung chi con han, nhung ung dung tu choi vi serial khong khop).
  * Khoa bi mat nginx<->ung dung (X-CS-TLS-Secret): chi nginx cong 8443 biet, de ung dung tin cac header X-CS-Client-* (khong ai
    di qua cong 80 gia mao duoc).
Tat ca nam trong <thu muc du lieu>/pki (0700, root). Khoa CA khong bao gio roi may Console System.
"""
import datetime
import ipaddress
import json
import os
import re
import secrets
import socket
import subprocess

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from . import tk_dulieu as DL

CONG_TLS = 8443                 # cong mac dinh; cong that doc tu cai-dat.json qua cong()
FILE_NGINX = "/etc/nginx/conf.d/console-pi-agent-tls.conf"


def _dir():
    d = os.path.join(DL.DIR, "pki")
    os.makedirs(d, mode=0o700, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def _p(ten):
    return os.path.join(_dir(), ten)


def _ghi(duong, data, mode=0o600):
    tam = duong + ".tmp"
    fd = os.open(tam, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tam, duong)


def cai_dat():
    """{domain, cong}: dia chi cong khai (tuy chon) va cong mTLS (doi duoc de tang bao mat)."""
    try:
        with open(_p("cai-dat.json"), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    cong = d.get("cong")
    return {"domain": str(d.get("domain") or ""), "cong": cong if isinstance(cong, int) and 1024 <= cong <= 65535 else CONG_TLS}


def cong():
    return cai_dat()["cong"]


def luu_cai_dat(domain, cong_moi):
    d = cai_dat()
    if domain is not None:
        d["domain"] = domain
    if cong_moi is not None:
        d["cong"] = cong_moi
    _ghi(_p("cai-dat.json"), json.dumps(d).encode("utf-8"))


def _doc(ten):
    with open(_p(ten), "rb") as f:
        return f.read()


def _khoa_moi():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _pem_khoa(k):
    return k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())


def _ten(cn):
    return x509.Name([x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Console System"), x509.NameAttribute(NameOID.COMMON_NAME, cn)])


def ca():
    """(chung_chi, khoa) cua CA - tao neu chua co."""
    if not (os.path.exists(_p("ca.pem")) and os.path.exists(_p("ca.key"))):
        k = _khoa_moi()
        now = datetime.datetime.now(datetime.timezone.utc)
        c = (x509.CertificateBuilder().subject_name(_ten("Console System CA")).issuer_name(_ten("Console System CA"))
             .public_key(k.public_key()).serial_number(x509.random_serial_number())
             .not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=3650))
             .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
             .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True, content_commitment=False, key_encipherment=False,
                                          data_encipherment=False, key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
             .add_extension(x509.SubjectKeyIdentifier.from_public_key(k.public_key()), critical=False)
             .sign(k, hashes.SHA256()))
        _ghi(_p("ca.key"), _pem_khoa(k))
        _ghi(_p("ca.pem"), c.public_bytes(serialization.Encoding.PEM), 0o644)
    return x509.load_pem_x509_certificate(_doc("ca.pem")), serialization.load_pem_private_key(_doc("ca.key"), None)


def ca_pem():
    ca()
    return _doc("ca.pem")


def ca_sha256():
    """Dau van tay SHA-256 cua CA (hex hoa, khong dau ':') - hien tren giao dien de nguoi quan tri doi chieu."""
    c, _k = ca()
    return c.fingerprint(hashes.SHA256()).hex().upper()


def server_sha256():
    """Dau van tay SHA-256 cua chung chi MAY CHU hien tai (de lenh cai dan vao PowerShell ghim dung chung chi nay)."""
    may_chu()
    return x509.load_pem_x509_certificate(_doc("server.pem")).fingerprint(hashes.SHA256()).hex().upper()


def ips_pi():
    """Moi dia chi IPv4 cua Console System (de dua vao SAN cua chung chi may chu)."""
    ra = set()
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr"], capture_output=True, text=True, timeout=5).stdout
        ra |= set(re.findall(r"inet (\d+\.\d+\.\d+\.\d+)/", out))
    except Exception:
        pass
    try:
        ra |= set(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    ra.add("127.0.0.1")
    return sorted(ra)


def _san_hien_co(c):
    try:
        e = c.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        return {str(i) for i in e.get_values_for_type(x509.IPAddress)}
    except Exception:
        return set()


def may_chu():
    """Dam bao chung chi may chu khop IP hien tai. Tra ve True neu vua tao moi (nginx can nap lai)."""
    ca_c, ca_k = ca()
    ips = set(ips_pi())
    if os.path.exists(_p("server.pem")) and os.path.exists(_p("server.key")):
        c = x509.load_pem_x509_certificate(_doc("server.pem"))
        het = c.not_valid_after_utc - datetime.datetime.now(datetime.timezone.utc)
        if ips <= _san_hien_co(c) and het > datetime.timedelta(days=30):
            return False
    k = _khoa_moi()
    now = datetime.datetime.now(datetime.timezone.utc)
    ten = socket.gethostname() or "console-system"
    san = [x509.IPAddress(ipaddress.ip_address(i)) for i in sorted(ips)] + [x509.DNSName(ten), x509.DNSName("console-system.local")]
    c = (x509.CertificateBuilder().subject_name(_ten(ten)).issuer_name(ca_c.subject).public_key(k.public_key())
         .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=800))
         .add_extension(x509.SubjectAlternativeName(san), critical=False)
         .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
         .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
         .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_c.public_key()), critical=False)
         .sign(ca_k, hashes.SHA256()))
    _ghi(_p("server.key"), _pem_khoa(k))
    _ghi(_p("server.pem"), c.public_bytes(serialization.Encoding.PEM), 0o644)
    ghi_chain()
    return True


def ghi_chain():
    """server-chain.pem = server.pem + ca.pem. PHAI ghi lai moi khi server.pem doi, neu khong khoa va chung chi
    lech nhau va nginx -t hong luc khoi dong lai (loi that 24/10/2026: IP doi -> may_chu() cap lai chung chi nhung
    chain cu con nguyen -> mat dien/khoi dong lai thi ca trang web khong len)."""
    _ghi(_p("server-chain.pem"), _doc("server.pem") + b"\n" + _doc("ca.pem"), 0o644)


def cap_khach(may_id):
    """Cap chung chi KHACH cho 1 agent. Tra ve dict {pfx(bytes), mat_khau, serial(hex thuong), han}. Khoa bi mat chi nam trong PFX gui cho agent."""
    if not re.fullmatch(r"[A-Za-z0-9]{1,32}", may_id or ""):
        raise ValueError("ma may khong hop le")
    ca_c, ca_k = ca()
    k = _khoa_moi()
    now = datetime.datetime.now(datetime.timezone.utc)
    c = (x509.CertificateBuilder().subject_name(_ten("cs-agent-" + may_id)).issuer_name(ca_c.subject).public_key(k.public_key())
         .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=730))
         .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
         .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
         .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_c.public_key()), critical=False)
         .sign(ca_k, hashes.SHA256()))
    mk = secrets.token_urlsafe(18)
    # PKCS#12 kieu cu (3DES + SHA1) de moi ban Windows (10 tro len, Server 2016 tro len) deu nhap duoc; khoa van chi nam trong file nay.
    enc = (serialization.PrivateFormat.PKCS12.encryption_builder().kdf_rounds(2048).key_cert_algorithm(pkcs12.PBES.PBESv1SHA1And3KeyTripleDESCBC)
           .hmac_hash(hashes.SHA1()).build(mk.encode()))
    pfx = pkcs12.serialize_key_and_certificates(("cs-agent-" + may_id).encode(), k, c, [ca_c], enc)
    return {"pfx": pfx, "mat_khau": mk, "serial": format(c.serial_number, "x"), "han": c.not_valid_after_utc.timestamp()}


def bi_mat_nginx():
    p = _p("nginx-secret")
    if not os.path.exists(p):
        _ghi(p, secrets.token_hex(32).encode(), 0o600)
    return _doc("nginx-secret").decode().strip()


def nginx_conf():
    d = _dir()
    bm = bi_mat_nginx()
    may_chu()
    ghi_chain()
    proxy = (f"        proxy_pass http://127.0.0.1:5000;\n        proxy_http_version 1.1;\n        proxy_set_header Host $host;\n"
             f"        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-CS-TLS-Secret \"{bm}\";\n"
             "        proxy_set_header X-CS-Client-Verify $ssl_client_verify;\n        proxy_set_header X-CS-Client-DN $ssl_client_s_dn;\n"
             "        proxy_set_header X-CS-Client-Serial $ssl_client_serial;\n")
    return f"""# Console System - cong mTLS danh RIENG cho agent (mTLS). Tao tu dong boi ui/uem_pki.py - KHONG sua tay.
server {{
    listen {cong()} ssl;
    server_name _;
    ssl_certificate     {d}/server-chain.pem;
    ssl_certificate_key {d}/server.key;
    ssl_client_certificate {d}/ca.pem;
    ssl_verify_client optional;
    ssl_verify_depth 2;
    ssl_protocols TLSv1.2 TLSv1.3;
    client_max_body_size 4g;
    proxy_request_buffering off;
    proxy_buffering off;

    # May Windows tai script cai (chua chung chi khach) - chi can TLS may chu, ma cai dung 1 lan + het han 30 phut
    location ~ ^/uem/agent/cai/[A-Za-z0-9_-]+\\.ps1$ {{
{proxy}    }}

    # Tunnel VNC do agent mo ra (WebSocket) - bat buoc chung chi khach
    location /uem-agent-ws/ {{
        if ($ssl_client_verify != SUCCESS) {{ return 403; }}
        proxy_pass http://127.0.0.1:8895;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-CS-TLS-Secret "{bm}";
        proxy_set_header X-CS-Client-Verify $ssl_client_verify;
        proxy_set_header X-CS-Client-DN $ssl_client_s_dn;
        proxy_set_header X-CS-Client-Serial $ssl_client_serial;
        proxy_read_timeout 7200;
        proxy_send_timeout 7200;
    }}

    # Moi duong khac cua agent - bat buoc chung chi khach hop le
    location /uem/agent/ {{
        if ($ssl_client_verify != SUCCESS) {{ return 403; }}
        proxy_read_timeout 120s;
        proxy_send_timeout 3600s;
{proxy}    }}

    location / {{ return 404; }}
}}
"""


def dang_nghe():
    try:
        s = socket.create_connection(("127.0.0.1", cong()), timeout=2)
        s.close()
        return True
    except OSError:
        return False


def san_sang():
    """True khi nginx da bat cong mTLS (de giao dien cho phep cai agent)."""
    return os.path.exists(FILE_NGINX) and dang_nghe()


def bat_tls():
    """Tao PKI (neu thieu) + ghi cau hinh nginx + nginx -t + nap lai. Loi thi tra ban cu. Tra ve (ok, thong_diep). Can quyen root."""
    try:
        ca()
        may_chu()
        moi = nginx_conf()
    except Exception as e:
        return False, f"Không tạo được khóa/chứng chỉ: {e}"
    cu = None
    try:
        with open(FILE_NGINX, encoding="utf-8") as f:
            cu = f.read()
    except OSError:
        pass
    if cu == moi and dang_nghe():
        return True, "Cổng mTLS của agent đã bật."
    try:
        with open(FILE_NGINX, "w", encoding="utf-8") as f:
            f.write(moi)
        os.chmod(FILE_NGINX, 0o640)
    except OSError as e:
        return False, f"Không ghi được {FILE_NGINX} (cần chạy bằng root): {e}"
    t = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if t.returncode != 0:
        try:
            if cu is None:
                os.remove(FILE_NGINX)
            else:
                with open(FILE_NGINX, "w", encoding="utf-8") as f:
                    f.write(cu)
        except OSError:
            pass
        return False, "Cấu hình nginx mới bị lỗi, đã trả lại bản cũ: " + (t.stderr or t.stdout)[-300:]
    if subprocess.run(["systemctl", "is-active", "--quiet", "nginx"]).returncode != 0:
        return True, f"Đã ghi cấu hình; cổng {cong()} sẽ mở khi nginx chạy."        # vd: dang cai dat/ISO, nginx chua khoi dong
    r = subprocess.run(["systemctl", "reload", "nginx"], capture_output=True, text=True)
    if r.returncode != 0:
        subprocess.run(["nginx", "-s", "reload"], capture_output=True, text=True)
    import time
    for _ in range(10):
        if dang_nghe():
            return True, f"Đã bật cổng mTLS {cong()} cho agent."
        time.sleep(0.5)
    return False, f"Đã nạp nginx nhưng cổng {cong()} chưa mở (cổng bị chiếm?)."


def nap_lai_neu_doi():
    """Goi luc khoi dong: IP Console System doi -> cap lai chung chi may chu va nap lai nginx."""
    try:
        if not os.path.exists(FILE_NGINX):
            return
        may_chu()
        ghi_chain()        # luon dong bo, ke ca khi may_chu() khong cap lai (chain hong do mat dien/loi cu)
        t = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
        if t.returncode == 0:
            subprocess.run(["systemctl", "reload-or-restart", "nginx"], capture_output=True, text=True)    # nginx dang hong sau khi khoi dong -> tu bat lai
        else:
            # Cong mTLS hong KHONG duoc keo sap trang web chinh: dua file cau hinh ra ngoai de nginx khoi dong duoc,
            # nguoi dung bat lai cong agent trong giao dien (bat_tls ghi lai file).
            os.replace(FILE_NGINX, FILE_NGINX + ".hong")
            if subprocess.run(["nginx", "-t"], capture_output=True, text=True).returncode == 0:
                subprocess.run(["systemctl", "restart", "nginx"], capture_output=True, text=True)
    except Exception:
        pass


def doi_cong(cong_moi, domain):
    """Luu domain + doi cong mTLS: ghi nginx, kiem tra, nap lai; loi thi tra cai dat cu. Tra ve (ok, thong_diep)."""
    cu = cai_dat()
    if cong_moi != cu["cong"]:
        if not (1024 <= cong_moi <= 65535) or cong_moi in (5000, 8880, 8895):
            return False, "Cổng phải từ 1024 đến 65535 và không trùng cổng nội bộ của Console System (5000, 8880, 8895)."
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sk.bind(("0.0.0.0", cong_moi))
        except OSError:
            return False, f"Cổng {cong_moi} đang được chương trình khác dùng."
        finally:
            sk.close()
    luu_cai_dat(domain, cong_moi)
    if cong_moi == cu["cong"] or not os.path.exists(FILE_NGINX):
        return True, "Đã lưu."
    ok, tb = bat_tls()
    if not ok:
        luu_cai_dat(cu["domain"], cu["cong"])
        bat_tls()
        return False, tb + " Đã trả lại cổng cũ."
    return True, f"Đã đổi cổng mTLS sang {cong_moi}. Agent đã cài trước đó vẫn nối cổng cũ, cần cài lại bằng file mới."

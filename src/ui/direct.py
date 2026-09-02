"""
Console Pi - Che do cam thang thiet bi (iLO / iDRAC / switch quan ly).

Tinh huong: ra hien truong, may chu tat lim, chi con cong quan ly iLO. Khong
co switch, khong co DHCP, khong co gi ca - chi co soi day mang va con Pi.

Bat che do nay thi Pi tro thanh mot "mang mini" tren cong eth0:
  - Pi lay dia chi tinh 192.168.99.1/24
  - Chay DHCP nho cap 192.168.99.50-99 cho thiet bi vua cam
  - Quet ARP tim thiet bi, tra ten hang tu 3 byte dau cua MAC
  - Do them mot so dai IP tinh pho bien cua iLO khi no khong xin DHCP

CANH BAO quan trong: bat che do nay se cat DHCP tren eth0. Neu nguoi dung
dang truy cap dashboard QUA chinh cong eth0 do thi ho se mat ket noi - trang
web phai canh bao truoc, giong nut ngat WiFi.
"""
import ipaddress
import os
import re
import subprocess

STATE_FLAG = "/run/console-pi-direct.flag"
DNSMASQ_CONF = "/etc/dnsmasq-direct.conf"
IFACE = "eth0"
PI_IP = "192.168.99.1"
PI_CIDR = f"{PI_IP}/24"
NM_CONN = "netplan-eth0"

# Dai IP tinh hay gap khi iLO/iDRAC duoc dat cung, khong xin DHCP.
# Quet them cac dai nay de khong bo sot.
DAI_TINH_PHO_BIEN = ["192.168.1.0/24", "192.168.0.0/24", "16.1.0.0/24"]

# 3 byte dau MAC -> hang. Danh sach ngan, chi nhung hang hay gap o cong quan ly.
OUI = {
    "00:17:a4": "HPE (iLO)",    "00:1f:29": "HPE (iLO)",
    "9c:8e:99": "HPE (iLO)",    "b4:b5:2f": "HPE (iLO)",
    "3c:d9:2b": "HPE (iLO)",    "80:c1:6e": "HPE (iLO)",
    "00:14:22": "Dell (iDRAC)", "b8:2a:72": "Dell (iDRAC)",
    "18:66:da": "Dell (iDRAC)", "f8:bc:12": "Dell (iDRAC)",
    "00:25:90": "Supermicro (IPMI)", "0c:c4:7a": "Supermicro (IPMI)",
    "e4:1f:13": "IBM/Lenovo (IMM)",  "00:1a:64": "IBM/Lenovo (IMM)",
    "00:0c:29": "VMware",
    "00:1b:0d": "Cisco",        "00:1e:14": "Cisco",  "00:24:14": "Cisco",
    "b8:27:eb": "Raspberry Pi", "dc:a6:32": "Raspberry Pi",
    "e4:5f:01": "Raspberry Pi",
}


def dang_bat():
    return os.path.exists(STATE_FLAG)


def _sh(cmd, timeout=25):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def hang_cua_mac(mac):
    return OUI.get((mac or "").lower()[:8], "")


def bat_che_do():
    """eth0 -> IP tinh + DHCP server nho. Tra ve (ok, thong bao)."""
    if dang_bat():
        return True, "Che do cam thang dang bat san."

    # Tach eth0 khoi NetworkManager de no khong doi lai DHCP ngay sau lung
    _sh(["nmcli", "device", "set", IFACE, "managed", "no"])
    _sh(["ip", "addr", "flush", "dev", IFACE])
    ok, out = _sh(["ip", "addr", "add", PI_CIDR, "dev", IFACE])
    if not ok and "File exists" not in out:
        _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
        return False, f"Khong dat duoc IP tinh cho {IFACE}: {out[:120]}"
    _sh(["ip", "link", "set", IFACE, "up"])

    try:
        with open(DNSMASQ_CONF, "w") as f:
            f.write(
                f"# Console Pi - DHCP cho che do cam thang thiet bi.\n"
                f"# Chi phuc vu {IFACE}, khong dung chung voi dnsmasq cua AP hay PAN.\n"
                f"interface={IFACE}\n"
                f"bind-interfaces\n"
                f"except-interface=lo\n"
                f"dhcp-range=192.168.99.50,192.168.99.99,255.255.255.0,12h\n"
                f"dhcp-option=3,{PI_IP}\n"
                f"dhcp-option=6,{PI_IP}\n"
                f"port=0\n"          # khong lam DNS server, chi DHCP
                f"log-dhcp\n"
            )
    except OSError as e:
        return False, f"Khong ghi duoc cau hinh DHCP: {e}"

    ok, out = _sh(["systemctl", "start", "dnsmasq-direct"])
    if not ok:
        return False, f"Khong bat duoc DHCP: {out[:150]}"

    open(STATE_FLAG, "w").close()
    return True, (f"Da bat che do cam thang. Pi la {PI_IP}, se cap IP "
                  f"192.168.99.50-99 cho thiet bi cam vao cong LAN. "
                  f"Cam day roi bam Quet - thiet bi thuong mat 15-30 giay de len.")


def tat_che_do():
    if not dang_bat():
        return True, "Che do cam thang von da tat."
    _sh(["systemctl", "stop", "dnsmasq-direct"])
    _sh(["ip", "addr", "flush", "dev", IFACE])
    _sh(["nmcli", "device", "set", IFACE, "managed", "yes"])
    _sh(["nmcli", "connection", "up", NM_CONN], timeout=30)
    try:
        os.remove(STATE_FLAG)
    except OSError:
        pass
    return True, f"Da tra {IFACE} ve che do DHCP binh thuong."


def quet_thiet_bi(them_dai_tinh=False, dai_tu_nhap=""):
    """
    Quet ARP tren eth0. Tra ve danh sach {ip, mac, hang, nguon}.
    ARP hoat dong o lop 2 nen thay duoc ca thiet bi dat IP tinh khac dai.
    """
    thay = {}

    def _quet(args, nguon):
        ok, out = _sh(["arp-scan", "--interface", IFACE, "--retry=2"] + args, timeout=90)
        if not ok:
            return
        for line in out.splitlines():
            m = re.match(r"^(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]{17})", line)
            if m:
                ip, mac = m.group(1), m.group(2).lower()
                thay.setdefault(mac, {"ip": ip, "mac": mac,
                                      "hang": hang_cua_mac(mac), "nguon": nguon})

    _quet(["--localnet"], "dai cua Pi")

    # Dai do nguoi dung tu go - kiem tra ky truoc khi dua vao dong lenh
    if dai_tu_nhap:
        try:
            mang = ipaddress.ip_network(dai_tu_nhap.strip(), strict=False)
            if mang.version == 4 and mang.num_addresses <= 1024:
                _quet([str(mang)], f"dai tu nhap {mang}")
        except ValueError:
            pass

    if them_dai_tinh:
        for dai in DAI_TINH_PHO_BIEN:
            _quet([dai], f"do dai tinh {dai}")

    # Them ca nhung gi dnsmasq da cap (thiet bi co the khong tra loi ARP quet)
    try:
        with open("/var/lib/misc/dnsmasq.leases") as f:
            for line in f:
                p = line.split()
                if len(p) >= 4 and p[2].startswith("192.168.99."):
                    mac = p[1].lower()
                    thay.setdefault(mac, {"ip": p[2], "mac": mac,
                                          "hang": hang_cua_mac(mac),
                                          "nguon": "DHCP cua Pi"})
                    if p[3] != "*":
                        thay[mac]["ten"] = p[3]
    except OSError:
        pass

    ds = sorted(thay.values(), key=lambda d: ipaddress.ip_address(d["ip"]))
    return ds


def cong_web_mo(ip):
    """Thiet bi quan ly co mo cong web nao? Tra ve danh sach cong."""
    ok, out = _sh(["nmap", "-Pn", "--host-timeout", "20s", "-p",
                   "80,443,8080,17988,17990,5900,623", "-oG", "-", ip], timeout=40)
    if not ok:
        return []
    m = re.search(r"Ports:\s*(.+)", out)
    if not m:
        return []
    cong = []
    for phan in m.group(1).split(","):
        pm = re.match(r"\s*(\d+)/open", phan)
        if pm:
            cong.append(int(pm.group(1)))
    return cong


# =============================================================== giao dien web
def register_direct(app):
    from flask import request
    from .layout import render_page
    from .home import _esc

    def khach_qua_eth0():
        """Nguoi dung co dang truy cap qua chinh cong LAN sap bi doi khong?"""
        ip = request.headers.get("X-Forwarded-For",
                                 request.remote_addr or "").split(",")[0].strip()
        ok, out = _sh(["ip", "-4", "-o", "addr", "show", IFACE], timeout=5)
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", out or "")
        if not m or not ip:
            return False
        try:
            net = ipaddress.ip_network(f"{m.group(1)}/{m.group(2)}", strict=False)
            return ipaddress.ip_address(ip) in net
        except ValueError:
            return False

    def page(msg="", ok=True, ds=None):
        bat = dang_bat()
        msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

        canh_bao = ""
        if not bat and khach_qua_eth0():
            canh_bao = ('<div class="msg warn">⚠️ Ban dang truy cap QUA chinh cong LAN nay. '
                        'Bat che do cam thang se doi IP cua cong do va lam mat ket noi cua ban. '
                        'Hay vao bang WiFi hoac man hinh gan tren Pi truoc.</div>')

        # Khoi quet dung duoc o CA HAI che do: cam thang vao iLO, hay cam vao
        # mang co san DHCP roi tim thiet bi - deu la viec thuong lam.
        quet_html = """
        <div class="card">
          <div class="row" style="gap:10px;flex-wrap:wrap;">
            <form method="POST" action="/direct/quet">
              <button type="submit" data-busy="Dang quet, toi 30 giay...">🔍 Quet dai hien tai</button>
            </form>
            <form method="POST" action="/direct/quet">
              <input type="hidden" name="rong" value="1">
              <button type="submit" class="gray" data-busy="Dang quet rong, toi 2 phut...">
                🔎 Quet rong (them dai IP tinh)</button>
            </form>
          </div>
          <form method="POST" action="/direct/quet" style="margin-top:13px;">
            <label>Hoac quet mot dai cu the (khi biet truoc IP cua iLO)</label>
            <div class="row" style="gap:9px;">
              <input type="text" name="dai" placeholder="vi du 192.168.1.0/24"
                     style="max-width:250px;">
              <button type="submit" class="gray" data-busy="Dang quet...">Quet dai nay</button>
            </div>
          </form>
        </div>"""

        rows = ""
        for d in (ds or []):
            cong = d.get("cong", [])
            lien_ket = ""
            for c in cong:
                giao_thuc = "https" if c in (443, 17990) else "http"
                lien_ket += (f'<a class="btn small" target="_blank" rel="noopener" '
                             f'href="{giao_thuc}://{_esc(d["ip"])}:{c}">Mo :{c}</a> ')
            rows += f"""
            <tr>
              <td><code>{_esc(d['ip'])}</code>
                  {f"<br><small style='color:#8b93a1;'>{_esc(d['ten'])}</small>" if d.get('ten') else ''}</td>
              <td><code style="font-size:12px;">{_esc(d['mac'])}</code></td>
              <td>{_esc(d['hang']) or '<span style="color:#8b93a1;">khong ro hang</span>'}</td>
              <td style="color:#8b93a1;font-size:13px;">{_esc(d['nguon'])}</td>
              <td>{lien_ket or '<span style="color:#8b93a1;">chua do cong</span>'}</td>
            </tr>"""

        if bat:
            dieu_khien = f"""
            <div class="msg ok">🟢 Dang bat. Pi la <code>{PI_IP}</code> tren cong LAN,
            cap IP <code>192.168.99.50-99</code>.</div>
            <div class="row" style="gap:10px;margin-top:12px;flex-wrap:wrap;">
              <form method="POST" action="/direct/tat">
                <button type="submit" class="red" data-busy="Dang tra ve DHCP...">⏏ Tat che do</button>
              </form>
            </div>"""
        else:
            dieu_khien = f"""
            {canh_bao}
            <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
              Cong LAN dang o che do binh thuong (xin DHCP). Neu noi day vao mang
              da co san DHCP thi khong can bat che do nay - quet luon o duoi.</p>
            <form method="POST" action="/direct/bat"
                  onsubmit="return confirm('Bat che do cam thang?\\n\\nCong LAN se doi sang {PI_IP} va ngung xin DHCP.');">
              <button type="submit" data-busy="Dang chuyen cong LAN...">▶ Bat che do cam thang</button>
            </form>"""



        body = f"""
        {msg_html}
        <div class="card">
          <h3>Cach dung</h3>
          <ol style="margin:0;padding-left:19px;line-height:1.75;">
            <li>Cam day mang tu Pi thang sang cong quan ly (iLO / iDRAC / IPMI) hoac switch</li>
            <li>Bam <strong>Bat che do cam thang</strong> - Pi tro thanh DHCP server nho</li>
            <li>Doi 15-30 giay roi bam <strong>Quet thiet bi</strong></li>
            <li>Bam nut <strong>Mo</strong> de vao giao dien web cua thiet bi</li>
          </ol>
          <p style="color:#8b93a1;font-size:13px;margin:11px 0 0;">
            Thiet bi dat IP tinh khong xin DHCP thi dung <strong>Quet rong</strong> -
            no do them cac dai hay gap. Quet ARP o lop 2 nen van thay duoc thiet bi
            khac dai IP.</p>
        </div>

        <h2>Dieu khien</h2>
        <div class="card">{dieu_khien}</div>

        <h2>Tim thiet bi</h2>
        {quet_html}

        {'<h2>Thiet bi tim thay (' + str(len(ds)) + ')</h2>' if ds is not None else ''}
        {'''<table>
          <tr><th style="width:150px;">Dia chi IP</th><th style="width:160px;">MAC</th>
              <th style="width:170px;">Hang</th><th style="width:150px;">Tim thay qua</th>
              <th>Giao dien web</th></tr>''' + rows + '</table>' if ds else ''}
        {'<p style="color:#8b93a1;">Khong thay thiet bi nao. Kiem tra day da cam chua, den cong LAN co sang khong, va thiet bi da khoi dong xong chua (iLO mat 30-60 giay).</p>' if ds is not None and not ds else ''}"""

        return render_page(body, active="/direct", title="Cam thang thiet bi",
                           subtitle="Vao iLO / iDRAC / IPMI khi khong co mang san")

    @app.route("/direct")
    def direct_page():
        return page()

    @app.route("/direct/bat", methods=["POST"])
    def direct_on():
        ok_b, msg = bat_che_do()
        return page(msg=msg, ok=ok_b)

    @app.route("/direct/tat", methods=["POST"])
    def direct_off():
        ok_t, msg = tat_che_do()
        return page(msg=msg, ok=ok_t)

    @app.route("/direct/quet", methods=["POST"])
    def direct_scan():
        rong = request.form.get("rong") == "1"
        dai = request.form.get("dai", "")
        ds = quet_thiet_bi(them_dai_tinh=rong, dai_tu_nhap=dai)
        # Chi do cong cho toi da 6 thiet bi - nmap cham, quet het thi cho lau
        for d in ds[:6]:
            d["cong"] = cong_web_mo(d["ip"])
        return page(ds=ds, msg=f"Quet xong, thay {len(ds)} thiet bi.", ok=True)

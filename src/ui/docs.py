"""
Console Pi - Trang Tai lieu trong dashboard

Muc dich: khi thiet bi mang di hien truong, khong co internet va khong nho
duoc lenh, van tra cuu duoc ngay tren man hinh. Noi dung gom: kien truc,
vi tri file, lenh bao tri, va cac su co da tung gap kem cach sua.
"""
from .layout import render_page

SECTIONS = [
    ("kientruc", "🏗️ Kien truc he thong", """
<pre>Trinh duyet ──> nginx :80 ──┬──> Flask 127.0.0.1:5000    (giao dien)
                            ├──> ttyd 127.0.0.1:8010     (Terminal local)
                            ├──> ttyd 127.0.0.1:8011     (Terminal SSH)
                            └──> ttyd 127.0.0.1:800x     (Console serial)</pre>
<p><strong>Vi sao co nginx:</strong> truoc day terminal chay o cong rieng va tu bao ve
bang mat khau HTTP co ban. Nhung trinh duyet <strong>cam iframe khac origin hien hop
thoai nhap mat khau</strong> (chong lua dao), nen khung terminal luon bao loi. Dua tat ca
qua nginx cong 80 thi moi thu cung origin, va terminal dung luon phien dang nhap cua
dashboard - khong con mat khau rieng.</p>
<p><strong>Cac ttyd chi lang nghe 127.0.0.1</strong> nen khong the vao thang tu mang.
Moi duong vao deu qua nginx va bi kiem tra dang nhap truoc (<code>auth_request</code>).</p>
<table>
<tr><th style="width:210px;">Duong dan</th><th>Di toi</th></tr>
<tr><td><code>/</code></td><td>Flask - toan bo giao dien</td></tr>
<tr><td><code>/term-local/</code></td><td>Terminal local (tmux <code>consolepi-local</code>)</td></tr>
<tr><td><code>/term-ssh/</code></td><td>Terminal SSH (tmux <code>consolepi-ssh</code>)</td></tr>
<tr><td><code>/term-console/ttyUSB0/</code></td><td>Console serial (tmux <code>console-ttyUSB0</code>)</td></tr>
<tr><td><code>/_auth</code></td><td>nginx hoi Flask: phien nay da dang nhap chua</td></tr>
</table>"""),

    ("dangnhap", "🔑 Dang nhap va bao mat", """
<p>Dang nhap bang <strong>tai khoan Linux cua chinh Pi</strong> (vi du
<code>administrator</code>) qua PAM. Khong co tai khoan rieng, khong luu mat khau
tren dashboard.</p>
<div class="msg info"><strong>Ngoai le co y:</strong> truy cap tu <strong>chinh man hinh
gan tren Pi</strong> (127.0.0.1) thi KHONG hoi dang nhap - de bat may len la dung duoc ngay,
va vi go mat khau tren man cam ung rat bat tien.
<br><br>
Danh doi: ai cham duoc man hinh do thi vao duoc ca terminal quyen root. Chap nhan duoc
vi nguoi do da dung truoc mat thiet bi - luc ay ho rut duoc ca the nho ra doc.
<strong>Truy cap tu mang van phai dang nhap binh thuong.</strong>
<br><br>
Muon that chat: them <code>"local_screen_no_login": false</code> vao
<code>/opt/console-pi/config.json</code>.</div>
<div class="msg warn"><strong>Luu y:</strong> dashboard chay HTTP khong ma hoa. Trong mang
noi bo hoac qua AP ConsolePi thi chap nhan duoc. Neu mo ra internet thi mat khau Linux se
truyen dang ro - luc do can them HTTPS hoac chi vao qua VPN.</div>"""),

    ("vitri", "📁 Vi tri cac file quan trong", """
<table>
<tr><th style="width:340px;">Duong dan</th><th>Noi dung</th></tr>
<tr><td><code>/opt/console-pi/app.py</code></td><td>Diem khoi dong, chi lap rap cac phan</td></tr>
<tr><td><code>/opt/console-pi/ui/</code></td><td>Giao dien: Tong quan, WiFi, Bluetooth, Terminal, SSH, Thu vien, Cai dat, Tai lieu</td></tr>
<tr><td><code>/opt/console-pi/nettools/</code></td><td>9 cong cu chan doan mang</td></tr>
<tr><td><code>/opt/console-pi/scripts/</code></td><td>Script he thong (wifi-fallback, ttyd, kiosk, terminal)</td></tr>
<tr><td><code>/opt/console-pi/config.json</code></td><td>Cau hinh (chmod 600 - chua thong tin nhay cam)</td></tr>
<tr><td><code>/opt/console-pi/screen-rotation</code></td><td>Huong man hinh (tach rieng vi kiosk chay quyen user, khong doc duoc config.json)</td></tr>
<tr><td><code>/opt/console-pi/command-library.json</code></td><td><strong>Thu vien lenh cua ban</strong></td></tr>
<tr><td><code>/opt/console-pi/port-names.json</code></td><td>Ten goi nho cua cac cong console</td></tr>
<tr><td><code>/opt/console-pi/nettools/ifthen-rules.json</code></td><td>Rule IF/THEN</td></tr>
<tr><td><code>/etc/wpa_supplicant/wpa_supplicant-wlan0.conf</code></td><td><strong>Danh sach WiFi da luu</strong></td></tr>
<tr><td><code>/etc/hostapd/hostapd.conf</code></td><td>Cau hinh phat WiFi "ConsolePi" (SSID, mat khau)</td></tr>
<tr><td><code>/etc/dnsmasq.conf</code></td><td>Cap IP cho AP (dai 192.168.50.x)</td></tr>
<tr><td><code>/etc/dnsmasq-bt.conf</code></td><td>Cap IP cho Bluetooth PAN (192.168.60.x)</td></tr>
<tr><td><code>/etc/systemd/network/12-wlan0.network</code></td><td>Co <code>KeepConfiguration=yes</code> - RAT QUAN TRONG, xem muc su co</td></tr>
<tr><td><code>/etc/nginx/sites-available/console-pi.conf</code></td><td>Cau hinh cong trung gian</td></tr>
<tr><td><code>/var/log/console-pi-fallback.log</code></td><td>Nhat ky tu chuyen WiFi/AP</td></tr>
<tr><td><code>/var/log/console-pi-netmiko.log</code></td><td>Nhat ky moi lan chay lenh len thiet bi mang</td></tr>
</table>
<div class="msg ok">Cac file <strong>in dam</strong> duoc GIU NGUYEN khi cai de ban moi.</div>"""),

    ("wifi", "📶 Quan ly WiFi va AP", """
<pre>* Xem WiFi da luu
sudo cat /etc/wpa_supplicant/wpa_supplicant-wlan0.conf

* Them WiFi bang tay (them vao cuoi file)
  network={
      ssid="TEN_WIFI"
      psk="MAT_KHAU"
  }

* Ep quet lai va ket noi ngay
sudo /opt/console-pi/scripts/wifi-fallback.sh

* Xem dang o che do nao
iw dev wlan0 info

* Xem nhat ky chuyen mang
sudo tail -20 /var/log/console-pi-fallback.log

* Ep phat AP va KHOA (khong tu chuyen ve WiFi)
sudo touch /opt/console-pi/force-ap.flag
* Go khoa
sudo rm /opt/console-pi/force-ap.flag

* Doi SSID / mat khau AP
sudo nano /etc/hostapd/hostapd.conf && sudo systemctl restart hostapd</pre>
<div class="msg warn"><strong>Canh bao:</strong> file wpa_supplicant co
<code>update_config=1</code> nghia la wpa_supplicant duoc phep TU GHI DE len no.
Chay <code>wpa_supplicant</code> thu cong sai cach co the lam MAT het WiFi da luu.
Khoi phuc khi dang ket noi: <code>sudo wpa_cli -i wlan0 save_config</code></div>"""),

    ("terminal", "⌨️ Terminal, SSH va Thu vien lenh", """
<p>Ca 3 khung terminal deu chay trong <strong>tmux</strong>, nen:</p>
<ul>
<li>Phien khong mat khi dong trinh duyet giua chung</li>
<li>Dan duoc lenh tu Thu vien vao terminal (qua <code>tmux send-keys</code>)</li>
<li>Ban phim ao tren man hinh cam ung go duoc vao terminal</li>
</ul>
<pre>* Xem cac phien dang chay
sudo tmux ls

* Vao thang 1 phien tu dong lenh (khong qua web)
sudo tmux attach -t consolepi-local
sudo tmux attach -t console-ttyUSB0

* Thoat khoi tmux ma KHONG dong phien: bam Ctrl+B roi bam D

* Dan lenh vao phien tu dong lenh
sudo tmux send-keys -t consolepi-local "show version" Enter</pre>
<p><strong>Thu vien lenh:</strong> luu tai
<code>/opt/console-pi/command-library.json</code>. Nut <em>Gui vao Terminal</em> dan lenh
vao nhung <strong>khong tu bam Enter</strong> - ban xem lai roi tu chay.
Nut <em>Dung o tab SSH</em> chep sang tab SSH de sua IP/ten truoc khi chay hang loat.</p>"""),

    ("console", "🔌 Cong console (RS232)", """
<pre>* Xem cong dang cam
ls -l /dev/ttyUSB*

* Kiem tra dich vu cua tung cong
systemctl status console-pi-ttyd@ttyUSB0

* Khoi dong lai 1 cong
sudo systemctl restart console-pi-ttyd@ttyUSB0

* Doi toc do baud (mac dinh 9600)
sudo nano /opt/console-pi/scripts/ttyd-one.sh
sudo systemctl restart console-pi-ttyd@ttyUSB0</pre>
<p>Cong <code>ttyUSB0</code> &rarr; duong dan <code>/term-console/ttyUSB0/</code>,
<code>ttyUSB1</code> &rarr; <code>/term-console/ttyUSB1/</code>. Cam them cap la
tu nhan (dich vu bam theo <code>dev-ttyUSB*.device</code> cua udev).</p>
<div class="msg warn">Chi duoc <strong>1 tien trinh</strong> giu moi cong serial. Neu
console bi dinh/rot ky tu, kiem tra co ai giu trung khong:
<code>sudo lsof /dev/ttyUSB0</code></div>"""),

    ("bluetooth", "🔵 Bluetooth", """
<p>Trang Bluetooth lam 2 viec: <strong>ghep ban phim/chuot</strong> (khi man hinh cam ung
kho go) va <strong>ket noi mang PAN du phong</strong>.</p>
<pre>* Xem thiet bi da ghep cap
bluetoothctl devices

* Ghep bang tay
bluetoothctl scan on          (doi thay thiet bi)
bluetoothctl pair AA:BB:CC:DD:EE:FF
bluetoothctl trust AA:BB:CC:DD:EE:FF
bluetoothctl connect AA:BB:CC:DD:EE:FF

* Xoa 1 thiet bi (khi khong ket noi lai duoc)
bluetoothctl remove AA:BB:CC:DD:EE:FF

* Khoi dong lai toan bo (bt-agent va bt-nap tu theo)
sudo systemctl restart bluetooth</pre>
<p>Ket noi mang qua Bluetooth: ghep may voi ten <strong>ConsolePi</strong> roi vao
<code>http://192.168.60.1</code>. Tren Windows: mo <code>devicesandprinters</code>,
chuot phai ConsolePi &rarr; <em>Connect using</em> &rarr; <em>Access point</em>.</p>
<div class="msg warn">Neu ghep cap that bai voi loi
<code>br-connection-profile-unavailable</code>: xoa ghep cap o CA HAI phia roi ghep lai.
Tren Windows nho tat/bat lai Bluetooth de giai phong trang thai ket.</div>"""),

    ("manhinh", "🖥️ Man hinh cam ung", """
<pre>* Xoay man hinh: dung nut trong tab Cai dat (tu chinh ca toa do cham)

* Xoay bang tay
echo 180 | sudo tee /opt/console-pi/screen-rotation
sudo systemctl restart console-pi-kiosk

* Tat kiosk, tra lai man hinh dong lenh
sudo systemctl disable --now console-pi-kiosk
sudo systemctl start getty@tty1

* Bat lai kiosk
sudo systemctl enable --now console-pi-kiosk

* Kiem tra man hinh co duoc nhan khong
cat /sys/class/drm/card*-HDMI*/status

* Kiem tra cam ung co gui du lieu khong (cham trong luc chay)
sudo libinput debug-events</pre>
<p><strong>Ban phim ao:</strong> chi hien khi mo tu <strong>chinh man hinh Pi</strong>
(127.0.0.1). Vao tu laptop/iPad thi khong hien - vi may do da co ban phim rieng.
Nut tron goc phai duoi de bat/tat.</p>"""),

    ("services", "⚙️ Dich vu he thong", """
<table>
<tr><th style="width:250px;">Dich vu</th><th>Chuc nang</th></tr>
<tr><td><code>nginx</code></td><td>Cong trung gian - moi truy cap deu qua day</td></tr>
<tr><td><code>console-pi-dashboard</code></td><td>Giao dien web (Flask, 127.0.0.1:5000)</td></tr>
<tr><td><code>console-pi-ttyd@ttyUSB0</code></td><td>Console cho tung cong serial</td></tr>
<tr><td><code>console-pi-term-local</code></td><td>Terminal local</td></tr>
<tr><td><code>console-pi-term-ssh</code></td><td>Terminal cho SSH</td></tr>
<tr><td><code>console-pi-kiosk</code></td><td>Hien dashboard len man hinh gan tren Pi</td></tr>
<tr><td><code>wifi-fallback.timer</code></td><td>Cu 2 phut kiem tra, tu chuyen WiFi/AP</td></tr>
<tr><td><code>bt-pan0 / bt-agent / bt-nap</code></td><td>Bluetooth PAN</td></tr>
<tr><td><code>dnsmasq / dnsmasq-bt</code></td><td>Cap IP cho AP va Bluetooth</td></tr>
<tr><td><code>lldpd</code></td><td>Nhan LLDP/CDP tu switch</td></tr>
</table>
<pre>* Xem trang thai tat ca
systemctl is-active nginx console-pi-dashboard console-pi-term-local \\
  console-pi-term-ssh console-pi-kiosk lldpd bluetooth

* Xem nhat ky khi co loi
sudo journalctl -u console-pi-dashboard -n 50

* Kiem tra cu phap TRUOC khi restart (tranh restart xong bi sap)
python3 -m py_compile /opt/console-pi/app.py /opt/console-pi/ui/*.py \\
    /opt/console-pi/nettools/*.py
sudo nginx -t

* Khoi dong lai
sudo systemctl restart console-pi-dashboard
sudo systemctl reload nginx</pre>"""),

    ("update", "⬆️ Cap nhat / cai lai", """
<pre>* Cai lai hoac cap nhat (chay lai duoc nhieu lan, khong mat cau hinh)
curl -fsSL https://raw.githubusercontent.com/USER/consolepi-toolkit/main/install.sh | sudo bash

* May KHONG co man hinh (bo qua kiosk, tiet kiem ~500MB)
curl -fsSL .../install.sh | sudo bash -s -- --no-screen

* Cai tu thu muc co san (khong can mang)
sudo bash install.sh --local /duong/dan/consolepi-toolkit

* Go cai dat
sudo /opt/console-pi/uninstall.sh              (giu cau hinh)
sudo /opt/console-pi/uninstall.sh --purge      (xoa sach)</pre>
<div class="msg ok">Khi cai de ban moi, cac file sau <strong>duoc giu nguyen</strong>:
WiFi da luu, ten cong console, thu vien lenh, rule IF/THEN, cau hinh AP,
huong man hinh.</div>"""),

    ("suco", "🔧 Su co da tung gap va cach sua", """
<table>
<tr><th style="width:290px;">Trieu chung</th><th>Nguyen nhan &amp; cach sua</th></tr>

<tr><td><strong>Khong vao duoc dashboard</strong></td>
    <td>Cam day LAN thang vao laptop, doi 30-60s roi vao
    <code>http://&lt;hostname&gt;.local</code>. Kiem tra:
    <code>sudo systemctl status nginx console-pi-dashboard</code></td></tr>

<tr><td><strong>Console dinh/rot ky tu</strong></td>
    <td>Co nhieu tien trinh cung giu 1 cong serial.
    <code>sudo lsof /dev/ttyUSB0</code> roi <code>kill</code> cai thua.</td></tr>

<tr><td><strong>Bat AP xong mat IP 192.168.50.1</strong></td>
    <td>systemd-networkd "reconfigure" va xoa mat IP tinh do script tu gan.
    Kiem tra <code>/etc/systemd/network/12-wlan0.network</code> phai co dong
    <code>KeepConfiguration=yes</code>.</td></tr>

<tr><td><strong>Man hinh: cham khong trung nut, vuot nguoc chieu</strong></td>
    <td>Toa do cham va huong man hinh khong khop. cage/wlroots
    <strong>khong tu</strong> xoay toa do cham. Hai cho phai cung huong:
    <code>/opt/console-pi/screen-rotation</code> va ma tran trong
    <code>/etc/udev/rules.d/99-consolepi-touch.rules</code>.
    Dung nut xoay trong tab Cai dat de no tu dong bo ca hai.
    <br><br><strong>Luu y:</strong> cage chi doc cau hinh thiet bi luc MO thiet bi -
    doi xong phai <code>sudo systemctl restart console-pi-kiosk</code> moi co hieu luc.
    De nham tuong da sua xong trong khi chua.</td></tr>

<tr><td><strong>Cham duoc nhung khong bam duoc gi</strong></td>
    <td>Neu xay ra khi ban phim ao dang mo: loi cu do
    <code>preventDefault()</code> tren <code>touchstart</code> chan luon su kien
    click. Da sua bang <code>pointerdown</code>. Neu tai lai trang van con,
    xoa cache trinh duyet.</td></tr>

<tr><td><strong>Icon hien o vuong tren man hinh Pi</strong></td>
    <td>Thieu font emoji (Pi OS Lite khong co san):
    <code>sudo apt install fonts-noto-color-emoji</code> roi restart kiosk.</td></tr>

<tr><td><strong>Khung terminal bao loi khong tai duoc</strong></td>
    <td>Kiem tra nginx: <code>sudo nginx -t</code> va
    <code>systemctl status nginx console-pi-term-local</code>.
    ttyd chi lang nghe 127.0.0.1 nen KHONG vao thang cong 8010 duoc - phai qua
    nginx o <code>/term-local/</code>.</td></tr>

<tr><td><strong>Dang nhap bao "thieu thu vien PAM"</strong></td>
    <td><code>sudo apt install python3-pam</code>. Luu y goi Debian cung cap module
    ten <code>PAM</code> (chu hoa), khac voi <code>pam</code> tren PyPI - code ho tro
    ca hai.</td></tr>

<tr><td><strong>Bam "Mo Console" bi ket tren man hinh Pi</strong></td>
    <td>Da sua: console gio nhung trong dashboard, van con thanh dieu huong.
    Tren man hinh tai cho, moi lien ket <code>target="_blank"</code> deu tu bi go
    de khong mo cua so moi khong co duong quay lai.</td></tr>

<tr><td><strong>Cam ung khong nhan gi ca</strong></td>
    <td>Cam cap USB cam ung <strong>thang vao Pi</strong>, khong qua hub. Doi cap khac
    (nhieu cap chi co day nguon). Kiem tra:
    <code>lsusb | grep -i touch</code> va <code>sudo libinput debug-events</code></td></tr>
</table>"""),
]


def register_docs(app):
    @app.route("/docs")
    def docs_page():
        nav = " &middot; ".join(f'<a href="#{sid}">{title.split(" ", 1)[1]}</a>'
                                for sid, title, _ in SECTIONS)
        blocks = ""
        for sid, title, html in SECTIONS:
            blocks += f'<h2 id="{sid}">{title}</h2><div class="card">{html}</div>'

        body = f"""
        <div class="msg info">Trang nay hoat dong hoan toan ngoai tuyen - tra cuu duoc
        ca khi thiet bi khong co internet.</div>
        <div class="card"><strong>Muc luc:</strong><br>{nav}</div>
        {blocks}"""

        return render_page(body, active="/docs", title="Tai lieu",
                           subtitle="Kien truc, vi tri file, lenh bao tri, su co thuong gap")

    return app

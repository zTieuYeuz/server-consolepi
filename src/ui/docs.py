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

    ("mau", "🎨 Mau sac trong terminal", """
<p>Ca 3 khung terminal dung chung bang mau tuong phan cao. Quy uoc mau theo
thoi quen doc cua dan mang:</p>
<table>
<tr><th style="width:130px;">Mau</th><th>Y nghia</th></tr>
<tr><td><span style="color:#ff6b6b;font-weight:600;">Do</span></td>
    <td>Van de: down, err-disabled, error, timeout, drops</td></tr>
<tr><td><span style="color:#7ddc7d;font-weight:600;">Xanh la</span></td>
    <td>Tot: up, connected, established, permit, success</td></tr>
<tr><td><span style="color:#ffd166;">Vang</span></td>
    <td>Canh bao / trung gian: half-duplex, learning, administratively</td></tr>
<tr><td><span style="color:#68d5d5;">Xanh nhat</span></td><td>Dia chi IP</td></tr>
<tr><td><span style="color:#6cb6ff;">Xanh duong</span></td><td>Dia chi MAC</td></tr>
<tr><td><span style="color:#d99bff;">Tim</span></td><td>Ten cong / interface</td></tr>
</table>

<h3 style="color:#4CAF50;font-size:14px;margin-top:16px;">Terminal local</h3>
<p>Shell da co san mau (dau nhac, <code>ls</code>, <code>grep</code>) va cac lenh
mang duoc to mau qua <code>grc</code>: <code>ping</code>, <code>traceroute</code>,
<code>ip</code>, <code>ss</code>, <code>netstat</code>, <code>nmap</code>,
<code>tcpdump</code>, <code>mtr</code>, <code>dig</code>...</p>
<pre>* Loi tat co san
ports     xem cong dang mo
myip      dia chi IP cac giao dien
routes    bang dinh tuyen
serial    cac cong console dang cam
logs      nhat ky dashboard

* Xem file output thiet bi voi mau kieu Cisco
cisco capture.txt
cat file.txt | grcat /opt/console-pi/scripts/grc-cisco.conf</pre>

<h3 style="color:#4CAF50;font-size:14px;margin-top:16px;">Ket qua chay lenh hang loat (tab SSH)</h3>
<p>Output hien tren web duoc to mau day du theo bang tren - IP, MAC, ten cong,
trang thai up/down deu co mau rieng.</p>

<div class="msg info"><strong>Vi sao console Cisco tuong tac khong tu co mau:</strong>
output do chinh thiet bi gui ve, ma da so thiet bi Cisco khong gui ma mau ANSI.
To mau theo thoi gian thuc phai loc tung dong, se lam tre viec go phim - danh doi
khong dang. Bu lai: thiet bi CO gui mau (NX-OS, IOS-XE, thiet bi nen Linux) se
hien dung mau, va ket qua chay hang loat tren web thi luon co mau.</div>

<p>Sua bang mau: <code>/opt/console-pi/scripts/console-bashrc</code> (shell) va
<code>/opt/console-pi/scripts/grc-cisco.conf</code> (output thiet bi).</p>"""),

    ("suckhoe", "🩺 Suc khoe thiet bi va nut nguon", """
<p>Tab <strong>Tong quan</strong> co khoi <em>Suc khoe thiet bi</em>:</p>
<ul>
  <li><strong>Nguon dien</strong> - doc tu <code>vcgencmd get_throttled</code>. Day la
      canh bao quan trong nhat voi Raspberry Pi: cap sac yeu lam Pi treo hoac hong
      the nho, va no bao TRUOC khi hong. Thay chu do "DANG xay ra" thi doi nguon ngay.</li>
  <li><strong>Nhiet do CPU</strong> - duoi 65&deg;C la tot, tren 80&deg;C Pi tu giam xung.</li>
  <li>Thoi gian chay, tai he thong, RAM, dung luong dia.</li>
</ul>
<p><strong>Ve pin:</strong> may nay khong co pin nao Pi doc duoc. Da kiem tra:
<code>i2cdetect</code> bao dia chi 0x36 nhung doc 6 lan ra 6 gia tri ngau nhien -
do la nhieu tren bus chu khong phai chip pin. Khong co HAT (khong co EEPROM),
<code>lsusb</code> khong thay UPS nao. Pin trong man hinh di dong khong co duong
du lieu toi Pi. Neu sau nay gan UPS HAT that, chi can them ham doc chip vao
<code>BATTERY_READERS</code> trong <code>ui/health.py</code> la muc pin tu hien ra.</p>
<p><strong>Nut Tat may / Khoi dong lai:</strong> luon dung nut nay truoc khi rut dien.
Rut dien dot ngot la nguyen nhan pho bien nhat lam hong the nho. Sau khi bam Tat may,
doi den khi den xanh tren Pi ngung nhap nhay roi hay rut.</p>
"""),

    ("pin", "🔋 Hien % pin - can gan gi", """
<p><strong>Tinh trang hien tai: may nay khong co pin nao Pi doc duoc.</strong>
Da kiem chung bang ba cach doc lap:</p>
<ul>
  <li><code>/sys/class/power_supply/</code> &rarr; <strong>rong</strong>, khong co thiet bi nao</li>
  <li><code>upower</code> &rarr; bao <code>battery-missing-symbolic</code>, 0%</li>
  <li><code>lsusb</code> &rarr; khong co UPS nao. <code>i2cdetect</code> bao dia chi
      <code>0x36</code> nhung doc 6 lan ra 6 gia tri ngau nhien
      (<code>0x39 0x1c 0x2b 0x1e 0x24 0x29</code>) &mdash; do la <strong>nhieu tren bus</strong>,
      khong phai chip do pin</li>
</ul>
<p>Pin trong man hinh di dong khong giup duoc: no chi noi voi Pi qua HDMI va day
nguon, <strong>khong co duong du lieu</strong> nao de bao dung luong.</p>

<h3>Gan gi thi hien duoc ngay</h3>
<p>Dashboard da co san lop doc pin. Cam phan cung vao la <strong>tu hien</strong>,
khong phai sua code:</p>
<table>
<tr><th style="width:250px;">Phan cung</th><th>Cach Pi doc duoc</th></tr>
<tr><td><strong>UPS USB theo chuan HID Power Device</strong><br>
    <small style="color:#8b93a1;">APC Back-UPS, Eaton, CyberPower...</small></td>
    <td>Cam USB, cai <code>nut</code>. Kernel tu tao muc trong
    <code>/sys/class/power_supply</code> &rarr; muc 1 thay ngay, khong can bat gi.
    <strong>Day la cach chac chan nhat.</strong></td></tr>
<tr><td><strong>UPS HAT co driver kernel</strong><br>
    <small style="color:#8b93a1;">vd loai dung chip co driver san</small></td>
    <td>Cung xuat hien trong <code>/sys/class/power_supply</code>. Tu hien.</td></tr>
<tr><td><strong>UPS HAT doc qua I2C</strong><br>
    <small style="color:#8b93a1;">Waveshare UPS HAT (B)/(C), Geekworm X1200/X728,
    PiSugar - dung chip INA219 hoac MAX17040/17048</small></td>
    <td>Bat I2C (<code>raspi-config</code> &rarr; Interface &rarr; I2C), roi vao
    <strong>Cai dat</strong> bat <em>Doc pin qua I2C</em>.</td></tr>
</table>

<h3>Vi sao doc I2C phai TU BAT, khong bat san</h3>
<p>Do dia chi I2C mu la khong an toan. Chinh may nay tung cho ket qua <strong>gia</strong>
o <code>0x36</code>. Neu code tin ngay lan doc dau thi dashboard se hien mot con so
pin <strong>hoan toan bia dat</strong> &mdash; con te hon la khong hien gi, vi anh se
tin no khi dang o hien truong.</p>
<p>Khi bat, code doc <strong>4 lan lien tiep</strong> va chi tin khi ca ba dieu kien
cung dung:</p>
<ol>
  <li>Moi lan doc deu cho dien ap trong khoang pin Li-ion that (2.5V - 4.6V)</li>
  <li>Cac lan doc <strong>gan nhau</strong> (lech duoi 0.15V) &mdash; nhieu bus se nhay lung tung</li>
  <li>Phan tram nam trong 0-100</li>
</ol>
<p>Sai bat ky dieu kien nao thi bo qua dia chi do. Tha khong hien con hon hien sai.</p>

<h3>Cai khong nen lam</h3>
<p><strong>Dung suy pin tu <code>vcgencmd measure_volts</code>.</strong> Lenh do do dien ap
<em>loi CPU</em> (khoang 0.9V), khong phai dien ap nguon vao. Khong co quan he gi voi
dung luong pin. Suy ra % tu no la bia so.</p>
<p>Trong khi chua co phan cung pin, hay dung <strong>canh bao sut ap</strong> o tab
Tong quan (<code>vcgencmd get_throttled</code>). No khong cho biet con bao nhieu %,
nhung <strong>bao truoc</strong> khi nguon yeu den muc lam Pi treo - la dieu thuc su
can biet o hien truong.</p>
"""),

    ("khofile", "💾 Kho file (ISO, firmware)", """
<p>Tab <strong>Kho file</strong> de mang theo bo cai OS, firmware switch, file cau hinh -
dung khi ra hien truong khong co internet.</p>
<ul>
  <li>Uu tien ghi ra <strong>USB neu co cam</strong>, khong thi ghi vao the nho cua Pi
      (<code>/opt/console-pi/storage</code>).</li>
  <li>File duoc ghi <strong>theo tung khoi 1MB ra dia</strong>, khong nap vao RAM -
      neu khong thi mot file ISO 5GB se lam het bo nho Pi.</li>
  <li>Chan tai len khi con duoi <strong>3GB</strong> trong. The nho day co the lam
      hong he thong file.</li>
  <li>Moi file kem <strong>SHA256</strong> de doi chieu sau khi chep sang may khac.</li>
  <li>Chi nhan cac duoi file du lieu (iso, img, bin, tar, gz, xz, zip, conf, cfg...).
      Khong nhan <code>.sh</code> hay <code>.py</code> - trang nay khong phai cho nap
      ma tuy y len thiet bi.</li>
</ul>
<p>nginx da duoc nang <code>client_max_body_size</code> len <strong>8GB</strong> va
thoi gian cho len 900 giay. Mac dinh 64m thi ISO nao cung truot voi loi
<em>413 Request Entity Too Large</em>.</p>
"""),

    ("camthang", "🔌 Cam thang thiet bi (iLO / iDRAC)", """
<p>Tinh huong: ra hien truong, may chu tat lim, chi con cong quan ly iLO. Khong co
switch, khong co DHCP.</p>
<p>Tab <strong>Cam thang thiet bi</strong> bien Pi thanh mot mang mini tren cong LAN:</p>
<ol>
  <li>Cam day mang tu Pi thang sang cong quan ly</li>
  <li>Bam <strong>Bat che do cam thang</strong> - Pi lay <code>192.168.99.1</code>
      va chay DHCP cap <code>192.168.99.50-99</code></li>
  <li>Doi 15-30 giay (iLO khoi dong cham) roi bam <strong>Quet thiet bi</strong></li>
  <li>Bam nut <strong>Mo</strong> de vao giao dien web cua thiet bi</li>
</ol>
<p>Thiet bi dat IP tinh khong xin DHCP thi dung <strong>Quet rong</strong> (do them
cac dai hay gap) hoac <strong>go thang dai IP</strong> neu biet truoc. Quet ARP hoat
dong o lop 2 nen van thay duoc thiet bi khac dai IP.</p>
<p>Hang thiet bi duoc doan tu 3 byte dau cua MAC: HPE (iLO), Dell (iDRAC),
Supermicro (IPMI), Lenovo (IMM), Cisco, VMware.</p>
<p><strong>Canh bao:</strong> bat che do nay doi IP cua cong LAN. Neu ban dang truy cap
dashboard qua chinh cong do thi se mat ket noi - trang web co canh bao san. Bam
<strong>Tat che do</strong> de tra cong LAN ve DHCP binh thuong.</p>
"""),

    ("tuxa", "🌍 Truy cap tu xa (Cloudflare Tunnel)", """
<p>Kich ban: dua Pi cho nguoi khac mang toi diem xa, ho chi cam console va cam mang
internet. Ban ngoi nha van vao cau hinh duoc.</p>
<ol>
  <li>Tab <strong>Truy cap tu xa</strong> &rarr; bam <em>Cai cloudflared</em> (can internet)</li>
  <li>Vao <strong>Cloudflare Zero Trust &rarr; Networks &rarr; Tunnels</strong>, tao tunnel moi,
      chon <em>Debian / arm64</em>, sao chep chuoi token sau <code>--token</code></li>
  <li>Tro tunnel do vao <code>http://127.0.0.1:80</code></li>
  <li>Dan token vao trang, bam Luu</li>
</ol>
<p><strong>Khong can mo port tren router, khong can IP tinh</strong> - cloudflared tu mo
duong ham ra ngoai, nen chay duoc ca sau 4G va sau nhieu lop NAT.</p>
<p><strong>Bao mat:</strong> duong ham chi tro vao <code>127.0.0.1:80</code>, ma cong do
da co lop dang nhap bang tai khoan Linux. Nen bat them <strong>Cloudflare Access</strong>
de chan ngay tu bien. Token luu quyen 600, chi root doc duoc - ai co token deu dung
lai duoc duong ham, dung gui qua chat hay email. Xong viec thi tat duong ham.</p>
"""),

    ("tukiemtra", "✅ Tu kiem tra sau khi khoi dong lai", """
<p>Chay mot lenh la biet moi thu con dung khong:</p>
<pre>sudo /opt/console-pi/scripts/selftest.sh</pre>
<p>No kiem tra: tat ca dich vu, tat ca trang web, tung cong console, va <strong>ba kich
ban</strong> quan trong nhat:</p>
<ol>
  <li><strong>Cam day LAN thang sang laptop</strong> - eth0 co link-local du phong
      (169.254.x.x) khi khong ai cap DHCP</li>
  <li><strong>Tu phat AP khi khong co WiFi quen</strong> - kiem tra
      <code>wpa_supplicant@wlan0</code> duoc bat luc khoi dong,
      <code>KeepConfiguration=static</code>, va tiet kiem dien WiFi da tat</li>
  <li><strong>Thiet bi Bluetooth da ghep tu noi lai</strong> - kiem tra
      <code>ReconnectUUIDs</code> va tat ca thiet bi deu <em>trusted</em></li>
</ol>
<p>Ma thoat 0 = tat ca dat. Chay sau moi lan reboot hoac moi lan cai lai.</p>
"""),

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
</table>
<h3>WiFi ket noi duoc nhung KHONG BAO GIO co IP</h3>
<p><strong>Trieu chung:</strong> <code>wpa_cli status</code> bao <code>wpa_state=COMPLETED</code>,
nhung <code>ip addr</code> khong co dia chi nao. Nhat ky networkd co dong
<em>"DHCPv4 connection considered critical, ignoring request to reconfigure it"</em>.</p>
<p><strong>Nguyen nhan:</strong> <code>KeepConfiguration=yes</code> trong
<code>/etc/systemd/network/12-wlan0.network</code>. Khoa nay bao networkd coi lease DHCP
la "quan trong"; khi dia chi bi xoa (bam nut Ngat WiFi, hoac fallback doi che do),
networkd TU CHOI xin lai va WiFi chet cung cho den khi restart networkd.</p>
<p><strong>Sua:</strong> doi thanh <code>KeepConfiguration=static</code>. Van giu IP tinh
cua AP (muc dich ban dau) nhung khong khoa lease DHCP.</p>

<h3>Sau khi khoi dong lai thi mat WiFi hoan toan</h3>
<p><strong>Nguyen nhan:</strong> ban cai cu <code>mask</code> dich vu
<code>wpa_supplicant</code> toan cuc (de no khong tranh card voi hostapd) nhung
<strong>khong bat dich vu thay the</strong>. May van chay duoc chi vi tien trinh tu lan
boot cu con song - reboot mot phat la mat.</p>
<p><strong>Sua:</strong> bat <code>wpa_supplicant@wlan0</code>. Kiem tra:
<code>systemctl is-enabled wpa_supplicant@wlan0</code> phai tra ve <em>enabled</em>.</p>

<h3>Fallback chuyen che do xong thi WiFi khong len lai</h3>
<p><strong>Nguyen nhan:</strong> <code>wifi-fallback.service</code> la <code>Type=oneshot</code>.
Systemd giet toan bo cgroup khi service ket thuc - ke ca tien trinh
<code>wpa_supplicant -B</code> ma script vua sinh ra. Nghia la duong phuc hoi WiFi
<strong>chua bao gio chay duoc</strong>, va no chi lo ra dung luc can nhat.</p>
<p><strong>Sua:</strong> script goi <code>systemctl restart wpa_supplicant@wlan0</code>
thay vi chay tien trinh roi. Tien trinh nam trong cgroup rieng, duoc giam sat.</p>

<h3>Dang dung WiFi binh thuong thi Pi tu nhay sang che do AP</h3>
<p><strong>Nguyen nhan:</strong> <code>iw scan</code> tra ve rong (hay xay ra khi
wpa_supplicant vua khoi dong lai hoac card dang ban). Script hieu nham thanh
"khong co WiFi quen" va bat AP, cat dut ket noi dang dung.</p>
<p><strong>Sua:</strong> quet toi 3 lan; neu khong thay <strong>MOT SSID nao ca</strong>
(ke ca mang la) thi ket luan la "quet loi", giu nguyen hien trang.</p>

<h3>Pi bi ghim o che do AP mai khong ve WiFi</h3>
<p><strong>Nguyen nhan:</strong> chot "AP dang co client thi khong dung toi" khong co gioi
han thoi gian. Mot thiet bi la (dien thoai hang xom, bo lap wifi) tu bam vao AP la ghim
Pi vinh vien, mat duong vao qua WiFi nha.</p>
<p><strong>Sua:</strong> chi giu toi da 5 vong (10 phut) roi danh gia lai mot lan.</p>

<h3>Chuyen tu AP ve client: associate thanh cong nhung khong co IP</h3>
<p><strong>Nguyen nhan:</strong> goi <code>networkctl reconfigure</code> ngay sau khi bat
supplicant, luc card chua associate. Khong co gi de xin DHCP, va networkd
<strong>khong tu thu lai</strong> khi carrier len sau do.</p>
<p><strong>Sua:</strong> doi <code>wpa_state=COMPLETED</code> roi moi goi reconfigure.
Do duoc: sau khi sua, chu trinh AP &rarr; client hoan tat trong <strong>17 giay</strong>.</p>

<h3>Dashboard chi nhan 1 trong 2 soi cap console</h3>
<p><strong>Nguyen nhan:</strong> code chi quet <code>/dev/ttyUSB*</code>. Cap Cisco USB
Console la thiet bi CDC-ACM nen kernel tao <code>/dev/ttyACM0</code> - bi bo sot hoan toan.</p>
<p><strong>Sua:</strong> quet ca hai ho. Cap cong rieng: <code>ttyUSB0-3</code> &rarr; 8001-8004,
<code>ttyACM0-3</code> &rarr; 8005-8008. Cong thuc nay phai KHOP o ba noi:
<code>ui/home.py</code>, <code>scripts/ttyd-one.sh</code>, va bang <code>map</code> trong
<code>config/nginx-console-pi.conf</code>. Kem udev rule tu khoi dong dich vu cho bat ky
cong serial USB moi cam nao.</p>

<h3>Ban cai chay xong ma thieu mot nua</h3>
<p><strong>Nguyen nhan:</strong> <code>install.sh</code> dung <code>set -e</code>, va vong lap
chep script gap thu muc <code>__pycache__</code> (Python sinh ra khi chay thu). Lenh
<code>install</code> bao loi <em>"omitting directory"</em> va ca ban cai dung ngay giua chung -
khong co thong bao gi ro rang.</p>
<p><strong>Sua:</strong> chi chep FILE (<code>[[ -f "$f" ]] || continue</code>).
Bai hoc: moi vong lap chep file trong script co <code>set -e</code> deu phai loc kieu.</p>

<h3>Ghep cap Bluetooth thanh cong nhung thiet bi khong tu noi lai</h3>
<p><strong>Nguyen nhan:</strong> thieu <code>ReconnectUUIDs</code> trong
<code>/etc/bluetooth/main.conf</code>, va thiet bi chua duoc <code>trust</code>.</p>
<p><strong>Sua:</strong> khai bao UUID cua HID (ban phim/chuot) va PAN (mang) trong muc
<code>[Policy]</code>, va luon <code>trust</code> sau khi ghep cap. Chay
<code>selftest.sh</code> se bao neu con thiet bi nao chua trusted.</p>
<p><strong>Luu y khi sua cau hinh:</strong> chot kiem tra trong <code>install.sh</code> phai
kiem <strong>tat ca</strong> khoa can co, khong chi mot khoa. Chi kiem
<code>AutoEnable</code> thi ban nang cap them <code>ReconnectUUIDs</code> se bi bo qua im lang.</p>

<h3>File chua mat khau WiFi doc duoc boi moi tai khoan</h3>
<p><strong>Nguyen nhan:</strong> <code>install.sh</code> chi <code>chmod 600</code> luc TAO MOI
file. May da co san file thi giu nguyen quyen mac dinh 644.</p>
<p><strong>Sua:</strong> siet quyen o moi lan cai, cho ca
<code>wpa_supplicant-wlan0.conf</code> va <code>hostapd.conf</code>. Kiem tra:
<code>stat -c "%a" /etc/hostapd/hostapd.conf</code> phai la <code>600</code>.</p>
"""),
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

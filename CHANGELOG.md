# Changelog

## 0.4.4

Sua triet de loi **dan tap lenh bi mat ky tu dau dong** tren switch that
(`show inventory` -> `how inventory`). Ban 0.4.3 cho co dinh 0.18s giua cac
dong - VAN MAT CHU, vi `show version` tren switch in ra hang tram dong mat
vai giay, thiet bi con dang in thi dong sau da toi noi.

Nay khong cho theo dong ho nua ma **cho den khi thiet bi thuc su san sang**:
man hinh ngung thay doi 0.5s **va** dong cuoi giong dau nhac (ket thuc bang
`#`, `>`, `$`). Chi "im lang" thoi la chua du - thiet bi cham co the ngung
giua chung roi in tiep. Neu im lang 2.5s ma van khong thay dau nhac thi cung
di tiep, de khong ket lai voi thiet bi co dau nhac la.

Kem theo xu ly **`--More--`** (Cisco chia trang): tu bam Space de thiet bi in
tiep. Trong luc lam da gap them 1 loi cung kieu **ngay trong ma vua viet**:
ban dau chi kiem tra `--More--` khi man hinh CO THAY DOI, nhung thiet bi dung
o `--More--` thi man hinh dung im -> bi cham nham la "da in xong" -> gui dong
ke tiep va ky tu dau tien cua dong do bi thiet bi an lam PHIM BAM sang trang,
mat chu dung y het loi cu. Nay kiem tra o moi vong.

Da kiem chung bang 2 "thiet bi gia" mo phong switch that (loai in cham vai
giay va loai co chia trang `--More--`): ca 2 deu giu nguyen ven tung ky tu,
dong cuoi nam cho bam Enter dung nhu thiet ke.

## 0.4.3

Bon loi thuc te khi dung tab SSH/terminal, moi loi deu do dac lai truoc khi sua:

- **Dan tap lenh bi ROI KY TU DAU DONG** (vi du that: `show interfaces trunk`
  thanh `how interfaces trunk`). Da kiem chung duong dan phia server KHONG cat
  chu (dan vao bash nhan du nguyen van), nen thu pham la ban ca khoi ra 1 luot
  qua nhanh: thiet bi mang khong co dieu khien luong o CLI, trong luc con dang
  echo dong truoc thi ky tu dau dong sau bi mat. Nay **gui tung dong mot, giai
  lao 0.18s giua cac dong**; dong CUOI khong bam Enter de con doc lai.
- **Hoi "Leave site?" moi lan bam Ket noi / Dan**. Hai nut do truoc day la form
  POST binh thuong nen ca trang tai lai, ma ttyd co dang ky canh bao truoc khi
  roi trang. Nay **gui bang fetch, khong tai lai trang** - khung terminal giu
  nguyen phien, khong con hop thoai. Neu JS loi thi form van chay nhu cu
  (khong mat duong lui). Kem theo bat `disableLeaveAlert` cho ttyd.
- **Lan con lan chuot len lai chay cac lenh cu**: tmux chua bat chuot nen banh
  xe bi dich thanh phim Mui ten (= goi lai lich su lenh). Nay bat `mouse on`
  cho tmux -> banh xe cuon dung lich su man hinh.
- **Khung terminal nho, phan tren nhieu chu thua**: bo tieu de danh so va cac
  doan giai thich dai, gop o nhap thanh 1 hang; khung terminal tu `100vh-470px`
  len `100vh-330px` (cao them ~140px).

## 0.4.2

**Thu vien lenh** - bo tri lai cho de nhin, de tim:
- Them **o tim kiem** loc tuc thi theo ten + mo ta + the + noi dung lenh.
- Them **nut the (tag)** bam 1 cai la loc ngay - dung duoc khi khong co ban phim.
- Danh sach chuyen thanh **luoi the**, moi tap lenh 1 the gon; form "Them tap
  lenh moi" thu gon xuong duoi (truoc day choan het phan tren, vao trang khong
  thay ngay thu vien de tim).

**Tab SSH** - lam lai theo dung cach lam viec thuc te:
- Them **o mat khau** dien san. Mat khau duoc go vao terminal DUNG LUC thiet bi
  hoi (doi bang `tmux capture-pane` toi khi thay dau nhac), nen khong hien tren
  man hinh, khong vao `ps`, khong vao lich su lenh - **khac han `sshpass -p`**
  von dat mat khau tho ngay tren dong lenh. Qua 12 giay khong thay dau nhac thi
  bao that la khong thay, khong im lang coi nhu xong.
- Them **o soan tap lenh** ngay duoi khung terminal: chon tap lenh tu Thu vien →
  sua IP/ten → **Copy** / **Dan tu clipboard** / **Dan vao terminal** (dan xong
  khong tu bam Enter). Noi dung dang soan duoc giu lai khi tai lai trang.
- **Bo "chay hang loat"** (trung vai tro voi cong cu Netmiko Config ben Network
  Tools).

**2 lo hong that duoc va trong lan sua nay** (phat hien bang kiem thu, khong
phai doc code suong):
- **Chen lenh qua o dia chi/tai khoan**: dia chi va tai khoan truoc day duoc
  ghep thang vao 1 dong lenh chay trong terminal QUYEN ROOT ma khong loc gi -
  nhap `1.1.1.1; rm -rf /` la chay that. Nay chan bang bieu thuc chinh quy.
- **Chen ma qua noi dung thu vien lenh**: noi dung tap lenh duoc nhung vao the
  `<script>` cua trang SSH. Chi thay `</` bang `<\/` la CHUA DU - mot tap lenh
  chua `<script>` van lot nguyen ven, ma theo chuan HTML thi gap `<script` ben
  trong the script se day bo phan tich sang trang thai dac biet khien the
  `</script>` ke tiep khong con dong the nua. Nay ma hoa ca `< > &` thanh
  `< > &`.

## 0.4.1

Bo tinh nang **Ping lien tuc (do thi song)** (`/nettools/ping-monitor`) da
them o 0.4.0 - danh gia thuc te khong huu dung du da sua 2 loi that (silent-
rejection khi bam Bat dau, va endpoint `/data` bi Cloudflare Worker rieng
cua nguoi dung tra ve 404 khi truy cap tu xa). Go het module, route, muc
tai lieu, dong nhac trong README - khong de sot code chet.

## 0.4.0

Them 6 cong cu chan doan mang moi, tat ca da kiem chung bang do dac that
tren phan cung (khong chi doc code) - danh sach chi tiet o phan "Loi da
phat hien va sua trong luc lam" ben duoi cho biet nhung gi khong nhu du
tinh ban dau va cach sua.

### Tinh nang moi
- **MTU Discovery** (`/nettools/mtu`): tim MTU that toi 1 dia chi bang ping
  DF nhi phan. Khi mot router bao thang ICMP "Frag needed" thi dung ngay
  ket qua do (dang tin cay nhat). Canh bao nguyen nhan pho bien khi MTU
  duoi 1500 (PPPoE ~1492, VPN/GRE/IPsec ~1400-1436). Da kiem chung tren
  chinh mang nha: phat hien dung MTU 1492 (PPPoE that) toi 8.8.8.8, va
  1500 sach toi gateway cung subnet
- **Kiem tra DNS** (`/nettools/dns-check`): doi chieu 1 ten mien qua DNS he
  thong + Google/Cloudflare/Quad9, dung scapy dung goi UDP/53 qua socket
  thuong (khong can quyen root). Canh bao lech ket qua kem chu thich CDN
  de khong bao gia
- **Kiem tra chung chi TLS** (`/nettools/tls-check`): xem chi tiet + tinh
  trang tin cay chung chi HTTPS quan tri (switch/router/iLO). Luon phan
  biet ro "lay duoc de xem" va "duoc he thong tin cay" - khong bao gio
  hien banner "hop le" cho chung chi tu ky/het han/sai ten
- **Ping lien tuc kem do thi song** (`/nettools/ping-monitor`): theo doi
  rot goi thoi gian thuc khi rung/cam lai day, do thi canvas tu ve tay
  (khong thu vien ngoai). Tu dong dung sau toi da 30 phut
- **So do mang 1 doan** (`/nettools/topology`): ghep ARP Scan + LLDP/CDP co
  san thanh so do Pi → switch → cac host. Noi ro gioi han chi 1 doan mang,
  khong ve duoc nhieu switch noi tiep
- **May chu TFTP** (`/nettools/tftp`): bat/tat TFTP de `copy running-config
  tftp://` (sao luu config len Pi) va `copy tftp://.../firmware.bin flash:`
  (nap firmware). Mac dinh TAT, chi lang nghe tren eth0

### Loi da phat hien va sua trong luc lam (khong doan, do dac that)
- **TFTP: du dinh ban dau dung dnsmasq (da co san, khong can cai them) la
  SAI.** Doc ky tai lieu dnsmasq moi phat hien TFTP tich hop san cua no
  CHI HO TRO DOC, khong ho tro GHI - nghia la lenh quan trong nhat (switch
  ghi config len Pi) se khong bao gio chay duoc. Sua bang cach dung
  `tftpd-hpa` (them 1 goi moi, co `--create` de ho tro ghi), va tat ngay
  dich vu mac dinh cua goi nay sau khi cai (no tu bat luc cai dat - di
  nguoc nguyen tac khong tu bat dich vu mang khong xac thuc)
- **DNS check qua scapy `sr1()` can quyen root** (raw socket) - doi sang
  dung lop DNS/DNSQR cua scapy CHI DE DUNG GOI TIN, gui/nhan qua socket UDP
  thuong (`socket.SOCK_DGRAM`) - vua khong can quyen root, vua nhanh hon
- **TLS check voi CERT_NONE**: `ssl.getpeercert()` chuan tra ve RONG khi
  tat xac thuc (gioi han da biet cua thu vien chuan) - phai lay dang nhi
  phan roi phan tich bang `cryptography` (da co san trong du an)

### Don dep
- Xoa `iperf3` khoi danh sach goi cai dat (con sot tu tinh nang da bo o
  ban 0.3.1, khong con noi nao dung den)

## 0.3.1

Vong nay sua mot **lo hong bao mat nghiem trong**, gop hai cong cu chan
doan lam mot, va sua nhieu loi phat hien duoc trong luc kiem thu that tren
may (khong phai doan - tat ca deu do dac/tai hien duoc).

### Bao mat (quan trong - nen cap nhat ngay neu dang dung Cloudflare Tunnel)
- **Nguoi di qua Cloudflare Tunnel bi cham nham la man hinh gan tai cho,
  vao thang dashboard va terminal quyen root khong can dang nhap.** Dieu
  kien mien dang nhap truoc day dua vao dia chi IP (`127.0.0.1`), nhung
  `cloudflared` chay ngay tren Pi va cung goi vao dia chi do. Da sua bang
  cach chuyen sang phan biet theo CONG: cong 80 (LAN/WiFi/Cloudflare) luon
  doi dang nhap, cong 8880 (chi loopback) danh rieng cho man hinh kiosk.
  `selftest.sh` co them chot chan mo phong dung kieu tan cong nay.

### Tinh nang moi
- **Duong vao danh cho may/AI** (`GET /ai`, `/api/system`,
  `/api/console/<dev>/read|send`): dua thiet bi toi diem xa va nho mot AI
  o dau khac dieu khien giup. Mac dinh tat, tu tao token trong tab *Truy
  cap tu xa*, hai muc quyen (chi doc / day du), token chi hien mot lan.
- **Kiem tra toan dien cong mang** (gop DHCP Testing + Kiem tra cong vat ly
  thanh MOT nut bam): toc do/duplex that, thong ke loi duong truyen, PoE,
  DHCP, va neu co IP thi tu dong kiem tra ra Internet (ping 8.8.8.8, ping
  google.com, mo web that) + do bang thong qua Cloudflare Speed Test -
  khong can iperf3 hay may thu hai. Da bo tinh nang do cap TDR (`ethtool
  --test`) vi chip mang tren Raspberry Pi khong ho tro - thay vi hien ket
  qua sai thi bo han, khong con nhac den trong giao dien lan tai lieu.
- Cho phep bat/tat ban phim ao tren trang truy cap tu xa (truoc day chi co
  o man hinh gan tai cho).
- Doc pin an toan hai muc (kernel/UPower luon bat; UPS HAT qua I2C phai tu
  bat trong Cai dat, vi do dia chi I2C mu de cho ket qua gia).

### Loi da sua (phat hien va kiem chung bang do dac that)
- **LLDP/CDP Discovery** hien ten thiet bi la "?" va Mgmt IP la "-" moi
  lan, ke ca khi router/switch quang ba day du - ham phan tich JSON gia
  dinh sai cau truc du lieu that su cua `lldpcli`.
- **Ghep cap Bluetooth "hong mot nua"**: thiet bi bao `Connected: yes`
  nhung khong `Bonded`, khien ban phim khong go duoc gi ma giao dien van
  hien "dang ket noi" mau xanh. Them kiem tra `Bonded` rieng, nut "Ghep
  cap lai" tu xoa ban ghi cu truoc khi ghep lai.
- **DHCP Testing tren wlan0 khong bao gio nhan duoc OFFER**: goi tin co
  hai dia chi MAC mau thuan nhau (Ethernet header vs BOOTP chaddr) khien
  AP WiFi im lang khong tra loi. Sua xong: 5/5 lan thu deu thanh cong.
- **Kiem tra Internet qua DHCP bao "That bai" gia**: khi OFFER tra ve
  trung IP da co san tren cong (rat hay gap khi test tren chinh cong quan
  tri), va khi mot router WiFi co tuyen duong rieng cho dung 8.8.8.8 danh
  cuop goi tin sang cong khac.

## 0.3.0

Vong nay tap trung vao **do tin cay**. Thiet bi nay duoc dung khi switch/router
DA hong - khong the vua sua mang vua sua con Pi. Nhieu loi duoi day chi lo ra
dung luc can phuc hoi nhat, nen deu duoc kiem chung bang do dac that.

### Loi nghiem trong da sua
- **`install.sh` dung giua chung ma khong bao loi.** Vong lap chep script gap
  thu muc `__pycache__`, `install` bao loi, `set -e` dung ca ban cai - nua sau
  khong bao gio chay. Nay chi chep FILE.
- **WiFi ket noi duoc nhung khong bao gio co IP.** `KeepConfiguration=yes` lam
  systemd-networkd coi lease DHCP la "critical"; khi dia chi bi xoa no TU CHOI
  xin lai. Doi sang `KeepConfiguration=static`.
- **Reboot la mat WiFi.** `install.sh` mask `wpa_supplicant` toan cuc nhung
  khong bat dich vu thay the. May van chay chi vi tien trinh tu lan boot cu con
  song. Nay bat `wpa_supplicant@wlan0`.
- **Duong phuc hoi WiFi chua bao gio chay duoc.** `wifi-fallback.service` la
  `Type=oneshot`, systemd giet luon `wpa_supplicant -B` ma script vua sinh ra.
  Nay dung unit `wpa_supplicant@wlan0`.
- **Mot lan quet WiFi that bai lam Pi nhay sang AP,** cat dut ket noi dang dung.
  Nay quet 3 lan va phan biet "quet loi" voi "khong co WiFi quen".
- **Pi bi ghim o che do AP mai mai** khi co thiet bi la bam vao. Nay chi giu toi
  da 5 vong (10 phut).
- **Chuyen AP -> client: associate xong nhung khong co IP.** `networkctl
  reconfigure` goi truoc khi associate xong thi khong bao gio xin duoc dia chi.
  Nay doi `wpa_state=COMPLETED`. Do duoc: chu trinh hoan tat trong **17 giay**.
- **Rot WiFi sau mot luc.** `power_save` dang bat: card ngu, router mat lien lac,
  nhung IP van con tren interface nen nhin vao tuong mang van tot. Nay tat vinh
  vien bang udev rule.
- **File chua mat khau WiFi va mat khau AP doc duoc boi moi tai khoan** (644).
  `install.sh` chi `chmod 600` luc tao moi. Nay siet quyen o moi lan cai.

### Tinh nang moi
- **Nhan moi loai cap console.** Truoc day chi quet `/dev/ttyUSB*` nen bo sot cap
  Cisco USB Console (CDC-ACM, `/dev/ttyACM*`). Nay nhan ca hai ho, cap cong rieng
  (8001-8004 / 8005-8008), kem udev rule tu khoi dong cho cap chua tung thay.
  Dashboard hien ten chip.
- **Suc khoe thiet bi**: canh bao sut ap, nhiet do CPU, tai, RAM, dia, thoi gian
  chay. Nut **Tat may / Khoi dong lai** co xac nhan.
- **Kho file** (`/storage`): mang theo ISO, firmware, cau hinh. Ghi theo luong ra
  dia (khong nap vao RAM), uu tien USB, chan khi sap day, kem SHA256.
  nginx nang gioi han 64m -> 8g.
- **Cam thang thiet bi** (`/direct`): Pi thanh mang mini `192.168.99.1` co DHCP,
  quet ARP tim iLO/iDRAC/IPMI, nhan dien hang qua OUI, mo thang giao dien web.
  Quet duoc ca dai IP tinh tu nhap.
- **Truy cap tu xa** (`/remote`): Cloudflare Tunnel - khong can mo port, khong
  can IP tinh, chay duoc sau 4G. Token luu quyen 600.
- **Nut ngat WiFi**, canh bao neu dang truy cap qua chinh WiFi do.
- **Phan loai Bluetooth dung**: giai ma Class of Device + UUID dich vu thay vi
  chi dua vao `Icon`. Nut ket noi khop dung ho so (PAN cho may tinh/dien thoai,
  HID cho ban phim/chuot). `ReconnectUUIDs` cho thiet bi da ghep tu noi lai.
- **Hieu ung cho**: nut chuyen sang trang thai dang chay va tu khoa, kem vach
  tien do tren cung - mot co che chung (`data-busy`) cho moi trang.
- **`scripts/selftest.sh`**: kiem tra toan bo he thong va ba kich ban quan trong.
  Ma thoat 0 = tat ca dat.
- Mau khi go lenh: bat `colored-stats`, `colored-completion-prefix`, mau cho
  trang `man`. `install.sh` xoa phien tmux cu de cau hinh moi duoc ap dung -
  thieu buoc nay thi cai xong khong thay gi doi.

### Tai lieu
- Them 5 muc moi va **10 su co** vao trang Tai lieu trong dashboard, moi su co
  ghi ro trieu chung / nguyen nhan / cach sua va cach kiem tra.

### Don dep
- Xoa import thua trong `ui/ssh.py`, `ui/commands.py`, `ui/terminal.py`,
  `nettools/ifthen.py`
- Moi trang tai duoi 50ms; Flask dung 3MB RAM

## 0.2.1

### Toi uu hieu nang
- Trang WiFi: **2.865s -> 0.015s** (nhanh hon ~190 lan). Truoc day quet WiFi
  dong bo moi lan tai trang; gio quet o luong nen va nho ket qua 45 giay,
  co nut "Quet lai" khi can du lieu moi
- Trang chu: 0.170s -> 0.051s. Gop 8 lenh `systemctl is-active` thanh 1
- Thanh trang thai: doc IP bang `ioctl` thay vi goi lenh `ip` (khong spawn
  tien trinh), them cache 4 giay
- Chromium tu dieu chinh theo RAM: may duoi 1.5GB (Pi 3, Pi Zero 2W) gioi han
  so tien trinh render va bo nho JS; may duoi 3GB gioi han vua phai

### Mau sac terminal
- Bang mau tuong phan cao dung chung cho ca 3 khung terminal
- Shell co mau san: dau nhac, `ls`, `grep`, va lenh mang qua `grc`
  (ping, traceroute, ip, ss, netstat, nmap, tcpdump, mtr, dig)
- Bo mau rieng cho output thiet bi Cisco (`grc-cisco.conf`)
- Ket qua chay lenh hang loat tren web duoc to mau: do=loi, xanh la=tot,
  vang=canh bao, xanh nhat=IP, xanh duong=MAC, tim=ten cong
- Loi tat: `ports`, `myip`, `routes`, `serial`, `logs`

## 0.2.0

Bản đầu tiên đóng gói được để cài lên máy khác.

### Thêm mới
- **Giao diện mới**: thanh điều hướng trái + thanh trạng thái mạng luôn hiện
  IP của cả 3 giao diện (LAN / WiFi / Bluetooth), tự làm mới mỗi 30 giây
- **Đăng nhập** bằng tài khoản Linux qua PAM
- **Terminal local** và **SSH** (tương tác + chạy hàng loạt) qua ttyd + tmux
- **Thư viện lệnh** — thêm/sửa/xoá, sẵn 5 tập lệnh Cisco, dán được vào terminal
- **Trang Tài liệu** tra cứu ngoại tuyến ngay trên thiết bị
- **nginx** làm cổng trung gian — mọi thứ chung cổng 80
- **Bàn phím ảo** cho màn hình cảm ứng, gõ được cả vào terminal
- **Bluetooth**: quét + ghép cặp bàn phím/chuột, kèm PAN
- **Nút xoay màn hình** trong tab Cài đặt
- `install.sh` cài một lệnh, tự phát hiện có màn hình hay không

### Sửa lỗi đáng chú ý
- `ttyd` chạy `Type=oneshot` nên systemd không giám sát — ttyd chết vẫn báo
  `active`. Đã thay bằng template unit có `Restart=always`
- systemd-networkd xoá mất IP tĩnh của AP sau khi bật — thêm
  `KeepConfiguration=yes`
- Đăng ký NAP của Bluetooth bị huỷ ngay khi script thoát (D-Bus gắn với vòng
  đời tiến trình) — chuyển sang daemon chạy thường trú
- `srp()` của scapy không bắt được DHCPOFFER — chuyển sang `sniff()` + `sendp()`
- Bàn phím ảo: `preventDefault()` trên `touchstart` chặn luôn sự kiện click —
  chuyển sang `pointerdown`
- Toạ độ cảm ứng không tự xoay theo màn hình — cần ma trận hiệu chỉnh khớp
  hướng, và `install.sh` từng tự ghi đè mất ma trận đúng

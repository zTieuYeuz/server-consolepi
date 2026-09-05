# Changelog

## 0.4.21

**Sua loi that gap tai mang cong ty: "Kiem tra toan dien cong mang" bao
nham "khong co gateway hop le" du mang hoan toan binh thuong.** Nguoi dung
bam nut kiem tra, cong cu bao loi va tu choi test Internet/bang thong -
nhung `ping`/`traceroute` lam tay qua CHINH cong do (kem ICMP Redirect that
tu router) lai chay hoan toan binh thuong.

**Nguyen nhan:** mang do khong gui Option 3 (Router) co dien - chi gui
**Option 121 (Classless Static Routes, RFC 3442)**, mot chuan quoc te ngay
cang pho bien o mang doanh nghiep/hien dai. He dieu hanh (Windows/Linux) da
tu biet doc Option 121 tu lau, nhung cong cu nay truoc gio chi biet doc
Option 3 nen ket luan sai "khong co gateway" du du lieu dinh tuyen that su
CO trong goi tin, chi la o option khac.

**Sua:** them ham doc Option 121, uu tien no hon Option 3 dung theo RFC
3442 khi ca hai cung co mat (tim tuyen mac dinh 0.0.0.0/0, lay gateway cua
tuyen do). Da kiem thu voi 4 tinh huong: chi co Option 121 (dung du lieu mo
phong khop chinh xac mang cong ty da gap), chi co Option 3, Option 121 co
nhieu tuyen khong tuyen mac dinh ro rang (lay tuyen dau lam du phong), va
khong co gi ca.

**Them nhat ky rieng cho cong cu nay** (`/var/log/console-pi-dhcptest.log`)
- ghi lai OFFER/ACK that su nhan duoc moi lan bam kiem tra. Ly do: cong cu
nay hay dung o hien truong (mang la, cong ty) dung luc khong the SSH hay
nho su ho tro tu xa - truoc day ket qua chi hien tren man hinh roi mat, ve
nha khong con cach nao xem lai. Cung them 2 dong vao bang "Vi tri file quan
trong" trong tai lieu (`console-pi-dhcptest.log` va `console-pi-errors.log`
tu 0.4.16).

## 0.4.20

**Sua triet de: DNS bi xoa trang khi rut day mang, chi con WiFi.** Ban
0.4.19 them DNS du phong vao TUNG giao dien rieng le (nmcli +ipv4.dns cho
eth0, DNS= trong 12-wlan0.network cho wlan0) - VAN CHUA DU, vi
NetworkManager (ben ghi `/etc/resolv.conf`) chi biet DNS cua eth0 (do no
quan ly), hoan toan khong biet gi ve cau hinh DNS rieng cua wlan0 (do
systemd-networkd quan ly). Ngat eth0 la NetworkManager xoa trang DNS,
khong con dong nameserver nao ca - da tai hien duoc dung loi nay bang cach
ngat that eth0 va quan sat.

**Sua dung goc:** them `/etc/NetworkManager/conf.d/99-consolepi-dns-fallback.conf`
voi cau hinh **global DNS** (`[global-dns]` + `[global-dns-domain-*]`) -
day la cap DNS cua toan bo NetworkManager, AP DUNG BAT KE GIAO DIEN NAO
DANG HOAT DONG, khong phu thuoc giao dien cu the nao con song hay khong.

**Da kiem chung that bang cach ngat han eth0** (dat luoi an toan tu bat lai
sau 90 giay truoc khi thu, tranh mat mang that su):
- `resolv.conf` van con `1.1.1.1`, `8.8.8.8` sau khi ngat eth0
- Phan giai duoc `region1.v2.argotunnel.com`, `cloudflare.com`
- Cloudflare Tunnel van `active`, 0 loi
- Truy cap qua `https://consolepi.home-server.id.vn` tra ve `403` (trang
  Cloudflare Access, KHONG PHAI loi ket noi 502/523) - xac nhan duong
  truyen thong suot end-to-end chi bang WiFi, khong can eth0.

`install.sh` cung cai file nay khi cai lai, khong mat.

## 0.4.19

**TIM RA NGUYEN NHAN THAT cua "cam day mang thi duoc, dung WiFi thi khong"**
- day moi la ly do tunnel fail o cong ty, khong phai giao thuc QUIC (0.4.18
  van dung nhung chua du).

**Van de: DNS ghim cung vao mang cu.** May chu DNS do DHCP cap chi ton tai
TRONG MANG DO. `/etc/resolv.conf` chi co dung 1 dong:
`nameserver 192.168.110.21` - dia chi thuoc mang day o nha. Mang Pi sang noi
khac (hotspot 4G/5G tu dien thoai o cong ty) thi may chu DNS do khong con
lien lac duoc -> khong phan giai duoc bat ky ten mien nao -> cloudflared
khong tim duoc `region1.v2.argotunnel.com` -> **duong ham tu xa chet**. Khop
dung log that sang nay: `Failed to refresh DNS local resolver ... i/o timeout`.

**Sua:** them DNS cong cong `1.1.1.1` + `8.8.8.8` lam du phong cho ca hai
duong:
- `eth0` (NetworkManager): `nmcli con mod ... +ipv4.dns`
- `wlan0` (systemd-networkd): them `DNS=` vao `12-wlan0.network`
- `install.sh` cung dat lai khi cai lai, khong mat.

Da kiem chung sau khi sua: `resolv.conf` co du 3 nameserver, phan giai duoc
`region1.v2.argotunnel.com`, `cloudflare.com`, `github.com`; tunnel van chay
`protocol=http2`, 0 loi.

**selftest.sh: them 2 muc kiem tra** - co DNS du phong khong, va co phan giai
duoc ten mien cua Cloudflare Tunnel khong. Neu sau nay cau hinh bi mat (cai
lai he dieu hanh, doi mang) la biet ngay thay vi doi den luc ra hien truong
moi phat hien. **38 dat / 2 luu y** (truoc la 36/2).

**Con mot bay nua da ghi vao tai lieu:** duong ra qua `eth0` luon duoc uu
tien hon `wlan0` (metric 100 so voi 1024). O cong ty neu cam day mang ma day
bi port-security chan, may van co gang di ra bang day do va chet, du hotspot
WiFi van tot. Cach chac an: **rut han day mang khi dung hotspot dien thoai**.
Kiem tra bang `ip route get 1.1.1.1` - phai thay `dev wlan0`.

## 0.4.18

**1. SUA LOI TUNNEL KHONG CHAY DUOC TREN HOTSPOT DIEN THOAI** (da fail that
o cong ty). Kich ban: khong co WiFi, Bluetooth bi cam, day mang bi
port-security chan - chi con hotspot 4G/5G tu dien thoai.

Nguyen nhan doc duoc tu log that: `write udp [::]:... sendmsg: network is
unreachable`. Cloudflared mac dinh dung **QUIC (chay tren UDP)**, ma mang di
dong rat hay chan/khong on dinh voi UDP; kem theo do la mang di dong thuong
cap IPv6 nhung duong di IPv6 thuc te khong hoat dong.

Sua: ep `--protocol http2` (TCP cong 443, gan nhu luon duoc cho qua vi
khong phan biet duoc voi HTTPS thuong) va `--edge-ip-version 4`. Da kiem
chung that sau khi sua: `cloudflared will use 'http2' as primary protocol`,
ca 2 ket noi deu `protocol=http2`, **0 loi trong 30 giay theo doi lien tuc**.

*Chi tiet ky thuat quan trong*: co `--protocol` da bi ban cloudflared moi
(2026.8.3) AN KHOI `--help` nhung VAN HOAT DONG - kiem chung bang cach so
sanh voi mot co khong ton tai (co la bi tu choi ngay, `--protocol` thi duoc
chap nhan binh thuong). Neu ban tuong lai go han co nay thi phai ghim lai
phien ban cu hon.

**2. HE THONG NHAT KY LOI** - tab moi "Nhat ky loi" tren menu:
- Ghi lai **moi loi Python khong duoc bat** trong dashboard kem traceback
  day du (truoc day chi hien trang loi chung chung roi bien mat khong dau
  vet - o hien truong khong con cach nao biet chuyen gi da xay ra).
- Xem duoc canh bao/loi journal cua tung dich vu chinh ngay tren web,
  khong can nho lenh `journalctl`.
- Tu xoay vong o 2MB (giu 3 ban, toi da ~8MB), khong lo day the nho.

*LOI THAT DA BAT DUOC KHI VIET TINH NANG NAY (truoc khi trien khai)*: cach
lam ban dau la "ghi log roi `raise` lai loi nguyen van" voi y dinh khong doi
hanh vi. Nhung Flask goi `errorhandler(Exception)` o **hai cho** khac nhau,
va `raise` lai o lan goi thu hai se thoat ra ngoai ca tang WSGI - lam
**trinh duyet nhan ket noi bi ngat** thay vi trang loi 500, va con bien
**loi 404 binh thuong thanh 500**. Neu trien khai ban do thi te hon han so
voi truoc khi co tinh nang. Da phat hien qua kiem thu HTTP that (khong phai
test client, vi test client co hanh vi khac) va sua thanh tra ve response
truc tiep, khong `raise` o bat ky nhanh nao.

**3. XOAY VONG NHAT KY (logrotate)** cho cac file log con lai: da do that
`console-pi-fallback.log` ghi 1 dong moi 2 phut va chua tung duoc xoay vong -
sau vai thang dung ngoai hien truong co the len hang tram MB. Day the nho
la mot trong nhung nguyen nhan hong Pi pho bien nhat.

## 0.4.17

**Va lo hong chen co lenh (argument injection) qua dia chi/tai khoan** o 4
noi: Ping/Traceroute, MTU Discovery, Kiem tra TLS, va tab SSH. Ra soat lai
code phat hien, khong phai da gap that.

Mau kiem tra dau vao cu (`[A-Za-z0-9.\-:]`) cho phep dau "-" o **vi tri dau
chuoi**. Voi cong cu goi subprocess dang list (khong `shell=True`) thi
khong chen duoc lenh shell, nhung mot gia tri nhu `--flood` co the bi
`ping` hieu nham la MOT CO LENH thay vi dia chi - va tien trinh Flask nay
chay duoi quyen root nen `ping --flood` se chay duoc that.

**Rieng tab SSH nghiem trong hon nhieu**: host/user o day duoc go THANG
vao mot shell that qua tmux de chay lenh `ssh`. Mot host bat dau bang
`-oProxyCommand=<lenh tuy y>` la ky thuat chen co SSH THAT SU va nguy
hiem - cho phep chay lenh tuy y ngay khi ket noi, hoan toan khong can
dung den cac ky tu `; $ \` & |` da bi chan tu truoc.

Sua bang cach bat buoc **ky tu dau tien phai la chu hoac so**, khong duoc
la dau "-" hay bat ky ky tu dac biet nao khac, o ca 4 noi. Da kiem thu voi
cac chuoi chen thuc te (`-f`, `--flood`, `-oProxyCommand=...`, `-l`,
`-4.4.4.4`) - deu bi chan; dia chi/tai khoan hop le (`8.8.8.8`,
`google.com`, `switch-01.lan`, `fe80::1`) van hoat dong binh thuong qua
kiem thu voi phien tmux that.

## 0.4.16

**Phat hien nghiem trong nhat trong dot ra soat toi nay: tinh nang "Tab
Terminal giong tab SSH" (them o soan lenh, nut Dan tu chon cach dan) o
0.4.6 CHUA BAO GIO DUOC TRIEN KHAI THAT SU len may, du da bao voi nguoi
dung la xong.** Nguyen nhan: luc do khong co quyen sudo nen chi dua lenh
`sudo cp ...` de nguoi dung tu chay, nhung dong lenh do khong duoc thuc
hien (co le bi cuon troi giua luc dang xu ly su co Bluetooth ngay sau do).
Nhung lan sau co sudo lai chi deploy CAC FILE lien quan Bluetooth, khong
kiem tra lai toan bo hang doi deploy con thieu.

Phat hien bang cach **so sanh truc tiep `diff -rq src/ui /opt/console-pi/ui`**
- day nen la buoc kiem tra chuan sau moi phien lam viec dai co xen ke nhieu
chu de, thay vi tin tren tri nho hoi thoai la "da deploy roi". Da deploy du
`soanlenh.py`, `ssh.py`, `terminal.py`, `docs.py` va xac nhan lai qua HTTP
that: ca 2 tab deu co o soan lenh, route `/terminal/paste` va `/ssh/paste`
chay dung.

## 0.4.15

**Da vao duoc mang qua Bluetooth PAN that su tren Windows 11** - ghi lai dung
quy trinh vao tai lieu (thay cho phan canh bao loi truoc do):

1. **Ghep cap phai khoi dong TU PHIA WINDOWS** (Settings -> Bluetooth &
   devices -> Add device), khong phai bam Ghep cap tren Pi truoc.
2. Ghep xong Windows bao "Connected" nhung **CHUA vao mang duoc ngay** - day
   chi la ghep cap Bluetooth thuan tuy.
3. **Buoc quyet dinh**: mo Devices and Printers kieu cu (`control printers`)
   -> chuot phai ConsolePi -> **Connect using -> Access point**.

Da kiem chung that sau buoc 3: giao dien `bnep0` xuat hien trong cau `pan0`,
dnsmasq cap dung IP (`192.168.60.29`) cho may tinh.

Them nhac nho: phai bam **Trust** cho may tinh sau khi xong (nhu da lam voi
ban phim) - thieu buoc nay thi lan sau Bluetooth rot la phai lam lai tu buoc 3
moi lan, khong tu noi lai duoc.

## 0.4.14

**Ghi lai quy trinh ghep ban phim Bluetooth DA THANH CONG that** vao tai lieu
(muc dau tien cua trang Bluetooth), sau nhieu vong debug that tren may cua
nguoi dung:

- Ghep MOI: giu nut Connect LIEN TUC den khi den nhap nhay NHANH, RIENG luc do
  moi bam Ghep cap tren web - bam tre la that bai kieu "khong tim thay" du
  ban phim hoan toan binh thuong.
- Sau khi ghep, ban phim TU DONG ngat sau vai giay khong go gi - day la tinh
  nang tiet kiem pin cua chinh ban phim, khong phai loi, khoa lien ket
  (Bonded) khong mat.
- De NOI LAI (khac voi ghep lai): bam NHANH 1 cai vao nut Connect (KHONG giu
  lau - giu lau vao lai che do ghep MOI, co nguy co lam mat khoa cu).
- **Canh bao quan trong nhat**: TUYET DOI khong bam "Ghep cap lai" khi ban
  phim chi don gian mat ket noi tam thoi (van "da ghep, chua noi") - nut do
  XOA khoa lien ket dang co roi ghep MOI TU DAU, mo lai nguy co that bai neu
  ban phim khong dang o che do ghep cap dung luc do bam.
- Them lenh kiem tra khoa lien ket con luu tren dia hay khong (nguon su that
  cuoi cung, khong phu thuoc bo nho tam cua bluetoothctl):
  `sudo cat /var/lib/bluetooth/*/<mac>/info` - tim muc `[LinkKey]`.

## 0.4.13

**Ban phim Bluetooth bi mat ghep cap** - tim ra do o "🔄 Reset Bluetooth" o
cuoi trang co o tick "Quen tat ca thiet bi da ghep cap". Nguoi dung dang loi
khac (khong vao mang PAN duoc) nen thu bam Reset de "sua dai", vo tinh tick
nham o do va mat luon ban phim da ghep cap thanh cong truoc - phai ghep lai
tu dau oan uong. Xac nhan lai: **phia Pi khong he hong gi** (adapter, Class,
cac dich vu deu binh thuong), ghep lai la duoc ngay.

Sua de khong lap lai: hop `confirm()` gio **doc trang thai o tick truoc khi
hoi** - neu dang tick "Quen tat ca" thi hien canh bao rieng, noi thang se mat
ban phim/chuot/dien thoai va phai ghep lai tu dau, kem ghi ro **loi vao mang
PAN khong lien quan gi den viec nay** (tranh nham tuong reset-quen-het se sua
duoc loi PAN). Truoc day chi co 1 dong canh bao chung chung "Reset Bluetooth?"
du co tick "Quen tat ca" hay khong, de bam qua ma khong doc ky.

## 0.4.12

Sua loi **man hinh Pi hien trang trang "Method Not Allowed"** sau khi thu
ket noi Bluetooth. Bat duoc qua log that: `GET /bt-connect HTTP/1.1" 405`.

NGUYEN NHAN GOC, anh huong CA APP chu khong rieng Bluetooth: rat nhieu route
POST (`bt-connect`, `bt-unpair`, `wifi-*`, `bt-scan`...) hien trang HTML
thang ra sau khi xu ly xong, KHONG chuyen huong. Vi vay dia chi tren trinh
duyet dung nguyen o duong dan POST do sau khi bam nut. Tren man hinh cam
ung, chi can cu chi **keo xuong lam moi (pull-to-refresh)** la trinh duyet
gui lai dung request do nhung bang GET - Flask tu choi (route chi cho
POST), Werkzeug hien trang loi trang boc xau xi, nguoi dung tuong ca
dashboard bi vo.

Sua tan goc (doi het cac route POST sang chuyen huong sau khi xu ly) la
thay doi lon dung vao rat nhieu file, rui ro cao. Thay bang cach an toan
hon: bat loi 405 O TOAN APP (`app.py`), dua nguoi dung ve lai trang truoc
do (doc tu header Referer) thay vi hien trang loi - cho **moi route trong
app**, khong chi Bluetooth. Co kiem tra Referer phai cung goc voi chinh
Pi truoc khi tin, tranh bi dan sang trang la neu header do bi gia mao.

## 0.4.11

**Nut "Ket noi mang (PAN)" lam NGUOC chieu.** Nut nay goi
`Network1.Connect("nap")` - tuc la bao *Pi di XIN mang cua may kia*, trong khi
viec can lam la *may kia xin mang cua Pi*. May Windows chi quang ba **PANU**
(vai tro may xin mang), khong co dich vu NAP, nen BlueZ tra ve
`Operation is not supported` - da do that tren may nguoi dung. Nguoi dung doc
dong loi do khong the biet phai lam gi.

Trong Bluetooth PAN, ben CHO mang (NAP) **khong bao gio tu bat dau ket noi
duoc** - luon phai ben XIN mang (PANU) goi sang. Pi la ben cho mang nen chi
co the ngoi doi. Nay nut kiem tra truoc: neu may kia khong co dich vu NAP thi
noi thang viec can lam **o may do**, thay vi nem ra dong loi kho hieu.

**Tai lieu - cai bay lon nhat tren Windows:** trang *Settings &rarr; Bluetooth
&amp; other devices* (giao dien moi) KHONG HE CO chuc nang PAN - o do ConsolePi
chi hien "Connected" kem moi nut *Remove device*. Phai dung Control Panel kieu
cu (`control printers`, hoac `explorer shell:::{A8A91A66-...}`, hoac qua
`ncpa.cpl`). Da ghi ro ca 3 duong vao tai lieu, kem cach xu ly khi khong thay
dong "Connect using" (Windows luu danh sach dich vu tu luc ghep cap, phai xoa
o ca hai phia roi ghep lai).

Da kiem chung phia Pi hoan toan san sang: `pan0` dung la cau noi, DHCP lang
nghe tren 192.168.60.1, va adapter dang quang ba dung UUID NAP
(`00001116`) - xac nhan qua D-Bus.

## 0.4.10

**Phan biet "da ket noi Bluetooth" voi "da vao mang"** - dung cho gay hieu
nham cho nguoi dung: may ban ghep cap xong, dashboard hien "🟢 dang ket noi"
mau xanh, nhung vao `192.168.60.1` thi khong duoc.

Do tren may that: may ban `DESKTOP-I2O01BN` co `Connected: yes` nhung
**khong he co giao dien `bnep` nao gan vao cau `pan0`, dnsmasq chua cap IP
cho ai**. Tuc la moi ket noi Bluetooth (Windows tu noi ho so am thanh khi
ghep cap xong), chua he vao mang. Pi la ben CHO mang nen **khong the tu ep**
may tinh vao mang - may tinh phai tu chu dong noi vao dich vu NAP.

Nay trang Bluetooth doc dau hieu THAT (co `bnep` trong cau `pan0` + IP da cap
trong file lease cua dnsmasq) va hien 3 trang thai khac nhau cho may tinh/
dien thoai:
- 🟢 **da vao mang** (kem IP da cap)
- 🟡 **co ket noi Bluetooth, CHUA vao mang** - kem huong dan ngay tai cho:
  chuot phai ConsolePi &rarr; Connect using &rarr; Access point
- ⚪ da ghep, chua noi

**Xac nhan: ghep nhieu thiet bi cung luc VAN DUOC.** Do tren may nay: ban
phim (HID) va may ban (PAN) cung ket noi mot luc, khong xung dot.

## 0.4.9

**Da ghep duoc ban phim Bluetooth tren may that** (Samsung `04E8:7021`):
Paired/Bonded/Trusted/Connected deu `yes`, nhan tao ra thiet bi nhap lieu
that (`input: Bluetooth Keyboard`). selftest tu 33 dat/3 luu y len
**36 dat/2 luu y**.

Hai dieu do duoc trong luc ghep, deu di nguoc gia dinh ban dau:

- **Ban phim nay KHONG can go ma nao ca.** Agent khong he duoc BlueZ hoi cau
  nao - no dung kieu ghep "Just Works". Nghia la nguoi dung noi dung: *ban
  phim dau can ghep bang ma so*. Voi ban phim kieu nay, man hinh khong hien
  so gi la BINH THUONG, khong phai loi. (Cac sua o 0.4.7 ve nhanh ma PIN van
  can, nhung danh cho ban phim doi cu hon.)
- **Ban phim mat 116 GIAY moi chiu quang ba** ke tu luc bat dau quet. Cua so
  quet cu 20 giay - va ca muc 60 giay thu o ban sua truoc - **deu khong du**.
  Nay de **150 giay**, kem dem nguoc hien ngay tren trang de nguoi dung biet
  con bao lau. Vi qua trinh dung ngay o buoc quet nen truoc day khong he de
  lai dau vet nao trong log, rat kho lan ra nguyen nhan.

Tai lieu: noi ro nhieu ban phim khong can ma, va nhan manh den phai nhap nhay
NHANH moi la che do ghep cap.

## 0.4.8

Hai loi that lam **khong ghep duoc ban phim Bluetooth**, ca hai deu do dac
tren may that (khong phai doc code suong):

- **Pi tu khai la thiet bi "khong ro loai"**. BlueZ tu sinh class
  `0x420000` - major class = `0x00` (Miscellaneous). Nhieu ban phim Bluetooth
  chi chiu ghep voi host tu khai la MAY TINH, thay "khong ro loai" thi bo qua.
  Nay dat `Class = 0x000100` trong `/etc/bluetooth/main.conf` (khoa nay von co
  san trong file nhung bi chu thich). Da do lai sau khi sua: class thanh
  `0x420100` (major = Computer) va **van giu nguyen bit Networking** nen
  Bluetooth PAN khong he anh huong (pan0 giu nguyen 192.168.60.1). install.sh
  cung dat khoa nay nen cai lai khong mat.

- **Tat quet NGAY TRUOC khi ghep cap**. Luong cu: quet -> thay thiet bi ->
  `scan off` -> `pair`. BlueZ coi thiet bi vua quet duoc ma chua ghep la "tam
  thoi" va xoa khoi danh sach rat nhanh sau khi ngung quet, nen den luc `pair`
  thi bao thang `Device ... not available` du vai giay truoc con thay ro. **Da
  tai hien duoc dung loi nay 2 lan tren may that.** Nay giu quet chay suot ca
  qua trinh pair/trust/connect, chi tat o khoi `finally`.

## 0.4.7

Sua loi ghep cap **ban phim Bluetooth kieu PIN cu** - dung cai lam nguoi dung
thay "vo ly": ban phim doi go mot day so, nhung tren man hinh khong hien so nao.

- **Nhanh PIN kieu cu bi bo quen hoan toan o giao dien.** Agent nhan yeu cau
  `RequestPinCode` (Bluetooth 2.x), tra ve `0000` va ghi trang thai
  `kind="pin"` - nhung trang web CHI co nhanh hien `passkey` va `confirm`,
  khong he co nhanh nao hien `pin`. Ket qua: ban phim dung cho go ma, nguoi
  dung chi thay "dang ghep cap" roi treo den het gio. Nay ca 2 kieu (passkey
  doi moi va PIN kieu cu) deu hien so to ro giua man hinh kem huong dan.
- **Ban phim lien touchpad bi nhan dien nham.** Theo chuan Bluetooth, 2 bit
  loai thiet bi co 4 gia tri: `01` = ban phim, `11` = ban phim lien
  chuot/touchpad. Ban dau chi bat `01` nen loai combo (rat pho bien) bi coi la
  "thiet bi khong go duoc" va bi day sang nhanh ma co dinh, khong hien ma.
  Kiem thu voi cac ma CoD that da bat duoc loi nay truoc khi giao.
- **Ma PIN cho ban phim gio sinh ngau nhien** thay vi co dinh `0000` (an toan
  hon, va van dung cach lam chuan). Rieng thiet bi khong go duoc (tai nghe,
  loa) van giu ma co dinh vi ma cua chung do nha may quy dinh - sinh ngau
  nhien la chac chan hong.
- **Them 2 nhanh trang thai truoc day cung bi bo roi**: `need-passkey` (thiet
  bi doi Pi nhap ma do chinh no hien - ban phim khong dung kieu nay) va
  `cancelled` (thiet bi huy giua chung), deu noi ro ly do thay vi im lang.
- **Agent nay ghi log tung buoc** ra `journalctl -u bt-agent`. Truoc day chi
  in 1 dong luc khoi dong nen ghep cap that bai la khong con dau vet nao de
  lan ra nguyen nhan - da xac nhan dung tren may that.
- Tai lieu: them muc giai thich vi sao ban phim chua ket noi van go duoc ma
  xac thuc (day la cach chuan, Windows/macOS cung vay).

## 0.4.6

**Tab Terminal nay giong tab SSH**: them o soan tap lenh ngay duoi khung
terminal (chon tap lenh tu Thu vien -> sua -> Copy / Dan tu clipboard / Dan vao
terminal), gui bang fetch nen khong tai lai trang va khong dinh hop thoai
"Leave site?". Khung terminal cung cao them (`100vh-330px`).

Khoi soan lenh duoc tach ra `src/ui/soanlenh.py` dung chung cho ca 2 tab - sua
1 lan la ca 2 cung duoc, khong bi lech nhau theo thoi gian. Moi tab giu rieng
noi dung dang soan (soan do o tab SSH khong de len tab Terminal).

**Nut Dan tu chon dung cach dan** dua vao chuong trinh dang chay trong terminal
(`tmux display-message -p '#{pane_current_command}'`):
- Dang o **shell cua Pi** (bash/sh/zsh): dan ca khoi, **khong dong nao chay** -
  an toan cho shell quyen root, nguoi dung bam Enter moi chay.
- Dang **SSH/console vao thiet bi** (ssh, microcom...): gui tung dong, cho
  thiet bi in xong moi gui tiep (khoi roi mat ky tu dau dong), dong cuoi de
  nguoi dung tu bam Enter.

Chon nham cach la hong: dan ca khoi vao thiet bi thi mat chu, con gui tung
dong vao shell quyen root thi tung lenh se CHAY luon. Da kiem chung: bash ->
'bash', chay ssh -> 'ssh', chay python3 -> 'python3'. *Gioi han that da do
duoc:* neu chay mot **script bash** tu no noi chuyen voi thiet bi thi tmux van
bao "bash" nen se dan ca khoi - truong hop hiem, da ghi ro trong tai lieu.

## 0.4.5

**Trang Tai lieu lam lai theo tab** cho de tra, de doc, de tim:
- Cot ben trai la danh sach muc **xep theo nhom** (He thong / Ket noi / Lam viec
  hang ngay / Cong cu mang / Thiet bi & nguon / Su co), bam la mo dung muc do -
  khong con cuon mot trang dai 20 muc.
- **O tim kiem toan van**: go tu khoa thi tung muc hien **so lan xuat hien**, cac
  muc khong khop tu an di, va tu mo muc khop dau tien de thay ket qua ngay.
  Chi muc tim kiem doc tu chinh noi dung dang co tren trang nen **khong lam trang
  nang them**.
- Nut **Xem tat ca** de doc lien mach, dung Ctrl+F cua trinh duyet, hoac in ra giay.
- Giu nguyen duong dan cu kieu `/docs#suco`, va nho muc dang xem lan truoc.
- Muc nao quen xep nhom van hien ra o nhom "Khac" - them muc moi khong so bi mat.

**Cap nhat noi dung tai lieu** cho khop nhung gi vua sua:
- Cach o mat khau tab SSH hoat dong, va vi sao co tinh khong dung `sshpass -p`.
- Vi sao dan tap lenh phai cham (doi thiet bi in xong), va xu ly `--More--`.
- Con lan chuot cuon man hinh (`mouse on`).
- Them 2 su co that vao bang su co: SSH bao "no matching key exchange method
  found" voi thiet bi cu (kem canh bao KHONG duoc them `ssh-dss`), va dan tap
  lenh bi mat ky tu dau dong.
- Sua "6 cong cu mang moi" thanh 5 (Ping lien tuc da bo o 0.4.1).

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

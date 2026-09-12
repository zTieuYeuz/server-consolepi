@echo off
REM ============================================================
REM  Console Pi - Ung dung mau de KIEM CHUNG co che "nhieu file"
REM
REM  Ung dung nay khong cai gi that ca. Muc dich duy nhat: chung
REM  minh bang BANG CHUNG GHI RA DIA rang toan bo chuoi da chay
REM  dung, de biet chac cac ung dung nhieu file THAT SU (Office,
REM  bo cai phuc tap...) se chay duoc.
REM
REM  No kiem tra 4 dieu - dung 4 dieu ma mot ung dung that can:
REM    1. Thu muc ung dung da duoc chep sang may dich
REM    2. Thu muc CON cung duoc chep (robocopy /E chay dung)
REM    3. Lenh cai chay duoc voi quyen he thong
REM    4. `cd /d` dat dung thu muc - doc duoc file bang duong dan
REM       TUONG DOI (day la dieu Office 365 can:
REM       "setup.exe /configure Configuration.xml")
REM
REM  Ket qua ghi ra: C:\ConsolePi\ket-qua-ung-dung.txt
REM ============================================================

set KQ=C:\ConsolePi\ket-qua-ung-dung.txt
if not exist C:\ConsolePi mkdir C:\ConsolePi

echo ================================================ > "%KQ%"
echo  KIEM CHUNG CO CHE UNG DUNG NHIEU FILE >> "%KQ%"
echo  Thoi diem: %DATE% %TIME% >> "%KQ%"
echo  Chay boi tai khoan: %USERNAME% >> "%KQ%"
echo  Thu muc dang dung: %CD% >> "%KQ%"
echo ================================================ >> "%KQ%"
echo. >> "%KQ%"

REM --- 1. Lenh cai co chay khong ---
echo [ DAT ] 1. Lenh cai da chay - neu khong thi file nay khong ton tai >> "%KQ%"

REM --- 2. cd /d co dat dung thu muc ung dung khong ---
REM     Doc file canh no bang duong dan TUONG DOI (khong ghi duong
REM     dan tuyet doi) - dung y het cach Office goi Configuration.xml
if exist "cauhinh.txt" (
    echo [ DAT ] 2. Doc duoc file tuong doi "cauhinh.txt" - cd /d dung >> "%KQ%"
    echo         Noi dung: >> "%KQ%"
    type "cauhinh.txt" >> "%KQ%"
) else (
    echo [ LOI ] 2. KHONG doc duoc "cauhinh.txt" bang duong dan tuong doi >> "%KQ%"
    echo         Nghia la lenh cai khong chay trong dung thu muc ung dung. >> "%KQ%"
)
echo. >> "%KQ%"

REM --- 3. Thu muc con co duoc chep khong ---
if exist "dulieu\thumuc-con\file-sau-3-tang.txt" (
    echo [ DAT ] 3. Thu muc con da duoc chep day du ^(robocopy /E dung^) >> "%KQ%"
    type "dulieu\thumuc-con\file-sau-3-tang.txt" >> "%KQ%"
) else (
    echo [ LOI ] 3. THIEU thu muc con - robocopy khong chep het >> "%KQ%"
)
echo. >> "%KQ%"

REM --- 4. File noi bo cua Console Pi co bi chep nham sang khong ---
if exist "_thongtin.json" (
    echo [ XEM LAI ] 4. File noi bo _thongtin.json BI chep sang may nay >> "%KQ%"
) else (
    echo [ DAT ] 4. File noi bo _thongtin.json da duoc loai tru dung >> "%KQ%"
)
echo. >> "%KQ%"

echo --- Danh sach toan bo file da duoc chep sang --- >> "%KQ%"
dir /s /b >> "%KQ%" 2>&1
echo. >> "%KQ%"
echo ================================================ >> "%KQ%"
echo  KET THUC - neu thay du 4 dong [ DAT ] o tren >> "%KQ%"
echo  thi co che ung dung nhieu file chay hoan toan dung. >> "%KQ%"
echo ================================================ >> "%KQ%"

exit /b 0

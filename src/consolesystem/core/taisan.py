# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Doc TAI NGUYEN van ban (HTML/CSS/JS/PowerShell...) da tach ra khoi ma Python (B6): file nam o `consolesystem/assets/<duong dan>`.
Tra ve DUNG tung byte chuoi truoc kia nam trong ma (doc nhi phan -> utf-8, giu nguyen xuong dong) nen dau ra trang/script khong doi.
Nap MOT LAN luc import module (nhu hang so cu); thieu file -> loi ro rang ngay luc khoi dong (ban phat hanh da kiem ma bam tung file)."""
import os

GOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def doc(duong):
    with open(os.path.join(GOC, duong), "rb") as f:
        return f.read().decode("utf-8")

#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# In bang ket qua thu-script-kho.sh tu ket-qua.json
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8-sig"))
m = d.get("may", {})
print(f"May mau: {m.get('ten')} build {m.get('build')} ({m.get('ban')}) user={m.get('user')} admin={m.get('admin')} PS {m.get('ps')}")
cp = {x["id"]: x["loi"] for x in d.get("cu_phap", [])}
lan = d.get("lan", [])
sau = {x["id"]: x["kiem"] for x in d.get("sau_khoi_dong", [])}
hs = d.get("ho_so_mac_dinh", {})
hs_loi = {}
for x in hs.get("muc", []):
    if not x["dung"]: hs_loi.setdefault(x["id"], []).append(f"{x['name']} mong={x['mong']} co={x['co']}")
ids = [x["id"] for x in (lan[0]["kq"] if lan else [])] or sorted(cp)
def tim(l, i): return next((x for x in (lan[l]["kq"] if len(lan) > l else []) if x["id"] == i), None)
bad = 0
print(f"{'script':34} {'cu phap':8} {'luot1':>12} {'luot2':>12} {'sau reboot':10} {'Default':8}")
for i in ids:
    a, b = tim(0, i), tim(1, i)
    def f(x): return "-" if not x else f"{'OK' if x['ma']==0 else 'ma'+str(x['ma'])}/{'DAT' if x['kiem'] else 'LOI'} {x['giay']}s"
    cpok = not cp.get(i)
    sr = sau.get(i)
    hok = i not in hs_loi if hs.get("nap_duoc") else None
    ok = cpok and a and b and a["ma"] == 0 and b["ma"] == 0 and a["kiem"] and b["kiem"] and sr is True and hok is not False
    bad += 0 if ok else 1
    print(f"{'DAT ' if ok else 'LOI '}{i:30} {'ok' if cpok else 'LOI':8} {f(a):>12} {f(b):>12} {str(sr) if sr is not None else '-':10} {str(hok) if hok is not None else '-':8}")
    if not cpok: print("      cu phap:", cp[i])
    if i in hs_loi: print("      Default User:", hs_loi[i])
print(f"\nTONG: {len(ids)-bad}/{len(ids)} dat, {bad} loi.  hoan_tat={d.get('hoan_tat')}  ho so mac dinh nap duoc={hs.get('nap_duoc')}")
sys.exit(1 if bad else 0)

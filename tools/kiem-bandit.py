#!/usr/bin/env python3
"""V7-1 (2.0.8): bandit KHONG con --exit-zero. So phat hien muc >= Medium (severity va confidence) voi NGUONG da biet (tools/bandit-nen.txt);
vuot nguong (co phat hien MOI) thi CI do. Giam duoc thi ha nguong trong tep nen. Dung: kiem-bandit.py <duong bandit>"""
import json
import os
import subprocess
import sys

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
bandit = sys.argv[1] if len(sys.argv) > 1 else "bandit"
r = subprocess.run([bandit, "-q", "-r", "src", "-ll", "-ii", "-f", "json"], cwd=GOC, capture_output=True, text=True)
try:
    kq = json.loads(r.stdout)["results"]
except (ValueError, KeyError):
    print("bandit khong chay duoc:", (r.stderr or r.stdout)[-400:])
    sys.exit(2)
nen = int(open(os.path.join(GOC, "tools", "bandit-nen.txt")).read().split()[0])
print("bandit: %d phat hien muc >= Medium (nguong da biet: %d)" % (len(kq), nen))
if len(kq) > nen:
    for x in kq:
        print("  %s:%s %s %s" % (x["filename"], x["line_number"], x["test_id"], x["issue_text"][:90]))
    print("!!! Co phat hien MOI so voi nen. Sua, hoac (neu la false positive da duyet) # nosec co ly do.")
    sys.exit(1)
if len(kq) < nen:
    print("(da giam: ha tools/bandit-nen.txt xuong %d de khoa thanh qua)" % len(kq))

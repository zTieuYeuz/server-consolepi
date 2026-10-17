#!/bin/bash
# CHI DE TEST (may build): bien dich TOAN BO file .py trong repo bang Python 3.11 cua chroot i386 (Debian 12).
# Ban i386 chay Python 3.11 - cu phap moi cua Python 3.12+ (f-string long nhau cung loai dau nhay, ...)
# lam dich vu dashboard chet khi khoi dong (da gap that o 1.9.0, chi lo ra o ban i386).
# Dung: bash iso/test/kiem-python311.sh      -> in "loi 3.11: 0" la dat
CH=/build/console-system-i386/chroot; D=$CH/tmp/repo-py311
mkdir -p "$D" && rsync -a --delete --include='*/' --include='*.py' --exclude='*' "$(dirname "$0")/../../" "$D/"
chroot "$CH" /usr/bin/python3.11 -c "
import py_compile,glob
bad=0;n=0
for f in sorted(glob.glob('/tmp/repo-py311/**/*.py',recursive=True)):
    n+=1
    try: py_compile.compile(f,doraise=True,cfile='/tmp/x.pyc')
    except Exception as e: bad+=1; print(f, str(e)[:200])
print('file',n,'loi 3.11:',bad)"

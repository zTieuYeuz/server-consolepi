#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# ====================================================================
# THU HANG LOAT nhieu phan mem cai im lang + go cai dat (chay tren MAY BUILD).
# Moi dong cua file danh sach (ngan cach bang dau |, dong bat dau # bi bo qua):
#     ten | url tai ve | ten file luu | tham so cai | lenh go (de trong hoac "auto")
# Voi moi phan mem: tai tu URL chinh hang -> thu-silent.sh (cai + go, GO_CAI) -> neu cai KHONG DAT
# thi tu thu --tu-do (cac tham so thuong gap) -> ghi 1 dong vao tong-hop.tsv -> XOA bo cai (do day o).
# Ket qua day du: /build/test/ket-qua-phan-mem/ (log + json tung phan mem).
#
#   thu-hang-loat.sh danh-sach.tsv
# ====================================================================
set -u
DS=${1:?thieu file danh sach}
KQ=/build/test/ket-qua-phan-mem
TAM=/build/test/tai-phan-mem
mkdir -p $KQ $TAM
TH=$KQ/tong-hop.tsv
[ -f $TH ] || printf 'ten\tfile\tkich_thuoc\tsha256\tket_qua\tgo_cai_that_su\tsach_sau_go\tthong_bao\n' > $TH

while IFS='|' read -r TEN URL FILE THAMSO GOCAI; do
  [ -z "${TEN// }" ] && continue
  case $TEN in \#*) continue;; esac
  [ -n "$FILE" ] || FILE=$(basename "${URL%%\?*}")
  F=$TAM/$FILE; LOG=$KQ/$(echo "$TEN" | tr ' /' '__').log
  echo "=== $TEN ($(date +%H:%M:%S))" | tee "$LOG"
  rm -f "$F"
  CON=$(df -BG --output=avail /build | tail -1 | tr -dc 0-9)
  [ "$CON" -lt 6 ] && { echo "HET CHO (${CON}G) - dung" | tee -a "$LOG"; break; }
  if ! curl -fsSL --retry 2 -m 1500 -A "Mozilla/5.0" -o "$F" "$URL"; then
    printf '%s\t%s\t\t\tKHONG_TAI_DUOC\t\t\t%s\n' "$TEN" "$FILE" "$URL" >> $TH; echo "  khong tai duoc" | tee -a "$LOG"; continue
  fi
  SZ=$(stat -c %s "$F"); SHA=$(sha256sum "$F" | cut -d' ' -f1)
  # file tai ve phai la bo cai (MZ) hoac .msi (D0CF) - khong phai trang HTML bao loi
  case $(head -c 2 "$F" | od -An -c | tr -d ' ') in
    MZ|\\320\\317) ;;
    *) printf '%s\t%s\t%s\t%s\tKHONG_PHAI_BO_CAI\t\t\t%s\n' "$TEN" "$FILE" "$SZ" "$SHA" "$URL" >> $TH
       echo "  khong phai bo cai (HTML?)" | tee -a "$LOG"; rm -f "$F"; continue;;
  esac
  GO=${GOCAI:-auto}
  OUT=$(GO_CAI="$GO" bash /build/test/thu-silent.sh "$F" "$THAMSO" 420 2>&1 </dev/null); RC=$?
  echo "$OUT" | tee -a "$LOG"
  KQ_TXT=OK; DUNG="$THAMSO"
  if [ $RC -ne 0 ]; then
    echo "  -> tham so '$THAMSO' KHONG DAT, thu --tu-do" | tee -a "$LOG"
    OUT=$(GO_CAI="$GO" bash /build/test/thu-silent.sh "$F" --tu-do 300 2>&1 </dev/null); RC=$?
    echo "$OUT" | tee -a "$LOG"
    if [ $RC -eq 0 ]; then
      DUNG=$(echo "$OUT" | sed -n 's/^THAM SO IM LANG: //p' | tail -1); KQ_TXT=SUA_THAM_SO
    else KQ_TXT=KHONG_IM_LANG; DUNG=""; fi
  fi
  GOTHAT=$(echo "$OUT" | grep -E '^  GO: .*=> (xong|khong_tu_thoat) ' | sed -n 's/^  GO: \(.*\)  => .*/\1/p' | tail -1)
  SACH=$(echo "$OUT" | sed -n 's/^  sau go: \(.*\)/\1/p' | head -1)
  GOIY=$(echo "$OUT" | sed -n 's/^  go goi y: .* -> \(.*\)/\1/p' | head -1)
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$TEN" "$FILE" "$SZ" "$SHA" "$KQ_TXT:$DUNG" "$GOTHAT" "$SACH" "goi y: $GOIY" >> $TH
  rm -f "$F"
done < "$DS"
echo "XONG $(date +%H:%M:%S)"

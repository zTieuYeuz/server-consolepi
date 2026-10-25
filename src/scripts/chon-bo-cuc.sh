# shellcheck shell=bash
# Console System - chon/chuyen BO CUC du lieu luc cai dat (install.sh nap file nay). Can bash.
# chon_bo_cuc <thu_muc_ma_nguon_goc>:
#   - da la bo cuc moi            -> khong lam gi
#   - may moi hoan toan           -> tao bo cuc moi san
#   - co du lieu bo cuc cu        -> SAO CHEP sang bo cuc moi + kiem ma bam; loi thi GIU bo cuc cu (cai dat van tiep tuc)
# Dat CS_KHONG_DOI_BO_CUC=1 de ep giu bo cuc cu. Ket thuc luon nap lai duong-dan.sh (CS_* cap nhat).
_cs_nhac() { if declare -F "$1" >/dev/null; then "$@"; else shift; echo "$*"; fi; }

chon_bo_cuc() {
    local goc="$1" lenh="$1/src/scripts/dichuyen.py"
    # shellcheck source=duong-dan.sh
    . "$goc/src/scripts/duong-dan.sh"
    if [[ "$CS_BO_CUC" == moi ]]; then return 0; fi
    if [[ -n "${CS_KHONG_DOI_BO_CUC:-}" ]]; then _cs_nhac warn "CS_KHONG_DOI_BO_CUC: giu bo cuc cu"; return 0; fi
    if [[ -n "${CONSOLE_PI_DATA:-}" ]]; then return 0; fi
    if [[ ! -d "$CS_GOC_CU" && ! -e "$CS_OPT/config.json" && ! -e "$CS_OPT/flask-secret.key" ]]; then
        python3 "$lenh" khoi-tao-moi --moi "$CS_GOC_MOI" >/dev/null \
            && _cs_nhac ok "Bo cuc du lieu moi: $CS_GOC_MOI" \
            || _cs_nhac warn "Khong tao duoc bo cuc moi - dung bo cuc cu"
    else
        # Co du lieu cu: dung dich vu ghi du lieu trong luc chep (khoi dong lai o cuoi cai dat)
        local s
        if [[ -z "${CS_KHONG_DUNG_DICH_VU:-}" ]]; then
            for s in console-pi-dashboard console-pi-tftp; do systemctl stop "$s" >/dev/null 2>&1 || true; done
        fi
        if python3 "$lenh" bo-cuc-moi --tu "$CS_GOC_CU" --opt "$CS_OPT" --moi "$CS_GOC_MOI" >/dev/null \
           && python3 "$lenh" kiem-bo-cuc --moi "$CS_GOC_MOI" >/dev/null; then
            _cs_nhac ok "Da chuyen du lieu sang $CS_GOC_MOI (ban cu van giu nguyen o $CS_GOC_CU de doi chieu)"
        else
            rm -rf "$CS_GOC_MOI.dang-chuyen"
            [[ -e "$CS_GOC_MOI/.bo-cuc-moi" ]] && python3 "$lenh" hoantac-bo-cuc --moi "$CS_GOC_MOI" >/dev/null 2>&1
            _cs_nhac warn "Chua chuyen duoc sang bo cuc moi - GIU bo cuc cu, khong mat gi (xem: $lenh bo-cuc-moi)"
        fi
    fi
    . "$goc/src/scripts/duong-dan.sh"
}

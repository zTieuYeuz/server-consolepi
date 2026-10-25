# shellcheck shell=sh
# Console System - xac dinh BO CUC du lieu cho script shell. Dung:  . /opt/console-pi/scripts/duong-dan.sh
# (tuong ung ui/duongdan.py cua Python). Chua co dau .bo-cuc-moi -> y het 1.9.5. POSIX sh.
CS_GOC_CU="${CS_GOC_CU:-/var/lib/console-pi}"
CS_GOC_MOI="${CS_GOC_MOI:-/var/lib/console-system}"
CS_OPT="${CS_OPT:-/opt/console-pi}"
if [ -n "${CONSOLE_PI_DATA:-}" ]; then
    CS_GOC="$CONSOLE_PI_DATA"
elif [ -e "$CS_GOC_MOI/.bo-cuc-moi" ]; then
    CS_GOC="$CS_GOC_MOI"
else
    CS_GOC="$CS_GOC_CU"
fi
if [ -e "$CS_GOC/.bo-cuc-moi" ]; then
    CS_BO_CUC=moi
    CS_DATA="$CS_GOC/data"
    CS_FILE_CONFIG="$CS_GOC/config/config.json"
    CS_FILE_PORT="$CS_GOC/config/port-names.json"
    CS_FILE_XOAY="$CS_GOC/config/screen-rotation"
    CS_FILE_FORCE_AP="$CS_GOC/config/force-ap.flag"
    CS_FILE_MAC_SPOOF="$CS_GOC/config/wifi-mac-spoof.flag"
    CS_FILE_FLASK_SECRET="$CS_GOC/secrets/flask-secret.key"
    CS_KHOA_SAMBA="$CS_GOC/secrets/samba-deploy.key"
    CS_FILE_CF_ACCESS="$CS_GOC/secrets/cf-access.json"
else
    CS_BO_CUC=cu
    CS_DATA="$CS_GOC"
    CS_FILE_CONFIG="$CS_OPT/config.json"
    CS_FILE_PORT="$CS_OPT/port-names.json"
    CS_FILE_XOAY="$CS_OPT/screen-rotation"
    CS_FILE_FORCE_AP="$CS_OPT/force-ap.flag"
    CS_FILE_MAC_SPOOF="$CS_OPT/wifi-mac-spoof.flag"
    CS_FILE_FLASK_SECRET="$CS_OPT/flask-secret.key"
    CS_KHOA_SAMBA="$CS_GOC/samba-deploy.key"
    CS_FILE_CF_ACCESS="$CS_GOC/cf-access.json"
fi
CS_DEPLOY="$CS_GOC/deploy"
CS_STORAGE="$CS_GOC/storage"

# C2-C5 - kho cap nhat, tab Cap nhat, nang cap, ha cap (25/10/2026)

- Kho (repo kho-console-pi, `src/capnhat.py`): luu goi `.cspkg` (da ma hoa), khoa goi boc theo tung may bang `khoa_may`, danh muc + tai lieu tin cay da ky; API `/api/cap-nhat/{danh-muc,goi,khoa-goi,bao-cao}`; kenh `thu-nghiem` chi cho may trong LAN. Nap ban: `tools/nap-ban.py`.
- May khach: `core/capnhat/{may,nangcap}.py`, UI `features/updates/`, runner `scripts/console-system-nang-cap.py` (don vi systemd rieng + don vi phuc hoi luc boot).
- Co the dung kho rieng: `updates/cau-hinh.json` {"kho_url","kho_token"}.

## Thu THAT tren .30 (khoa TEST, kho tam :8199, goi 2.0.x ky bang khoa thu)
| Kich ban | Ket qua |
|---|---|
| 2.0.0 -> 2.0.1 (co migration that) | XONG: kiem chu ky, giai ma, doi chieu tung file, migration, doi `current`, khoi dong lai, suc khoe, don ban cu |
| 2.0.2: migration hong co y | Tu hoan tac, du lieu khoi phuc, web van chay ban cu |
| 2.0.5: app.py hong khoi dong | Suc khoe that bai sau 90s -> hoan tac ve 2.0.3, web 302 binh thuong |
| 2.0.4: migration cham + kill -9 ca don vi | Job treo o `migration`; `phuc-hoi` (nhu luc boot) -> da hoan tac an toan |
| Ha cap 2.0.3 -> 2.0.1 | XONG (co sao luu trang thai hien tai truoc khi doi) |
| Danh muc cu trong bo nho dem | Dung thiet ke: phai bam "Kiem tra" de lay danh muc moi |
| Goi 2.0.3 tai do voi sha khac (goi cu con trong tai/) | Tu tai lai, khong dung goi cu |
| Du lieu schema moi hon ma | Tu choi (bao ve), tu hoan tac |

Da dung xong: .30 tra ve ban 1.9.5 cua repo, xoa cau hinh/khoa thu, schema du lieu = 1. Don vi `console-system-nang-cap-phuc-hoi.service` van cai tren .30.
Luu y van hanh: ha cap KHONG khoi phuc du lieu thi schema co the cao hon ma cu (da co kiem tra dieu kien); `hoantac` cua dichuyen chi lui duoc migration ma ban dang chay biet.

/* Console System - cac trang gioi thieu hien trong luc chep he thong.
 * Chi dung chu + mau (khong anh) de nhe va khong phu thuoc do phan giai.
 */
import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    // Nen toi phu KIN khung slideshow (lan thu dau con vien trang quanh slide)
    Rectangle { anchors.fill: parent; color: "#0B0E14"; z: -1 }

    // running: true (khong phu thuoc activatedInCalamares): lan thu dau slide
    // dung yen o trang 3 suot qua trinh cai.
    Timer {
        interval: 8000
        running: true
        repeat: true
        onTriggered: {
            if (presentation.currentSlide + 1 >= presentation.slides.length)
                presentation.currentSlide = 0;
            else
                presentation.goToNextSlide();
        }
    }

    component Trang: Slide {
        property string tieuDe: ""
        property string noiDung: ""
        Rectangle {
            anchors.fill: parent
            color: "#0B0E14"
            Column {
                anchors.centerIn: parent
                width: parent.width * 0.8
                spacing: 18
                Text {
                    text: tieuDe
                    color: "#38BDF8"
                    font.pixelSize: 30
                    font.bold: true
                    width: parent.width
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
                Text {
                    text: noiDung
                    color: "#E3E8EF"
                    font.pixelSize: 17
                    width: parent.width
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    lineHeight: 1.3
                }
            }
        }
    }

    Trang {
        tieuDe: "Chào mừng đến với Console System"
        noiDung: "Bộ công cụ cho kỹ sư mạng: console thiết bị, quét mạng, kiểm tra DHCP/DNS/MTU, triển khai Windows qua mạng - tất cả trong trình duyệt.\n\nPhát triển bởi zTieuYeuz."
    }
    Trang {
        tieuDe: "Dùng từ máy khác"
        noiDung: "Cài xong, màn hình máy này hiện sẵn địa chỉ dạng http://192.168.x.x. Mở trình duyệt trên laptop hoặc điện thoại cùng mạng rồi vào địa chỉ đó."
    }
    Trang {
        tieuDe: "Đăng nhập bằng tài khoản Linux"
        noiDung: "Trang web dùng chính tài khoản bạn vừa tạo ở bước trước. Không có mật khẩu mặc định nào được cài sẵn."
    }
    Trang {
        tieuDe: "An toàn khi cắm vào mạng khách"
        noiDung: "Các dịch vụ có thể gây ảnh hưởng mạng (DHCP, phát WiFi, TFTP, Samba) đều TẮT sẵn. Chỉ bật khi bạn chủ động bật trong giao diện."
    }
    Trang {
        tieuDe: "Tác giả"
        noiDung: "Console System do zTieuYeuz thiết kế và phát triển.\n© 2026 zTieuYeuz. Bảo lưu mọi quyền."
    }
    Trang {
        tieuDe: "Sắp xong rồi"
        noiDung: "Đang chép hệ thống vào ổ đĩa. Khi xong, rút USB ra và khởi động lại máy."
    }

    function onActivate() { presentation.currentSlide = 0; }
    function onLeave() { }
}

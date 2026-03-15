# 🎸 Frame2Sheet: YouTube to Ukulele/Guitar Sheet Music 🎶

**Frame2Sheet** là một ứng dụng Full-stack giúp người chơi nhạc cụ (Ukulele, Guitar) dễ dàng trích xuất khuông nhạc (Sheet/Tab) từ các video hướng dẫn trên YouTube và đóng gói chúng thành file PDF chất lượng cao, sẵn sàng để in ấn.

---

## 🌟 Tính năng nổi bật
* **Xử lý Video trực tiếp:** Chỉ cần dán link YouTube, ứng dụng sẽ tự động tải và xử lý.
* **Khoanh vùng trực quan:** Giao diện kéo-thả trên trình duyệt giúp chọn chính xác khu vực chứa khuông nhạc.
* **Thuật toán thông minh:** Sử dụng OpenCV để nhận diện sự thay đổi khung hình, chỉ trích xuất những dòng nhạc mới, tránh lặp lại.
* **Tối ưu hóa In ấn:** Tự động sắp xếp các dòng nhạc đã cắt vào trang giấy A4, có lề chuẩn cho việc đóng tập.
* **Chạy mượt mà trên Local:** Sử dụng Cookie trình duyệt để tránh bị YouTube chặn (Bot Detection).

---

## 🛠️ Công nghệ sử dụng
* **Backend:** Python, FastAPI, OpenCV, yt-dlp, Pillow.
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla JS).
* **Layout:** Canvas-based cropping logic.

---

## 🚀 Hướng dẫn cài đặt & Chạy Local

### 1. Yêu cầu hệ thống
* Python 3.10 trở lên.
* Trình duyệt Chrome/Edge (để lấy Cookie tự động cho YouTube).

### 2. Cài đặt
Mở Terminal và chạy các lệnh sau:

```bash
# Clone dự án
git clone [https://github.com/taiituan13/frame2sheet-web.git](https://github.com/taiituan13/frame2sheet-web.git)
cd frame2sheet-web

# Tạo và kích hoạt môi trường ảo
python -m venv venv
# Windows:
.\venv\Scripts\Activate
# macOS/Linux:
source venv/bin/activate

# Cài đặt thư viện
pip install fastapi uvicorn yt-dlp opencv-python numpy Pillow
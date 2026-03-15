import cv2
import numpy as np
import os
import uuid
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
from fastapi.middleware.cors import CORSMiddleware # Thêm dòng này

app = FastAPI(title="Sheet Music Generator API")

# MỞ CỔNG CORS ĐỂ GIAO TIẾP VỚI FRONTEND HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép mọi trang web gọi vào API này
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Cấu trúc dữ liệu nhận từ Frontend (Đã đổi sang tỷ lệ % float)
class SheetRequest(BaseModel):
    youtube_url: str
    x_pct: float
    y_pct: float
    w_pct: float
    h_pct: float

# 2. Hàm lõi xử lý video
def process_video_to_sheet(url: str, x_pct: float, y_pct: float, w_pct: float, h_pct: float, output_pdf: str):
    temp_video = f"temp_{uuid.uuid4().hex}.mp4"
    temp_dir = f"temp_tabs_{uuid.uuid4().hex}"
    
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    cap = None # Khởi tạo cap trước để block finally không bị lỗi
    
    try:
        print(f"⏳ Đang tải video từ: {url}")
        ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]',
        'outtmpl': temp_video,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("⏳ Bắt đầu trích xuất Sheet...")
        cap = cv2.VideoCapture(temp_video)
        if not cap.isOpened():
            raise Exception("Không thể mở video vừa tải.")

        # Lấy kích thước THỰC TẾ của video vừa tải về
        real_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        real_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        # Quy đổi tỷ lệ % ra pixel tương ứng
        x = int(x_pct * real_width)
        y = int(y_pct * real_height)
        w = int(w_pct * real_width)
        h = int(h_pct * real_height)
        
        # Đảm bảo không bị tràn viền
        x, y = max(0, x), max(0, y)
        w = min(int(real_width) - x, w)
        h = min(int(real_height) - y, h)

        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 5)) # Bỏ qua 5s đầu

        fps_extract = 2
        frame_interval = int(fps / fps_extract) if fps > 0 else 15
        
        count = 0
        saved_images = []
        prev_gray_roi = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if count % frame_interval == 0:
                roi_frame = frame[y:y+h, x:x+w]
                gray_roi = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)

                if prev_gray_roi is None:
                    img_path = os.path.join(temp_dir, f"tab_{count}.png")
                    cv2.imwrite(img_path, roi_frame)
                    saved_images.append(img_path)
                    prev_gray_roi = gray_roi
                else:
                    diff = cv2.absdiff(gray_roi, prev_gray_roi)
                    _, thresh = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
                    change_score = np.count_nonzero(thresh)
                    
                    area = w * h
                    if change_score > (area * 0.03): 
                        img_path = os.path.join(temp_dir, f"tab_{count}.png")
                        cv2.imwrite(img_path, roi_frame)
                        saved_images.append(img_path)
                        prev_gray_roi = gray_roi

            count += 1

       # --- BƯỚC C: XUẤT PDF VÀ DỌN DẸP ---
        if saved_images:
            print(f"✅ Đã cắt được {len(saved_images)} dòng tab. Đang ghép vào trang A4...")
            
            # Khởi tạo kích thước chuẩn của trang A4 (Độ phân giải 300 DPI)
            A4_W, A4_H = 2480, 3508 
            MARGIN = 120 # Lề giấy 120 pixel
            GAP = 60     # Khoảng cách giữa các dòng tab là 60 pixel
            
            AVAILABLE_W = A4_W - (2 * MARGIN)
            AVAILABLE_H = A4_H - (2 * MARGIN)

            pages = [] # Mảng chứa các trang A4
            
            # Tạo tờ giấy A4 đầu tiên
            current_page = Image.new('RGB', (A4_W, A4_H), 'white')
            y_offset = MARGIN

            for img_path in saved_images:
                img = Image.open(img_path).convert('RGB')
                
                # Tính toán tỷ lệ để thu phóng ảnh vừa khít chiều ngang trang giấy
                aspect_ratio = img.height / img.width
                new_w = AVAILABLE_W
                new_h = int(new_w * aspect_ratio)
                
                # Resize ảnh cho sắc nét
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # Kiểm tra xem dán tấm ảnh này vào có bị tràn tờ giấy không?
                if y_offset + new_h > AVAILABLE_H and y_offset > MARGIN:
                    # Tràn rồi -> Lưu tờ hiện tại vào mảng, lấy tờ A4 mới ra
                    pages.append(current_page)
                    current_page = Image.new('RGB', (A4_W, A4_H), 'white')
                    y_offset = MARGIN # Reset tọa độ Y về đầu trang

                # Dán ảnh vào tờ giấy
                current_page.paste(img_resized, (MARGIN, y_offset))
                
                # Cộng dồn tọa độ Y cho tấm ảnh tiếp theo
                y_offset += new_h + GAP

            # Đừng quên thêm tờ giấy cuối cùng (dù chưa dán đầy) vào mảng
            pages.append(current_page)

            # Xuất toàn bộ các tờ A4 ra file PDF
            pages[0].save(output_pdf, save_all=True, append_images=pages[1:])
            print(f"🎉 Hoàn tất! File in A4 đã sẵn sàng tại: {output_pdf}")
        else:
            raise Exception("Không trích xuất được hình ảnh nào từ vùng đã chọn.")
    finally:
        # Nhả file video ra trước khi xóa
        if cap is not None and cap.isOpened():
            cap.release()
            
        if os.path.exists(temp_video):
            try:
                os.remove(temp_video)
            except Exception as e:
                print(f"Cảnh báo: Không thể xóa {temp_video}: {e}")
                
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)

# 3. API Endpoint
@app.post("/api/generate-sheet")
async def generate_sheet_endpoint(req: SheetRequest):
    output_filename = f"sheet_{uuid.uuid4().hex[:8]}.pdf"
    
    try:
        # Truyền các biến _pct vào hàm xử lý
        process_video_to_sheet(
            url=req.youtube_url, 
            x_pct=req.x_pct, 
            y_pct=req.y_pct, 
            w_pct=req.w_pct, 
            h_pct=req.h_pct, 
            output_pdf=output_filename
        )
        
        return FileResponse(
            path=output_filename, 
            filename="Sheet_Nhac.pdf", 
            media_type='application/pdf'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

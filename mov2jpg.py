import cv2
import os

def extract_first_frame(directory):
    # 支援的影片副檔名
    valid_extensions = ('.mov', '.MOV', '.MP4', '.mp4')
    
    # 確保輸出目錄存在（也可以直接存在同目錄）
    for filename in os.listdir(directory):
        if filename.endswith(valid_extensions):
            video_path = os.path.join(directory, filename)
            
            # 使用 OpenCV 開啟影片
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print(f"無法開啟影片: {filename}")
                continue
            
            # 讀取第一幀 (success 為布林值, frame 為影像矩陣)
            success, frame = cap.read()
            
            if success:
                # 產生新的圖片檔名
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(directory, f"{base_name}.jpg")
                
                # 儲存為 JPEG
                cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                os.remove(video_path)
                print(f"成功提取: {output_path}")
            else:
                print(f"讀取失敗: {filename}")
            
            # 釋放資源
            cap.release()

# 使用方式
# extract_first_frame('/你的/影片/路徑')
extract_first_frame('.')

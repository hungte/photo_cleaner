#!/usr/bin/env python3

import cv2
import os

def get_blur_score(image):
    """計算影像的拉普拉斯方差，得分越高代表越清晰"""
    if image is None:
        return 0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def extract_best_frame(directory):
    # 支援的影片副檔名
    valid_extensions = ('.mov', '.mp4')

    for filename in os.listdir(directory):
        if filename.lower().endswith(valid_extensions):
            video_path = os.path.join(directory, filename)
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                print(f"無法開啟影片: {filename}")
                continue

            # --- 邏輯優化：設定選幀範圍 ---
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 1. 為了避開手機對焦，從第 1 秒（或總長度的 10%）開始找
            start_frame = int(fps) if total_frames > fps else 0
            # 2. 往後搜索約 2 秒的長度，從中找最清楚的一張
            search_range = int(fps * 2)
            end_frame = min(start_frame + search_range, total_frames)

            best_frame = None
            max_score = -1

            # 設定起始讀取位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # 抽樣檢查（例如每 3 幀檢查一次以節省效能）
            for i in range(start_frame, end_frame, 3):
                success, frame = cap.read()
                if not success:
                    break

                # 跳過 3 幀中的另外兩幀
                cap.set(cv2.CAP_PROP_POS_FRAMES, i + 3)

                score = get_blur_score(frame)
                if score > max_score:
                    max_score = score
                    best_frame = frame.copy()

            # --- 儲存結果 ---
            if best_frame is not None:
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(directory, f"{base_name}.jpg")

                # 儲存為高品質 JPEG
                cv2.imwrite(output_path, best_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

                # 釋放 cap 後再刪除影片，避免檔案被佔用
                cap.release()
                os.remove(video_path)
                print(f"成功提取最清晰幀 (Score: {max_score:.2f}): {output_path}")
            else:
                print(f"處理失敗: {filename}")
                cap.release()

# 使用方式
if __name__ == "__main__":
    extract_best_frame('.')

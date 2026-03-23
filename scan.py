import os
import cv2
import csv
from PIL import Image
import imagehash

def master_scan(folder_path, output_file="photo_data.csv"):
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    all_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)])
    
    data_dict = {} # {filename: [score, hash]}
    cache_path = os.path.join(folder_path, output_file)
    
    # 讀取舊快取
    if os.path.exists(cache_path):
        with open(cache_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) == 3:
                    data_dict[row[0]] = [float(row[1]), row[2]]

    new_files = [f for f in all_files if f not in data_dict]
    if not new_files:
        print("✅ 所有照片已掃描完畢。")
        return

    print(f"🚀 開始分析 {len(new_files)} 張照片 (模糊度 + 相似度)...")
    
    try:
        for i, fname in enumerate(new_files):
            path = os.path.join(folder_path, fname)
            # 1. 計算模糊度 (OpenCV)
            img_cv = cv2.imread(path)
            if img_cv is None: continue
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 2. 計算雜湊值 (ImageHash)
            with Image.open(path) as img_pil:
                h = imagehash.phash(img_pil)
            
            data_dict[fname] = [score, str(h)]
            
            if (i + 1) % 10 == 0:
                print(f"進度: {i+1}/{len(new_files)}")
    except KeyboardInterrupt:
        print("\n🛑 掃描中斷，儲存已完成部分...")

    # 存入 CSV
    with open(cache_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "blur_score", "phash_hex"])
        for f in sorted(data_dict.keys()):
            writer.writerow([f, data_dict[f][0], data_dict[f][1]])
    
    print(f"✨ 掃描存檔完成：{cache_path}")

if __name__ == "__main__":
    master_scan(".") # 修改為你的資料夾

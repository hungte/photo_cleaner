#!/usr/bin/env python3
import os
import json
import datetime

def rename_photos_by_json(directory):
    # 設定時區偏移量 (CST 為 UTC+8)
    tz_offset = datetime.timezone(datetime.timedelta(hours=8))
    
    # 掃描目錄下所有檔案
    for filename in os.listdir(directory):
        if filename.endswith(".supplemental-metadata.json"):
            json_path = os.path.join(directory, filename)
            
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 取得照片拍攝時間的 timestamp (Unix 秒數)
                timestamp = int(data.get("photoTakenTime", {}).get("timestamp", 0))
                
                if timestamp == 0:
                    continue
                
                # 轉換為 CST 時間格式
                dt = datetime.datetime.fromtimestamp(timestamp, tz=tz_offset)
                new_base_name = dt.strftime("IMG_%Y%m%d_%H%M%S")
                
                # 找出對應的原始照片檔案 (通常 JSON 檔名是 "照片名.副檔名.supplemental-metadata.json")
                # 或是 "照片名.supplemental-metadata.json"
                original_file_base = filename.replace(".supplemental-metadata.json", "")
                
                # 檢查原始檔案是否存在 (不限副檔名，以匹配 .jpg, .png, .mp4 等)
                target_file = os.path.join(directory, original_file_base)
                
                if os.path.exists(target_file):
                    file_extension = os.path.splitext(target_file)[1]
                    new_filename = f"{new_base_name}{file_extension}"
                    new_file_path = os.path.join(directory, new_filename)
                    
                    # 處理檔名重複的情況（例如同一秒鐘拍了兩張）
                    counter = 1
                    while os.path.exists(new_file_path):
                        new_filename = f"{new_base_name}_{counter}{file_extension}"
                        new_file_path = os.path.join(directory, new_filename)
                        counter += 1
                    
                    # 執行重新命名
                    os.rename(target_file, new_file_path)
                    print(f"已重新命名: {original_file_base} -> {new_filename}")
                    os.remove(filename)
                
            except Exception as e:
                print(f"處理 {filename} 時發生錯誤: {e}")

# 使用範例：將路徑替換為你存放照片的資料夾
# rename_photos_by_json('C:/Users/YourName/Downloads/GooglePhotos')
if __name__ == '__main__':
  rename_photos_by_json('.')

#!/usr/bin/env python3
import os
from PIL import Image
from pillow_heif import register_heif_opener

# 註冊 HEIF 解碼器
register_heif_opener()

def batch_convert_to_jpg(folder_path):
    if not os.path.exists(folder_path):
        print("找不到該資料夾")
        return

    # 定義要處理的副檔名
    target_extensions = (".heic", ".png")

    for filename in os.listdir(folder_path):
        ext = os.path.splitext(filename)[1].lower()

        if ext in target_extensions:
            src_path = os.path.join(folder_path, filename)
            jpg_filename = os.path.splitext(filename)[0] + ".jpg"
            jpg_path = os.path.join(folder_path, jpg_filename)

            try:
                img = Image.open(src_path)

                # 處理透明度問題（不論是 HEIC 還是 PNG，只要有透明度就墊白底）
                if img.mode in ("RGBA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                    background.save(jpg_path, "JPEG", quality=95)
                else:
                    img.convert("RGB").save(jpg_path, "JPEG", quality=95)

                print(f"已成功轉換 [{ext.upper()} -> JPG]: {filename}")

            except Exception as e:
                print(f"轉換 {filename} 失敗: {e}")

# 使用範例
if __name__ == '__main__':
  batch_convert_to_jpg(".")

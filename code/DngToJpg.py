# -*- coding: utf-8 -*-
import rawpy
import imageio
import numpy as np
import os
import glob
import shutil

def get_brightness_metrics(image):
    # RGB → 灰度亮度 Y（感知亮度）
    R, G, B = image[..., 0], image[..., 1], image[..., 2]
    Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
    return Y

def check_exposure(image, over_pct_thresh=0.05, under_pct_thresh=0.05):
    Y = get_brightness_metrics(image)
    total_pixels = Y.size
    over_exposed = np.sum(Y > 235) / total_pixels
    under_exposed = np.sum(Y < 20) / total_pixels
    
    status = "Normal"
    if over_exposed > over_pct_thresh:
        status = "Overexposed"
    elif under_exposed > under_pct_thresh:
        status = "Underexposed"
    return status, over_exposed, under_exposed

def adjust_exposure_auto(dng_path):
    with rawpy.imread(dng_path) as raw:
        rgb = raw.postprocess(use_camera_wb=True)
        status, over_pct, under_pct = check_exposure(rgb)
        
        # ⾃动判断曝光调整系数
        if status == "Underexposed":
            factor = 1.5
        elif status == "Overexposed":
            factor = 0.7
        else:
            factor = 1.0
        
        # 应⽤调整（线性乘法），裁剪并转换类型
        adjusted = np.clip(rgb.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        
        # 创建输出路径（同一目录，JPG格式）
        jpg_path = dng_path.replace('.dng', '.jpg')
        
        # 输出 JPG 文件
        imageio.imwrite(jpg_path, adjusted)
        print(f"{os.path.basename(dng_path)} - {status} | Over: {over_pct:.2%} | Under: {under_pct:.2%} -> Saved as {os.path.basename(jpg_path)}")
        
        # 返回JPG路径用于后续操作
        return jpg_path

def process_dng_files(input_dir):
    # 查找所有四级子目录下的DNG文件
    dng_files = []
    
    # 第一级子目录
    for level1 in os.listdir(input_dir):
        level1_path = os.path.join(input_dir, level1)
        if not os.path.isdir(level1_path):
            continue
            
        # 第二级子目录
        for level2 in os.listdir(level1_path):
            level2_path = os.path.join(level1_path, level2)
            if not os.path.isdir(level2_path):
                continue
                
            # 第三级子目录
            for level3 in os.listdir(level2_path):
                level3_path = os.path.join(level2_path, level3)
                if not os.path.isdir(level3_path):
                    continue
                    
                # 第四级子目录
                for level4 in os.listdir(level3_path):
                    level4_path = os.path.join(level3_path, level4)
                    if not os.path.isdir(level4_path):
                        continue
                    
                    # 查找当前四级目录中的所有DNG文件
                    for dng_file in glob.glob(os.path.join(level4_path, '*.dng')):
                        dng_files.append(dng_file)
    
    if not dng_files:
        print("No DNG files found in any subdirectories.")
        return
    
    print(f"Found {len(dng_files)} DNG files in subdirectories")
    
    processed_count = 0
    deleted_count = 0
    
    for dng_file in dng_files:
        try:
            # 处理DNG文件（在同一目录创建JPG）
            jpg_path = adjust_exposure_auto(dng_file)
            
            # 验证JPG文件是否创建成功
            if os.path.exists(jpg_path):
                # 删除原始DNG文件
                os.remove(dng_file)
                print(f"Deleted original DNG: {os.path.basename(dng_file)}")
                deleted_count += 1
                processed_count += 1
            else:
                print(f"Warning: JPG not created for {dng_file}, skipping deletion")
                
        except Exception as e:
            print(f"Error processing {dng_file}: {str(e)}")
    
    print(f"\nProcessing completed:")
    print(f"- Processed files: {processed_count}")
    print(f"- Deleted DNG files: {deleted_count}")

# ✅ 使用示例：处理四级子目录中的DNG文件
process_dng_files(
    input_dir=r'D:\AcourseFile\5研三上\语料收集\数据标注'  # 包含四级子目录的根目录
)
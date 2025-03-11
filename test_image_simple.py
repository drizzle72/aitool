import os
import sys
from PIL import Image
import time

# 确保可以导入image_generator模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from image_generator import ImageGenerator, IMAGE_STYLES, IMAGE_QUALITY, enhance_prompt

def run_tests():
    """
    运行简单的图像生成测试
    """
    print("开始图像生成测试...")
    generator = ImageGenerator(api_key="测试")
    
    # 测试模拟模式
    print("\n== 测试模拟模式 ==")
    prompt = "蓝色背景下的红色花朵"
    style = "写实"
    quality = "标准"
    
    start_time = time.time()
    mock_image_path = generator.generate_from_text(
        prompt=prompt, 
        style=style, 
        quality=quality, 
        use_mock=True, 
        seed=42
    )
    mock_time = time.time() - start_time
    
    print(f"模拟模式生成时间: {mock_time:.2f}秒")
    print(f"生成的图像路径: {mock_image_path}")
    
    # 测试提示词增强
    print("\n== 测试提示词增强 ==")
    enhanced_prompt = enhance_prompt(prompt, style)
    print(f"原始提示词: {prompt}")
    print(f"增强后提示词: {enhanced_prompt}")
    
    # 显示生成的图像信息
    if os.path.exists(mock_image_path):
        try:
            img = Image.open(mock_image_path)
            print(f"图像尺寸: {img.size}")
            print(f"图像模式: {img.mode}")
        except Exception as e:
            print(f"无法打开生成的图像: {e}")
    else:
        print(f"错误: 生成的图像文件不存在 ({mock_image_path})")
    
    # 测试实际API调用（仅当有API密钥时）
    if generator.stability_api_key and generator.stability_api_key != "测试":
        print("\n== 测试实际API调用 ==")
        try:
            start_time = time.time()
            api_image_path = generator.generate_from_text(
                prompt="一只可爱的小猫坐在窗台上", 
                style="写实",
                quality="标准",
                aspect_ratio="1:1 方形",
                use_mock=False
            )
            api_time = time.time() - start_time
            
            print(f"API调用生成时间: {api_time:.2f}秒")
            print(f"API生成的图像路径: {api_image_path}")
        except Exception as e:
            print(f"API调用失败: {e}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    run_tests() 
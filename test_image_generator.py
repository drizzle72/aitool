from image_generator import ImageGenerator, IMAGE_STYLES
import os
from dotenv import load_dotenv

def main():
    # 加载环境变量
    load_dotenv()
    
    print("开始运行图像生成测试...")
    
    # 获取API密钥
    stability_api_key = os.getenv("STABILITY_API_KEY")
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not stability_api_key:
        print("错误: 未设置Stability API密钥，请在.env文件中配置STABILITY_API_KEY")
        return
        
    if not dashscope_api_key:
        print("错误: 未设置通义千问API密钥，请在.env文件中配置DASHSCOPE_API_KEY")
        return
    
    # 创建图像生成器实例
    print("创建图像生成器实例...")
    generator = ImageGenerator(
        api_key=stability_api_key,
        dashscope_api_key=dashscope_api_key,
        translation_api="dashscope"
    )
    
    # 测试图像生成
    prompt = "一只可爱的熊猫正在竹林中吃竹子"
    style = "水彩"  # 使用水彩风格
    quality = "标准"  # 使用标准质量
    
    print(f"\n准备生成图像...")
    print(f"中文提示词: {prompt}")
    print(f"风格: {style}")
    print(f"质量: {quality}")
    
    try:
        # 先获取翻译后的提示词
        if style and style in IMAGE_STYLES:
            enhanced_prompt = f"{prompt}，{IMAGE_STYLES[style]}"
        else:
            enhanced_prompt = prompt
            
        english_prompt = generator._translate_text(enhanced_prompt)
        print(f"\n增强后的中文提示词: {enhanced_prompt}")
        print(f"翻译后的英文提示词: {english_prompt}")
        
        # 生成图像
        print("\n开始生成图像...")
        output_path = generator.generate_from_text(
            prompt=prompt,
            style=style,
            quality=quality,
            use_mock=False  # 使用实际的API
        )
        
        print(f"\n图像已生成：{output_path}")
        
    except Exception as e:
        print(f"\n生成图像时出错：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
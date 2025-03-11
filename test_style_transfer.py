from image_generator import ImageGenerator

def test_style_transfer():
    """测试图像风格转换功能"""
    
    # 创建图像生成器实例
    generator = ImageGenerator()
    
    print("1. 生成基础图片...")
    base_image_path = generator.generate_image(
        prompt="一只可爱的熊猫坐在竹林中",
        quality="标准",
        use_mock=True
    )
    print(f"基础图片已生成：{base_image_path}")
    
    # 测试更多风格
    styles = [
        # 艺术流派
        "印象派",
        "超现实主义",
        "波普艺术",
        # 特定风格
        "奇幻",
        "蒸汽朋克",
        "哥特",
        # 简约风格
        "极简主义",
        "写实",
        "复古"
    ]
    
    print("\n2. 开始生成不同风格的变体...")
    for style in styles:
        print(f"\n正在生成{style}风格...")
        # 根据不同风格调整强度
        strength = 0.9 if style in ["印象派", "超现实主义", "波普艺术"] else 0.7
        
        styled_image_path = generator.generate_styled_variation(
            image_path=base_image_path,
            target_style=style,
            strength=strength,  # 不同风格使用不同的强度
            quality="标准",
            use_mock=True
        )
        print(f"已生成{style}风格图片：{styled_image_path}")
        print(f"使用的风格强度：{strength}")

if __name__ == "__main__":
    test_style_transfer() 
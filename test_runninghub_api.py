from image_generator import ImageGenerator

def test_runninghub_api():
    """测试RunningHub API的图像生成功能"""
    
    # 创建图像生成器实例
    generator = ImageGenerator()
    
    # 测试新增的风格
    styles = [
        "动漫",
        "3D",
        "素描",
        "水墨",
        "霓虹"
    ]
    
    print("\n测试新增风格...")
    for style in styles:
        print(f"\n正在生成{style}风格的熊猫图片...")
        image_path = generator.generate_image(
            prompt="一只可爱的熊猫坐在竹林中",
            style=style,
            quality="标准",
            api="runninghub",
            use_mock=False  # 使用真实API
        )
        print(f"已生成{style}风格图片：{image_path}")

if __name__ == "__main__":
    test_runninghub_api() 
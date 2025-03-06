"""
通义千问视觉语言模型(Qwen-VL) 智能识别助手

主应用程序，使用Streamlit构建Web界面
"""

import os
import io
import time
from PIL import Image
import streamlit as st
from dotenv import load_dotenv

# 导入自定义模块
from qwen_api import QwenAPI, analyze_description
from food_calories import get_food_calories, get_similar_foods
from product_search import generate_purchase_links, is_likely_product
from cartoon_generator import (
    get_cartoon_image, 
    get_available_styles, 
    get_available_effects,
    generate_multiple_styles, 
    CARTOON_STYLES, 
    CARTOON_EFFECTS
)

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="通义千问视觉语言模型智能识别助手",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #F5F5F5;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .info-text {
        color: #666;
        font-size: 0.9rem;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 0.2rem 0.5rem;
        border-radius: 3px;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.8rem;
        margin-top: 3rem;
    }
    .purchase-btn {
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        border-radius: 4px;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 标题和介绍
    st.markdown('<h1 class="main-header">通义千问视觉语言模型智能识别助手</h1>', unsafe_allow_html=True)
    st.markdown("""
    此应用使用通义千问视觉语言模型(Qwen-VL)来识别图片内容，并提供相关信息。
    * 上传一张图片进行识别
    * 获取食物热量信息（如果是食物）
    * 找到相似产品和购买链接（如果是商品）
    * 生成多种风格的卡通图像
    """)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("设置")
        
        # API密钥输入
        api_key = st.text_input("通义千问API密钥 (选填)", type="password")
        st.caption("如果不提供，将使用环境变量中的API密钥")
        
        # 使用模拟数据的选项
        use_mock = st.checkbox("使用模拟数据 (无需API)")
        
        # 卡通图像生成选项
        st.markdown("---")
        st.subheader("卡通图像设置")
        
        # 选择卡通图像生成模式
        cartoon_mode = st.radio(
            "卡通图像生成模式",
            ["简单匹配", "AI生成", "多样风格"]
        )
        
        # 如果选择AI生成，显示风格选择
        if cartoon_mode == "AI生成":
            cartoon_style = st.selectbox(
                "选择卡通风格",
                CARTOON_STYLES,
                format_func=lambda x: x.replace("_", " ").title()
            )
            
            cartoon_effect = st.selectbox(
                "选择卡通效果",
                CARTOON_EFFECTS,
                format_func=lambda x: x.replace("_", " ").title()
            )
            
        # 如果选择多样风格，显示高级选项
        elif cartoon_mode == "多样风格":
            st.write("将生成多种不同风格的卡通图像")
            
            # 风格多选
            cartoon_styles = st.multiselect(
                "选择多种卡通风格（最多3种）",
                CARTOON_STYLES,
                default=CARTOON_STYLES[:3] if len(CARTOON_STYLES) >= 3 else CARTOON_STYLES,
                format_func=lambda x: x.replace("_", " ").title(),
                max_selections=3
            )
            
            # 效果多选
            cartoon_effects = st.multiselect(
                "选择多种卡通效果（最多2种）",
                CARTOON_EFFECTS,
                default=["normal"],
                format_func=lambda x: x.replace("_", " ").title(),
                max_selections=2
            )
        else:
            cartoon_style = None
            cartoon_effect = "normal"
            cartoon_styles = None
            cartoon_effects = None
        
        st.markdown("---")
        
        # 关于信息
        st.header("关于")
        st.markdown("""
        **通义千问视觉语言模型(Qwen-VL)智能识别助手** 由阿里云通义千问驱动。
        
        此应用可以：
        * 识别图片内容
        * 提供食物热量信息
        * 推荐相似产品和购买链接
        """)
    
    # 文件上传器
    uploaded_file = st.file_uploader("上传图片", type=["jpg", "jpeg", "png"])
    
    # 或使用示例图片
    example_col1, example_col2, example_col3 = st.columns(3)
    with example_col1:
        use_example_food = st.button("使用食物示例图片")
    with example_col2:
        use_example_product = st.button("使用商品示例图片")
    with example_col3:
        use_example_other = st.button("使用其他示例图片")
    
    # 处理示例图片
    if use_example_food:
        uploaded_file = "example_food.jpg"  # 此处需要有示例图片文件
    elif use_example_product:
        uploaded_file = "example_product.jpg"  # 此处需要有示例图片文件
    elif use_example_other:
        uploaded_file = "example_other.jpg"  # 此处需要有示例图片文件
    
    # 如果有上传的文件
    if uploaded_file is not None:
        try:
            # 读取上传的图片
            image = Image.open(uploaded_file)
            st.image(image, caption="上传的图片", use_column_width=True)
            
            # 保存上传的图片到临时文件
            image_path = "temp_image.jpg"
            image.save(image_path)
            
            # 获取base64编码
            image_base64 = None
            try:
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
                
                import base64
                image_base64 = base64.b64encode(file_bytes).decode('utf-8')
            except Exception as e:
                st.warning(f"无法直接处理上传的文件: {e}，将使用保存的图片文件")
                # 如果直接处理文件失败，将依赖于API中使用图片文件的方法
                image_base64 = None
        except Exception as e:
            st.error(f"无法处理上传的图片: {e}")
            return
        
        # 进度条
        with st.spinner("AI正在识别图片内容..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # 初始化API客户端
            try:
                api_client = QwenAPI(api_key=api_key if api_key else None)
                
                # 获取图片描述
                description = api_client.get_image_description(
                    image_path=image_path,
                    image_base64=image_base64,
                    use_mock=use_mock
                )
            except Exception as e:
                st.error(f"初始化API客户端失败: {e}")
                if not api_key and not use_mock:
                    st.warning("请提供API密钥或选择使用模拟数据")
                return
        
        # 显示识别结果
        st.markdown('<h2 class="sub-header">识别结果</h2>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.subheader("Qwen-VL分析")
            st.write(description)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 分析描述，确定内容类型
            content_type, content_name = analyze_description(description)
            
            # 根据内容类型提供不同的信息
            if content_type == "food":
                st.markdown('<h2 class="sub-header">食物热量信息</h2>', unsafe_allow_html=True)
                
                # 获取食物热量信息
                calories_info = get_food_calories(content_name)
                
                with st.container():
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.subheader("食物名称")
                        st.markdown(f'<p class="highlight">{content_name}</p>', unsafe_allow_html=True)
                        
                        if calories_info["热量"]:
                            st.subheader("热量")
                            st.markdown(f'<p class="highlight">{calories_info["热量"]} 千卡/100克</p>', unsafe_allow_html=True)
                    
                    with col2:
                        st.subheader("详细信息")
                        st.write(calories_info["描述"])
                        
                        # 如果没有找到精确热量，提供类似食物
                        if not calories_info["热量"]:
                            similar = get_similar_foods(content_name)
                            if similar:
                                st.subheader("类似食物")
                                for food in similar[:5]:  # 最多显示5个类似食物
                                    similar_calories = get_food_calories(food)
                                    if similar_calories["热量"]:
                                        st.write(f"- {food}: {similar_calories['热量']} 千卡/100克")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                # 添加健康提示
                st.info("📊 食物热量仅供参考，实际热量会因烹饪方式、配料和份量而异。")
                
            elif content_type == "product":
                st.markdown('<h2 class="sub-header">商品购买信息</h2>', unsafe_allow_html=True)
                
                # 获取商品购买链接
                product_info = generate_purchase_links(content_name)
                
                with st.container():
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.subheader("商品名称")
                        st.markdown(f'<p class="highlight">{product_info["商品名称"]}</p>', unsafe_allow_html=True)
                    
                    with col2:
                        st.subheader("购买链接")
                        for platform, link in product_info["购买链接"].items():
                            st.markdown(f'<a href="{link}" target="_blank" class="purchase-btn">{platform}</a>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                # 添加购物提示
                st.info("💡 购买链接基于识别结果自动生成，请在购买前确认商品信息和商家信用。")
                
            else:
                st.markdown('<h2 class="sub-header">通用信息</h2>', unsafe_allow_html=True)
                
                with st.container():
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.write("这不是食物或商品，无法提供热量或购买信息。")
                    
                    # 尝试判断是否可能是商品
                    if is_likely_product(description):
                        st.write("不过，如果你想将其视为产品搜索，可以点击下方按钮：")
                        if st.button("作为商品搜索"):
                            product_info = generate_purchase_links(description[:30])
                            
                            st.subheader("商品搜索结果")
                            for platform, link in product_info["购买链接"].items():
                                st.markdown(f'<a href="{link}" target="_blank" class="purchase-btn">{platform}</a>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # 生成卡通图像
            st.markdown('<h2 class="sub-header">卡通图像生成</h2>', unsafe_allow_html=True)
            
            with st.spinner("正在生成卡通图像..."):
                # 根据设置选择卡通生成模式
                if cartoon_mode == "AI生成":
                    use_ai = True
                    
                    # 生成卡通图像
                    cartoon_path = get_cartoon_image(
                        image_path=image_path, 
                        description=description,
                        use_ai_generation=use_ai,
                        style=cartoon_style,
                        effect=cartoon_effect
                    )
                    
                    if cartoon_path and os.path.exists(cartoon_path):
                        # 显示卡通图像
                        cartoon_image = Image.open(cartoon_path)
                        st.image(cartoon_image, caption=f"风格: {cartoon_style.replace('_', ' ').title()}, 效果: {cartoon_effect.replace('_', ' ').title()}", use_column_width=True)
                        
                        # 提供下载链接
                        with open(cartoon_path, "rb") as file:
                            cartoon_bytes = file.read()
                            
                        st.download_button(
                            label="下载卡通图像",
                            data=cartoon_bytes,
                            file_name=os.path.basename(cartoon_path),
                            mime="image/jpeg"
                        )
                        
                        st.info(f"使用{cartoon_style.replace('_', ' ').title()}风格和{cartoon_effect.replace('_', ' ').title()}效果生成")
                    else:
                        st.error("无法生成卡通图像，请尝试其他图片或选择其他生成模式")
                
                elif cartoon_mode == "多样风格":
                    # 生成多种风格的卡通图像
                    cartoon_paths = generate_multiple_styles(
                        image_path=image_path,
                        description=description,
                        styles=cartoon_styles,
                        effects=cartoon_effects
                    )
                    
                    if cartoon_paths and len(cartoon_paths) > 0:
                        # 创建多列布局显示多个卡通图像
                        cols = st.columns(min(3, len(cartoon_paths)))
                        
                        for i, path in enumerate(cartoon_paths):
                            if os.path.exists(path):
                                with cols[i % len(cols)]:
                                    # 从文件名解析风格和效果信息
                                    filename = os.path.basename(path)
                                    style_info = filename.split("_")[1]
                                    effect_info = filename.split("_")[2] if len(filename.split("_")) > 2 else "normal"
                                    
                                    # 显示卡通图像
                                    cartoon_image = Image.open(path)
                                    st.image(cartoon_image, caption=f"{style_info.replace('_', ' ').title()}", use_column_width=True)
                                    
                                    # 提供下载链接
                                    with open(path, "rb") as file:
                                        cartoon_bytes = file.read()
                                        
                                    st.download_button(
                                        label=f"下载 {style_info}",
                                        data=cartoon_bytes,
                                        file_name=os.path.basename(path),
                                        mime="image/jpeg"
                                    )
                        
                        st.success(f"成功生成 {len(cartoon_paths)} 种不同风格的卡通图像")
                    else:
                        st.error("生成多样风格卡通图像失败，请尝试其他图片或选择其他生成模式")
                
                else:
                    # 简单匹配模式
                    use_ai = False
                    
                    # 生成卡通图像
                    cartoon_path = get_cartoon_image(
                        image_path=image_path, 
                        description=description,
                        use_ai_generation=use_ai
                    )
                    
                    if cartoon_path and os.path.exists(cartoon_path):
                        # 显示卡通图像
                        cartoon_image = Image.open(cartoon_path)
                        st.image(cartoon_image, caption="匹配的卡通图像", use_column_width=True)
                        
                        # 提供下载链接
                        with open(cartoon_path, "rb") as file:
                            cartoon_bytes = file.read()
                            
                        st.download_button(
                            label="下载卡通图像",
                            data=cartoon_bytes,
                            file_name=os.path.basename(cartoon_path),
                            mime="image/jpeg"
                        )
                        
                        st.info("卡通图像是通过内容匹配生成的")
                    else:
                        st.error("无法生成卡通图像，请尝试其他图片或选择其他生成模式")
        
        # 删除临时文件
        if not isinstance(uploaded_file, str) and os.path.exists("temp_image.jpg"):
            try:
                os.remove("temp_image.jpg")
            except:
                pass
    
    # 底部信息
    st.markdown('<div class="footer">通义千问视觉语言模型智能识别助手 © 2023</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    # 获取端口号，如果在环境变量中设置了PORT，则使用环境变量中的值
    port = int(os.environ.get("PORT", 8501))
    
    # 使用main函数启动应用
    main()
    
    # 注意：在某些云平台(如Heroku)上，可能需要指定host和port
    # 但是streamlit run已经处理了这些参数，所以这里不需要额外配置 
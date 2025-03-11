#!/usr/bin/env python
"""
图像生成API测试界面

使用Streamlit创建的用户友好界面，用于测试图像生成API和各种参数组合
"""

import os
import time
import json
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from image_generator import (
    ImageGenerator, get_available_styles, get_quality_options, 
    get_aspect_ratios, get_prompt_enhancers, GENERATED_IMAGES_DIR
)

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="AI绘画接口测试",
    page_icon="🎨",
    layout="wide"
)

# 样式设置
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2196F3;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .subsection {
        background-color: #F3F6F9;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .success-message {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 1rem;
        border-radius: 5px;
        text-align: center;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 1rem;
        border-radius: 5px;
        text-align: center;
        margin: 1rem 0;
    }
    .image-container {
        text-align: center;
        margin: 1.5rem 0;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .comparison-container {
        display: flex;
        justify-content: center;
        margin: 1.5rem 0;
    }
    .comparison-image {
        margin: 0 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def check_api_key():
    """检查API密钥是否配置正确"""
    api_key = os.getenv("STABILITY_API_KEY")
    return api_key is not None and len(api_key) > 10

def generate_test_image(prompt, style, quality, aspect_ratio, enhancers, use_mock=False, negative_prompt=None, seed=None):
    """生成测试图像"""
    # 创建生成器实例
    generator = ImageGenerator()
    
    start_time = time.time()
    result = generator.generate_from_text(
        prompt=prompt,
        style=style,
        quality=quality,
        aspect_ratio=aspect_ratio,
        enhancers=enhancers,
        negative_prompt=negative_prompt,
        seed=seed,
        use_mock=use_mock
    )
    end_time = time.time()
    
    generation_time = round(end_time - start_time, 2)
    
    return result, generation_time

def create_comparison(image1_path, image2_path):
    """创建对比图像"""
    if not (os.path.exists(image1_path) and os.path.exists(image2_path)):
        return None
    
    try:
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)
        
        # 调整图像大小使它们具有相同的高度
        height = min(img1.height, img2.height)
        if img1.height != height:
            width = int(img1.width * (height / img1.height))
            img1 = img1.resize((width, height), Image.LANCZOS)
        
        if img2.height != height:
            width = int(img2.width * (height / img2.height))
            img2 = img2.resize((width, height), Image.LANCZOS)
        
        # 创建一个新图像来并排显示两个图像
        width = img1.width + img2.width
        comparison = Image.new('RGB', (width, height), (255, 255, 255))
        
        # 粘贴两个图像
        comparison.paste(img1, (0, 0))
        comparison.paste(img2, (img1.width, 0))
        
        # 保存对比图
        comparison_path = os.path.join(GENERATED_IMAGES_DIR, f"comparison_{int(time.time())}.png")
        comparison.save(comparison_path)
        return comparison_path
    except Exception as e:
        st.error(f"创建对比图失败: {str(e)}")
        return None

def save_test_results(result_info):
    """保存测试结果到JSON文件"""
    results_dir = os.path.join(GENERATED_IMAGES_DIR, "test_results")
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = int(time.time())
    filename = os.path.join(results_dir, f"test_result_{timestamp}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result_info, f, ensure_ascii=False, indent=2)
    
    return filename

def main():
    st.markdown('<h1 class="main-header">AI绘画接口测试工具</h1>', unsafe_allow_html=True)
    
    # API状态检查
    has_api_key = check_api_key()
    
    if has_api_key:
        st.markdown('<div class="success-message">✅ 已检测到Stability API密钥</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-message">⚠️ 未检测到Stability API密钥，将使用模拟模式</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        要使用真实API，请在<code>.env</code>文件中设置<code>STABILITY_API_KEY</code>变量。
        <br>可以从<a href="https://stability.ai/" target="_blank">Stability AI</a>获取API密钥。
        </div>
        """, unsafe_allow_html=True)
    
    # 主要测试部分
    st.markdown('<h2 class="section-header">接口测试</h2>', unsafe_allow_html=True)
    
    # 选择测试类型
    test_type = st.radio(
        "选择测试类型",
        ["单图生成测试", "参数对比测试", "模拟与API对比测试"]
    )
    
    if test_type == "单图生成测试":
        st.markdown('<div class="subsection">', unsafe_allow_html=True)
        st.markdown("### 单图生成测试")
        st.write("测试单个图像的生成，使用指定的参数")
        
        prompt = st.text_area("输入提示词", value="日落时分的海滩，波浪轻轻拍打着沙滩")
        
        col1, col2 = st.columns(2)
        
        with col1:
            styles = list(get_available_styles().keys())
            style = st.selectbox("选择风格", styles)
            
            quality_options = list(get_quality_options().keys())
            quality = st.selectbox("选择质量", quality_options, index=0)
            
            seed = st.number_input("随机种子 (0表示随机)", min_value=0, max_value=2147483647, value=0)
        
        with col2:
            aspect_ratios = list(get_aspect_ratios().keys())
            aspect_ratio = st.selectbox("选择比例", aspect_ratios, index=0)
            
            enhancers = list(get_prompt_enhancers().keys())
            selected_enhancers = st.multiselect("选择提示词增强器", enhancers)
            
            use_mock = st.checkbox("使用模拟模式", value=not has_api_key)
        
        negative_prompt = st.text_area("负面提示词 (可选)", value="")
        
        if st.button("生成测试图像"):
            with st.spinner("正在生成图像..."):
                actual_seed = seed if seed > 0 else None
                try:
                    result_path, generation_time = generate_test_image(
                        prompt=prompt,
                        style=style,
                        quality=quality,
                        aspect_ratio=aspect_ratio,
                        enhancers=selected_enhancers,
                        use_mock=use_mock,
                        negative_prompt=negative_prompt if negative_prompt else None,
                        seed=actual_seed
                    )
                    
                    if os.path.exists(result_path):
                        st.markdown('<div class="success-message">✅ 图像生成成功!</div>', unsafe_allow_html=True)
                        st.markdown(f"生成用时: {generation_time} 秒")
                        
                        st.markdown('<div class="image-container">', unsafe_allow_html=True)
                        st.image(result_path, caption=f"{style}风格 - {quality}质量", use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 保存测试结果
                        result_info = {
                            "prompt": prompt,
                            "style": style,
                            "quality": quality,
                            "aspect_ratio": aspect_ratio,
                            "enhancers": selected_enhancers,
                            "negative_prompt": negative_prompt,
                            "seed": seed,
                            "use_mock": use_mock,
                            "generation_time": generation_time,
                            "result_path": result_path,
                            "timestamp": time.time()
                        }
                        
                        result_file = save_test_results(result_info)
                        st.markdown(f"测试结果已保存到: `{result_file}`")
                    else:
                        st.markdown('<div class="error-message">❌ 图像生成失败</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-message">❌ 错误: {str(e)}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif test_type == "参数对比测试":
        st.markdown('<div class="subsection">', unsafe_allow_html=True)
        st.markdown("### 参数对比测试")
        st.write("对比两组不同参数生成的图像效果")
        
        prompt = st.text_area("输入提示词", value="日落时分的海滩，波浪轻轻拍打着沙滩")
        
        st.markdown("#### 参数组1")
        col1, col2 = st.columns(2)
        
        with col1:
            styles = list(get_available_styles().keys())
            style1 = st.selectbox("选择风格", styles, key="style1")
            
            aspect_ratios = list(get_aspect_ratios().keys())
            aspect_ratio1 = st.selectbox("选择比例", aspect_ratios, index=0, key="ratio1")
        
        with col2:
            enhancers = list(get_prompt_enhancers().keys())
            selected_enhancers1 = st.multiselect("选择提示词增强器", enhancers, key="enhancers1")
            
            quality_options = list(get_quality_options().keys())
            quality1 = st.selectbox("选择质量", quality_options, index=0, key="quality1")
        
        st.markdown("#### 参数组2")
        col3, col4 = st.columns(2)
        
        with col3:
            style2 = st.selectbox("选择风格", styles, key="style2")
            
            aspect_ratio2 = st.selectbox("选择比例", aspect_ratios, index=0, key="ratio2")
        
        with col4:
            selected_enhancers2 = st.multiselect("选择提示词增强器", enhancers, key="enhancers2")
            
            quality2 = st.selectbox("选择质量", quality_options, index=0, key="quality2")
        
        # 公共参数
        use_mock = st.checkbox("使用模拟模式", value=not has_api_key)
        seed = st.number_input("随机种子 (使用相同种子确保公平对比)", min_value=1, max_value=2147483647, value=42)
        
        if st.button("生成对比图像"):
            with st.spinner("正在生成对比图像..."):
                try:
                    # 生成第一张图像
                    result1_path, time1 = generate_test_image(
                        prompt=prompt,
                        style=style1,
                        quality=quality1,
                        aspect_ratio=aspect_ratio1,
                        enhancers=selected_enhancers1,
                        use_mock=use_mock,
                        seed=seed
                    )
                    
                    # 生成第二张图像
                    result2_path, time2 = generate_test_image(
                        prompt=prompt,
                        style=style2,
                        quality=quality2,
                        aspect_ratio=aspect_ratio2,
                        enhancers=selected_enhancers2,
                        use_mock=use_mock,
                        seed=seed
                    )
                    
                    if os.path.exists(result1_path) and os.path.exists(result2_path):
                        st.markdown('<div class="success-message">✅ 对比图像生成成功!</div>', unsafe_allow_html=True)
                        
                        st.markdown('<div class="comparison-container">', unsafe_allow_html=True)
                        
                        col_img1, col_img2 = st.columns(2)
                        
                        with col_img1:
                            st.markdown('<div class="comparison-image">', unsafe_allow_html=True)
                            st.image(result1_path, caption=f"参数组1: {style1}", use_container_width=True)
                            st.markdown(f"生成用时: {time1} 秒")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col_img2:
                            st.markdown('<div class="comparison-image">', unsafe_allow_html=True)
                            st.image(result2_path, caption=f"参数组2: {style2}", use_container_width=True)
                            st.markdown(f"生成用时: {time2} 秒")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 显示参数差异
                        st.markdown("#### 参数差异")
                        
                        col_diff1, col_diff2 = st.columns(2)
                        
                        with col_diff1:
                            st.markdown("**参数组1**")
                            st.write(f"- 风格: {style1}")
                            st.write(f"- 质量: {quality1}")
                            st.write(f"- 比例: {aspect_ratio1}")
                            st.write(f"- 增强器: {', '.join(selected_enhancers1) if selected_enhancers1 else '无'}")
                        
                        with col_diff2:
                            st.markdown("**参数组2**")
                            st.write(f"- 风格: {style2}")
                            st.write(f"- 质量: {quality2}")
                            st.write(f"- 比例: {aspect_ratio2}")
                            st.write(f"- 增强器: {', '.join(selected_enhancers2) if selected_enhancers2 else '无'}")
                    else:
                        st.markdown('<div class="error-message">❌ 图像生成失败</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-message">❌ 错误: {str(e)}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif test_type == "模拟与API对比测试":
        if not has_api_key:
            st.markdown('<div class="error-message">⚠️ 此测试需要配置Stability API密钥</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="subsection">', unsafe_allow_html=True)
            st.markdown("### 模拟与API对比测试")
            st.write("对比模拟模式和实际API调用的结果差异")
            
            prompt = st.text_area("输入提示词", value="春天的樱花树下，花瓣随风飘落")
            
            col1, col2 = st.columns(2)
            
            with col1:
                styles = list(get_available_styles().keys())
                style = st.selectbox("选择风格", styles)
                
                aspect_ratios = list(get_aspect_ratios().keys())
                aspect_ratio = st.selectbox("选择比例", aspect_ratios, index=0)
            
            with col2:
                quality_options = list(get_quality_options().keys())
                quality = st.selectbox("选择质量", quality_options, index=0)
                
                seed = st.number_input("随机种子", min_value=1, max_value=2147483647, value=42)
            
            enhancers = list(get_prompt_enhancers().keys())
            selected_enhancers = st.multiselect("选择提示词增强器", enhancers)
            
            if st.button("生成对比图像"):
                with st.spinner("正在生成对比图像..."):
                    try:
                        # 使用模拟模式生成
                        mock_path, mock_time = generate_test_image(
                            prompt=prompt,
                            style=style,
                            quality=quality,
                            aspect_ratio=aspect_ratio,
                            enhancers=selected_enhancers,
                            use_mock=True,
                            seed=seed
                        )
                        
                        # 使用API模式生成
                        api_path, api_time = generate_test_image(
                            prompt=prompt,
                            style=style,
                            quality=quality,
                            aspect_ratio=aspect_ratio,
                            enhancers=selected_enhancers,
                            use_mock=False,
                            seed=seed
                        )
                        
                        if os.path.exists(mock_path) and os.path.exists(api_path):
                            st.markdown('<div class="success-message">✅ 对比图像生成成功!</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="comparison-container">', unsafe_allow_html=True)
                            
                            col_img1, col_img2 = st.columns(2)
                            
                            with col_img1:
                                st.markdown('<div class="comparison-image">', unsafe_allow_html=True)
                                st.image(mock_path, caption="模拟模式生成", use_container_width=True)
                                st.markdown(f"生成用时: {mock_time} 秒")
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            with col_img2:
                                st.markdown('<div class="comparison-image">', unsafe_allow_html=True)
                                st.image(api_path, caption="API模式生成", use_container_width=True)
                                st.markdown(f"生成用时: {api_time} 秒")
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # 创建并显示对比图
                            comparison_path = create_comparison(mock_path, api_path)
                            if comparison_path:
                                st.markdown('<h4 style="text-align: center">并排对比</h4>', unsafe_allow_html=True)
                                st.image(comparison_path, caption="左侧: 模拟模式 | 右侧: API模式", use_container_width=True)
                            
                            # 显示性能对比
                            speedup = round(api_time / mock_time, 2) if mock_time > 0 else 0
                            st.markdown(f"### 性能对比")
                            st.write(f"- 模拟模式用时: {mock_time} 秒")
                            st.write(f"- API模式用时: {api_time} 秒")
                            st.write(f"- 速度比: API模式耗时是模拟模式的 {speedup} 倍")
                            
                            # 保存测试结果
                            result_info = {
                                "prompt": prompt,
                                "style": style,
                                "quality": quality,
                                "aspect_ratio": aspect_ratio,
                                "enhancers": selected_enhancers,
                                "seed": seed,
                                "mock_time": mock_time,
                                "api_time": api_time,
                                "mock_path": mock_path,
                                "api_path": api_path,
                                "comparison_path": comparison_path,
                                "timestamp": time.time()
                            }
                            
                            result_file = save_test_results(result_info)
                            st.markdown(f"测试结果已保存到: `{result_file}`")
                        else:
                            st.markdown('<div class="error-message">❌ 图像生成失败</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="error-message">❌ 错误: {str(e)}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 底部信息
    st.markdown("""
    ---
    ### 注意事项
    - 测试过程中生成的所有图像都保存在 `generated_images` 目录中
    - 测试结果保存在 `generated_images/test_results` 目录中
    - 模拟模式下生成的图像仅用于测试接口，质量不如实际API生成的图像
    - 使用相同的种子值可以确保对比测试的公平性
    """)

if __name__ == "__main__":
    main() 
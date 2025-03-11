"""
图像分析组件模块
"""

import streamlit as st
from PIL import Image
import io

def render_image_analysis():
    """渲染图像分析界面"""
    st.markdown("## 图像分析")
    
    # 创建两列布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 图像上传
        uploaded_file = st.file_uploader(
            "上传图片",
            type=["png", "jpg", "jpeg"],
            help="支持PNG、JPG、JPEG格式的图片"
        )
        
        if uploaded_file:
            # 显示上传的图片
            image = Image.open(uploaded_file)
            st.image(image, caption="上传的图片", use_column_width=True)
            
            # 将图片转换为字节流，以便后续处理
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=image.format)
            img_byte_arr = img_byte_arr.getvalue()
            
            # 分析类型选择
            analysis_type = st.selectbox(
                "选择分析类型",
                options=[
                    "图像描述",
                    "场景分析",
                    "物体识别",
                    "文字提取",
                    "问题解答",
                    "故事创作",
                    "诗歌创作",
                    "科普讲解"
                ]
            )
            
            # 自定义提示词
            custom_prompt = st.text_area(
                "自定义提示词（可选）",
                help="您可以输入特定的提示词来引导AI的分析方向"
            )
            
            # 分析按钮
            if st.button("开始分析", type="primary"):
                with st.spinner("正在分析图片..."):
                    try:
                        # TODO: 调用图像分析服务
                        st.success("分析完成！")
                        st.markdown("### 分析结果")
                        st.write("这是一个示例结果，实际功能需要接入图像分析服务。")
                    except Exception as e:
                        st.error(f"分析过程中发生错误: {str(e)}")
    
    with col2:
        st.markdown("### 使用说明")
        st.write("""
        1. 上传一张想要分析的图片
        2. 选择分析类型
        3. 可以输入自定义提示词来引导分析
        4. 点击"开始分析"按钮
        """)
        
        st.markdown("### 分析类型说明")
        st.write("""
        - **图像描述**：生成对图像内容的详细描述
        - **场景分析**：分析图像中的场景、环境和氛围
        - **物体识别**：识别并列出图像中的主要物体
        - **文字提取**：提取图像中的文字内容
        - **问题解答**：基于图像回答相关问题
        - **故事创作**：根据图像创作有趣的故事
        - **诗歌创作**：将图像内容转化为诗歌形式
        - **科普讲解**：对图像内容进行科普解释
        """) 
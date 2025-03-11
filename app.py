"""
Streamlit 应用程序 - AI 图像生成器和识别助手
"""

import os
import json
import streamlit as st
import random
from src.services.image_generator import (
    generate_image_runninghub,
    WorkflowType,
    validate_api_key,
    validate_workflow_id,
    validate_prompt
)
from qwen_api import QwenAPI, TASK_TYPES
import logging
from PIL import Image
from io import BytesIO
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 默认提示词配置
DEFAULT_PROMPTS = {
    "text_to_image": [
        "一个美丽的年轻女孩，穿着白色连衣裙，站在樱花树下，阳光温柔地洒在她身上，整体画面唯美梦幻，8k超清，电影感",
        "一只可爱的小猫咪，在阳光明媚的窗台上打盹，周围有绿色植物，温馨自然的氛围，细节丰富，高清摄影",
        "未来科技感的城市夜景，霓虹灯光照亮天际线，飞行器穿梭其中，赛博朋克风格，4k超清渲染",
        "童话般的森林场景，萤火虫点缀其中，蘑菇小屋若隐若现，魔幻梦幻风格，细节精美",
        "中国传统水墨画风格的山水画，远山含黛，近水清澈，意境优美，艺术感强",
    ],
    "image_to_image": [
        "保持原图构图，增加梦幻感，提高细节，添加柔和光效，8k超清",
        "将原图转换为油画风格，增加艺术感，保持主体特征，提升画面质感",
        "为原图添加赛博朋克风格，增加科技感和未来感，保持主要元素",
        "将原图转换为水彩画风格，增加艺术气息，保持画面和谐",
        "为原图添加动漫风格，提升可爱度，保持主要特征",
    ]
}

def get_random_prompt(workflow_type):
    """
    根据工作流类型获取随机默认提示词
    
    参数:
        workflow_type: WorkflowType, 工作流类型
        
    返回:
        str: 随机选择的提示词
    """
    if workflow_type == WorkflowType.IMAGE_TO_IMAGE:
        return random.choice(DEFAULT_PROMPTS["image_to_image"])
    else:
        return random.choice(DEFAULT_PROMPTS["text_to_image"])

def load_workflows():
    """
    加载工作流配置
    
    返回:
        dict: 工作流配置字典
    """
    try:
        with open("workflows.json", "r", encoding="utf-8") as f:
            workflows = json.load(f)
            print("加载的工作流配置:", workflows)  # 添加日志
            return workflows
    except Exception as e:
        print(f"加载工作流配置出错: {str(e)}")  # 添加错误日志
        return {}

def save_uploaded_file(uploaded_file):
    """
    保存上传的文件到临时目录
    
    参数:
        uploaded_file: Streamlit上传的文件对象
        
    返回:
        str: 临时文件的路径
    """
    try:
        # 创建临时目录（如果不存在）
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 生成临时文件路径
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        temp_path = os.path.join(temp_dir, f"{uploaded_file.name}")
        
        # 保存文件
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        logger.info(f"文件已保存到: {temp_path}")
        return temp_path
    except Exception as e:
        logger.error(f"保存上传文件时出错: {str(e)}")
        raise e

def validate_image_file(file):
    """
    验证上传的图片文件
    
    参数:
        file: Streamlit上传的文件对象
        
    异常:
        ValueError: 当文件格式不支持或大小超限时
    """
    # 检查文件类型
    allowed_types = {"image/png", "image/jpeg", "image/jpg"}
    if file.type not in allowed_types:
        raise ValueError(f"不支持的文件类型: {file.type}。支持的类型: PNG, JPEG, JPG")
    
    # 检查文件大小（限制为10MB）
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    if file.size > max_size:
        raise ValueError(f"文件过大: {file.size / 1024 / 1024:.2f}MB。最大允许: 10MB")

def display_image(image_path, key_suffix="default"):
    """
    在Streamlit中显示图片，并添加下载按钮
    
    参数:
        image_path: str, 图片文件路径
        key_suffix: str, 用于创建唯一按钮key的后缀
    """
    try:
        # 显示图片
        image = Image.open(image_path)
        st.image(image, caption="生成的图片", use_column_width=True)
        
        # 添加下载按钮
        with open(image_path, "rb") as file:
            btn = st.download_button(
                label="下载图片",
                data=file,
                file_name=os.path.basename(image_path),
                mime="image/png",
                key=f"download_btn_{key_suffix}"
            )
    except Exception as e:
        logger.error(f"显示图片时出错: {str(e)}")
        st.error(f"显示图片时出错: {str(e)}")

def get_workflow_type(workflow):
    workflow_type = workflow.get('type', '')
    if workflow_type == 'image_to_image':
        return WorkflowType.IMAGE_TO_IMAGE
    elif workflow_type == 'text_to_image':
        return WorkflowType.TEXT_TO_IMAGE
    else:
        return WorkflowType.TEXT_TO_IMAGE

def render_workflow_tab(workflow_id, workflow):
    workflow_type = get_workflow_type(workflow)
    
    # 创建状态变量，用于存储生成的图片路径
    if 'generated_image_path' not in st.session_state:
        st.session_state.generated_image_path = None
    
    with st.form(key=f"form_{workflow_id}"):
        if workflow_type == WorkflowType.IMAGE_TO_IMAGE:
            uploaded_file = st.file_uploader("上传参考图片", type=['png', 'jpg', 'jpeg'], key=f"uploader_{workflow_id}")
            if uploaded_file:
                st.image(uploaded_file, caption="上传的图片")
        
        # 获取默认提示词
        default_prompt = get_random_prompt(workflow_type)
        
        # 添加提示词输入框，使用默认提示词作为占位符
        prompt = st.text_area("提示词", 
                            placeholder=f"示例提示词：{default_prompt}",
                            help="如果不输入提示词，将使用随机的优质提示词",
                            key=f"prompt_{workflow_id}")
        
        negative_prompt = st.text_area("反向提示词（可选）", key=f"negative_prompt_{workflow_id}")
        seed = st.number_input("随机种子", value=-1, key=f"seed_{workflow_id}")
        
        # 显示当前使用的提示词
        if not prompt:
            st.info(f"将使用默认提示词：{default_prompt}")
        
        submitted = st.form_submit_button("生成图片")
        
        if submitted:
            if workflow_type == WorkflowType.IMAGE_TO_IMAGE and not uploaded_file:
                st.error("请先上传参考图片")
                return
                
            try:
                with st.spinner("正在生成图片..."):
                    # 如果是图生图，保存上传的图片
                    reference_image_path = None
                    if workflow_type == WorkflowType.IMAGE_TO_IMAGE and uploaded_file:
                        temp_dir = "temp"
                        os.makedirs(temp_dir, exist_ok=True)
                        reference_image_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(reference_image_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                    
                    # 使用用户输入的提示词或默认提示词
                    final_prompt = prompt if prompt else default_prompt
                    
                    # 生成图片
                    output_path = generate_image_runninghub(
                        workflow_id=str(workflow_id),  # 确保 workflow_id 是字符串
                        workflow_config=workflow,  # 传递完整的工作流配置
                        prompt=final_prompt,
                        negative_prompt=negative_prompt,
                        seed=seed if seed != -1 else None,
                        workflow_type=workflow_type,
                        reference_image_path=reference_image_path
                    )
                    
                    # 清理临时文件
                    if reference_image_path and os.path.exists(reference_image_path):
                        os.remove(reference_image_path)
                    
                    # 显示生成的图片
                    if isinstance(output_path, dict) and 'image_path' in output_path:
                        image_path = output_path['image_path']
                        if os.path.exists(image_path):
                            st.session_state.generated_image_path = image_path
                            st.success("图片生成成功！")
                            st.image(image_path, caption="生成的图片")
                    else:
                        st.error("图片生成失败，请重试")
                        
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
    
    # 表单外部添加下载按钮
    if st.session_state.generated_image_path and os.path.exists(st.session_state.generated_image_path):
        with open(st.session_state.generated_image_path, "rb") as file:
            st.download_button(
                label="下载图片",
                data=file,
                file_name=os.path.basename(st.session_state.generated_image_path),
                mime="image/png",
                key=f"download_btn_{workflow_id}"
            )

def render_recognition_tab():
    """渲染图像识别选项卡"""
    st.header("图像识别")
    
    # 初始化千问API客户端
    try:
        qwen = QwenAPI()
    except ValueError as e:
        st.error(str(e))
        return
    
    # 上传图片
    uploaded_file = st.file_uploader("上传图片进行识别", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        try:
            # 验证上传的图片
            validate_image_file(uploaded_file)
            
            # 显示上传的图片
            st.image(uploaded_file, caption="上传的图片", use_column_width=True)
            
            # 保存上传的图片
            image_path = save_uploaded_file(uploaded_file)
            
            # 选择任务类型
            task_type = st.selectbox(
                "选择识别任务类型",
                ["通用识别", "人脸识别", "文字识别", "物体检测"]
            )
            
            # 自定义提示词
            use_custom_prompt = st.checkbox("使用自定义提示词")
            if use_custom_prompt:
                custom_prompt = st.text_area("自定义提示词", help="请输入您的自定义提示词")
            else:
                custom_prompt = None
            
            # 分析按钮
            if st.button("开始分析", key="analyze_image"):
                with st.spinner("正在分析图片..."):
                    try:
                        # 根据任务类型调用不同的处理函数
                        if task_type == "识别":
                            result = qwen.get_image_description(image_path=image_path)
                        elif task_type == "作文":
                            result = qwen.generate_essay(image_path=image_path, custom_prompt=custom_prompt)
                        elif task_type == "解题":
                            result = qwen.solve_problem(image_path=image_path, custom_prompt=custom_prompt)
                        else:
                            result = qwen.generate_creative_content(
                                image_path=image_path,
                                content_type=task_type,
                                custom_prompt=custom_prompt
                            )
                        
                        # 显示结果
                        if "error" in str(result):
                            st.error(result)
                        else:
                            st.success("分析完成！")
                            st.write(result)
                            
                    except Exception as e:
                        logger.exception("分析图片时出错")
                        st.error(f"分析图片时出错: {str(e)}")
                
            # 清理临时文件
            try:
                os.remove(image_path)
                logger.info(f"已删除临时文件: {image_path}")
            except Exception as e:
                logger.warning(f"删除临时文件时出错: {str(e)}")
                
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            logger.exception("处理上传文件时出错")
            st.error(f"处理上传文件时出错: {str(e)}")
    
    else:
        st.info("请上传一张图片")

def main():
    """主函数"""
    try:
        # 设置页面标题
        st.set_page_config(page_title="AI 图像生成器和识别助手", layout="wide")
        st.title("AI 图像生成器和识别助手")
        
        # 加载工作流配置
        workflows = load_workflows()
        if not workflows:
            st.error("加载工作流配置失败")
            return
        
        # 创建选项卡列表
        tab_names = []
        tab_workflows = []
        
        # 添加所有工作流
        for workflow_id, workflow in workflows.items():
            # 根据工作流ID判断类型
            workflow_type = get_workflow_type(workflow)
            
            tab_names.append(workflow['name'])
            tab_workflows.append((workflow_id, workflow, workflow_type))
        
        # 添加图像识别选项卡
        tab_names.append("图像识别")
        
        # 创建选项卡
        tabs = st.tabs(tab_names)
        
        # 渲染工作流选项卡
        for i, (workflow_id, workflow, workflow_type) in enumerate(tab_workflows):
            with tabs[i]:
                render_workflow_tab(workflow_id, workflow)
        
        # 渲染图像识别选项卡
        with tabs[-1]:
            render_recognition_tab()
                
    except Exception as e:
        logger.exception("应用程序运行时出错")
        st.error(f"应用程序运行时出错: {str(e)}")

if __name__ == "__main__":
    main() 
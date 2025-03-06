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
import textwrap
import json

# 导入自定义模块
from qwen_api import QwenAPI, analyze_description, TASK_TYPES, parse_qwen_response
from food_calories import get_food_calories, get_similar_foods
from product_search import generate_purchase_links, is_likely_product
from image_generator import ImageGenerator, get_available_styles, get_quality_options, enhance_prompt

# 加载环境变量
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="通义千问视觉智能助手",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 使用CSS美化界面
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem !important;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem !important;
        color: #424242;
        text-align: center;
        margin-bottom: 2rem;
    }
    .task-header {
        font-size: 1.5rem !important;
        color: #1976D2;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #1976D2;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    .result-box {
        background-color: #f5f5f5;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1976D2;
    }
    .essay-content {
        font-size: 1.1rem;
        line-height: 1.8;
        text-indent: 2em;
        white-space: pre-wrap;
    }
    .problem-solution {
        font-size: 1.1rem;
        line-height: 1.8;
        white-space: pre-wrap;
    }
    .food-section {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 0.5rem;
    }
    .product-section {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 0.5rem;
    }
    .creative-section {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 0.5rem;
    }
    .generated-image {
        margin-top: 1rem;
        margin-bottom: 1rem;
        text-align: center;
        max-width: 100%;
    }
    .style-option {
        margin-right: 10px;
        margin-bottom: 10px;
        display: inline-block;
    }
    .info-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def save_text_as_file(text, filename):
    """保存文本为文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

def download_button(text, filename, button_text):
    """创建下载按钮"""
    # 转换text为字符串（如果是字典则进行JSON转换）
    if isinstance(text, dict):
        text_str = json.dumps(text, ensure_ascii=False, indent=2)
    else:
        text_str = str(text)
        
    with open("temp.txt", "w", encoding="utf-8") as f:
        f.write(text_str)
    with open("temp.txt", "r", encoding="utf-8") as f:
        st.download_button(
            label=button_text,
            data=f,
            file_name=filename,
            mime="text/plain"
        )
    os.remove("temp.txt")

def handle_api_response(response_data, default_message="无法解析响应"):
    """
    处理API响应数据，提取其中的文本内容
    
    参数:
        response_data (str or dict): API返回的响应数据
        default_message (str): 当无法解析响应时返回的默认消息
        
    返回:
        str: 提取出的文本内容
    """
    try:
        # 使用parse_qwen_response函数解析响应
        result = parse_qwen_response(response_data)
        
        # 如果结果以"无法解析"或"错误"开头，记录原始响应并返回默认消息
        if result.startswith("无法解析") or result.startswith("错误"):
            print(f"API响应解析失败: {result}")
            print(f"原始响应: {json.dumps(response_data, ensure_ascii=False)[:1000]}...")
            return default_message
            
        return result
    except Exception as e:
        print(f"处理API响应时出错: {str(e)}")
        print(f"原始响应: {str(response_data)[:1000]}...")
        return default_message

def main():
    # 标题和介绍
    st.markdown('<h1 class="main-title">通义千问视觉智能助手</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">基于通义千问视觉语言模型的多功能AI助手，支持图像分析、作文生成、解题辅助和AI绘画</p>', unsafe_allow_html=True)
    
    # 创建侧边栏选择功能区
    with st.sidebar:
        st.markdown("## 功能选择")
        
        # 创建两个选项卡：图像分析和图像生成
        tab_analysis, tab_generation = st.tabs(["📸 图像分析", "🎨 图像生成"])
        
        with tab_analysis:
            # 图像分析任务选择
            task_options = {
                "识别": "📋 图像识别与描述",
                "作文": "📝 看图写作文",
                "解题": "🧮 看图解题",
                "故事": "📚 生成故事",
                "诗歌": "🎭 创作诗歌",
                "科普": "🔬 科普解释"
            }
            
            selected_tasks = []
            st.write("### 选择任务")
            for task_key, task_label in task_options.items():
                if st.checkbox(task_label, key=f"task_{task_key}"):
                    selected_tasks.append(task_key)
                    
            # 自定义提示选项
            st.markdown("### 自定义提示 (可选)")
            custom_prompt = {}
            for task in selected_tasks:
                custom_prompt[task] = st.text_area(
                    f"{task_options[task]}的自定义提示", 
                    key=f"prompt_{task}",
                    placeholder=f"输入自定义的{task_options[task]}提示..."
                )
                
            st.markdown("### 上传图片")
            uploaded_file = st.file_uploader("选择一张图片...", type=["jpg", "jpeg", "png"])
            
            # 将分析按钮设为隐藏状态，仅作为后备选项
            auto_analyze = st.checkbox("自动分析", value=True, key="auto_analyze", 
                                       help="上传图片后自动开始分析，无需点击按钮")
            
            # 添加一个简短的提示
            if len(selected_tasks) == 0:
                st.info("请至少选择一项分析任务")
                
            if auto_analyze and uploaded_file is not None and len(selected_tasks) > 0:
                st.success("✅ 已自动开始分析图像...")
            
            if not auto_analyze:
                analyze_button = st.button("开始分析", key="analyze_button", 
                                         disabled=len(selected_tasks) == 0 or uploaded_file is None)
            elif uploaded_file is not None and len(selected_tasks) > 0:
                # 如果启用了自动分析，且有上传文件和选择了任务，自动设置分析按钮为已点击状态
                st.session_state["analyze_button"] = True
                
        with tab_generation:
            # 图像生成选项
            st.write("### AI绘画")
            
            # 生成模式选择
            generation_mode = st.radio(
                "选择生成模式",
                options=["文本生成图像", "图像变体生成"],
                key="generation_mode"
            )
            
            if generation_mode == "文本生成图像":
                # 文本提示输入
                text_prompt = st.text_area(
                    "输入图像描述", 
                    placeholder="描述你想要生成的图像，例如：'一只可爱的小猫在阳光下玩耍'",
                    key="text_prompt"
                )
                
                # 选择图像风格
                styles = get_available_styles()
                style_names = list(styles.keys())
                
                st.write("### 选择图像风格")
                style_col1, style_col2, style_col3 = st.columns(3)
                
                with style_col1:
                    selected_style = st.radio(
                        "基础风格",
                        options=style_names[:5],
                        key="style_basic"
                    )
                    
                with style_col2:
                    selected_style2 = st.radio(
                        "艺术风格",
                        options=style_names[5:10],
                        key="style_art"
                    )
                    
                with style_col3:
                    selected_style3 = st.radio(
                        "特殊风格",
                        options=style_names[10:],
                        key="style_special"
                    )
                
                # 确定最终选择的风格
                final_style = selected_style
                if st.session_state.get("last_used_style_section") == "art":
                    final_style = selected_style2
                elif st.session_state.get("last_used_style_section") == "special":
                    final_style = selected_style3
                    
                # 更新最后使用的风格部分
                # 使用按钮或检查当前选择的值来确定最后使用的风格部分
                st_basic = st.button("使用此基础风格", key="use_basic_style")
                st_art = st.button("使用此艺术风格", key="use_art_style")
                st_special = st.button("使用此特殊风格", key="use_special_style")
                
                if st_basic:
                    st.session_state["last_used_style_section"] = "basic"
                    final_style = selected_style
                elif st_art:
                    st.session_state["last_used_style_section"] = "art"
                    final_style = selected_style2
                elif st_special:
                    st.session_state["last_used_style_section"] = "special"
                    final_style = selected_style3
                
                # 质量选择
                st.write("### 图像质量")
                quality_options = get_quality_options()
                selected_quality = st.select_slider(
                    "选择质量",
                    options=list(quality_options.keys()),
                    value="标准"
                )
                
                # 高级选项
                with st.expander("高级选项"):
                    negative_prompt = st.text_area(
                        "负面提示词", 
                        placeholder="输入你不希望在图像中出现的元素",
                        key="negative_prompt"
                    )
                    
                    use_random_seed = st.checkbox("使用随机种子", value=True, key="use_random_seed")
                    if not use_random_seed:
                        seed = st.number_input("种子值", min_value=1, max_value=2147483647, value=42, key="seed")
                    else:
                        seed = None
                        
                    use_mock = st.checkbox("使用模拟模式 (不调用外部API)", value=False, key="use_mock")
                
                # 生成按钮
                generate_text_button = st.button("生成图像", key="generate_text_button", disabled=not text_prompt)
                
            else:  # 图像变体生成
                st.write("### 上传原始图像")
                variation_file = st.file_uploader("选择一张图片作为基础...", type=["jpg", "jpeg", "png"], key="variation_file")
                
                # 变化强度
                variation_strength = st.slider("变化强度", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
                
                use_mock_variation = st.checkbox("使用模拟模式 (不调用外部API)", value=False, key="use_mock_variation")
                
                # 生成按钮
                generate_variation_button = st.button("生成变体", key="generate_variation_button", disabled=variation_file is None)
            
    # 主界面
    if uploaded_file is not None:
        # 处理上传的图片
        image = Image.open(uploaded_file)
        
        # 显示上传的图片
        st.image(image, caption="上传的图片", use_column_width=True)
        
        # 保存图片到临时文件，使用唯一的文件名避免冲突
        try:
            timestamp = int(time.time())
            random_suffix = os.urandom(4).hex()
            temp_image_path = f"temp_image_{timestamp}_{random_suffix}.jpg"
            
            # 确保临时目录存在
            temp_dir = os.path.dirname(temp_image_path)
            if temp_dir and not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
                
            # 保存图像
            image.save(temp_image_path)
        except Exception as e:
            st.error(f"保存临时图像时出错: {str(e)}")
            st.warning("将尝试使用内存中的图像进行处理...")
            temp_image_path = None
        
        # 分析按钮被点击且有任务被选择
        if st.session_state.get("analyze_button", False) and selected_tasks:
            # 生成唯一的处理标识符
            if uploaded_file is not None:
                # 生成一个基于文件内容和选定任务的唯一标识符
                file_content = uploaded_file.getvalue()
                image_hash = hash(file_content)
                tasks_hash = hash(tuple(sorted(selected_tasks)))
                process_id = f"{image_hash}_{tasks_hash}"
                
                # 检查是否已经处理过这张图像与这些任务的组合
                if "processed_images" not in st.session_state:
                    st.session_state["processed_images"] = {}
                
                # 如果这个组合已经被处理过，跳过处理
                if process_id in st.session_state["processed_images"]:
                    # 直接显示之前的结果
                    results = st.session_state["processed_images"][process_id]
                else:
                    # 进行新的处理
                    with st.spinner("正在分析图像..."):
                        # 创建API实例
                        api = QwenAPI()
                        
                        # 创建一个标志来表示已经进行了处理，而不是直接修改按钮状态
                        analysis_processed_key = "analysis_processed_" + str(int(time.time()))
                        st.session_state[analysis_processed_key] = True
                        
                        # 存储所有结果
                        results = {}
                        
                        # 对每个选定的任务进行处理
                        for task in selected_tasks:
                            try:
                                if temp_image_path is None:
                                    # 如果临时文件保存失败，则使用内存中的图像
                                    image_bytes = io.BytesIO()
                                    image.save(image_bytes, format="JPEG")
                                    image_bytes.seek(0)
                                    
                                    # 使用自定义提示
                                    if custom_prompt.get(task):
                                        task_result = api.process_image_request(
                                            image_data=image_bytes.getvalue(),
                                            task_type=task,
                                            custom_prompt=custom_prompt[task]
                                        )
                                    else:
                                        # 使用默认提示
                                        task_result = api.process_image_request(
                                            image_data=image_bytes.getvalue(),
                                            task_type=task
                                        )
                                else:
                                    # 使用临时文件路径
                                    if custom_prompt.get(task):
                                        # 使用自定义提示
                                        task_result = api.process_image_request(
                                            image_path=temp_image_path,
                                            task_type=task,
                                            custom_prompt=custom_prompt[task]
                                        )
                                    else:
                                        # 使用默认提示
                                        task_result = api.process_image_request(
                                            image_path=temp_image_path,
                                            task_type=task
                                        )
                            except Exception as e:
                                st.error(f"处理任务 '{task}' 时出错: {str(e)}")
                                task_result = f"处理失败: {str(e)}"
                            
                            # 解析API响应以获取文本内容
                            if isinstance(task_result, dict) or isinstance(task_result, str):
                                task_result = handle_api_response(task_result, f"处理{task}任务失败")
                            
                            # 存储结果
                            results[task] = task_result
                        
                        # 保存处理结果以备后用
                        st.session_state["processed_images"][process_id] = results
                
                # 显示结果
                st.markdown('<h2 class="task-header">分析结果</h2>', unsafe_allow_html=True)
                
                # 首先总是显示识别结果（如果有）
                if "识别" in results:
                    with st.expander("📋 图像识别结果", expanded=True):
                        st.markdown(f'<div class="result-box">{results["识别"]}</div>', unsafe_allow_html=True)
                        
                        # 下载按钮
                        download_button(results["识别"], "图像识别结果.txt", "下载识别结果")
                        
                        # 分析识别结果
                        food_items, products = analyze_description(results["识别"])
                        
                        # 显示食物信息（如果有）
                        if food_items:
                            st.markdown('<div class="food-section">', unsafe_allow_html=True)
                            st.markdown("#### 🍎 食物热量信息")
                            
                            for food in food_items:
                                food_info = get_food_calories(food)
                                
                                # 检查返回值是否为字典类型
                                if isinstance(food_info, dict):
                                    calories = food_info.get("热量")
                                    description = food_info.get("描述", "")
                                    
                                    if calories:
                                        st.markdown(f"**{food}**: {calories} 千卡/100克")
                                        
                                        # 如果有更详细的描述，显示它
                                        if description and description != f"{food}平均每100克含有{calories}千卡热量":
                                            st.caption(description)
                                            
                                        # 如果有营养素信息，显示它
                                        if "营养素" in food_info:
                                            with st.expander(f"查看「{food}」的营养素信息"):
                                                for nutrient, value in food_info["营养素"].items():
                                                    st.markdown(f"**{nutrient}**: {value}克")
                                        
                                        # 显示类似食物
                                        similar_foods = get_similar_foods(food)
                                        if similar_foods:
                                            with st.expander(f"查看类似于「{food}」的食物"):
                                                if isinstance(similar_foods, dict):
                                                    for similar_food, similar_calories in similar_foods.items():
                                                        st.markdown(f"**{similar_food}**: {similar_calories} 千卡")
                                                elif isinstance(similar_foods, list):
                                                    for similar_food in similar_foods:
                                                        st.markdown(f"**{similar_food}**")
                                    else:
                                        st.markdown(f"**{food}**: 未找到热量信息")
                                else:
                                    # 兼容旧版本返回格式
                                    calories, unit = food_info if isinstance(food_info, tuple) else (food_info, "100克")
                                    if calories:
                                        st.markdown(f"**{food}**: {calories} 千卡/{unit}")
                                    else:
                                        st.markdown(f"**{food}**: 未找到热量信息")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 显示商品信息（如果有）
                        if products:
                            st.markdown('<div class="product-section">', unsafe_allow_html=True)
                            st.markdown("#### 🛒 商品购买链接")
                            
                            for product in products:
                                links = generate_purchase_links(product)
                                st.markdown(f"**{product}**")
                                for platform, link in links.items():
                                    st.markdown(f"[{platform}]({link})")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                
                # 显示作文结果（如果有）
                if "作文" in results:
                    with st.expander("📝 看图写作文", expanded=True):
                        st.markdown(f'<div class="result-box"><div class="essay-content">{results["作文"]}</div></div>', unsafe_allow_html=True)
                        
                        # 下载按钮
                        download_button(results["作文"], "看图作文.txt", "下载作文")
                
                # 显示解题结果（如果有）
                if "解题" in results:
                    with st.expander("🧮 看图解题", expanded=True):
                        st.markdown(f'<div class="result-box"><div class="problem-solution">{results["解题"]}</div></div>', unsafe_allow_html=True)
                        
                        # 下载按钮
                        download_button(results["解题"], "题目解答.txt", "下载解答")
                
                # 显示创意内容（故事、诗歌、科普）
                for task in ["故事", "诗歌", "科普"]:
                    if task in results:
                        task_titles = {
                            "故事": "📚 生成故事",
                            "诗歌": "🎭 创作诗歌",
                            "科普": "🔬 科普解释"
                        }
                        
                        with st.expander(task_titles[task], expanded=True):
                            st.markdown(f'<div class="result-box creative-section"><div class="essay-content">{results[task]}</div></div>', unsafe_allow_html=True)
                            
                            # 下载按钮
                            download_button(results[task], f"{task_titles[task].split()[1]}.txt", f"下载{task}")
                
                # 如果这是新处理的结果，完成后删除临时文件
                if process_id not in st.session_state.get("processed_images", {}) or process_id == st.session_state.get("last_processed_id"):
                    if temp_image_path and os.path.exists(temp_image_path):
                        try:
                            os.remove(temp_image_path)
                            print(f"临时文件 {temp_image_path} 已删除")
                        except Exception as e:
                            print(f"删除临时文件出错: {str(e)}")
                
                # 记录最后处理的ID
                st.session_state["last_processed_id"] = process_id

    # 处理图像生成
    # 文本到图像生成
    if st.session_state.get("generation_mode") == "文本生成图像" and st.session_state.get("generate_text_button", False):
        if st.session_state.get("text_prompt"):
            with st.spinner("正在生成图像..."):
                # 创建一个标志来表示已经进行了处理，而不是直接修改按钮状态
                text_processed_key = "text_processed_" + str(int(time.time()))
                st.session_state[text_processed_key] = True
                
                # 获取参数
                prompt = st.session_state.get("text_prompt")
                
                # 根据最后使用的按钮决定使用哪个风格
                if "last_used_style_section" not in st.session_state:
                    # 默认使用基础风格
                    style = selected_style
                elif st.session_state["last_used_style_section"] == "art":
                    style = selected_style2
                elif st.session_state["last_used_style_section"] == "special":
                    style = selected_style3
                else:
                    style = selected_style
                
                quality = st.session_state.get("selected_quality", "标准")
                negative_prompt = st.session_state.get("negative_prompt")
                use_mock = st.session_state.get("use_mock", False)
                
                # 使用随机种子或指定种子
                if st.session_state.get("use_random_seed", True):
                    seed = None
                else:
                    seed = st.session_state.get("seed", 42)
                
                # 创建生成器实例
                generator = ImageGenerator()
                
                try:
                    # 生成图像
                    generated_image_path = generator.generate_from_text(
                        prompt=prompt,
                        style=style,
                        quality=quality,
                        negative_prompt=negative_prompt,
                        seed=seed,
                        use_mock=use_mock
                    )
                    
                    # 显示生成的图像
                    st.markdown('<h2 class="task-header">生成结果</h2>', unsafe_allow_html=True)
                    
                    if os.path.exists(generated_image_path):
                        # 打开生成的图像
                        generated_image = Image.open(generated_image_path)
                        
                        # 显示图像
                        st.markdown('<div class="generated-image">', unsafe_allow_html=True)
                        st.image(generated_image, caption=f"AI生成图像 - {style}风格", use_column_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 创建下载按钮
                        with open(generated_image_path, "rb") as img_file:
                            st.download_button(
                                label="下载图像",
                                data=img_file,
                                file_name=os.path.basename(generated_image_path),
                                mime="image/png"
                            )
                            
                        # 显示使用的提示词
                        with st.expander("查看提示词"):
                            enhanced_prompt = enhance_prompt(prompt, style)
                            st.write("**增强后的提示词:**")
                            st.write(enhanced_prompt)
                            if negative_prompt:
                                st.write("**负面提示词:**")
                                st.write(negative_prompt)
                    else:
                        st.error("图像生成失败，请重试。")
                
                except Exception as e:
                    st.error(f"生成过程中发生错误: {str(e)}")
    
    # 处理图像变体生成
    if st.session_state.get("generation_mode") == "图像变体生成" and st.session_state.get("generate_variation_button", False):
        if st.session_state.get("variation_file"):
            with st.spinner("正在生成图像变体..."):
                # 创建一个标志来表示已经进行了处理，而不是直接修改按钮状态
                variation_processed_key = "variation_processed_" + str(int(time.time()))
                st.session_state[variation_processed_key] = True
                
                # 获取上传的图像
                variation_file = st.session_state.get("variation_file")
                variation_image = Image.open(variation_file)
                
                # 保存到临时文件
                temp_variation_path = "temp_variation_image.jpg"
                variation_image.save(temp_variation_path)
                
                # 获取参数
                variation_strength = st.session_state.get("variation_strength", 0.7)
                use_mock = st.session_state.get("use_mock_variation", False)
                
                # 创建生成器实例
                generator = ImageGenerator()
                
                try:
                    # 生成变体
                    variation_image_path = generator.create_image_variation(
                        image_path=temp_variation_path,
                        variation_strength=variation_strength,
                        use_mock=use_mock
                    )
                    
                    # 显示结果
                    st.markdown('<h2 class="task-header">变体结果</h2>', unsafe_allow_html=True)
                    
                    # 显示原图和变体的对比
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**原始图像**")
                        st.image(variation_image, use_column_width=True)
                        
                    with col2:
                        if os.path.exists(variation_image_path):
                            st.markdown("**变体图像**")
                            
                            # 打开生成的变体图像
                            result_image = Image.open(variation_image_path)
                            st.image(result_image, use_column_width=True)
                            
                            # 创建下载按钮
                            with open(variation_image_path, "rb") as img_file:
                                st.download_button(
                                    label="下载变体图像",
                                    data=img_file,
                                    file_name=os.path.basename(variation_image_path),
                                    mime="image/png"
                                )
                        else:
                            st.error("变体生成失败，请重试。")
                    
                    # 完成后删除临时文件
                    if os.path.exists(temp_variation_path):
                        os.remove(temp_variation_path)
                
                except Exception as e:
                    st.error(f"生成过程中发生错误: {str(e)}")
                    if os.path.exists(temp_variation_path):
                        os.remove(temp_variation_path)
    
    # 提供使用说明
    with st.expander("使用说明"):
        st.markdown("""
        ## 功能介绍
        
        ### 图像分析功能
        - **图像识别与描述**: 识别并详细描述图像内容，包括食物热量和商品信息
        - **看图写作文**: 根据图像内容自动生成不少于300字的作文
        - **看图解题**: 识别图像中的题目并给出详细解答
        - **创意内容生成**: 可生成与图像相关的故事、诗歌或科普解释
        
        ### AI绘画功能
        - **文本生成图像**: 根据文字描述生成图像，支持15种艺术风格
        - **图像变体生成**: 基于上传的图像创建不同风格的变体
        - **多样风格**: 从写实、油画、水彩到二次元、赛博朋克等多种风格
        - **质量选择**: 支持标准、高清、超清多种分辨率
        
        ## 使用技巧
        1. 在进行图像分析时，可以同时选择多个任务一次性完成
        2. 生成图像时，尝试添加详细的描述和风格，会得到更好的效果
        3. 使用自定义提示来引导AI生成更符合期望的内容
        4. 高级选项中的负面提示词可以帮助排除不需要的元素
        """)
    
    # 添加API密钥设置指南
    with st.expander("API设置"):
        st.markdown("""
        ### API密钥设置
        
        本应用使用两个API：
        1. **通义千问API**: 用于图像识别、作文生成和解题
        2. **Stability AI API**: 用于AI图像生成
        
        #### 设置方法：
        1. 创建一个`.env`文件在应用根目录
        2. 添加以下内容：
           ```
           QWEN_API_KEY=你的通义千问API密钥
           STABILITY_API_KEY=你的Stability AI API密钥
           ```
        3. 如果没有Stability API密钥，应用将使用模拟模式生成图像
        
        #### 获取API密钥：
        - 通义千问API密钥: [阿里云通义平台](https://dashscope.aliyun.com/)
        - Stability AI API密钥: [Stability AI官网](https://stability.ai/)
        """)
                
if __name__ == "__main__":
    main() 
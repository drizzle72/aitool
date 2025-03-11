"""
AI图像生成模块

提供多种AI图像生成功能，包括文本生成图像、图像变体创建等
"""

import os
import io
import base64
import time
import random
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import numpy as np

# 加载环境变量
load_dotenv()

# 创建图像存储目录
GENERATED_IMAGES_DIR = "generated_images"
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)

# API配置
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")  # Stability AI API密钥
STABILITY_API_BASE = "https://api.stability.ai/v1/generation"
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")  # 通义千问API密钥
DASHSCOPE_API_BASE = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
RUNNINGHUB_API_KEY = os.getenv("RUNNINGHUB_API_KEY")  # RunningHub API密钥
RUNNINGHUB_API_BASE = "https://www.runninghub.cn"  # RunningHub API基础URL
RUNNINGHUB_WORKFLOW_ID = "1889944455695441922"  # RunningHub 工作流ID

# 翻译API选项
TRANSLATION_APIS = {
    "baidu": "百度翻译",
    "dashscope": "通义千问"
}

# 创建图像风格列表
IMAGE_STYLES = {
    "写实": {"name": "写实风格，高清细节，自然光效", "preset": "photographic"},
    "油画": {"name": "油画风格，明显的笔触，丰富的色彩和质感", "preset": "digital-art"},
    "水彩": {"name": "水彩画风格，柔和的色彩过渡，轻盈通透的效果", "preset": "analog-film"},
    "插画": {"name": "插画风格，简洁线条，鲜明色彩，平面化设计", "preset": "comic-book"},
    "二次元": {"name": "日本动漫风格，大眼睛，精致的线条，鲜艳的色彩", "preset": "anime"},
    "像素艺术": {"name": "复古像素游戏风格，方块化的图像元素", "preset": "pixel-art"},
    "赛博朋克": {"name": "赛博朋克风格，未来感，霓虹灯效果，高科技与低生活的对比", "preset": "neon-punk"},
    "奇幻": {"name": "奇幻风格，魔法元素，超自然景观和生物", "preset": "fantasy-art"},
    "哥特": {"name": "哥特风格，黑暗氛围，尖顶建筑，华丽装饰", "preset": "digital-art"},
    "印象派": {"name": "印象派风格，强调光和色彩的表现，笔触明显且色彩鲜艳", "preset": "analog-film"},
    "极简主义": {"name": "极简主义风格，简洁的线条和形状，有限的色彩", "preset": "line-art"},
    "复古": {"name": "复古风格，怀旧色调，老式摄影效果", "preset": "analog-film"},
    "蒸汽朋克": {"name": "蒸汽朋克风格，维多利亚时代美学与蒸汽动力科技的结合", "preset": "digital-art"},
    "波普艺术": {"name": "波普艺术风格，明亮饱和的色彩，大众流行文化元素", "preset": "digital-art"},
    "超现实主义": {"name": "超现实主义风格，梦幻与现实的混合，不符合常理的场景", "preset": "fantasy-art"},
    "动漫": {"name": "动漫风格，清新可爱的动画效果", "preset": "anime"},
    "3D": {"name": "3D渲染风格，逼真的立体效果", "preset": "3d-render"},
    "素描": {"name": "素描风格，黑白线条勾勒", "preset": "sketch"},
    "水墨": {"name": "中国水墨画风格，意境优美", "preset": "ink"},
    "霓虹": {"name": "霓虹风格，明亮的发光效果", "preset": "neon"}
}

# 图像质量选项
IMAGE_QUALITY = {
    "标准": {"width": 1024, "height": 1024, "steps": 30},
    "高清": {"width": 1152, "height": 896, "steps": 40},
    "超清": {"width": 1536, "height": 640, "steps": 50}
}

class ImageGenerator:
    """图像生成类"""
    
    def __init__(self, api_key=None, baidu_trans_appid=None, baidu_trans_key=None, 
                 dashscope_api_key=None, runninghub_api_key=None, translation_api="baidu"):
        """
        初始化图像生成器
        
        参数:
            api_key (str, optional): Stability API密钥
            baidu_trans_appid (str, optional): 百度翻译API的APPID
            baidu_trans_key (str, optional): 百度翻译API的密钥
            dashscope_api_key (str, optional): 通义千问API密钥
            runninghub_api_key (str, optional): RunningHub API密钥
            translation_api (str): 使用的翻译API
        """
        self.stability_api_key = api_key or STABILITY_API_KEY
        self.baidu_trans_appid = baidu_trans_appid or os.environ.get("BAIDU_TRANS_APPID")
        self.baidu_trans_key = baidu_trans_key or os.environ.get("BAIDU_TRANS_KEY")
        self.dashscope_api_key = dashscope_api_key or DASHSCOPE_API_KEY
        self.runninghub_api_key = runninghub_api_key or RUNNINGHUB_API_KEY
        self.translation_api = translation_api if translation_api in TRANSLATION_APIS else "baidu"
        
        if not self.stability_api_key and not self.runninghub_api_key:
            print("警告: 未提供任何API密钥，将使用模拟生成模式")
        
        if self.translation_api == "baidu" and (not self.baidu_trans_appid or not self.baidu_trans_key):
            print("警告: 未提供百度翻译API密钥，将使用模拟翻译模式")
        elif self.translation_api == "dashscope" and not self.dashscope_api_key:
            print("警告: 未提供通义千问API密钥，将使用模拟翻译模式")
            
    def generate_from_text(self, prompt, style=None, quality="标准", negative_prompt=None, seed=None, use_mock=False):
        """
        根据文本提示生成图像
        
        参数:
            prompt (str): 图像描述文本
            style (str, optional): 图像风格
            quality (str): 图像质量 ("标准", "高清", "超清")
            negative_prompt (str, optional): 负面提示词
            seed (int, optional): 随机种子
            use_mock (bool): 是否使用模拟模式
            
        返回:
            str: 生成的图像文件路径
        """
        # 确保prompt不为None
        if not prompt:
            prompt = "空白图像"
            
        # 如果指定了风格，将风格描述添加到提示词
        if style and style in IMAGE_STYLES:
            enhanced_prompt = f"{prompt}，{IMAGE_STYLES[style]['name']}"
        else:
            enhanced_prompt = prompt
            
        # 中文提示词转换为英文(实际项目中应调用翻译API)
        # 这里我们简单模拟这个过程，实际应用中可以使用百度、谷歌等翻译API
        english_prompt = self._translate_text(enhanced_prompt)
        
        # 获取质量参数
        quality_params = IMAGE_QUALITY.get(quality, IMAGE_QUALITY["标准"])
        
        # 如果未提供种子，生成随机种子
        if seed is None:
            seed = random.randint(1, 2147483647)
            
        # 选择生成模式
        if use_mock or not self.stability_api_key:
            return self._mock_generate_image(prompt, style, quality_params, seed)
        else:
            try:
                # 准备API调用参数
                payload = {
                    "text_prompts": [
                        {
                            "text": english_prompt,
                            "weight": 1.0
                        }
                    ],
                    "cfg_scale": 7.0,
                    "height": quality_params["height"],
                    "width": quality_params["width"],
                    "samples": 1,
                    "steps": quality_params["steps"],
                    "seed": seed
                }
                
                # 添加负面提示词
                if negative_prompt:
                    payload["text_prompts"].append({
                        "text": negative_prompt,
                        "weight": -1.0
                    })
                
                # 添加风格预设
                if style and style in IMAGE_STYLES:
                    payload["style_preset"] = IMAGE_STYLES[style]["preset"]
                
                # 调用API
                endpoint = "stable-diffusion-xl-1024-v1-0/text-to-image"
                headers = {
                    "Accept": "image/png",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.stability_api_key}"
                }
                
                image_data = self._call_stability_api(endpoint=endpoint, payload=payload, headers=headers)
                
                if image_data:
                    # 保存图像
                    timestamp = int(time.time())
                    output_path = os.path.join(GENERATED_IMAGES_DIR, f"gen_{timestamp}_{seed}.png")
                    
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                        
                    return output_path
                else:
                    return self._mock_generate_image(prompt, style, quality_params, seed)
                    
            except Exception as e:
                print(f"API调用失败，切换到模拟模式: {e}")
                return self._mock_generate_image(prompt, style, quality_params, seed)
    
    def create_image_variation(self, image_path, variation_strength=0.7, use_mock=False):
        """
        创建图像变体
        
        参数:
            image_path (str): 原始图像路径
            variation_strength (float): 变化强度 (0-1)
            use_mock (bool): 是否使用模拟模式
            
        返回:
            str: 生成的变体图像文件路径
        """
        if use_mock or not self.stability_api_key:
            return self._mock_image_variation(image_path, variation_strength)
        else:
            try:
                # 实际项目中应调用API实现
                # 由于Stability AI API变体生成较复杂，这里我们用模拟实现
                return self._mock_image_variation(image_path, variation_strength)
            except Exception as e:
                print(f"API调用失败，切换到模拟模式: {e}")
                return self._mock_image_variation(image_path, variation_strength)
    
    def _call_stability_api(self, endpoint, payload, headers=None):
        """
        调用Stability AI的API
        
        参数:
            endpoint (str): API端点
            payload (dict): 请求参数
            headers (dict, optional): 请求头
            
        返回:
            bytes: 生成的图像数据
        """
        if not self.stability_api_key:
            print("API调用失败，切换到模拟模式: 未提供API密钥")
            return None
            
        try:
            # 设置默认请求头
            if headers is None:
                headers = {
                    "Accept": "image/png",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.stability_api_key}"
                }
            
            # 添加安全过滤
            if "text_prompts" in payload:
                for prompt in payload["text_prompts"]:
                    prompt["text"] = self._sanitize_prompt(prompt["text"])
            
            # 发送请求
            response = requests.post(
                f"{STABILITY_API_BASE}/{endpoint}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code == 200:
                return response.content
            elif response.status_code == 400:
                error_data = response.json()
                if "message" in error_data:
                    print(f"API调用失败，切换到模拟模式: API调用失败: {response.status_code} - {error_data}")
                    if "style_preset" in error_data.get("message", ""):
                        # 如果是风格预设错误，尝试使用默认风格
                        payload["style_preset"] = "photographic"
                        return self._call_stability_api(endpoint, payload, headers)
            elif response.status_code == 403:
                error_data = response.json()
                if "content_moderation" in error_data.get("name", ""):
                    print(f"API调用失败，切换到模拟模式: 内容被审核系统拦截")
                    # 尝试清理提示词后重试
                    if "text_prompts" in payload:
                        for prompt in payload["text_prompts"]:
                            prompt["text"] = self._sanitize_prompt(prompt["text"], strict=True)
                        return self._call_stability_api(endpoint, payload, headers)
            
            print(f"API调用失败，切换到模拟模式: API调用失败: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            print(f"API调用失败，切换到模拟模式: {str(e)}")
            return None
            
    def _sanitize_prompt(self, prompt, strict=False):
        """
        清理提示词，移除可能触发内容审核的内容
        
        参数:
            prompt (str): 原始提示词
            strict (bool): 是否使用严格模式
            
        返回:
            str: 清理后的提示词
        """
        # 基础清理
        cleaned = prompt.replace("血腥", "").replace("暴力", "").replace("恐怖", "")
        
        if strict:
            # 严格模式下的额外清理
            cleaned = cleaned.replace("裸", "").replace("性", "").replace("死", "")
            cleaned = cleaned.replace("恐怖", "").replace("血", "").replace("暴力", "")
            
        return cleaned.strip()
    
    def _mock_generate_image(self, prompt, style, quality_params, seed):
        """
        模拟图像生成（用于测试或API不可用时）
        
        参数:
            prompt (str): 提示词
            style (str): 风格
            quality_params (dict): 质量参数
            seed (int): 随机种子
            
        返回:
            str: 生成的图像文件路径
        """
        # 设置随机种子以保证可重复性
        random.seed(seed)
        np.random.seed(seed)
        
        # 创建一个随机颜色的基础图像
        width = quality_params["width"]
        height = quality_params["height"]
        
        # 根据提示词和风格确定主色调
        # 这只是一个简单的演示，实际上不同提示词应有不同的视觉效果
        colors = self._get_colors_from_prompt(prompt, style)
        
        # 创建图像
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 根据风格选择不同的生成方式
        if style in ["像素艺术", "二次元", "极简主义"]:
            # 创建方块图案
            block_size = max(4, width // 64)
            for y in range(0, height, block_size):
                for x in range(0, width, block_size):
                    color = random.choice(colors)
                    img_array[y:min(y+block_size, height), x:min(x+block_size, width)] = color
        
        elif style in ["水彩", "油画", "印象派"]:
            # 创建渐变和笔触效果
            for _ in range(100):
                # 随机形状
                center_x = np.random.randint(0, width)
                center_y = np.random.randint(0, height)
                size = np.random.randint(width//20, width//4)
                color = random.choice(colors)
                
                # 画一个柔和的圆形区域
                y, x = np.ogrid[-center_y:height-center_y, -center_x:width-center_x]
                mask = x*x + y*y <= size*size
                img_array[mask] = color
        
        else:
            # 默认：创建抽象渐变
            for _ in range(20):
                # 随机渐变
                start_x = np.random.randint(0, width)
                start_y = np.random.randint(0, height)
                end_x = np.random.randint(0, width)
                end_y = np.random.randint(0, height)
                
                color1 = random.choice(colors)
                color2 = random.choice(colors)
                
                # 创建渐变
                for y in range(height):
                    for x in range(width):
                        # 计算当前点到起点和终点的距离比例
                        d1 = np.sqrt((x - start_x)**2 + (y - start_y)**2)
                        d2 = np.sqrt((x - end_x)**2 + (y - end_y)**2)
                        
                        # 混合颜色
                        if d1 + d2 > 0:
                            ratio = d1 / (d1 + d2)
                            color = (
                                int(color1[0] * (1 - ratio) + color2[0] * ratio),
                                int(color1[1] * (1 - ratio) + color2[1] * ratio),
                                int(color1[2] * (1 - ratio) + color2[2] * ratio)
                            )
                            
                            # 与现有颜色混合
                            img_array[y, x] = (img_array[y, x] * 0.7 + np.array(color) * 0.3).astype(np.uint8)
        
        # 转换为PIL图像
        img = Image.fromarray(img_array)
        
        # 添加一些文本说明
        timestamp = int(time.time())
        prompt_short = prompt[:30] + "..." if len(prompt) > 30 else prompt
        output_path = os.path.join(GENERATED_IMAGES_DIR, f"mock_{timestamp}_{seed}.png")
        
        # 保存图像
        img.save(output_path)
        
        return output_path
    
    def _mock_image_variation(self, image_path, variation_strength):
        """
        模拟图像变体创建
        
        参数:
            image_path (str): 原始图像路径
            variation_strength (float): 变化强度
            
        返回:
            str: 变体图像文件路径
        """
        try:
            # 加载原始图像
            original_img = Image.open(image_path)
            
            # 调整大小（保持统一处理）
            max_size = 1024
            width, height = original_img.size
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                original_img = original_img.resize((new_width, new_height), Image.LANCZOS)
            
            # 转换为numpy数组
            img_array = np.array(original_img)
            
            # 添加随机变化
            noise = np.random.normal(0, 30 * variation_strength, img_array.shape).astype(np.int16)
            varied_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # 调整颜色和对比度
            varied_img = Image.fromarray(varied_array)
            
            # 随机调整亮度、对比度和饱和度
            from PIL import ImageEnhance
            
            enhancer = ImageEnhance.Brightness(varied_img)
            varied_img = enhancer.enhance(random.uniform(0.8, 1.2))
            
            enhancer = ImageEnhance.Contrast(varied_img)
            varied_img = enhancer.enhance(random.uniform(0.9, 1.3))
            
            enhancer = ImageEnhance.Color(varied_img)
            varied_img = enhancer.enhance(random.uniform(0.9, 1.4))
            
            # 保存结果
            timestamp = int(time.time())
            output_path = os.path.join(GENERATED_IMAGES_DIR, f"var_{timestamp}_{os.path.basename(image_path)}")
            varied_img.save(output_path)
            
            return output_path
        
        except Exception as e:
            print(f"创建图像变体失败: {e}")
            # 如果处理失败，返回原图
            return image_path
    
    def _get_colors_from_prompt(self, prompt, style):
        """
        从提示词和风格中提取颜色
        
        参数:
            prompt (str): 提示词
            style (str): 风格
            
        返回:
            list: 颜色列表
        """
        # 常见颜色关键词映射
        color_keywords = {
            "红": [200, 50, 50],
            "绿": [50, 180, 50],
            "蓝": [50, 100, 200],
            "黄": [230, 200, 50],
            "紫": [150, 50, 200],
            "青": [50, 200, 200],
            "橙": [230, 140, 30],
            "粉": [230, 150, 180],
            "棕": [140, 80, 20],
            "灰": [130, 130, 130],
            "黑": [30, 30, 30],
            "白": [240, 240, 240],
        }
        
        # 风格相关的默认颜色
        style_colors = {
            "写实": [[100, 100, 100], [150, 150, 150], [200, 200, 200]],
            "油画": [[120, 80, 40], [40, 100, 160], [160, 160, 80]],
            "水彩": [[200, 220, 255], [255, 200, 200], [200, 250, 200]],
            "插画": [[255, 200, 100], [100, 200, 255], [200, 100, 255]],
            "二次元": [[255, 170, 200], [170, 200, 255], [170, 255, 200]],
            "像素艺术": [[100, 120, 200], [200, 100, 100], [100, 200, 100]],
            "赛博朋克": [[0, 200, 255], [255, 0, 150], [150, 255, 0]],
            "奇幻": [[100, 50, 200], [50, 200, 100], [200, 100, 50]],
            "哥特": [[50, 0, 100], [100, 0, 50], [30, 30, 50]],
            "印象派": [[200, 220, 100], [100, 200, 220], [220, 100, 200]],
            "极简主义": [[240, 240, 240], [30, 30, 30], [200, 200, 200]],
            "复古": [[200, 180, 140], [140, 120, 100], [180, 160, 120]],
            "蒸汽朋克": [[180, 140, 100], [100, 80, 60], [140, 100, 60]],
            "波普艺术": [[255, 50, 50], [50, 50, 255], [255, 255, 50]],
            "超现实主义": [[100, 200, 255], [255, 100, 200], [200, 255, 100]]
        }
        
        # 从风格获取基础颜色
        if not style or style not in style_colors:
            base_colors = [[100, 100, 100], [200, 200, 200], [150, 150, 150]]
        else:
            base_colors = style_colors.get(style)
        
        # 从提示词中查找颜色关键词
        detected_colors = []
        if prompt:
            for keyword, color in color_keywords.items():
                if keyword in prompt:
                    detected_colors.append(color)
        
        # 组合颜色
        colors = base_colors + detected_colors if detected_colors else base_colors
        return colors
    
    def _translate_text(self, text, from_lang="zh", to_lang="en"):
        """
        使用通义千问API进行翻译
        
        参数:
            text (str): 需要翻译的文本
            from_lang (str): 源语言（未使用）
            to_lang (str): 目标语言（未使用）
            
        返回:
            str: 翻译后的文本
        """
        if not text:
            return ""
            
        if not self.dashscope_api_key:
            print("警告: 未提供通义千问API密钥，将使用模拟翻译模式")
            return f"[原文: {text}]"
            
        try:
            # 构建翻译提示词
            prompt = f"请将以下中文翻译成英文，只返回翻译结果，不要解释：\n{text}"
            
            # 准备API调用参数
            payload = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.dashscope_api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            response = requests.post(
                DASHSCOPE_API_BASE,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                if "output" in result and "text" in result["output"]:
                    return result["output"]["text"].strip()
            
            print(f"翻译API调用失败: {response.status_code} - {response.text}")
            return f"[原文: {text}]"
            
        except Exception as e:
            print(f"翻译过程中出错: {str(e)}")
            return f"[原文: {text}]"

    def _check_task_status(self, task_id):
        """
        检查RunningHub任务状态
        
        参数:
            task_id (str): 任务ID
            
        返回:
            str: 任务状态
        """
        try:
            # 准备API调用参数
            payload = {
                "taskId": task_id,
                "apiKey": self.runninghub_api_key
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Host": "www.runninghub.cn"
            }
            
            # 创建Session对象以自定义SSL验证
            session = requests.Session()
            session.verify = False  # 禁用SSL证书验证
            
            # 发送请求
            response = session.post(
                f"{RUNNINGHUB_API_BASE}/task/openapi/status",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return result.get("data")
            
            return None
            
        except Exception as e:
            print(f"检查任务状态失败: {str(e)}")
            return None

    def _get_task_outputs(self, task_id):
        """
        获取RunningHub任务输出
        
        参数:
            task_id (str): 任务ID
            
        返回:
            list: 输出文件列表，每个元素包含fileUrl和fileType
        """
        try:
            # 准备API调用参数
            payload = {
                "taskId": task_id,
                "apiKey": self.runninghub_api_key
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
                "Accept": "*/*",
                "Host": "www.runninghub.cn",
                "Connection": "keep-alive"
            }
            
            # 创建Session对象以自定义SSL验证
            session = requests.Session()
            session.verify = False  # 禁用SSL证书验证
            
            # 发送请求
            response = session.post(
                f"{RUNNINGHUB_API_BASE}/task/openapi/outputs",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 and "data" in result:
                    return result["data"]
            
            return None
            
        except Exception as e:
            print(f"获取任务输出失败: {str(e)}")
            return None

    def _download_image(self, url, output_path):
        """
        下载图像文件
        
        参数:
            url (str): 图像URL
            output_path (str): 保存路径
            
        返回:
            bool: 下载是否成功
        """
        try:
            # 创建Session对象以自定义SSL验证
            session = requests.Session()
            session.verify = False  # 禁用SSL证书验证
            
            # 下载图像
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                # 保存图像
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
            
            return False
            
        except Exception as e:
            print(f"下载图像失败: {str(e)}")
            return False

    def generate_image_runninghub(self, prompt, style=None, quality="标准", 
                                negative_prompt=None, seed=None, use_mock=False):
        """
        使用RunningHub API生成图像
        
        参数:
            prompt (str): 提示词
            style (str, optional): 图像风格
            quality (str): 图像质量
            negative_prompt (str, optional): 负面提示词
            seed (int, optional): 随机种子
            use_mock (bool): 是否使用模拟模式
            
        返回:
            str: 生成的图像文件路径
        """
        if not prompt:
            prompt = "空白图像"
            
        # 如果使用模拟模式或未提供API密钥
        if use_mock or not self.runninghub_api_key:
            return self._mock_generate_image(prompt, style, IMAGE_QUALITY[quality], seed)
            
        try:
            # 如果未提供种子，生成随机种子
            if seed is None:
                seed = random.randint(1, 1000000)
                
            # 准备API调用参数
            payload = {
                "workflowId": RUNNINGHUB_WORKFLOW_ID,
                "apiKey": self.runninghub_api_key,
                "nodeInfoList": [
                    {
                        "nodeId": "6",
                        "fieldName": "text",
                        "fieldValue": prompt
                    },
                    {
                        "nodeId": "3",
                        "fieldName": "seed",
                        "fieldValue": seed
                    }
                ]
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
                "Accept": "*/*",
                "Host": "www.runninghub.cn",
                "Connection": "keep-alive"
            }
            
            # 创建Session对象以自定义SSL验证
            session = requests.Session()
            session.verify = False  # 禁用SSL证书验证
            
            # 发送请求
            print(f"发送请求到RunningHub API: {RUNNINGHUB_API_BASE}/task/openapi/create")
            response = session.post(
                f"{RUNNINGHUB_API_BASE}/task/openapi/create",
                headers=headers,
                json=payload,
                timeout=60  # 增加超时时间
            )
            
            # 打印响应状态码和响应内容以便调试
            print(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"API响应: {result}")
                
                if result.get("code") == 0 and "data" in result:
                    task_data = result["data"]
                    task_id = task_data.get("taskId")
                    task_status = task_data.get("taskStatus")
                    
                    print(f"任务创建成功，任务ID: {task_id}, 状态: {task_status}")
                    
                    # 轮询任务状态
                    max_retries = 30  # 最大重试次数
                    retry_interval = 2  # 重试间隔（秒）
                    
                    for _ in range(max_retries):
                        status = self._check_task_status(task_id)
                        print(f"当前任务状态: {status}")
                        
                        if status == "SUCCESS":
                            print("任务完成，准备获取图像")
                            # 获取任务输出
                            outputs = self._get_task_outputs(task_id)
                            if outputs and len(outputs) > 0:
                                # 获取第一个输出文件
                                output = outputs[0]
                                file_url = output.get("fileUrl")
                                file_type = output.get("fileType", "png")
                                
                                if file_url:
                                    # 准备保存路径
                                    timestamp = int(time.time())
                                    output_path = os.path.join(GENERATED_IMAGES_DIR, 
                                                             f"rh_gen_{timestamp}_{seed}.{file_type}")
                                    
                                    # 下载图像
                                    if self._download_image(file_url, output_path):
                                        print(f"图像已保存到: {output_path}")
                                        return output_path
                            
                            print("获取生成的图像失败")
                            break
                        elif status == "FAILED":
                            print("任务失败")
                            break
                        elif status == "RUNNING":
                            time.sleep(retry_interval)
                            continue
                        else:
                            print(f"未知任务状态: {status}")
                            break
                    
                    # 如果获取图像失败，返回模拟结果
                    quality_params = IMAGE_QUALITY[quality]
                    return self._mock_generate_image(prompt, style, quality_params, seed)
                else:
                    print(f"任务创建失败: {result.get('msg', '未知错误')}")
            
            print(f"RunningHub API调用失败: {response.status_code} - {response.text}")
            return self._mock_generate_image(prompt, style, IMAGE_QUALITY[quality], seed)
            
        except Exception as e:
            print(f"RunningHub API调用失败: {str(e)}")
            return self._mock_generate_image(prompt, style, IMAGE_QUALITY[quality], seed)
    
    def generate_image(self, prompt, style=None, quality="标准", 
                      negative_prompt=None, seed=None, use_mock=False, api="stability"):
        """
        生成图像的统一接口
        
        参数:
            prompt (str): 提示词
            style (str, optional): 图像风格
            quality (str): 图像质量
            negative_prompt (str, optional): 负面提示词
            seed (int, optional): 随机种子
            use_mock (bool): 是否使用模拟模式
            api (str): 使用的API服务 ("stability" 或 "runninghub")
            
        返回:
            str: 生成的图像文件路径
        """
        if api == "runninghub":
            return self.generate_image_runninghub(
                prompt, style, quality, negative_prompt, seed, use_mock
            )
        else:
            # 使用原有的Stability API方法
            return self.generate_from_text(
                prompt, style, quality, negative_prompt, seed, use_mock
            )

# 预处理提示词
def enhance_prompt(prompt, style=None, extra_details=None):
    """
    增强提示词，添加风格和细节描述
    
    参数:
        prompt (str): 基础提示词
        style (str, optional): 风格名称
        extra_details (str, optional): 额外细节描述
        
    返回:
        str: 增强后的提示词
    """
    enhanced = prompt
    
    # 添加风格描述
    if style and style in IMAGE_STYLES:
        enhanced += f"，{IMAGE_STYLES[style]['name']}"
    
    # 添加额外细节
    if extra_details:
        enhanced += f"，{extra_details}"
    
    return enhanced

# 获取可用的图像风格
def get_available_styles():
    """
    获取所有可用的图像风格
    
    返回:
        dict: 风格名称及描述
    """
    return IMAGE_STYLES

# 获取图像质量选项
def get_quality_options():
    """
    获取图像质量选项
    
    返回:
        dict: 质量选项
    """
    return IMAGE_QUALITY 
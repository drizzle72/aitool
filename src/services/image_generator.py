"""
图像生成服务模块
"""

import os
import json
import time
import random
import requests
from datetime import datetime
import urllib3
import logging
from enum import Enum
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API配置
API_KEY = os.getenv("RUNNINGHUB_API_KEY", "")
API_BASE_URL = "https://www.runninghub.cn"

class WorkflowType(Enum):
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"

def validate_api_key() -> None:
    """验证 API 密钥是否存在"""
    if not API_KEY:
        raise ValueError("未设置 API 密钥，请设置环境变量 RUNNINGHUB_API_KEY")

def validate_workflow_id(workflow_id: str) -> None:
    """验证工作流 ID"""
    if not workflow_id:
        raise ValueError("工作流 ID 不能为空")
    if not workflow_id.isdigit():
        raise ValueError("工作流 ID 必须是数字")

def validate_prompt(prompt: str) -> None:
    """验证提示词"""
    if not prompt:
        raise ValueError("提示词不能为空")
    if len(prompt.strip()) == 0:
        raise ValueError("提示词不能只包含空白字符")

def upload_image(image_path: str) -> Dict[str, str]:
    """
    上传图片到 RunningHub
    
    参数:
        image_path (str): 图片文件路径
        
    返回:
        dict: 包含上传结果的字典，格式为：
            {
                "fileName": str,  # 服务器上的文件名，格式如：api/xxx.png
                "fileType": str   # 文件类型，固定为 "image"
            }
            
    异常:
        ValueError: 当图片文件不存在或格式不支持时
        Exception: 当上传过程中发生错误时
    """
    logger.info(f"开始上传图片: {image_path}")
    
    if not os.path.exists(image_path):
        error_msg = f"图片文件不存在: {image_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 检查文件扩展名
    allowed_extensions = {'.png', '.jpg', '.jpeg'}
    file_ext = os.path.splitext(image_path)[1].lower()
    if file_ext not in allowed_extensions:
        error_msg = f"不支持的图片格式: {file_ext}，支持的格式: {', '.join(allowed_extensions)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 检查文件大小（限制为 10MB）
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    file_size = os.path.getsize(image_path)
    if file_size > max_size:
        error_msg = f"图片文件过大: {file_size / 1024 / 1024:.2f}MB，最大允许: {max_size / 1024 / 1024}MB"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # 准备上传请求
        upload_url = f"{API_BASE_URL}/task/openapi/upload"
        logger.info(f"调用上传API: {upload_url}")
        
        # 准备 multipart/form-data 表单数据
        files = {
            'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg' if file_ext in ['.jpg', '.jpeg'] else 'image/png')
        }
        data = {
            'apiKey': API_KEY,
            'fileType': 'image'
        }
        
        # 发送上传请求
        upload_response = requests.post(
            upload_url,
            files=files,
            data=data,
            verify=False,
            timeout=30
        )
        
        logger.debug(f"API响应状态码: {upload_response.status_code}")
        logger.debug(f"API响应内容: {upload_response.text}")
        
        if upload_response.status_code != 200:
            error_msg = f"上传失败 (状态码: {upload_response.status_code})"
            try:
                error_data = upload_response.json()
                error_msg += f": {error_data.get('msg', '未知错误')}"
            except:
                error_msg += f": {upload_response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            result = upload_response.json()
        except json.JSONDecodeError:
            error_msg = f"无效的 JSON 响应: {upload_response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        if result.get("code") != 0:
            error_msg = f"上传失败: {result.get('msg', '未知错误')}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        upload_result = result["data"]
        logger.info(f"图片上传成功: {upload_result['fileName']}")
        return upload_result
        
    except requests.Timeout:
        error_msg = "上传请求超时"
        logger.error(error_msg)
        raise Exception(error_msg)
    except requests.RequestException as e:
        error_msg = f"上传请求失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        logger.exception("图片上传过程中发生错误")
        raise e

def get_node_id_by_field(workflow_config: dict, field_name: str) -> Optional[str]:
    """
    从工作流配置中获取指定字段名称的节点ID
    
    参数:
        workflow_config (dict): 工作流配置信息
        field_name (str): 字段名称
        
    返回:
        Optional[str]: 节点ID，如果未找到则返回 None
    """
    try:
        node_info_list = workflow_config.get('nodeInfoList', [])
        for node_info in node_info_list:
            if node_info.get('fieldName') == field_name:
                return node_info.get('nodeId')
        return None
    except Exception as e:
        logger.warning(f"获取节点 ID 失败 (字段: {field_name}): {str(e)}")
        return None

def generate_image_runninghub(
    prompt: str,
    workflow_id: str,
    workflow_config: dict,
    workflow_type: WorkflowType = WorkflowType.TEXT_TO_IMAGE,
    reference_image_path: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    使用RunningHub API生成图像
    
    参数:
        prompt (str): 正向提示词
        workflow_id (str): 工作流ID
        workflow_config (dict): 工作流配置信息
        workflow_type (WorkflowType): 工作流类型，默认为文生图
        reference_image_path (str, optional): 参考图片路径（用于图生图）
        negative_prompt (str, optional): 反向提示词
        seed (int, optional): 随机种子
        
    返回:
        Optional[Dict[str, Any]]: 生成结果
    """
    try:
        # 验证参数
        validate_api_key()
        validate_workflow_id(workflow_id)
        validate_prompt(prompt)
        
        if workflow_type == WorkflowType.IMAGE_TO_IMAGE and not reference_image_path:
            raise ValueError("图生图模式需要提供参考图片")
        
        logger.info(f"开始生成图像 - 工作流ID: {workflow_id}")
        logger.debug(f"工作流类型: {workflow_type.value}")
        logger.debug(f"提示词: {prompt}")
        logger.debug(f"反向提示词: {negative_prompt}")
        logger.debug(f"参考图片: {reference_image_path}")
        logger.debug(f"种子: {seed}")
        
        # 确保输出目录存在
        output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"输出目录: {output_dir}")
        
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Host": "www.runninghub.cn",
            "Connection": "keep-alive",
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)"
        }
        logger.debug("API密钥是否存在: %s", bool(API_KEY))
        
        # 准备 nodeInfoList
        node_info_list = []
        
        # 如果是图生图模式，上传参考图片并添加到 nodeInfoList
        if workflow_type == WorkflowType.IMAGE_TO_IMAGE and reference_image_path:
            try:
                # 获取 LoadImage 节点 ID
                image_node_id = get_node_id_by_field(workflow_config, 'image')
                if not image_node_id:
                    raise ValueError("未找到图片节点配置")
                logger.debug(f"LoadImage 节点 ID: {image_node_id}")
                
                # 上传图片
                upload_result = upload_image(reference_image_path)
                uploaded_filename = upload_result["fileName"]
                logger.debug(f"上传的图片文件名: {uploaded_filename}")
                
                # 添加图片节点信息
                node_info_list.append({
                    "nodeId": image_node_id,  # 保持为字符串
                    "fieldName": "image",
                    "fieldValue": uploaded_filename
                })
            except Exception as e:
                logger.error(f"处理参考图片失败: {str(e)}")
                raise e
        
        # 获取提示词节点 ID
        text_node_id = get_node_id_by_field(workflow_config, 'text')
        if not text_node_id:
            logger.warning("未找到提示词节点配置，使用默认节点ID: 6")
            text_node_id = "6"
        
        # 添加提示词节点信息
        node_info_list.append({
            "nodeId": text_node_id,  # 保持为字符串
            "fieldName": "text",
            "fieldValue": prompt
        })
        
        # 获取种子节点 ID
        seed_node_id = get_node_id_by_field(workflow_config, 'seed')
        if not seed_node_id:
            logger.warning("未找到种子节点配置，使用默认节点ID: 3")
            seed_node_id = "3"
        
        # 如果有种子值，添加种子节点信息
        if seed is None:
            seed = random.randint(0, 2**32-1)
            logger.debug(f"生成的随机种子: {seed}")
        
        node_info_list.append({
            "nodeId": seed_node_id,  # 保持为字符串
            "fieldName": "seed",
            "fieldValue": seed  # 数值类型
        })
        
        # 准备请求数据
        data = {
            "workflowId": int(workflow_id),  # 转换为整数
            "apiKey": API_KEY,
            "nodeInfoList": node_info_list
        }
        
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
            
        logger.debug(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 创建会话并配置
        session = requests.Session()
        session.verify = False  # 禁用 SSL 验证
        
        # 创建任务
        create_url = f"{API_BASE_URL}/task/openapi/create"
        logger.info(f"调用创建任务API: {create_url}")
        
        create_response = session.post(
            create_url,
            headers=headers,
            json=data,
            timeout=30  # 设置30秒超时
        )
        
        logger.debug(f"API响应状态码: {create_response.status_code}")
        logger.debug(f"API响应头: {dict(create_response.headers)}")
        logger.debug(f"API响应内容: {create_response.text}")
        
        if create_response.status_code != 200:
            error_msg = f"API错误 (状态码: {create_response.status_code})"
            try:
                error_data = create_response.json()
                error_msg += f": {error_data.get('msg', '未知错误')}"
            except:
                error_msg += f": {create_response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            result = create_response.json()
        except json.JSONDecodeError:
            error_msg = f"无效的 JSON 响应: {create_response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        if result.get("code") != 0:
            error_msg = f"API错误: {result.get('msg', '未知错误')}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        task_id = result["data"]["taskId"]
        client_id = result["data"]["clientId"]
        logger.info(f"获取到任务ID: {task_id}")
        logger.info(f"获取到客户端ID: {client_id}")
        
        # 轮询任务状态
        max_retries = 60  # 增加最大重试次数
        retry_interval = 5  # 增加重试间隔
        
        for attempt in range(max_retries):
            logger.debug(f"检查任务状态 (尝试 {attempt + 1}/{max_retries})")
            
            # 检查任务状态
            status_url = f"{API_BASE_URL}/task/openapi/status"
            logger.debug(f"调用状态API: {status_url}")
            
            status_data = {
                "taskId": task_id,
                "apiKey": API_KEY,
                "clientId": client_id
            }
            
            logger.debug(f"状态请求数据: {json.dumps(status_data, ensure_ascii=False)}")
            
            try:
                status_response = session.post(
                    status_url,
                    headers=headers,
                    json=status_data,
                    timeout=30  # 设置30秒超时
                )
            except requests.Timeout:
                logger.warning("状态检查请求超时，将在下次重试")
                time.sleep(retry_interval)
                continue
            except requests.RequestException as e:
                logger.warning(f"状态检查请求失败: {str(e)}，将在下次重试")
                time.sleep(retry_interval)
                continue
            
            logger.debug(f"状态API响应状态码: {status_response.status_code}")
            logger.debug(f"状态API响应内容: {status_response.text}")
            
            if status_response.status_code != 200:
                error_msg = f"获取任务状态失败 (状态码: {status_response.status_code})"
                try:
                    error_data = status_response.json()
                    error_msg += f": {error_data.get('msg', '未知错误')}"
                except:
                    error_msg += f": {status_response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            try:
                status_result = status_response.json()
            except json.JSONDecodeError:
                error_msg = f"无效的任务状态响应: {status_response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            if status_result.get("code") != 0:
                error_msg = f"获取任务状态失败: {status_result.get('msg', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # 从data字段获取状态
            status = status_result["data"]
            logger.info(f"当前任务状态: {status}")
            
            if status == "SUCCESS":
                # 获取任务输出
                outputs_url = f"{API_BASE_URL}/task/openapi/outputs"
                logger.debug(f"调用输出API: {outputs_url}")
                
                outputs_data = {
                    "taskId": task_id,
                    "apiKey": API_KEY,
                    "clientId": client_id
                }
                
                try:
                    outputs_response = session.post(
                        outputs_url,
                        headers=headers,
                        json=outputs_data,
                        timeout=30  # 设置30秒超时
                    )
                except requests.Timeout:
                    error_msg = "获取任务输出超时"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                except requests.RequestException as e:
                    error_msg = f"获取任务输出失败: {str(e)}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                logger.debug(f"输出API响应状态码: {outputs_response.status_code}")
                logger.debug(f"输出API响应内容: {outputs_response.text}")
                
                if outputs_response.status_code != 200:
                    error_msg = f"获取任务输出失败 (状态码: {outputs_response.status_code})"
                    try:
                        error_data = outputs_response.json()
                        error_msg += f": {error_data.get('msg', '未知错误')}"
                    except:
                        error_msg += f": {outputs_response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                try:
                    outputs_result = outputs_response.json()
                except json.JSONDecodeError:
                    error_msg = f"无效的任务输出响应: {outputs_response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                if outputs_result.get("code") != 0:
                    error_msg = f"获取任务输出失败: {outputs_result.get('msg', '未知错误')}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # 下载图像
                outputs = outputs_result["data"]
                if not outputs:
                    error_msg = "任务输出为空"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                image_url = outputs[0]["fileUrl"]  # 从第一个输出项获取fileUrl
                logger.info(f"开始下载图像: {image_url}")
                
                try:
                    image_response = session.get(image_url, timeout=30)  # 设置30秒超时
                    image_response.raise_for_status()
                except requests.Timeout:
                    error_msg = "下载图像超时"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                except requests.RequestException as e:
                    error_msg = f"下载图像失败: {str(e)}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # 保存图像
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(output_dir, f"generated_{timestamp}.png")
                
                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                
                logger.info(f"图像已保存到: {image_path}")
                return {
                    "image_path": image_path,
                    "task_id": task_id,
                    "status": "SUCCESS"
                }
            elif status == "FAILED":
                error_msg = "任务执行失败"
                logger.error(error_msg)
                raise Exception(error_msg)
            elif status == "RUNNING":
                logger.debug(f"任务正在运行，等待 {retry_interval} 秒后重试")
                time.sleep(retry_interval)
            else:
                error_msg = f"未知的任务状态: {status}"
                logger.error(error_msg)
                raise Exception(error_msg)
        
        error_msg = "任务执行超时"
        logger.error(error_msg)
        raise Exception(error_msg)
        
    except Exception as e:
        logger.exception("图像生成过程中发生错误")
        print(f"图像生成失败: {str(e)}")
        return None 
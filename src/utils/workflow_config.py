"""
工作流配置模块
"""

import json
import os

class WorkflowConfig:
    def __init__(self, config_file="workflows.json"):
        self.config_file = config_file
        self.workflows = self._load_config()

    def _load_config(self):
        """加载工作流配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        return {}

    def save_config(self):
        """保存工作流配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.workflows, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def add_workflow(self, workflow_id, name, description, model="", parameters=None):
        """
        添加新的工作流配置
        
        参数:
            workflow_id (str): 工作流ID
            name (str): 工作流名称
            description (str): 工作流描述
            model (str): 使用的模型
            parameters (dict): 其他参数
        """
        self.workflows[workflow_id] = {
            "name": name,
            "description": description,
            "model": model,
            "parameters": parameters or {}
        }
        return self.save_config()

    def remove_workflow(self, workflow_id):
        """删除工作流配置"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return self.save_config()
        return False

    def get_workflow(self, workflow_id):
        """获取工作流配置"""
        return self.workflows.get(workflow_id)

    def get_all_workflows(self):
        """获取所有工作流配置"""
        return self.workflows

    def clear_workflows(self):
        """清空所有工作流配置"""
        self.workflows = {}
        return self.save_config() 
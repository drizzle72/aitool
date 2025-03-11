"""
工作流管理组件模块
"""

import streamlit as st
from src.utils.workflow_config import WorkflowConfig

def clear_form():
    """清空表单数据"""
    if "form_submitted" in st.session_state:
        del st.session_state.form_submitted
        st.session_state.workflow_id = ""
        st.session_state.workflow_name = ""
        st.session_state.workflow_description = ""
        st.session_state.workflow_model = ""
        st.session_state.workflow_parameters = ""

def render_workflow_manager():
    """渲染工作流管理界面"""
    st.markdown("## 工作流管理")
    
    # 初始化工作流配置
    workflow_config = WorkflowConfig()
    
    # 创建两列布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 添加新工作流")
        
        # 初始化表单状态
        if "form_submitted" not in st.session_state:
            st.session_state.form_submitted = False
        
        # 输入表单
        with st.form("add_workflow_form"):
            workflow_id = st.text_input(
                "工作流ID",
                key="workflow_id",
                value="" if st.session_state.get("form_submitted", False) else st.session_state.get("workflow_id", "")
            )
            name = st.text_input(
                "工作流名称",
                key="workflow_name",
                value="" if st.session_state.get("form_submitted", False) else st.session_state.get("workflow_name", "")
            )
            description = st.text_area(
                "工作流描述",
                key="workflow_description",
                value="" if st.session_state.get("form_submitted", False) else st.session_state.get("workflow_description", "")
            )
            model = st.text_input(
                "使用的模型（可选）",
                key="workflow_model",
                value="" if st.session_state.get("form_submitted", False) else st.session_state.get("workflow_model", "")
            )
            
            # 可选参数（以JSON格式输入）
            parameters = st.text_area(
                "其他参数（JSON格式，可选）",
                key="workflow_parameters",
                value="" if st.session_state.get("form_submitted", False) else st.session_state.get("workflow_parameters", ""),
                help="例如: {\"param1\": \"value1\", \"param2\": \"value2\"}"
            )
            
            submitted = st.form_submit_button("添加工作流")
            
            if submitted:
                try:
                    # 解析参数
                    params = {}
                    if parameters:
                        try:
                            params = eval(parameters)
                        except:
                            st.error("参数格式错误，请使用正确的JSON格式")
                            return
                    
                    # 添加工作流
                    if workflow_config.add_workflow(workflow_id, name, description, model, params):
                        st.success("工作流添加成功！")
                        # 标记表单已提交
                        st.session_state.form_submitted = True
                        # 使用 rerun 来清空表单
                        st.rerun()
                    else:
                        st.error("工作流添加失败")
                except Exception as e:
                    st.error(f"发生错误: {str(e)}")
    
    with col2:
        st.markdown("### 现有工作流")
        
        # 获取所有工作流
        workflows = workflow_config.get_all_workflows()
        
        if workflows:
            # 选择要删除的工作流
            workflow_to_delete = st.selectbox(
                "选择要删除的工作流",
                options=list(workflows.keys()),
                format_func=lambda x: f"{workflows[x]['name']} ({x})"
            )
            
            # 显示选中工作流的详细信息
            if workflow_to_delete:
                workflow = workflows[workflow_to_delete]
                st.markdown("#### 工作流详情")
                st.write(f"**ID:** {workflow_to_delete}")
                st.write(f"**名称:** {workflow['name']}")
                st.write(f"**描述:** {workflow['description']}")
                if workflow['model']:
                    st.write(f"**模型:** {workflow['model']}")
                if workflow['parameters']:
                    st.write("**参数:**")
                    st.json(workflow['parameters'])
                
                # 删除按钮
                if st.button(f"删除 {workflow['name']}"):
                    if workflow_config.remove_workflow(workflow_to_delete):
                        st.success("工作流删除成功！")
                        st.rerun()
                    else:
                        st.error("工作流删除失败")
        else:
            st.info("暂无工作流配置")
        
        # 清空所有工作流的按钮
        if workflows and st.button("清空所有工作流", type="secondary"):
            if workflow_config.clear_workflows():
                st.success("所有工作流已清空！")
                st.rerun()
            else:
                st.error("清空工作流失败")

def get_workflow_selector(default_id=None):
    """
    获取工作流选择器组件
    
    参数:
        default_id (str, optional): 默认选中的工作流ID
        
    返回:
        tuple: (selected_workflow_id, workflow_info)
    """
    workflow_config = WorkflowConfig()
    workflows = workflow_config.get_all_workflows()
    
    if not workflows:
        st.warning("未找到任何工作流配置，请先添加工作流")
        return None, None
    
    # 创建工作流选择器
    selected_id = st.selectbox(
        "选择工作流",
        options=list(workflows.keys()),
        index=list(workflows.keys()).index(default_id) if default_id in workflows else 0,
        format_func=lambda x: f"{workflows[x]['name']} - {workflows[x]['description'][:50]}..."
    )
    
    return selected_id, workflows.get(selected_id) 
"""
图像生成组件模块
"""

import streamlit as st
from src.components.workflow_manager import get_workflow_selector
from src.services.image_generator import generate_image_runninghub

def render_image_generation():
    """渲染图像生成界面"""
    st.markdown("## 图像生成")
    
    # 获取工作流选择器
    workflow_id, workflow_info = get_workflow_selector()
    
    if not workflow_id:
        return
        
    # 创建两列布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 提示词输入
        prompt = st.text_area(
            "正向提示词",
            height=120,
            help="描述你想要生成的图像内容"
        )
        
        negative_prompt = st.text_area(
            "反向提示词（可选）",
            height=80,
            help="描述你不想在生成的图像中出现的内容"
        )
        
        # 高级选项
        with st.expander("高级选项"):
            seed = st.number_input(
                "随机种子",
                min_value=-1,
                max_value=2**32-1,
                value=-1,
                help="设置-1为随机种子"
            )
    
    with col2:
        # 显示工作流信息
        st.markdown("### 当前工作流")
        st.write(f"**名称:** {workflow_info['name']}")
        st.write(f"**描述:** {workflow_info['description']}")
        if workflow_info.get('model'):
            st.write(f"**模型:** {workflow_info['model']}")
        if workflow_info.get('parameters'):
            st.write("**参数:**")
            st.json(workflow_info['parameters'])
        
        # 生成按钮
        if st.button("生成图像", type="primary", disabled=not prompt):
            if not prompt:
                st.error("请输入正向提示词")
                return
                
            try:
                with st.spinner("正在生成图像..."):
                    # 调用图像生成服务
                    result = generate_image_runninghub(
                        prompt=prompt,
                        negative_prompt=negative_prompt if negative_prompt else None,
                        seed=seed if seed >= 0 else None,
                        workflow_id=workflow_id
                    )
                    
                    if result and result.get("image_path"):
                        st.success("图像生成成功！")
                        st.image(result["image_path"], caption="生成的图像")
                    else:
                        st.error("图像生成失败")
            except Exception as e:
                st.error(f"生成过程中发生错误: {str(e)}") 
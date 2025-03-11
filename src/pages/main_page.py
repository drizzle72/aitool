"""
主页面模块
"""

import streamlit as st
from src.styles.theme import get_theme_css, THEMES, FONTS
from src.components.image_analysis import render_image_analysis
from src.components.image_generation import render_image_generation
from src.components.workflow_manager import render_workflow_manager

def render_theme_settings():
    """渲染主题设置部分"""
    with st.expander("🎨 应用主题设置", expanded=False):
        st.write("### 主题设置")
        theme_cols = st.columns(len(THEMES))
        
        # 初始化会话状态
        if "theme" not in st.session_state:
            st.session_state.theme = "默认蓝"
        
        if "font" not in st.session_state:
            st.session_state.font = "默认字体"
        
        # 显示主题选项
        for i, (theme_name, theme_config) in enumerate(THEMES.items()):
            with theme_cols[i]:
                # 创建主题样式预览
                st.markdown(
                    f"""
                    <div style="background-color: {theme_config['background_color']}; 
                                padding: 10px; 
                                border-radius: 5px;
                                border: 2px solid {theme_config['primary_color'] if theme_name == st.session_state.theme else 'transparent'};
                                text-align: center;
                                cursor: pointer;">
                        <h4 style="color: {theme_config['primary_color']}; margin: 5px 0;">{theme_name}</h4>
                        <div style="background-color: {theme_config['primary_color']}; height: 15px; margin: 5px 0;"></div>
                        <p style="color: {theme_config['text_color']}; margin: 5px 0;">示例文本</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                # 使用按钮选择主题
                if st.button(f"选择 {theme_name}", key=f"theme_{theme_name}"):
                    st.session_state.theme = theme_name
                    st.experimental_rerun()
        
        # 字体选择
        st.write("### 字体设置")
        selected_font = st.selectbox(
            "选择字体风格",
            options=list(FONTS.keys()),
            index=list(FONTS.keys()).index(st.session_state.get("font", "默认字体")),
            key="font_selector"
        )
        
        # 如果字体被改变
        if selected_font != st.session_state.get("font"):
            st.session_state.font = selected_font
            st.experimental_rerun()

def render_contact_section():
    """渲染联系方式部分"""
    if st.session_state.get("show_contact", False):
        with st.container():
            st.markdown("### 📞 联系作者")
            st.markdown("""
            如果您有任何问题、建议或合作意向，欢迎通过以下方式联系我：
            
            - 📧 邮箱：example@email.com
            - 💬 微信：your_wechat_id
            - 📱 电话：123-4567-8900
            """)
            
            if st.button("关闭", key="close_contact"):
                st.session_state.show_contact = False
                st.experimental_rerun()

def render_main_page():
    """渲染主页面"""
    st.set_page_config(
        page_title="通义千问视觉智能助手",
        page_icon="🎨",
        layout="wide"
    )
    
    st.title("通义千问视觉智能助手")
    
    # 创建选项卡
    tab_analysis, tab_generation, tab_workflow = st.tabs([
        "📸 图像分析",
        "🎨 图像生成",
        "⚙️ 工作流管理"
    ])
    
    # 图像分析选项卡
    with tab_analysis:
        render_image_analysis()
    
    # 图像生成选项卡
    with tab_generation:
        render_image_generation()
    
    # 工作流管理选项卡
    with tab_workflow:
        render_workflow_manager()
    
    # 应用主题样式
    st.markdown(
        get_theme_css(
            st.session_state.get("theme", "默认蓝"),
            st.session_state.get("font", "默认字体")
        ),
        unsafe_allow_html=True
    )
    
    # 在标题下方添加一个小型联系入口
    with st.container():
        cols = st.columns([5, 1])
        with cols[1]:
            if st.button("📞 联系作者", key="contact_button"):
                st.session_state["show_contact"] = True
    
    # 渲染主题设置
    render_theme_settings()
    
    # 渲染联系方式部分
    render_contact_section() 
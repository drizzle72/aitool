"""
主题样式配置模块
"""

# 主题配置
THEMES = {
    "默认蓝": {
        "primary_color": "#1E88E5",
        "background_color": "#FFFFFF",
        "text_color": "#333333",
        "secondary_color": "#64B5F6"
    },
    "暗夜黑": {
        "primary_color": "#BB86FC",
        "background_color": "#121212",
        "text_color": "#E1E1E1",
        "secondary_color": "#03DAC6"
    },
    "森林绿": {
        "primary_color": "#2E7D32",
        "background_color": "#F1F8E9",
        "text_color": "#1B5E20",
        "secondary_color": "#81C784"
    }
}

# 字体配置
FONTS = {
    "默认字体": "'Helvetica Neue', Helvetica, sans-serif",
    "优雅宋体": "'Noto Serif SC', serif",
    "现代黑体": "'Noto Sans SC', sans-serif"
}

def get_theme_css(theme_name="默认蓝", font_name="默认字体"):
    """
    生成主题CSS样式
    
    参数:
        theme_name (str): 主题名称
        font_name (str): 字体名称
        
    返回:
        str: CSS样式代码
    """
    theme = THEMES.get(theme_name, THEMES["默认蓝"])
    font = FONTS.get(font_name, FONTS["默认字体"])
    
    return f"""
        <style>
            /* 全局样式 */
            .stApp {{
                font-family: {font};
                color: {theme['text_color']};
                background-color: {theme['background_color']};
            }}
            
            /* 标题样式 */
            .main-title {{
                color: {theme['primary_color']};
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 0.5em;
            }}
            
            .subtitle {{
                color: {theme['secondary_color']};
                font-size: 1.2em;
                margin-bottom: 2em;
            }}
            
            /* 按钮样式 */
            .stButton>button {{
                background-color: {theme['primary_color']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0.5em 1em;
                transition: all 0.3s ease;
            }}
            
            .stButton>button:hover {{
                background-color: {theme['secondary_color']};
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            /* 输入框样式 */
            .stTextInput>div>div>input {{
                border-color: {theme['primary_color']};
            }}
            
            /* 选择框样式 */
            .stSelectbox>div>div>select {{
                border-color: {theme['primary_color']};
            }}
            
            /* 链接样式 */
            a {{
                color: {theme['primary_color']};
                text-decoration: none;
            }}
            
            a:hover {{
                color: {theme['secondary_color']};
                text-decoration: underline;
            }}
        </style>
    """ 
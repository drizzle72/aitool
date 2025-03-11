"""
文件处理工具模块
"""

import os
import json

def save_text_as_file(text, filename):
    """保存文本为文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

def create_download_button(st, text, filename, button_text):
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
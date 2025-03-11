@echo off
echo 正在启动 AI 图像生成器...

:: 检查并创建虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: 检查并创建输出目录
if not exist "outputs" mkdir outputs

:: 设置环境变量
set RUNNINGHUB_API_KEY=a2b6d581ad3c4544bbef2e593d47bbd4

:: 启动应用
echo 启动 Streamlit 应用...
streamlit run app.py

pause 
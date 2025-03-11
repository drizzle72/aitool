# AI 图像生成器

基于 Streamlit 和 RunningHub API 开发的 AI 图像生成应用。

## 功能特点

1. **文本生成图像**
   - Flux文生图：支持通过文本描述生成高质量图像
   - 人物一致性6宫格小红书风格：生成多格图片，适合社交媒体分享

2. **图像转换**
   - 梦幻油画风格：将上传的图片转换为油画风格

3. **智能提示**
   - 内置优质提示词库
   - 支持自定义提示词
   - 支持设置随机种子

## 快速开始

1. 克隆仓库：
```bash
git clone [仓库地址]
cd ai-image-generator
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
创建 `.env` 文件并添加：
```
RUNNINGHUB_API_KEY=your_api_key_here
```

4. 运行应用：
```bash
# Windows
run.bat

# Linux/Mac
streamlit run app.py
```

## 技术栈

- Python 3.8+
- Streamlit
- RunningHub API
- PIL (Python Imaging Library)

## 开发说明

- 代码遵循 PEP 8 规范
- 使用 Git Flow 工作流
- 提交信息使用中文，清晰描述改动

## 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/xxx`
3. 提交改动：`git commit -m '添加xxx功能'`
4. 推送分支：`git push origin feature/xxx`
5. 提交 Pull Request

## 许可证

MIT License

## 使用说明

1. 启动应用：
```bash
streamlit run app.py
```

2. 在浏览器中访问应用（默认地址：http://localhost:8503）

3. 选择需要使用的功能：
   - 文生图：输入文本描述生成图像
   - 图生图：上传参考图片进行风格转换
   - 可选择添加反向提示词和设置随机种子

## 注意事项

1. 确保已安装所有依赖包
2. 需要有效的 RunningHub API 密钥
3. 图片生成可能需要一定时间，请耐心等待
4. 生成的图片将保存在 outputs 目录下

## 更新日志

### v1.0.0 (2025-03-12)
- 初始版本发布
- 支持文生图和图生图功能
- 添加默认提示词功能
- 优化用户界面和交互体验
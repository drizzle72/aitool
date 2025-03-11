# AI 图像生成器部署指南

## 系统要求

- Python 3.8 或更高版本
- pip 包管理器
- Git（可选，用于版本控制）
- 至少 4GB 可用内存
- 稳定的网络连接

## 部署步骤

### 1. 准备环境

```bash
# 创建并进入项目目录
mkdir ai-image-generator
cd ai-image-generator

# 克隆代码（如果使用 Git）
git clone [项目地址]

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装所需包
pip install -r requirements.txt
```

### 3. 配置环境变量

1. 在项目根目录创建 `.env` 文件
2. 添加以下配置：
```
RUNNINGHUB_API_KEY=your_api_key_here
```

### 4. 创建必要的目录

```bash
# 创建输出目录
mkdir outputs
```

### 5. 启动应用

```bash
# 开发环境
streamlit run app.py

# 生产环境（使用 nohup 或 screen）
nohup streamlit run app.py &
```

### 6. 访问应用

- 本地访问：http://localhost:8503
- 远程访问：http://[服务器IP]:8503

## 生产环境配置建议

### 使用 Screen 或 tmux（Linux 环境）

```bash
# 使用 screen
screen -S ai-image-generator
streamlit run app.py
# 按 Ctrl+A+D 分离会话
```

### 配置防火墙

确保服务器防火墙允许 8503 端口访问：

```bash
# Ubuntu/Debian
sudo ufw allow 8503

# CentOS
sudo firewall-cmd --permanent --add-port=8503/tcp
sudo firewall-cmd --reload
```

## 监控和日志

- 日志文件位置：`./outputs/app.log`
- 监控应用状态：`ps aux | grep streamlit`

## 常见问题解决

1. 如果遇到权限问题：
```bash
chmod -R 755 ./
```

2. 如果端口被占用：
```bash
# 查找占用端口的进程
netstat -tulpn | grep 8503
# 终止进程
kill -9 [进程ID]
```

3. 如果遇到内存不足：
- 检查系统资源使用情况
- 考虑增加服务器内存
- 优化应用程序配置

## 安全建议

1. 使用 HTTPS
2. 定期更新依赖包
3. 不要在代码中硬编码敏感信息
4. 定期备份数据
5. 监控系统资源使用情况

## 备份策略

1. 定期备份配置文件
2. 备份生成的图像
3. 使用版本控制管理代码

## 更新维护

1. 定期检查依赖更新
2. 监控应用日志
3. 定期清理临时文件和缓存

## 联系支持

如遇到问题，请联系技术支持：
- 邮件：[支持邮箱]
- 问题追踪：[问题追踪系统地址] 
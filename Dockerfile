FROM python:3.11-slim

# 强制系统支持中文 UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# 复制文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 Streamlit 端口
EXPOSE 8501

# 启动命令
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
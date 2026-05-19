# 镜像仓库地址在 build/tag 阶段指定，例如：
# docker build -t registry.example.com/team/jomoo-api:latest .
FROM python:3.8-slim-buster

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Use TUNA mirrors for apt, then install runtime libs for OpenCV/torch
RUN sed -i 's#http://deb.debian.org#https://mirrors.tuna.tsinghua.edu.cn/#g' /etc/apt/sources.list \
    && apt-get --allow-releaseinfo-change update \
    && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r /app/requirements.txt --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && rm -rf /tmp/* /root/.cache/*

COPY . /app/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]

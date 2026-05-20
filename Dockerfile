# 镜像仓库地址在 build/tag 阶段指定，例如：
# docker build -t registry.example.com/team/jomoo-api:latest .
FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r /app/requirements.txt --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && rm -rf /tmp/* /root/.cache/*

COPY . /app/

EXPOSE 9234

CMD ["python", "-m", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "9234"]
# Jomoo 商品检测服务

这是一个基于 FastAPI + Ultralytics YOLO + ONNX 模型的商品检测接口服务。

服务启动后，可以通过浏览器访问接口文档：

```text
http://127.0.0.1:9234/docs
```

## 目录结构

```text
jomoo-detect/
├── Dockerfile
├── README.md
├── api_server.py
├── requirements.txt
└── base/
    ├── __init__.py
    └── model.onnx
```

## 模型准备

请确认模型文件已经放在下面的位置：

```text
base/model.onnx
```

如果这个文件不存在，服务启动时会报模型文件不存在。

## 方式一：本机启动（推荐先验证）

本方式不要求客户安装 conda。建议使用独立 Python 3.10 创建虚拟环境。

### 1. 安装 Python 3.10

建议安装 Windows 64 位 Python 3.10，并安装到固定目录，例如：

```text
D:\Python310\install
```

安装完成后确认 Python 可用：

```powershell
D:\Python310\install\python.exe --version
```

如果能看到 `Python 3.10.x`，说明安装正常。

### 2. 创建虚拟环境并安装依赖

在 PowerShell 中进入项目目录：

```powershell
cd E:\demo\jomoo\code\jomoo-detect
```

创建并进入虚拟环境：

```powershell
D:\Python310\install\python.exe -m venv .venv
.\.venv\Scripts\activate
```

进入成功后，命令行前面会出现 `(.venv)`。

升级 pip，并通过清华镜像逐个安装依赖。逐个安装的好处是：如果某一步卡住，可以直接知道是哪个包的问题。

```powershell
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --default-timeout 60
python -m pip install torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install onnx -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install fastapi uvicorn python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

如果启动时看到类似下面的提示：

```text
requirements: Ultralytics requirement ['onnx'] not found, attempting AutoUpdate...
```

一般表示 `onnx` 没装好，或者当前环境和 `ultralytics` 的依赖没有对齐。上面的流程已经单独安装了 `onnx`，正常按步骤安装后通常不会再出现这个提示。若仍然出现，请先执行：

```powershell
python -m pip install onnx -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

然后重新启动服务。

验证 `torch` 是否能正常导入：

```powershell
python -c "import torch; print(torch.__version__)"
```

### 3. 启动服务

```powershell
python api_server.py
```

启动成功后访问：

```text
http://127.0.0.1:9234/docs
```

也可以访问 ReDoc 文档：

```text
http://127.0.0.1:9234/redoc
```

## 方式二：Docker 启动

Docker 方式适合客户部署时使用，可以减少本机 Python 环境差异。

### 1. 安装并启动 Docker Desktop

从 Docker 官方网站安装 Docker Desktop for Windows：

```text
https://docs.docker.com/desktop/setup/install/windows-install/
```

安装完成后建议重启电脑。

重启后打开 Docker Desktop，等待左下角显示 `Engine running`。

在 PowerShell 中验证 Docker 是否正常：

```powershell
docker --version
docker info
```

如果 `docker info` 能看到 `Server` 信息，说明 Docker 引擎已经启动。

### 2. 构建镜像

国内访问 Docker Hub 可能很慢或超时，因此本项目支持传入国内镜像地址作为基础镜像来源。

推荐使用下面这条命令构建：

```powershell
cd E:\demo\jomoo\code\jomoo-detect
docker build --build-arg PYTHON_BASE_IMAGE=docker.1ms.run/library/python:3.10-slim-bookworm -t jomoo-api .
```

说明：

- `docker.1ms.run/library/python:3.10-slim-bookworm` 用于替代 Docker Hub 上的 `python:3.10-slim-bookworm`。
- Dockerfile 里已经把 Debian 的 `apt` 源切换为清华镜像。
- `.dockerignore` 已经排除了 `.venv`、`.git` 等目录，避免 Docker 构建时把本地虚拟环境一起打包进去。

### 3. 运行容器

如果本机没有其他程序占用 `9234` 端口：

```powershell
docker run --rm -p 9234:9234 jomoo-api
```

然后访问：

```text
http://127.0.0.1:9234/docs
```

如果 `9234` 端口已经被本机服务占用，可以改用 `9235`：

```powershell
docker run --rm -p 9235:9234 jomoo-api
```

然后访问：

```text
http://127.0.0.1:9235/docs
```

## 接口测试

打开 Swagger 文档：

```text
http://127.0.0.1:9234/docs
```

找到接口：

```text
POST /api/v1/detect/categories
```

测试步骤：

1. 点击 `Try it out`
2. 上传一张或多张图片
3. 点击 `Execute`
4. 查看返回的 `code`、`msg`、`data`

请求字段：

```text
images: multipart/form-data，多张图片文件
```

Python 调用示例：

```python
import requests

files = [
    ("images", open("img1.jpg", "rb")),
    ("images", open("img2.jpg", "rb")),
]

response = requests.post(
    "http://127.0.0.1:9234/api/v1/detect/categories",
    files=files,
)

print(response.json())
```

响应示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "filename": "img1.jpg",
      "categories": {
        "类别A": 3,
        "类别B": 1
      }
    }
  ]
}
```

## 常见问题

### 1. pip install 很慢或长时间没反应

请确认命令里带了清华镜像参数：

```powershell
-i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

不要只执行：

```powershell
python -m pip install --upgrade pip
```

建议执行：

```powershell
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --default-timeout 60
```

### 2. 启动时报 WinError 1114 或 c10.dll 错误

典型错误：

```text
OSError: [WinError 1114] 动态链接库(DLL)初始化例程失败。
Error loading "...torch\lib\c10.dll" or one of its dependencies.
```

先安装最新版 Microsoft Visual C++ Redistributable (x64)：

```text
https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist
```

下载时请选择 `X64` 版本。

如果安装后仍然报错，通常是当前 Python 环境里的 `torch` 或 DLL 依赖冲突。建议不要继续使用 conda 的 `base` 环境，改用独立 Python 3.10 创建 `.venv`。

### 3. Docker info 报 dockerDesktopLinuxEngine 找不到

典型错误：

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

处理方式：

1. 打开 Docker Desktop
2. 等待左下角显示 `Engine running`
3. 再执行 `docker info`

如果 Docker Desktop 没有启动，只有 `docker --version` 成功是不够的。

### 4. Docker build 拉不到 python:3.10-slim-bookworm

典型错误：

```text
failed to resolve source metadata for docker.io/library/python:3.10-slim-bookworm
```

这是 Docker Hub 访问失败。请使用国内基础镜像构建：

```powershell
docker build --build-arg PYTHON_BASE_IMAGE=docker.1ms.run/library/python:3.10-slim-bookworm -t jomoo-api .
```

### 5. Docker build 显示 transferring context 很大

如果看到类似：

```text
transferring context: 1.71GB
```

说明 Docker 正在把本地大目录传进构建环境。项目已经提供 `.dockerignore`，会排除 `.venv`、`.git` 等目录。

如果仍然很大，请检查项目目录里是否放了额外的大文件。

### 6. Docker build 卡在 apt-get update

容器里需要安装系统依赖：

```text
libgl1
libglib2.0-0
libgomp1
```

如果卡在 `apt-get update`，一般是 Debian 官方源访问慢。本项目 Dockerfile 已经切换到清华 Debian 镜像。

如果修改过 Dockerfile，请确认仍然保留了这段镜像源配置。

## 错误码

- `1001`：未上传图片
- `1002`：文件格式不支持
- `1003`：图片超过大小限制
- `1004`：服务端内部异常

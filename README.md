# 九牧商品检测服务

## 目录结构

```text
jomoo-testmodel/
├── Dockerfile
├── README.md
├── api_server.py
├── base/
│   ├── __init__.py
│   └── model.onnx
├── requirements.txt
```

## 模型准备

将训练导出的 ONNX 模型放到 `base/model.onnx`。

## 启动服务

```powershell
python api_server.py
```

## Docker 部署

构建镜像：

```powershell
docker build -t registry.example.com/team/jomoo-api:latest .
```

本地运行：

```powershell
docker run --rm -p 9234:9234 registry.example.com/team/jomoo-api:latest
```

推送镜像：

```powershell
docker push registry.example.com/team/jomoo-api:latest
```

## 接口

`POST /api/v1/detect/categories`

- 请求：`multipart/form-data`，字段名 `images`，支持多张图片
- 响应：`code`、`msg`、`data`

Python 多图片调用示例（multipart/form-data）：

```python
import requests

files = [
    ('images', open('img1.jpg', 'rb')),
    ('images', open('img2.jpg', 'rb')),
]
response = requests.post(
    "http://127.0.0.1:9234/api/v1/detect/categories",
    files=files
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
        "九牧安全快开": 3,
        "九牧防臭地漏": 1
      }
    },
    {
      "filename": "img2.jpg",
      "categories": {
        "九牧安全快开": 2,
        "九牧防臭地漏": 0
      }
    }
  ]
}
```

错误码：

- `1001`：未上传图片
- `1002`：文件格式不支持
- `1003`：图片超限
- `1004`：服务端内部异常

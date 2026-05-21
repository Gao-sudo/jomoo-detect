from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from typing import List

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from ultralytics import YOLO

# ====================== 配置 ======================
MODEL_PATH = Path("base") / "model.onnx"
MODEL_NAME = "yolov9c-onnx"
DEFAULT_DEVICE = "0"
DEFAULT_IMGSZ = 1280
DEFAULT_CONF = 0.25
DEFAULT_IOU = 0.7
DEFAULT_MAX_DET = 300
DEFAULT_MAX_IMAGE_MB = 0
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

class Settings:
    def __init__(self) -> None:
        self.device = os.environ.get("JOMOO_DEVICE", DEFAULT_DEVICE)
        self.imgsz = int(os.environ.get("JOMOO_IMGSZ", str(DEFAULT_IMGSZ)))
        self.conf = float(os.environ.get("JOMOO_CONF", str(DEFAULT_CONF)))
        self.iou = float(os.environ.get("JOMOO_IOU", str(DEFAULT_IOU)))
        self.max_det = int(os.environ.get("JOMOO_MAX_DET", str(DEFAULT_MAX_DET)))
        max_mb = float(os.environ.get("JOMOO_MAX_IMAGE_MB", str(DEFAULT_MAX_IMAGE_MB)))
        self.max_image_bytes = int(max(0.0, max_mb) * 1024 * 1024)

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

@lru_cache(maxsize=1)
def get_model_bundle() -> tuple[YOLO, Path, str]:
    weights_path = MODEL_PATH
    if not weights_path.exists():
        raise FileNotFoundError(f"权重不存在: {weights_path}")
    model = YOLO(str(weights_path))
    return model, weights_path, MODEL_NAME

app = FastAPI(title="Jomoo Detection API", version="1.0.0")

@app.exception_handler(Exception)
async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"code": 1004, "msg": "Server internal error", "data": None},
    )

def _decode_image(payload: bytes) -> np.ndarray | None:
    if not payload: return None
    array = np.frombuffer(payload, dtype=np.uint8)
    if array.size == 0: return None
    return cv2.imdecode(array, cv2.IMREAD_COLOR)

def _is_allowed_file(upload: UploadFile) -> bool:
    suffix = Path(upload.filename or "").suffix.lower()
    return suffix in SUPPORTED_IMAGE_EXTS

def _build_category_counter(result) -> dict[str, int]:
    boxes = result.boxes
    if not boxes or len(boxes) == 0: return {}
    clss = boxes.cls.cpu().tolist() if boxes.cls is not None else []
    counter = {}
    for cls_idx in clss:
        name = result.names.get(int(cls_idx), str(int(cls_idx)))
        counter[name] = counter.get(name, 0) + 1
    return counter

# ==================================================================================
# ✅✅✅ 【终极正确写法】Swagger 100% 显示文件选择框，支持一次多选多张 ✅✅✅
# ==================================================================================
@app.post("/api/v1/detect/categories")
async def detect_categories(
    images: List[UploadFile] = File(..., description="上传图片文件，支持多张", media_type="image/*")
) -> Any:
    settings = get_settings()

    if not images:
        return JSONResponse(status_code=400, content={"code":1001,"msg":"No image uploaded","data":None})
    if any(not _is_allowed_file(f) for f in images):
        return JSONResponse(status_code=400, content={"code":1002,"msg":"Invalid file format","data":None})

    model, _, _ = get_model_bundle()
    data = []
    for f in images:
        payload = await f.read()
        if settings.max_image_bytes and len(payload) > settings.max_image_bytes:
            return JSONResponse(status_code=413, content={"code":1003,"msg":"Image size exceeds limit","data":None})
        img = _decode_image(payload)
        if img is None:
            return JSONResponse(status_code=400, content={"code":1002,"msg":"Invalid file format","data":None})
        results = model.predict(
            source=img,
            imgsz=settings.imgsz,
            conf=settings.conf,
            iou=settings.iou,
            device=settings.device,
            max_det=settings.max_det,
            verbose=False,
        )
        result = results[0] if results else None
        data.append(
            {
                "filename": f.filename or "unknown",
                "categories": _build_category_counter(result) if result is not None else {},
            }
        )

    return {"code":200, "msg":"success", "data":data}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    path_item = openapi_schema.get("paths", {}).get("/api/v1/detect/categories", {}).get("post")
    if path_item and "requestBody" in path_item:
        content = path_item["requestBody"].setdefault("content", {})
        content.setdefault("multipart/form-data", {})
        content["multipart/form-data"]["schema"] = {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string", "format": "binary"},
                }
            },
            "required": ["images"],
        }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9234)
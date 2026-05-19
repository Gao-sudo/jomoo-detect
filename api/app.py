from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from ultralytics import YOLO


FORCED_WEIGHTS_PATH = Path(r"E:\code\jomoo-testmodel\outputs\yolov9c\20260428_105825\weights\best.pt")
FORCED_MODEL_NAME = "yolov9c"
DEFAULT_DEVICE = "0"
DEFAULT_IMGSZ = 640
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
    weights_path = FORCED_WEIGHTS_PATH
    model_name = FORCED_MODEL_NAME
    if not weights_path.exists():
        raise FileNotFoundError(f"权重不存在: {weights_path}")
    model = YOLO(str(weights_path))
    return model, weights_path, model_name


app = FastAPI(title="Jomoo Detection API", version="1.0.0")


@app.exception_handler(Exception)
async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"code": 1004, "msg": "Server internal error", "data": None},
    )

def _decode_image(payload: bytes) -> np.ndarray | None:
    if not payload:
        return None
    array = np.frombuffer(payload, dtype=np.uint8)
    if array.size == 0:
        return None
    return cv2.imdecode(array, cv2.IMREAD_COLOR)

def _is_allowed_file(upload: UploadFile) -> bool:
    suffix = Path(upload.filename or "").suffix.lower()
    return suffix in SUPPORTED_IMAGE_EXTS

def _build_category_counter(result) -> dict[str, int]:
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return {}
    clss = boxes.cls.cpu().tolist() if boxes.cls is not None else []
    counter: dict[str, int] = {}
    for cls_idx in clss:
        name = result.names.get(int(cls_idx), str(int(cls_idx))) if isinstance(result.names, dict) else str(int(cls_idx))
        counter[name] = counter.get(name, 0) + 1
    return counter

@app.post("/api/v1/detect/categories")
@app.post("/api/detect/categories")
async def detect_categories(images: list[UploadFile] = File(...)) -> Any:
    settings = get_settings()
    if not images:
        return JSONResponse(
            status_code=400,
            content={"code": 1001, "msg": "No image uploaded", "data": None},
        )

    if any(not _is_allowed_file(upload) for upload in images):
        return JSONResponse(
            status_code=400,
            content={"code": 1002, "msg": "Invalid file format", "data": None},
        )

    decoded_images: list[np.ndarray] = []
    filenames: list[str] = []

    for upload in images:
        payload = await upload.read()
        if settings.max_image_bytes and len(payload) > settings.max_image_bytes:
            return JSONResponse(
                status_code=413,
                content={"code": 1003, "msg": "Image size exceeds limit", "data": None},
            )
        image = _decode_image(payload)
        if image is None:
            return JSONResponse(
                status_code=400,
                content={"code": 1002, "msg": "Invalid file format", "data": None},
            )
        decoded_images.append(image)
        filenames.append(upload.filename or "unknown")

    if not decoded_images:
        return JSONResponse(
            status_code=400,
            content={"code": 1001, "msg": "No image uploaded", "data": None},
        )

    model, _weights_path, _model_name = get_model_bundle()

    results = model.predict(
        source=decoded_images,
        imgsz=settings.imgsz,
        conf=settings.conf,
        iou=settings.iou,
        device=settings.device,
        max_det=settings.max_det,
        verbose=False,
    )

    payload_results: list[dict[str, Any]] = []
    for filename, result in zip(filenames, results, strict=False):
        counter = _build_category_counter(result)
        payload_results.append(
            {
                "filename": filename,
                "categories": counter,
            }
        )

    return {
        "code": 200,
        "msg": "success",
        "data": payload_results,
    }

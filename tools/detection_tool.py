from ultralytics import YOLO

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")
        _model.to("cuda")
    return _model


def detect_objects(image_path: str) -> str:
    try:
        model = _get_model()
        results = model(image_path)[0]
        if results.boxes is None or len(results.boxes) == 0:
            return "No objects detected."
        detections = []
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < 0.5:
                continue
            cls_id = int(box.cls[0])
            name = model.names.get(cls_id, str(cls_id))
            detections.append(f"{name}({conf:.2f})")
        if not detections:
            return "No objects above confidence threshold."
        return "检测到: " + ', '.join(detections)
    except Exception as e:
        return f"Detection failed: {e}"

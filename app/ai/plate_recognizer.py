import os

# Real loyihada: YOLOv8 + EasyOCR
# Hozircha MVP uchun mock modul


class PlateRecognizer:
    def __init__(self):
        self.model_loaded = False
        self._try_load_model()

    def _try_load_model(self):
        try:
            import easyocr
            self.reader = easyocr.Reader(["en"], gpu=False)
            self.model_loaded = True
        except ImportError:
            self.model_loaded = False

    def recognize(self, image_path: str) -> str:
        if not self.model_loaded:
            return "MOCK_PLATE"
        try:
            from ultralytics import YOLO
            model = YOLO("yolov8n.pt")
            results = model(image_path)
            plate_text = ""
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    crop = r.orig_img[y1:y2, x1:x2]
                    if crop.size > 0:
                        detections = self.reader.readtext(crop)
                        for detection in detections:
                            if detection[2] > 0.5:
                                plate_text = detection[1]
                                break
            return plate_text if plate_text else "NOT_RECOGNIZED"
        except Exception:
            return "ERROR"


plate_recognizer = PlateRecognizer()

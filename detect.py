"""
Packaging Defect Detection - detect.py
Uses torch.hub to load YOLOv5 model, compatible with both custom-trained .pt files
and the provided Package-images.mp4 for demonstration.
"""

import warnings
# Suppress FutureWarning from cached torch.hub YOLOv5 about torch.cuda.amp.autocast deprecation
warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.cuda.amp.autocast.*")
warnings.filterwarnings("ignore", category=UserWarning)

import cv2
import torch
from pathlib import Path


def run(
        weights='trained_iqc_best.pt',
        source='0',
        imgsz=640,
        conf_thres=0.25,
        iou_thres=0.45,
        nosave=False,
        view_img=False,
        frame_callback=None,
        **kwargs  # accept but ignore extra parameters
):
    weights = str(weights)
    source = str(source)

    # Load model via torch.hub (handles version automatically)
    print(f"Loading model from: {weights}")
    try:
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights, verbose=False)
    except Exception as e:
        print(f"Failed to load custom weights: {e}")
        print("Falling back to yolov5s pretrained model...")
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', verbose=False)

    model.conf = conf_thres
    model.iou = iou_thres

    # Determine source type
    is_webcam = source.isnumeric()

    if is_webcam:
        cap = cv2.VideoCapture(int(source))
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"ERROR: Cannot open source: {source}")
        return

    print(f"Detection started on source: {source}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of stream or cannot read frame.")
            break

        # Run YOLOv5 inference
        results = model(frame, size=imgsz)

        # Render bounding boxes onto frame
        rendered = results.render()[0]  # numpy array with boxes drawn

        # Send frame to GUI callback if provided
        if frame_callback is not None:
            try:
                frame_callback(rendered)
            except Exception as e:
                print(f"Detection stopped by callback: {e}")
                break

        # Show in a cv2 window if requested
        if view_img:
            cv2.imshow('YOLOv5 Detection', rendered)
            if cv2.waitKey(1) == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("Detection finished.")

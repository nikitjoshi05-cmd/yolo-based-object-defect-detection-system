"""
Packaging Defect Detection - detect.py
Uses torch.hub to load YOLOv5 model, compatible with both custom-trained .pt files
and the provided Package-images.mp4 for demonstration.
Includes simple tracking to count each unique object only once.
"""

import warnings
# Suppress FutureWarning from cached torch.hub YOLOv5 about torch.cuda.amp.autocast deprecation
warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.cuda.amp.autocast.*")
warnings.filterwarnings("ignore", category=UserWarning)

import cv2
import torch
import numpy as np
from pathlib import Path
from scipy.spatial import distance as dist
from collections import OrderedDict


class CentroidTracker:
    def __init__(self, maxDisappeared=40):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.maxDisappeared = maxDisappeared
        self.countedIDs = set()
        self.objectClasses = {}  # Keep track of what class each object is

    def register(self, centroid, obj_class):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.objectClasses[self.nextObjectID] = obj_class
        self.nextObjectID += 1

    def deregister(self, objectID):
        if objectID in self.objects:
            del self.objects[objectID]
            del self.disappeared[objectID]
            # We keep objectClasses for counting purposes if needed, 
            # but usually it's better to clean up.
            # del self.objectClasses[objectID]

    def update(self, rects, obj_classes):
        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)
            return self.objects

        inputCentroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i], obj_classes[i])
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())
            D = dist.cdist(np.array(objectCentroids), inputCentroids)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            usedRows = set()
            usedCols = set()
            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue
                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.disappeared[objectID] = 0
                usedRows.add(row)
                usedCols.add(col)
            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)
            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1
                    if self.disappeared[objectID] > self.maxDisappeared:
                        self.deregister(objectID)
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col], obj_classes[col])
        return self.objects


def run(
        weights='trained_iqc_best.pt',
        source='0',
        imgsz=640,
        conf_thres=0.25,
        iou_thres=0.45,
        nosave=False,
        view_img=False,
        frame_callback=None,
        count_callback=None,   # called each frame with (good_count, damaged_count)
        arduino_serial=None,   # Serial object for signaling
        **kwargs               # accept but ignore extra parameters
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

    # Print available class names so user can verify detection labels
    print(f"Model classes: {model.names}")

    # Determine source type
    is_webcam = source.isnumeric()
    cap = cv2.VideoCapture(int(source) if is_webcam else source)

    if not cap.isOpened():
        print(f"ERROR: Cannot open source: {source}")
        return

    print(f"Detection started on source: {source}")

    # Single Tracker for all objects
    tracker = CentroidTracker(maxDisappeared=40)

    # Overall session counts
    total_good = 0
    total_damaged = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of stream or cannot read frame.")
            break

        # Run YOLOv5 inference
        results = model(frame, size=imgsz)

        rects = []
        classes = []

        if results.pred[0] is not None and len(results.pred[0]):
            for *box, conf, cls_idx in results.pred[0]:
                cls_name = model.names[int(cls_idx)].lower()
                rect = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
                rects.append(rect)
                
                if any(kw in cls_name for kw in ['good', 'ok', 'normal', 'pass', 'intact']):
                    classes.append('good')
                else:
                    classes.append('damaged')

        # Update tracker
        objects = tracker.update(rects, classes)

        # Count objects that haven't been counted yet
        for objectID in objects.keys():
            if objectID not in tracker.countedIDs:
                obj_class = tracker.objectClasses[objectID]
                if obj_class == 'good':
                    total_good += 1
                else:
                    total_damaged += 1
                    # Send signal to Arduino when defect is detected
                    if arduino_serial and arduino_serial.is_open:
                        try:
                            arduino_serial.write(b'D') # 'D' for Damaged
                            print("SENT: 'D' to Arduino")
                        except Exception as e:
                            print(f"Serial communication error: {e}")

                tracker.countedIDs.add(objectID)

        # Notify GUI of updated counts
        if count_callback is not None:
            try:
                count_callback(total_good, total_damaged)
            except Exception:
                pass

        # Render bounding boxes onto frame
        rendered = results.render()[0]  # numpy array with boxes drawn

        # Send frame to GUI callback if provided
        if frame_callback is not None:
            try:
                frame_callback(rendered)
            except Exception as e:
                print(f"Detection stopped by callback: {e}")
                break

        if view_img:
            cv2.imshow('YOLOv5 Detection', rendered)
            if cv2.waitKey(1) == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Detection finished. Total — Good: {total_good}, Damaged: {total_damaged}")

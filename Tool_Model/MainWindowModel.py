import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
import cv2
import serial
import serial.tools.list_ports

from Tool_Model.GlobalVariables import mainWindowUI

# Import the YOLOv5 detection module
# Make sure to append the project root so it can find things properly
sys.path.insert(0, str(Path(os.getcwd())))
import detect

class YoloThread(QThread):
    update_frame  = pyqtSignal(object)
    update_counts = pyqtSignal(int, int)  # good_count, damaged_count

    def __init__(self, source='0', weights='trained_iqc_best.pt', arduino_serial=None):
        super(YoloThread, self).__init__()
        self.source = str(source)
        self.weights = Path(weights)
        self.arduino_serial = arduino_serial
        self.running = True

    def run(self):
        # Frame callback — sends rendered frames to the GUI
        def frame_callback(im0):
            if self.running:
                self.update_frame.emit(im0.copy())
            else:
                raise Exception("Stop YOLO")

        # Count callback — sends live good/damaged totals to the GUI
        def count_callback(good, damaged):
            if self.running:
                self.update_counts.emit(good, damaged)
            else:
                raise Exception("Stop YOLO")

        try:
            detect.run(
                weights=self.weights,
                source=self.source,
                frame_callback=frame_callback,
                count_callback=count_callback,
                arduino_serial=self.arduino_serial,
                nosave=True,
                view_img=False
            )
        except Exception as e:
            print("YOLO detection loop exit:", e)

    def stop(self):
        self.running = False


class MainWindowClass(QMainWindow):
    def __init__(self):
        try:
            super(MainWindowClass, self).__init__()
            loadUi(mainWindowUI, self)
            self.btnClose.clicked.connect(lambda: self.ExitProgram())
            
            # Additional UI Setup
            self.yolo_thread = None
            self.arduino_serial = None
            self.current_source = '0' # default to webcam
            self.arduino_port = 'COM6' # Default port, user can change this
            
            # Connect the Run button (named pushButton in UI)
            self.pushButton.clicked.connect(self.start_detection)
            
            # Connect the Pause button (named pushButton_2 in UI)
            self.pushButton_2.clicked.connect(self.stop_detection)
            
            # Connect Load model as a File picker for video source
            self.btnLoadmodel.setText("Load Video")
            self.btnLoadmodel.clicked.connect(self.select_video_file)
            
            # Handle combo box for selecting source
            self.comboBox.currentTextChanged.connect(self.source_changed)

        except Exception as e:
            print("UI Setup Error:", e)

    def select_video_file(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mkv *.jpg *.png);;All Files (*)")
        if fileName:
            self.current_source = fileName
            print(f"Selected file source: {self.current_source}")

    def source_changed(self, text):
        if text == "Camera 1":
            self.current_source = '0'
        elif text == "Camera 2":
            self.current_source = '1'

    def start_detection(self):
        if self.yolo_thread is not None and self.yolo_thread.isRunning():
            return
            
        print(f"Starting detection with source {self.current_source}...")
        
        # Determine which weights to use
        # trained_iqc_best.pt is the actual trained model for packaging defect detection
        weights_path = 'trained_iqc_best.pt'
        if not os.path.exists(weights_path):
            weights_path = 'yolov5s.pt' # Fallback
            
        # Attempt to initialize Serial communication with Arduino
        try:
            if self.arduino_serial is None or not self.arduino_serial.is_open:
                self.arduino_serial = serial.Serial(self.arduino_port, 9600, timeout=1)
                print(f"Connected to Arduino on {self.arduino_port}")
        except Exception as e:
            print(f"Warning: Could not connect to Arduino on {self.arduino_port}. {e}")
            self.arduino_serial = None

        self.yolo_thread = YoloThread(source=self.current_source, weights=weights_path, arduino_serial=self.arduino_serial)
        self.yolo_thread.update_frame.connect(self.set_image)
        self.yolo_thread.update_counts.connect(self.set_counts)  # wire up live count display
        self.yolo_thread.start()

        # Reset counters in the UI when a new detection session starts
        self.txtGoodPackage.setText('0')
        self.txtDamagedPackage.setText('0')

    def stop_detection(self):
        if self.yolo_thread is not None:
            self.yolo_thread.stop()
            self.yolo_thread.wait(2000) # wait 2 seconds maximum
            self.yolo_thread = None
            
            if self.arduino_serial is not None:
                self.arduino_serial.close()
                self.arduino_serial = None
                print("Arduino serial closed.")
                
            print("Detection stopped.")

    def set_image(self, cv_img):
        """Convert from an opencv image to QPixmap and display in the GUI label"""
        try:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # Keep a reference to the data by using .data 
            # Note: Sometimes qimage goes black if data is GC'd. The numpy array needs to be retained or copied.
            # QImage handles memory well if using format_RGB888 with contiguous array
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(self.lblscreen1.width(), self.lblscreen1.height(), Qt.KeepAspectRatio)
            self.lblscreen1.setPixmap(QPixmap.fromImage(p))
        except Exception as e:
            print(f"Error drawing frame: {e}")

    def set_counts(self, good, damaged):
        """Update the Good/Damaged package counters live in the GUI"""
        try:
            self.txtGoodPackage.setText(str(good))
            self.txtDamagedPackage.setText(str(damaged))
        except Exception as e:
            print(f"Error updating counts: {e}")

    def ExitProgram(self):
        self.stop_detection()
        sys.exit(0)

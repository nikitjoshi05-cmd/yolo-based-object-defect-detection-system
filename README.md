# A YOLO-based Real-time Packaging Defect Detection System

## Project Architecture & Workflow

This project is an end-to-end automated quality control system that integrates machine learning with industrial hardware.

### 1. Software Layer (The 'Brain')
*   **Deep Learning**: Uses a custom-trained **YOLOv5** model to identify "Good" and "Damaged" packages in real-time.
*   **Tracking**: Implements a **Centroid Tracking** algorithm (in `detect.py`) which assigns unique IDs to every package. This ensures that each package is only counted and processed once, even as it moves across the camera's view.
*   **GUI**: Built with **PyQt5**, providing a real-time video feed, live damage counters, and controls to start/stop the system.

### 2. Communication Layer (The 'Nerve System')
*   **Protocol**: Serial communication via USB (at 9600 baud) using the `pyserial` library.
*   **Signal**: When a "Damaged" object is uniquely identified, the Python script sends a single byte trigger (`'D'`) to the Arduino.

### 3. Hardware Layer (The 'Hand')
*   **Controller**: An **Arduino Uno** running custom firmware that listens for the 'D' trigger.
*   **Actuator**: A **Robotic Arm** (Servo-controlled) that:
    1.  Moves to the object position.
    2.  Waits for 2 seconds (as requested).
    3.  Returns to its home position.

### End-to-End Workflow summary:
`Camera Input` -> `YOLOv5 Detection` -> `Object Tracking (Centroid)` -> `Defect Classification` -> `Serial Signal ('D')` -> `Arduino Processing` -> `Robotic Arm Action`

---

<p align="center">
  <img src="https://github.com/vuthithuhuyen/A-YOLO-based-Real-time-Packaging-Defect-Detection-System/blob/main/System_architecture.png" width="700">    
</p>
<p align="center"><label>**The system architecture**</label></p>

<p align="center">
  <img src="https://github.com/vuthithuhuyen/A-YOLO-based-Real-time-Packaging-Defect-Detection-System/blob/main/training%20results.png" width="700">    
</p>
<p align="center"><label>**Training results**</label></p>

<p align="center">
  <img src="https://github.com/vuthithuhuyen/A-YOLO-based-Real-time-Packaging-Defect-Detection-System/blob/main/training%20results%202.png" width="700">    
</p>
<p align="center"><label>**Training results**</label></p>


<p align="center">
  <img src="https://github.com/vuthithuhuyen/A-YOLO-based-Real-time-Packaging-Defect-Detection-System/blob/main/System%20GUI.png" width="700" title="The system GUI">    
</p>
<p align="center"><label>**The system GUI**</label></p>


## Project Architecture & Workflow

This project is an end-to-end automated quality control system that integrates machine learning with industrial hardware.

### 1. Software Layer (The 'Brain')
*   **Deep Learning**: Uses a custom-trained **YOLOv5** model to identify "Good" and "Damaged" packages in real-time.
*   **Tracking**: Implements a **Centroid Tracking** algorithm (in `detect.py`) which assigns unique IDs to every package. This ensures that each package is only counted and processed once, even as it moves across the camera's view.
*   **GUI**: Built with **PyQt5**, providing a real-time video feed, live damage counters, and controls to start/stop the system.

### 2. Communication Layer (The 'Nerve System')
*   **Protocol**: Serial communication via USB (at 9600 baud) using the `pyserial` library.
*   **Signal**: When a "Damaged" object is uniquely identified, the Python script sends a single byte trigger (`'D'`) to the Arduino.

### 3. Hardware Layer (The 'Hand')
*   **Controller**: An **Arduino Uno** running custom firmware that listens for the 'D' trigger.
*   **Actuator**: A **Robotic Arm** (Servo-controlled) that:
    1.  Moves to the object position.
    2.  Waits for 2 seconds (as requested).
    3.  Returns to its home position.

### End-to-End Workflow summary:
`Camera Input` -> `YOLOv5 Detection` -> `Object Tracking (Centroid)` -> `Defect Classification` -> `Serial Signal ('D')` -> `Arduino Processing` -> `Robotic Arm Action`

---



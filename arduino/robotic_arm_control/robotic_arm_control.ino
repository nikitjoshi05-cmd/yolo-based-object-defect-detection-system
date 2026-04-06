/*
 * Robotic Arm Defect Detection - Arduino Code
 * 
 * Flow:
 * 1. Wait for signal from Python (YOLO System).
 * 2. If 'D' (Defect detected) is received:
 *    - Move arm to the object position.
 *    - Wait for 2 seconds (as requested).
 *    - Return arm to home position.
 */

#include <Servo.h>

// Pins for the servos/actuators
const int SERVO_PIN = 9;

// Servo positions (adjust based on your mechanical setup)
const int HOME_POS = 80;    // Resting/Starting place
const int OBJECT_POS = 140; // Position to "move to the object"

Servo roboticArm;

void setup() {
  // Start Serial communication at 9600 baud
  Serial.begin(9600);
  
  // Attach the servo
  roboticArm.attach(SERVO_PIN);
  
  // Initialize to home position
  roboticArm.write(HOME_POS);
  
  Serial.println("Arduino Ready. Waiting for signals...");
}

void loop() {
  // Check if data is available on the Serial port
  if (Serial.available() > 0) {
    char signal = Serial.read();
    
    // Check if the signal is 'D' for Defect
    if (signal == 'D') {
      Serial.println("Defect Signal Received: Moving arm...");
      
      // 1. Move to the object
      roboticArm.write(OBJECT_POS);
      
      // 2. Wait for 2 seconds as requested
      delay(2000);
      
      // 3. Return to its place
      roboticArm.write(HOME_POS);
      
      Serial.println("Action Complete: Arm returned home.");
    }
  }
}

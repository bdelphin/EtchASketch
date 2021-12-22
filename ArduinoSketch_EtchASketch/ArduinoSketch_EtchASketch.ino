/*
  Etch a Sketch USB
  Baptiste DELPHIN - 2021
  https://github.com/bdelphin/EtchASketch
*/

// Pin mapping
const int leftPot = A0;    // Analog input pin that the left potentiometer is attached to
const int rightPot = A1;   // Analog input pin that the right potentiometer is attached to
const int tiltSwitch = 2;

// Define the number of samples to keep track of. The higher the number, the
// more the readings will be smoothed, but the slower the output will respond to
// the input. Using a constant rather than a normal variable lets us use this
// value to determine the size of the readings array.
// All credit for this potentiometer smoothing method goes to Arduino.cc :
// https://www.arduino.cc/en/Tutorial/BuiltInExamples/Smoothing
const int numReadings = 30;
int readIndex = 0;                  // the index of the current reading

int leftReadings[numReadings];      // the readings from the analog input
int leftTotal = 0;                  // the running total
int leftAverage = 0;                // the average

int rightReadings[numReadings];      // the readings from the analog input
int rightTotal = 0;                  // the running total
int rightAverage = 0;                // the average

int leftValue = 0;                   // value read from the left pot
int rightValue = 0;                  // value read from the right pot
int switchStatus = HIGH;             // switch status (HIGH by default)

int lastLeftValue = -10;             // last value read from the left pot
int lastRightValue = -10;            // last value read from the right pot
int lastSwitchStatus = HIGH;         // last switch status

// while this boolean is true, no reading will actually be sent
// (needed to avoid sending garbage data to the software)
bool warmupAverageReadings = true;

void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(9600);

  delay(5);
  Serial.println("Etch a Sketch USB");

  //configure pin 2 as an input and enable the internal pull-up resistor
  pinMode(2, INPUT_PULLUP);

  // initialize all the readings to 0:
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    leftReadings[thisReading] = 0;
    rightReadings[thisReading] = 0;
  }
}

void loop() {

  // subtract the last reading:
  leftTotal = leftTotal - leftReadings[readIndex];
  rightTotal = rightTotal - rightReadings[readIndex];
  
  // read from the sensor:
  leftReadings[readIndex] = map(analogRead(leftPot), 0, 1024, 1024, 0);
  rightReadings[readIndex] = analogRead(rightPot);
  
  // add the reading to the total:
  leftTotal = leftTotal + leftReadings[readIndex];
  rightTotal = rightTotal + rightReadings[readIndex];
  
  // advance to the next position in the array:
  readIndex = readIndex + 1;

  // if we're at the end of the array...
  if (readIndex >= numReadings) {
    // ...wrap around to the beginning:
    readIndex = 0;

    // the average system has warmed up, we can begin to send data
    warmupAverageReadings = false;
  }

  // calculate the average:
  leftAverage = leftTotal / numReadings;
  rightAverage = rightTotal / numReadings;

  // read switch status
  switchStatus = digitalRead(tiltSwitch);
  
  // if the average system is warmed up, we can send data
  if(!warmupAverageReadings) {

    // only if current values are different than last sent ones,
    // to avoid spamming the serial port
    if(leftAverage != lastLeftValue || rightAverage != lastRightValue || switchStatus != lastSwitchStatus) {
        // update last recorded values
        lastLeftValue = leftAverage;
        lastRightValue = rightAverage;
        lastSwitchStatus = switchStatus;

        // actually send to computer through serial port
        // syntax is left:right:switch
        Serial.print(leftAverage);
        Serial.print(":");
        Serial.print(rightAverage);
        Serial.print(":");
        Serial.println(switchStatus);
      }
  }
  
  delay(1); // delay in between reads for stability
}

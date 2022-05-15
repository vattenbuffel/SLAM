#include <Arduino.h>

#define ENCODER_LEFT_A 33
#define ENCODER_LEFT_B 14
#define ENCODER_RIGHT_A 13
#define ENCODER_RIGHT_B 11

#define ENA 25
#define ENB 26

#define IN1 32
#define IN2 32
#define IN3 32
#define IN4 32

#define REPORT_FREQ_MS 100

// TODO: Set in1,2,3,4 based on what direction the speed should go

// Data is sent to esp as a byte representing speed percent. 200 is full speed ahead, 100 is stationry and -50 is 50 % speed backwards.

// TODO: See how long it takes to write data to serial and see if it can be done at 100 hz while keeping rest of code at 1 khz



volatile uint32_t encoder_left = 0;
volatile uint32_t encoder_right = 0;

static void IRAM_ATTR encoder_right_int(){
	encoder_right++;
}

static void IRAM_ATTR encoder_left_int(){
	encoder_left++;
}

void setup() {
	Serial.begin(115200);
	Serial.println("hello world\n");

	pinMode(ENCODER_LEFT_A, INPUT_PULLUP);
	attachInterrupt(ENCODER_LEFT_A, encoder_left_int, CHANGE);
	pinMode(ENCODER_LEFT_B, INPUT_PULLUP);
	attachInterrupt(ENCODER_LEFT_B, encoder_left_int, CHANGE);
}

void loop() {
	static uint32_t t_first = millis();

	if (millis() - t_first > REPORT_FREQ_MS){
		Serial.print(encoder_left);
		Serial.print(", ");
		Serial.println(encoder_right);

		t_first = millis();
	}

}
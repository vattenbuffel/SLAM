#include <Arduino.h>

#define ENCODER_LEFT_A 33
#define ENCODER_LEFT_B 14
#define ENCODER_RIGHT_A 13
#define ENCODER_RIGHT_B 15

#define ENA 25
#define ENA_PWM_CHANNEL 1
#define ENB 26
#define ENB_PWM_CHANNEL 0

#define IN1 23
#define IN2 22
#define IN3 21
#define IN4 19

#define REPORT_FREQ_MS 5

#define CMD_LEN 3

// TODO: Set in1,2,3,4 based on what direction the speed should go

// Data is sent to esp as a byte representing speed percent. 200 is full speed ahead, 100 is stationry and -50 is 50 % speed backwards, -70 is 70 % speed backwards.

// TODO: See how long it takes to write data to serial and see if it can be done at 100 hz while keeping rest of code at 1 khz


volatile uint32_t encoder_left = 0;
volatile uint32_t encoder_right = 0;

static void IRAM_ATTR encoder_right_int(){
	encoder_right++;
}

static void IRAM_ATTR encoder_left_int(){
	encoder_left++;
}

static void motor_for(int gpio1, int gpio2){
	digitalWrite(gpio1, HIGH);
	digitalWrite(gpio2, LOW);

}

static void motor_rev(int gpio1, int gpio2){
	digitalWrite(gpio1, LOW);
	digitalWrite(gpio2, HIGH);
}

static void motor_off(int gpio1, int gpio2){
	digitalWrite(gpio1, LOW);
	digitalWrite(gpio2, LOW);
}

void write_data_in_bytes(uint32_t val){
	static uint8_t byte;
	static int i = 0;
	for (i = 0; i < 4; i++) {
		byte = val >> i*8;
		Serial.write(byte);
	}

}

void report(){
	static uint32_t t_first = millis();

	// Report current encoder values
	if (millis() - t_first > REPORT_FREQ_MS){
		Serial.write('#');
		write_data_in_bytes(encoder_right);
		write_data_in_bytes(encoder_left);
		
		t_first = millis();
	}
}

void cmd_handle(){
	static uint8_t buf[CMD_LEN];
	static char c;
	static int cnt;
	// Serial.print("serial.available: ");
	// Serial.println(Serial.available());

	if (Serial.available() == 0){
		return;
	}

	c = Serial.peek();
	// Serial.printf("serial.available: %d, serial.peek(): %d, '%c'\n", Serial.available(), c, c);

	if (c == '?'){
		Serial.write("<esp>");
		Serial.read();
	} else if (c == '!'){
		cnt = Serial.readBytes(buf, CMD_LEN);
		if(cnt != CMD_LEN){
			Serial.print("Invalid command. Expected ");
			Serial.print(CMD_LEN);
			Serial.print(" bytes. Received: ");
			Serial.println(cnt);
		}

		if(buf[1] == 0) {
			motor_off(IN1, IN2);
		} else if(buf[1] > 100){
			motor_for(IN1, IN2);
		}else if(buf[1] < 100){
			motor_rev(IN1, IN2);
		}
		ledcWrite(ENA_PWM_CHANNEL, map(buf[1] >= 100 ? buf[1]-100 : buf[1], 0, 100, 0, 255));

		if(buf[2] == 0) {
			motor_off(IN3, IN4);
		} else if(buf[2] > 100){
			motor_for(IN3, IN4);
		}else if(buf[2] < 100){
			motor_rev(IN3, IN4);
		}
		ledcWrite(ENB_PWM_CHANNEL, map(buf[2] >= 100 ? buf[2]-100 : buf[2], 0, 100, 0, 255));
		// Serial.print("received: !. right_vel: ");
		// Serial.print(buf[1]);
		// Serial.print(". left_vel: ");
		// Serial.println(buf[2]);
			
	} else{
		int bytes_available = Serial.available();
		char tmp[bytes_available + 1];
		tmp[bytes_available] = '\0';
		
		int read_b = Serial.readBytes(tmp, bytes_available);
		Serial.print("Invalid command received: \"");
		Serial.print(tmp);
		Serial.print("\", bytes: ");
		Serial.println(read_b);

		while(Serial.available() > 0){
			c = Serial.read();
		}
	}
}

void setup() {
	Serial.begin(115200);
	while(Serial.available() > 0){
		Serial.read();
	}
	Serial.println("hello world\n");

	pinMode(ENCODER_LEFT_A, INPUT_PULLUP);
	attachInterrupt(ENCODER_LEFT_A, encoder_left_int, CHANGE);
	pinMode(ENCODER_LEFT_B, INPUT_PULLUP);
	attachInterrupt(ENCODER_LEFT_B, encoder_left_int, CHANGE);

	pinMode(ENCODER_RIGHT_A, INPUT_PULLUP);
	attachInterrupt(ENCODER_RIGHT_A, encoder_right_int, CHANGE);
	pinMode(ENCODER_RIGHT_B, INPUT_PULLUP);
	attachInterrupt(ENCODER_RIGHT_B, encoder_right_int, CHANGE);

	pinMode(IN1, OUTPUT);
	pinMode(IN2, OUTPUT);
	pinMode(IN3, OUTPUT);
	pinMode(IN4, OUTPUT);
	motor_off(IN1 ,IN2);
	motor_off(IN3 ,IN4);

	// configure LED PWM functionalitites
	ledcSetup(ENA_PWM_CHANNEL, 5000, 8);
	ledcAttachPin(ENA, ENA_PWM_CHANNEL);
	ledcWrite(ENA_PWM_CHANNEL, 0);

	ledcSetup(ENB_PWM_CHANNEL, 5000, 8);
	ledcAttachPin(ENB, ENB_PWM_CHANNEL);
	ledcWrite(ENB_PWM_CHANNEL, 0);
}

void loop() {
	report();
	cmd_handle();
	// digitalWrite(IN4, HIGH);
	// digitalWrite(IN3, HIGH);
	// digitalWrite(IN2, HIGH);
	// digitalWrite(IN1, HIGH);
}
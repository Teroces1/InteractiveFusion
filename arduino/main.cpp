const int PWM_PIN = 9;

int pwn = 0;
String buffer = "";

void setup() {
    Serial.begin(9600);
    pinMode(PWM_PIN, OUTPUT);
}

void loop() {
    while Serial.available()) {
        char c = Serial.read();

        if (c == '\n') {
            int value = buffer.toInt();
            if (value >= 0 && value <= 255) {
                pwn = value;
            }
            buffer = "";
        } else if (isDigit(c)) {
            buffer += c;
        }
    }

    analogWrite(PWM_PIN, pwn);
}
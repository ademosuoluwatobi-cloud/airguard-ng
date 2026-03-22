/*
  AirGuard NG — Arduino Hardware Device
  =======================================
  Board:    Arduino Uno / Nano
  Sensors:  MQ2 (gas/smoke), DHT11 (temp + humidity)
  Display:  SSD1306 OLED 128x64 via I2C (U8glib)
  Outputs:  RGB LED (air quality indicator), Buzzer (danger alert)

  Wiring:
    MQ2   AO   → A0          DHT11 DATA → D2
    MQ2   VCC  → 5V          DHT11 VCC  → 5V
    MQ2   GND  → GND         DHT11 GND  → GND

    RGB   R    → D5 (PWM)    OLED SDA   → A4
    RGB   G    → D6 (PWM)    OLED SCL   → A5
    RGB   B    → D9 (PWM)    OLED VCC   → 3.3V
    RGB   GND  → GND         OLED GND   → GND

    BUZZER +   → D8
    BUZZER -   → GND

  Serial output (115200 baud) — structured for scraping:
    GAS_RAW:512,GAS_PPM:45.2,GAS_LEVEL:MODERATE,TEMP:27.3,HUM:61.0,RISK:Caution

  MQ2 Thresholds:
    0   – 599   → GOOD     → Green  LED
    600 – 799   → MODERATE → Cyan   LED
    800 – 999   → POOR     → Yellow LED
    1000– 1299  → BAD      → Orange LED
    1300+       → DANGER   → Red LED + Buzzer ON (continuous)
*/

#include <Arduino.h>
#include <Wire.h>
#include <U8glib.h>
#include <DHT.h>
#include <avr/wdt.h>

// ── PINS ─────────────────────────────────────────────────────
#define MQ2_PIN     A0
#define DHT_PIN     2
#define DHT_TYPE    DHT11
#define RED_PIN     5
#define GREEN_PIN   6
#define BLUE_PIN    9
#define BUZZER_PIN  8

// ── MQ2 THRESHOLDS ────────────────────────────────────────────
#define THRESHOLD_GOOD      200
#define THRESHOLD_MODERATE  300
#define THRESHOLD_POOR     400
#define THRESHOLD_BAD      500

// ── TIMING ────────────────────────────────────────────────────
#define READ_INTERVAL   2000
#define SERIAL_INTERVAL 2000

// ── OBJECTS ───────────────────────────────────────────────────
// Hardware I2C SSD1306 128x64 — U8glib constructor
U8GLIB_SSD1306_128X64 oled(U8G_I2C_OPT_NONE);
DHT dht(DHT_PIN, DHT_TYPE);

// ── STATE ─────────────────────────────────────────────────────
int    gasRaw    = 0;
float  gasPPM    = 0.0;
float  tempC     = 0.0;
float  humidity  = 0.0;
String gasLevel  = "---";
String riskLabel = "---";
bool   inDanger  = false;

unsigned long lastReadTime   = 0;
unsigned long lastSerialTime = 0;

// ── PPM CONVERSION ────────────────────────────────────────────
float toPPM(int raw) {
  if (raw <= 0) return 0.0;
  float voltage = raw * (5.0 / 1023.0);
  if (voltage <= 0) return 0.0;
  float rs  = ((5.0 / voltage) - 1.0) * 10.0;
  float ppm = 1000.0 * pow((rs / 9.83) / 0.3, 1.0 / -0.47);
  return max(0.0f, (float)ppm);
}

// ── GAS EVALUATION ────────────────────────────────────────────
void evaluateGas(int raw) {
  if (raw < THRESHOLD_GOOD) {
    gasLevel  = "GOOD";
    riskLabel = "Safe";
  } else if (raw < THRESHOLD_MODERATE) {
    gasLevel  = "MODERATE";
    riskLabel = "Caution";
  } else if (raw < THRESHOLD_POOR) {
    gasLevel  = "POOR";
    riskLabel = "Warning";
  } else if (raw < THRESHOLD_BAD) {
    gasLevel  = "BAD";
    riskLabel = "Danger";
  } else {
    gasLevel  = "DANGER";
    riskLabel = "Critical";
  }
  inDanger = (raw >= THRESHOLD_BAD);
}

// ── RGB LED ───────────────────────────────────────────────────
void setColor(uint8_t r, uint8_t g, uint8_t b) {
  analogWrite(RED_PIN,   r);
  analogWrite(GREEN_PIN, g);
  analogWrite(BLUE_PIN,  b);
}

void updateLED(int raw) {
  if      (raw < THRESHOLD_GOOD)     setColor(0,   255, 0);   // Green
  else if (raw < THRESHOLD_MODERATE) setColor(0,   255, 200); // Cyan
  else if (raw < THRESHOLD_POOR)     setColor(200, 255, 0);   // Yellow
  else if (raw < THRESHOLD_BAD)      setColor(255, 80,  0);   // Orange
  else                               setColor(255, 0,   0);   // Red
}

// ── BUZZER ────────────────────────────────────────────────────
void updateBuzzer(bool danger) {
  digitalWrite(BUZZER_PIN, danger ? HIGH : LOW);
}

// ── OLED DRAW (called inside firstPage/nextPage loop) ─────────
void drawScreen() {
  char tempBuf[8];
  char humBuf[8];
  char rawBuf[8];
  char ppmBuf[10];
  char line1[24];
  char line2[24];

  dtostrf(tempC,    4, 1, tempBuf);
  dtostrf(humidity, 4, 1, humBuf);
  itoa(gasRaw, rawBuf, 10);
  dtostrf(gasPPM, 6, 1, ppmBuf);
  snprintf(line1, sizeof(line1), "Raw:%-4s PPM:%s", rawBuf, ppmBuf);
  snprintf(line2, sizeof(line2), "T:%sC  H:%s%%",   tempBuf, humBuf);

  // ── Inverted header bar ──────────────────────────────────
  oled.setColorIndex(1);
  oled.drawBox(0, 0, 128, 13);
  oled.setColorIndex(0);                   // black text on white bar
  oled.setFont(u8g_font_6x10);
  oled.drawStr(3, 11, "AirGuard NG");
  oled.drawStr(78, 11, inDanger ? "DANGER!" : "  OK");
  oled.setColorIndex(1);                   // back to white-on-black

  // ── Gas level label ──────────────────────────────────────
  oled.setFont(u8g_font_7x14);
  oled.drawStr(2, 28, "Gas:");
  oled.drawStr(40, 28, gasLevel.c_str());

  // ── Raw + PPM ────────────────────────────────────────────
  oled.setFont(u8g_font_6x10);
  oled.drawStr(2, 41, line1);

  // ── Temp + Humidity ──────────────────────────────────────
  oled.drawStr(2, 53, line2);

  // ── Risk label ───────────────────────────────────────────
  oled.drawStr(2, 63, riskLabel.c_str());
}

void updateOLED() {
  oled.firstPage();
  do {
    drawScreen();
  } while (oled.nextPage());
}

// ── SERIAL ────────────────────────────────────────────────────
void printSerial() {
  Serial.print(F("GAS_RAW:"));    Serial.print(gasRaw);
  Serial.print(F(",GAS_PPM:"));   Serial.print(gasPPM, 1);
  Serial.print(F(",GAS_LEVEL:")); Serial.print(gasLevel);
  Serial.print(F(",TEMP:"));      Serial.print(tempC, 1);
  Serial.print(F(",HUM:"));       Serial.print(humidity, 1);
  Serial.print(F(",RISK:"));      Serial.println(riskLabel);
}

// ── SETUP ─────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println(F("AirGuard NG — starting..."));

  pinMode(RED_PIN,    OUTPUT);
  pinMode(GREEN_PIN,  OUTPUT);
  pinMode(BLUE_PIN,   OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  setColor(0, 0, 0);
  digitalWrite(BUZZER_PIN, LOW);

  Wire.begin();
  oled.begin();
  oled.setColorIndex(1); // white pixels on black background

  dht.begin();
  delay(1000);

  // MQ2 warm-up countdown — 30 s for stable baseline
  Serial.println(F("MQ2 warming up 30s..."));
  for (int i = 30; i > 0; i--) {
    wdt_reset();
    char wBuf[16];
    snprintf(wBuf, sizeof(wBuf), "Warm-up: %2ds", i);
    oled.firstPage();
    do {
      oled.setFont(u8g_font_7x14);
      oled.drawStr(10, 22, "AirGuard NG");
      oled.setFont(u8g_font_6x10);
      oled.drawStr(20, 38, "Warming up...");
      oled.drawStr(16, 52, wBuf);
    } while (oled.nextPage());
    delay(1000);
  }

  wdt_enable(WDTO_2S);

  lastReadTime   = millis();
  lastSerialTime = millis();

  Serial.println(F("Ready."));
  Serial.println(F("FORMAT: GAS_RAW,GAS_PPM,GAS_LEVEL,TEMP,HUM,RISK"));
}

// ── LOOP ──────────────────────────────────────────────────────
void loop() {
  wdt_reset();

  unsigned long now = millis();

  if (now - lastReadTime >= READ_INTERVAL) {
    lastReadTime = now;

    gasRaw = analogRead(MQ2_PIN);
    gasPPM = toPPM(gasRaw);
    evaluateGas(gasRaw);

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (!isnan(h) && !isnan(t)) {
      humidity = h;
      tempC    = t;
    }

    updateLED(gasRaw);
    updateBuzzer(inDanger);
    updateOLED();
  }

  if (now - lastSerialTime >= SERIAL_INTERVAL) {
    lastSerialTime = now;
    printSerial();
  }
}
#include <WiFi.h>
#include <HTTPClient.h>
#include <PZEM004Tv30.h>
#include <HardwareSerial.h>

// ==== WiFi Credentials ====
const char* ssid = "YB";
const char* password = "nasiorakarik";

// ==== Firebase Realtime Database URL ====
const char* firebaseHost = "https://piot-c14e2-default-rtdb.firebaseio.com";

// ==== PZEM Pin Config ====
#define PZEM_RX_PIN 16
#define PZEM_TX_PIN 17

// ==== Setup UART2 for PZEM ====
HardwareSerial pzemSerial(2); // UART2 pada ESP32
PZEM004Tv30 pzem(pzemSerial, PZEM_RX_PIN, PZEM_TX_PIN);

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Start Serial untuk PZEM
  pzemSerial.begin(9600, SERIAL_8N1, PZEM_RX_PIN, PZEM_TX_PIN);
  Serial.println("PZEM Test Started");

  // Koneksi ke WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");
}

void loop() {
  float voltage = pzem.voltage();
  float current = pzem.current();
  float power = pzem.power();
  float energy = pzem.energy();
  float frequency = pzem.frequency();
  float pf = pzem.pf();

  // Tampilkan data di Serial Monitor
  if (isnan(voltage) || isnan(current) || isnan(power) || 
      isnan(energy) || isnan(frequency) || isnan(pf)) {
    Serial.println("Gagal baca data dari sensor PZEM!");
  } else {
    Serial.println("=== Data Sensor PZEM ===");
    Serial.print("Tegangan (V): "); Serial.println(voltage);
    Serial.print("Arus (A): ");     Serial.println(current);
    Serial.print("Daya (W): ");     Serial.println(power);
    Serial.print("Energi (Wh): ");  Serial.println(energy);
    Serial.print("Frekuensi (Hz): "); Serial.println(frequency);
    Serial.print("Power Factor: "); Serial.println(pf);

    // Siapkan JSON untuk Firebase
    String jsonPayload = "{";
    jsonPayload += "\"voltage\":" + String(voltage, 2) + ",";
    jsonPayload += "\"current\":" + String(current, 2) + ",";
    jsonPayload += "\"power\":" + String(power, 2) + ",";
    jsonPayload += "\"energy\":" + String(energy, 3) + ",";
    jsonPayload += "\"frequency\":" + String(frequency, 1) + ",";
    jsonPayload += "\"pf\":" + String(pf, 2);
    jsonPayload += "}";

    // Kirim ke Firebase
    String url = String(firebaseHost) + "/pzemData.json";

    HTTPClient http;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.PUT(jsonPayload);

    if (httpResponseCode > 0) {
      Serial.print("HTTP Response Code: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("Gagal kirim data: ");
      Serial.println(http.errorToString(httpResponseCode).c_str());
    }

    http.end();
  }

  Serial.println();
  delay(5000); // Delay 5 detik sebelum kirim data lagi
}

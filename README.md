# 🛡️ AirGuard NG  
**Nigeria's Air Quality Intelligence & Gas Leakage Detection System**

AirGuard NG is an integrated IoT and data analytics platform designed to monitor atmospheric health across Nigeria while providing real-time indoor safety alerts.

Developed by a 3MTT Nextgen Participant who is an Electrical and Electronics Engineering graduate, this project bridges the gap between global air quality datasets (via OpenAQ v3) and hyper-local environmental sensing using embedded hardware (Arduino Uno + MQ2 sensor).

---

## 🚀 Key Features

- **Health Risk Score (HRS):**  
  A proprietary 0–100 index derived from PM2.5 concentrations, aligned with the WHO 2021 Air Quality Guidelines for accurate health risk assessment.

- **IoT Hardware Integration:**  
  Real-time indoor monitoring of LPG, smoke, and carbon monoxide using an Arduino-based sensing system.

- **Telegram Alert System:**  
  Instant notifications triggered when air quality or gas levels exceed safe thresholds.

- **Multi-State Coverage:**  
  Active monitoring across Lagos, Ogun, Cross River, and the Federal Capital Territory (Abuja).

---

## 🛠️ Tech Stack

- **Dashboard:**  
  Streamlit (Python 3.14), Plotly, Folium  

- **Data Pipeline:**  
  Pandas, Requests (OpenAQ v3 API), python-dotenv  

- **Hardware:**  
  Arduino Uno, MQ2 Gas Sensor, DHT11 (Temperature & Humidity), I2C OLED Display  

- **Communication:**  
  PySerial (USB communication), Flask (ESP32 WiFi integration)

---

## 📁 Project Structure

- `overview.py` – Main dashboard entry point  
- `styles.py` – Shared UI/UX components and HRS logic  
- `data_pipeline.py` – Fetches and processes air quality data across Nigeria  
- `serial_reader.py` – Bridges Arduino USB data to the dashboard  
- `pages/` – Contains 8 modular analysis pages (City insights, health guides, etc.)

---

## 👷 Author

**Oluwatobi Peter Ademosu**  
BSc. Electrical & Electronics Engineering 
3MTT | Data Science | GMNSE | GMNIEE
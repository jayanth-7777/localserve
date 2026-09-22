# LOCALServe
### A Hyperlocal Community Platform for Essential Services and Medicine Availability

LOCALServe connects local community residents, villages, and small towns with nearby verified service providers (electricians, plumbers, carpenters, mechanics, repair technicians) and local pharmacies reporting available medicines with last-updated timestamps.

---

## 🌟 Key Features & Academic Requirements

### 1. Local Service Discovery & Proximity Matching
- **GPS-Based Nearby Search**: Calculates distance using the **Haversine formula** (`haversine(lat1, lon1, lat2, lon2)`).
- **Radius Filtering**: Filter technicians within 5 km, 10 km, 15 km, 25 km, or 50 km.
- **Interactive Leaflet Map**: High-contrast interactive map with OpenStreetMap tiles displaying user location (📍 blue) and service providers (🔧 orange).
- **Service Categories**: Electrician, Plumber, Carpenter, Mechanic, Appliance Tech, House Cleaner, Painter, TV/Mobile Tech.

### 2. Pharmacy-Reported Medicine Availability Finder
- **Accurate Academic Terminology**: Labeled explicitly as **"Pharmacy-reported availability with last-updated timestamps"** rather than misleading "live" streaming:
  - 🟢 **Available** — *Updated 8 minutes ago*
  - 🟡 **Low Stock** — *Updated 25 minutes ago*
  - ⚪ **Unavailable** — *Updated 6 hours ago*
- **Relative Timestamps**: Real-time relative duration calculation (`time_ago()`) indicating how fresh the reported data is.
- **Store Contact**: Direct phone dialer and WhatsApp chat for every pharmacy.

### 3. Community Medicine Request Feature
- When a medicine is unlisted or out of stock, users can broadcast a **Medicine Request**:
  - Medicine name, strength, and quantity.
  - **Prescription Photo Upload**: Non-literate or elderly patients can simply take a photo of their doctor's slip without typing complex scientific names.
  - Nearby verified pharmacies receive instant notification in their dashboard and can respond with:
    - 🟢 **Available** (with pricing notes)
    - 🔴 **Not Available**
    - 🕒 **Expected Later** (with estimated arrival time)

### 4. Rural & Low-Literacy Accessibility Mode ("Gramin Sahayak Mode")
- **Visual Pictograms**: Large pictorial cards with universally recognizable icons and high-contrast color coding.
- **Voice Search (Speech-to-Text)**: Microphone button 🎙️ powered by the Web Speech API; speak in Telugu, Hindi, or English.
- **Audio Readout (Text-to-Speech)**: Loud and clear speaker 🔊 button on every provider card, medicine card, and booking status.
- **Multilingual Support (i18n)**: Instant language switcher right in the header:
  - **English**
  - **తెలుగు (Telugu)**
  - **हिंदी (Hindi)**
- **1-Tap Direct Call & WhatsApp**: Instant dialer (`tel:...`) so users can talk directly without getting stuck in digital forms.
- **Visual Status Progress Bar**: Pictorial stage tracker for bookings (📝 Requested → 👍 Accepted → 🛵 On the Way → 🔧 Working → ✅ Completed).

### 5. Multi-Role Dashboards
- **Customer Dashboard**: Track active bookings, review completed jobs (1-5 stars + feedback), view pharmacy responses to medicine requests, file complaints.
- **Provider Dashboard**: Toggle availability (Available / Busy / Offline), incoming booking queue (Accept/Decline), step-by-step job progress updater, reviews and earnings.
- **Pharmacy Dashboard**: Stock manager, 1-click "Confirm Stock Now" timestamp refresher, incoming medicine inquiries responder with prescription viewer.
- **Admin Console**: Platform KPI metrics, provider and pharmacy verification approval queue (Verified / Pending / Suspended / Rejected), complaints grievance redressal.

---

## 🛠️ Tech Stack

- **Backend**: Python 3 (Flask, Jinja2, Werkzeug)
- **Database**: SQLite3 (Compatible with Microsoft SQL Server / MySQL)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, FontAwesome 6
- **Maps**: Leaflet.js with OpenStreetMap
- **Voice & Accessibility**: Web Speech API (`SpeechRecognition`, `speechSynthesis`)

---

## 🚀 How to Run Locally

### 1. Activate Virtual Environment
```powershell
.venv\Scripts\activate
```

### 2. Run Application
```powershell
python run.py
```
Open your browser at: **`http://127.0.0.1:5000`**

---

## 🧪 Demo Accounts (1-Click Switch Bar)

At the top of every screen is a **Quick Demo Role Switcher** for evaluators:
| Role | Demo Account | Password | Primary Feature to Test |
| :--- | :--- | :--- | :--- |
| **Customer** | `customer@localserve.com` | `pass123` | Voice search, pictorial cards, booking, medicine requests |
| **Provider** | `ramesh@provider.com` | `pass123` | Electrician job queue, accept/reject, lifecycle updater |
| **Pharmacy** | `balaji@pharmacy.com` | `pass123` | Stock editor, confirm timestamps, prescription inquiry responder |
| **Admin** | `admin@localserve.com` | `admin123` | Verification queue, complaints moderation, KPI metrics |

---

## 🔬 Running Automated Tests
```powershell
.venv\Scripts\python.exe test_app.py
```
Runs 8 automated unit tests covering seeding, Haversine formula, booking lifecycle, medicine requests, and REST APIs.

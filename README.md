# Axioma Lexis

> **Adaptive Spaced Repetition Vocabulary & Flashcards for Android & Web**  
> A distraction-free vocabulary capture and adaptive spaced repetition workspace built for mobile and terminal ergonomics.

---

## 🌟 Key Features

### 🧠 Humane Spaced Repetition (Step-Back Fibonacci Spacing)
* **Zero Backlog Dread:** Capped micro-sessions (3 to 5 words max) so daily reviews take only 30 seconds.
* **Humane Step-Back Decay:** Struggling on a card steps it back by strictly 1 tier rather than punishing the learner with a reset to zero.
* **Dwell Patience Window:** A 10-second desirable difficulty window before revealing contextual hints.
* **Functorial 1-Tap Undo:** Instantly undo an accidental rating (swipe or button) with zero schedule corruption.

### 📱 Android Native Experience & Background Notifications
* **Native Android App (Kotlin):** Standalone fullscreen WebView app with offline asset caching and hardware vibration haptics.
* **Reliable Background Reminders:** Uses Android's system `AlarmManager` (with `setAlarmClock`) and `NotificationReceiver` so daily practice notifications reliably fire even when the app is closed, suspended, or device is locked.
* **Deep Linking (`lexis://review`):** Tapping notifications takes you directly into your active micro-review session.
* **Custom Status Bar Monogram:** Custom white status bar icon matching the app's clean `L` brand monogram.

### ⚡ Zero-Typing Instant Hydration
* Enter or paste any word to instantly auto-hydrate definitions, IPA pronunciation, context sentences, domain tags, and etymological hints.

### 💻 Multi-Substrate Interfaces
* **Mobile PWA Dashboard (`pwa_dashboard.html`):** Fluid touch drag physics, card flip animations, and offline service worker.
* **Terminal CLI (`cli.py`):** Fast keyboard-driven capture (`lexis add <word>`), status inspection (`lexis status`), and 30-second reviews (`lexis review`).
* **Edge Daemon (`daemon.py`):** Headless background daemon for spaced repetition audits and curiosity notification dispatch.

---

## 📂 Project Structure

```text
axioma-lexis/
├── android/                   # Native Android Studio project (Kotlin)
│   ├── app/
│   │   ├── src/main/AndroidManifest.xml
│   │   ├── src/main/java/com/axioma/lexis/
│   │   │   ├── MainActivity.kt        # Fullscreen webview & native bridge
│   │   │   └── NotificationReceiver.kt# AlarmManager background receiver
│   │   ├── src/main/res/drawable/     # Vector icons & drawables
│   │   └── src/main/assets/           # Bundled offline HTML/PWA assets
│   ├── build.gradle
│   └── gradlew
├── core.py                    # LexisCoreEngine (session management, hydration, undo)
├── srs_engine.py              # Humane Fibonacci tier intervals & rating transitions
├── types.py                   # Data models (WordCard, MicroSession, CuriosityNotification)
├── hydrator.py                # Dictionary hydration & contextual definitions
├── enclave.py                 # Self-healing deck schema validation & corruption recovery
├── phenomenology.py           # Dwell patience timer & cognitive flow accounting
├── server.py                  # Local HTTP server & REST API (port 8090)
├── cli.py                     # Terminal CLI interface
├── daemon.py                  # Edge background scheduling daemon
├── pwa_dashboard.html         # Single-file PWA client & dashboard
├── sw.js                      # Service worker for offline caching
├── manifest.json              # Web app manifest
└── test_axioma_lexis_g2.py    # Comprehensive verification test suite
```

---

## 🚀 Getting Started

### 1. Run the Local Web Server
```bash
python3 server.py
```
Open **`http://localhost:8090`** in your browser to access the PWA dashboard.

### 2. Use the Terminal CLI
```bash
# Capture a word with automatic hydration
python3 -m axioma_lexis.cli add tenacious

# Check deck tier distribution and due counts
python3 -m axioma_lexis.cli status

# Start a quick 30-second micro-review in terminal
python3 -m axioma_lexis.cli review
```

### 3. Build & Run the Android App
```bash
# Build the signed release APK
./android/gradlew -p android assembleRelease

# Install directly to a connected Android device
adb install -r android/app/build/outputs/apk/release/app-release.apk
```

---

## 🧪 Testing

Run the full automated verification test suite:

```bash
python3 -m unittest test_axioma_lexis_g2.py
```

---

## 📄 License
MIT License.

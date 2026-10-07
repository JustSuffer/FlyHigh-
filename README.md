# 🏐 FlyHigh! - 3D Arcade Volleyball Game (3v3 Edition)

**FlyHigh!**, modern arcade anime voleybol tarzında tasarlanmış; dinamik, akıcı ve yüksek tempolu bir 3D voleybol oyunudur.

Hem **klavye/fare** hem de **joystick / gamepad (Xbox, PlayStation, Logitech vb.)** ile sorunsuz oynanabilir. Modüler Python & Raylib mimarisi sayesinde ultra-komplike olmadan her türlü yeni mekaniğe ve geliştirmeye esneklik sağlar. Tek bir komut veya `.bat` dosyası ile bağımsız Windows `.exe` dosyası olarak paketlenebilir.

---

## 🌟 Yeni ve Öne Çıkan Özellikler (v1.2 Güncellemesi)

1. **3v3 Takım Maçları:**
   - 1v1 yerine gerçekçi **3 vs 3** takım formatı:
     - **Takımımız (3 Kişi):** Kaptan (Siz / #5), Pasör (AI Teammate #2), Smaçör/Blokör (AI Teammate #4).
     - **Rakip Takım (3 Kişi):** Smaçör Kaptan (#1), Pasör (#3), Libero/Defans (#6).
   - **Oyuncu Önceliği Kuralı (Player Priority):** Top size yakın düştüğünde takım arkadaşlarınız topu çalmaz, sizin manşet/pas/smaç vurmanız için alan açar!
2. **Modern Anime Chibi Karakter Tasarımı:**
   - Kutu/dikdörtgen modeller yerine; gümüş/beyaz dikenli anime saçlı, badem gözlü, sevimli yüz hatlarına sahip şık sporcu modeli.
   - **Yüzen Küresel Eller (Chibi Arcade Style):** Manşette birbirine kenetlenen, pas kaldırırken baş üstünde toplanan, smaç anında ateşlenen dinamik küre eller.
   - Beyaz kolsuz voleybol forması (#5 numara), turkuaz şort, siyah dizlikler ve mor boğazlı lacivert spor ayakkabılar.
3. **Tatlı ve Modern Arcade Ana Menü:**
   - Arkada dönen 3D stadyum kamerası, dinamik buton vurguları (hover), zorluk ayarı (Kolay / Normal / Zor), tuş rehberi modal penceresi ve ses açma/kapama.
4. **Düzeltilmiş ve Akıcı Yön Kontrolleri:**
   - `D` tuşu ve sağ analog çubuk artık ekranda doğrudan **SAĞA**, `A` tuşu ve sol analog çubuk doğrudan **SOLA** hareket eder.
5. **Arcade Vuruş Bildirimleri & Titreşim:**
   - Başarılı manşette `"NICE DIG!"`, pasa kalkınca `"PERFECT SET!"`, sert smaçta `"BOOM SPIKE!!"` dinamik görsel popupları ve Gamepad titreşim (rumble) desteği.
6. **Derinlik Algısı ve İniş Göstergesi (Landing Reticle):**
   - 3D sahada topun düşeceği yeri tam kestirebilmek için zeminde dinamik gölge ve iniş anına doğru daralan hedef halkası.
7. **Tek Tıkla `.exe` Derleme:**
   - `build_exe.bat` ile bağımsız `FlyHigh_Volleyball.exe` üretilir.

---

## 🎮 Kontroller (Controls)

| Aksiyon | Klavye & Fare | Joystick / Gamepad (Xbox / PS) |
| :--- | :--- | :--- |
| **Sağa Git** | `D` / Sağ Ok Tuşu | **Sol Analog Sağa** / D-Pad Sağ |
| **Sola Git** | `A` / Sol Ok Tuşu | **Sol Analog Sola** / D-Pad Sol |
| **İleri Git (Fileye)** | `W` / Yukarı Ok | **Sol Analog Yukarı** / D-Pad Yukarı |
| **Geri Çekil** | `S` / Aşağı Ok | **Sol Analog Aşağı** / D-Pad Aşağı |
| **Hedef Alma (Nişan)** | Yön Tuşları / Mouse | **Sağ Analog Çubuk** |
| **Sıçrama / Smaç** | `Boşluk (SPACE)` | **(A)** / Çarpı (Cross) |
| **Servis Fırlat (Toss)** | `Boşluk (SPACE)` veya `J` | **(A)** veya **(X)** |
| **Manşet (1. Vuruş)** | `J` / Sol Tık / `Z` | **(X)** / Kare (Square) |
| **Pas (2. Vuruş)** | `K` / Sağ Tık / `X` | **(Y)** / Üçgen (Triangle) |
| **Smaç Vuruşu (Havada)** | `Boşluk (SPACE)` veya `L` | **(A)** veya **(B)** |
| **Plonjon (Kurtarma)** | `Sol Shift` veya `C` | **(RB)** / R1 veya **(B)** |
| **Kamera Değiştirme** | `TAB` veya `V` | **(VIEW / BACK)** |
| **Menü / Duraklatma** | `ESC` veya `P` | **(START / MENU)** |

---

## 🚀 Çalıştırma Yöntemleri

### 1. Hazır `.exe` Dosyasını Başlatma
Doğrudan derlenmiş bağımsız yürütülebilir dosyaya çift tıklayabilirsiniz:
📁 `dist\FlyHigh_Volleyball\FlyHigh_Volleyball.exe`

### 2. Python ile Çalıştırma
Klasör içindeki **`run_game.bat`** dosyasına çift tıklayabilir veya terminalden:
```bash
python main.py
```

### 3. Yeni `.exe` Derleme
Kod üzerinde değişiklik yaptıktan sonra yeni `.exe` üretmek için:
- **`build_exe.bat`** dosyasına çift tıklamanız yeterlidir.

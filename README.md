# 🏐 FlyHigh! - 3D Arcade Volleyball Game

**FlyHigh!**, popüler arcade voleybol oyunu *"Just Volleyball"* tarzında tasarlanmış; sade, akıcı ve yüksek tempolu bir 3D voleybol oyunudur.

Hem **klavye/fare** hem de **joystick / gamepad (Xbox, PlayStation, Logitech vb.)** ile sorunsuz oynanabilir. Modüler Python & Raylib mimarisi sayesinde ultra-komplike olmadan her türlü yeni mekaniğe ve geliştirmeye esneklik sağlar. Tek bir komut veya `.bat` dosyası ile bağımsız Windows `.exe` dosyası olarak paketlenebilir.

---

## 🌟 Öne Çıkan Özellikler

1. **"Just Volleyball" Tarzı Düşük Poligonlu (Low-Poly) 3D Tasarım:**
   - Uluslararası standartlarda nizami saha (18m x 9m), file, antenler ve seyirci tribünleri.
   - Prosedürel animasyonlu 3D karakterler (Koşma, manşet pozisyonu, pas kaldırma, smaç vuruşu, plonjon, kutlama).
2. **Derinlik Algısı ve İniş Göstergesi (Landing Reticle):**
   - 3D voleybol oyunlarında topun düşeceği yeri kestirebilmek için topun tam altına düşen zemin gölgesi ve iniş anına doğru küçülen **tahmini iniş hedef halkası** (Arcade Prediction Ring).
3. **Gerçek Voleybol Rallisi & 3 Vuruş Kuralı:**
   - **Servis:** Topu havaya atma (Toss) ve ardından smaç veya plase servis ile karşı sahaya gönderme.
   - **Manşet (Bump / Dig):** Gelen topu yumuşatarak pasör bölgesine kaldırma.
   - **Pas (Set):** Smaçörün vurması için file üzerine yükseltme.
   - **Smaç (Spike / Attack):** Havada sıçrayıp rakip sahanın boş köşesine sert hücum vurma.
   - **Plonjon (Dive):** Yere yakın topları kurtarmak için öne doğru kayma.
   - 3 vuruş sınırlaması, file teması, aut / çizgi içi kontrolleri ve otomatik skor hakemi.
4. **Çift Kontrol Desteği (Klavye & Joystick / Gamepad):**
   - Gamepad veya klavyeye dokunulduğunda anında algılama ve arayüz tuş ipuçlarını dinamik güncelleme.
   - Gamepad titreşim (rumble) desteği (Smaçlarda ve sayılarda hissedilir geri bildirim).
5. **Dinamik 3D Kamera:**
   - Oyuncu arkasından dinamik takip kamerası, TV canlı yayın yan saha kamerası ve yüksek taktik kamera modları (`TAB` veya Gamepad `BACK` tuşu ile geçiş).
6. **Sıfır Harici Dosya Bağımlılığı ile Ses Motoru:**
   - Hakem düdüğü, sert smaç çarpması, manşet sesi, zemin sekmesi ve taraftar tezahüratları prosedürel olarak Python standard kütüphanesiyle otomatik sentezlenir.
7. **Tek Tıkla `.exe` Derleme:**
   - PyInstaller ile tüm bağımlılıklar paketlenmiş `FlyHigh_Volleyball.exe` üretilir.

---

## 🎮 Kontroller (Controls)

| Aksiyon | Klavye & Fare | Gamepad / Joystick (Xbox / PS) |
| :--- | :--- | :--- |
| **Hareket** | `W`, `A`, `S`, `D` veya Yön Tuşları | **Sol Analog Çubuk** / D-Pad |
| **Hedef Alma (Nişan)** | Yön Tuşları / Mouse | **Sağ Analog Çubuk** |
| **Sıçrama / Smaç** | `Boşluk (SPACE)` | **(A)** / Çarpı (Cross) |
| **Servis Atışı (Toss)** | `Boşluk (SPACE)` veya `J` | **(A)** veya **(X)** |
| **Manşet (Karşılama)** | `J` / Fare Sol Tık / `Z` | **(X)** / Kare (Square) |
| **Pas (Havaya Kaldırma)** | `K` / Fare Sağ Tık / `X` | **(Y)** / Üçgen (Triangle) |
| **Smaç Vuruşu (Havada)** | `Boşluk (SPACE)` veya `L` | **(A)** veya **(B)** |
| **Plonjon (Kurtarma)** | `Sol Shift` veya `C` | **(RB)** / R1 veya **(B)** |
| **Kamera Değiştirme** | `TAB` veya `V` | **(VIEW / BACK)** |
| **Duraklatma (Pause)** | `ESC` veya `P` | **(START / MENU)** |

---

## 🚀 Hızlı Başlangıç

### 1. Python ile Doğrudan Çalıştırma
Projeyi indirdikten sonra klasör içinde:
```bash
# Bağımlılıkları yükleyin
python -m pip install -r requirements.txt

# Oyunu başlatın
python main.py
```
*(veya doğrudan **`run_game.bat`** dosyasına çift tıklayın).*

---

### 2. Bağımsız `.exe` Oluşturma
Herhangi bir Python kurulumuna ihtiyaç duymadan arkadaşlarınızla paylaşabileceğiniz `.exe` oluşturmak için:

1. **`build_exe.bat`** dosyasına çift tıklayın.
2. Derleme tamamlandığında dosyanız hazır olacaktır:
   ```
   dist\FlyHigh_Volleyball\FlyHigh_Volleyball.exe
   ```

---

## 🛠️ Mimari ve Esneklik (Kod Özelleştirme)

Kod yapısı sade ve modüler tutulmuştur. İhtiyacınıza göre kolayca değiştirebilirsiniz:

- `constants.py`: Saha ölçüleri, yerçekimi ivmesi (`GRAVITY`), oyuncu hızı (`PLAYER_SPEED`), renkler ve puan hedefleri.
- `ball.py`: Top fiziği, zıplama katsayısı, yere düşme tahmin hesabı (`update_prediction`) ve file çarpışması.
- `character.py`: 3D oyuncu modeli, uzuv parçaları, forma renkleri ve prosedürel koşma/smaç animasyonları.
- `ai_controller.py`: Rakip bot zekası, tepki süreleri ve hücum taktikleri (Kolay, Orta, Zor seviyeleri).
- `input_manager.py`: Klavye ve Gamepad girişlerinin haritalanması ve ölü bölge (deadzone) ayarları.
- `court.py`: 3D salon ve voleybol sahası çizimleri.
- `match_manager.py`: Sayı kazanma kuralları, servis rotasyonu ve ralli durumları.
- `ui_renderer.py`: Skor tabelası, vuruş sayacı (1/3, 2/3, 3/3) ve durum bildirimleri.

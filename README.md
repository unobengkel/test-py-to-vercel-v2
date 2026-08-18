```markdown
# KameraTamu Middleware API (Vercel + FastAPI)

Repositori ini berisi server *middleware* berbasis **FastAPI** yang berjalan secara *serverless* di **Vercel**. Server ini bertugas untuk menerima kiriman gambar dari perangkat kamera (seperti ESP32-CAM atau Web Simulator), memprosesnya menggunakan AI Filter, lalu menyimpan hasilnya ke **Supabase Storage** dan **Database**.

---

## 📁 Struktur Projek

```text
test-py-to-vercel-v2/
├── api/
│   └── index.py               # Aplikasi utama FastAPI (Serverless Function)
├── tool_test/                 # Peralatan untuk pengujian lokal/client
│   ├── app.py                 # Skrip pengujian Python lokal
│   ├── esp32_web_simulator.html # Simulator UI berbasis HTML + Tailwind
│   └── test_photo.jpg         # Gambar sampel untuk testing
├── requirements.txt           # Dependensi pustaka Python
├── vercel.json                # Konfigurasi routing & CORS untuk Vercel
└── README.md

```

---

## 🛠️ Fitur Utama

* **API Endpoint**: `POST /upload-image/{slug}` untuk menerima kiriman gambar multipart/form-data.


* **Integrasi Supabase 1**: Mengambil *event_id*, *filter settings*, dan *capture settings* berdasarkan `slug` event.


* **Proses Filter AI**: Mengirim foto ke server AI `kameratamu.com` untuk diberi pemrosesan filter.


* **Integrasi Supabase 2**: Menyimpan gambar hasil akhir ke Supabase Storage (bucket `photos`) dan mencatat log transaksi ke database (`photos_data`).


* **Serverless Ready**: Dikonfigurasi penuh untuk runtime Vercel Python.

---

## 🚀 Cara Deploy ke Vercel

1. **Fork / Push** repositori ini ke akun GitHub Anda.
2. Buka dashboard [Vercel](https://vercel.com) dan pilih **Add New... > Project**.
3. Import repositori `test-py-to-vercel-v2`.
4. Vercel akan otomatis mendeteksi konfigurasi `vercel.json` dan folder `api/index.py`. Klik **Deploy**.

---

## 🧪 Cara Pengujian

Anda dapat melakukan pengujian fungsi endpoint mengunggah gambar dengan dua metode yang tersedia di folder `tool_test/`:

### 1. Menggunakan Web Simulator (`esp32_web_simulator.html`)

1. Buka berkas `tool_test/esp32_web_simulator.html` langsung di browser Anda.
2. Masukkan URL server Vercel Anda (misal: `https://test-py-to-vercel-v2.vercel.app`).
3. Masukkan **Event Slug** (contoh: `kamera-disposable`).


4. Pilih file gambar sampel, lalu klik **Simulasi Jepret & Upload**.

### 2. Menggunakan Skrip Python (`app.py`)

Jalankan perintah berikut di terminal komputer lokal Anda:

```bash
cd tool_test
python app.py

```

---

## 📋 Prasyarat Pustaka

Pustaka yang diinstal oleh Vercel secara otomatis (didefinisikan di `requirements.txt`):

* `fastapi`
* `requests`
* `python-multipart`

```

---

### Cara Memasukkan ke GitHub

1. Buka repositori **`test-py-to-vercel-v2`** di GitHub.
2. Klik berkas **`README.md`**, lalu pilih icon **pensil (Edit)**.
3. Salin dan tempel (paste) seluruh teks Markdown di atas.
4. Klik **Commit changes...**.

```

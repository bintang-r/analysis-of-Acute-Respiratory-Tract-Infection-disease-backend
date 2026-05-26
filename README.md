# Analisis Penyakit ISPA - Backend API

Backend API for the ISPA Expert System, built with Django and Django REST Framework.

## Prerequisites
- Python 3.12+

## Cara Menjalankan (How to Run)

1. Buka terminal dan masuk ke folder backend:
   ```bash
   cd analisis-penyakit-ispa-backend
   ```

2. Aktifkan Virtual Environment:
   - **Windows (Command Prompt / PowerShell):**
     ```bash
     .\venv\Scripts\activate
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. Jalankan Server Django:
   ```bash
   python manage.py runserver
   ```
   
   Server akan berjalan di `http://localhost:8000/`.

## Catatan Tambahan
- Database menggunakan **SQLite** secara default agar mudah dijalankan. Jika ingin menggunakan PostgreSQL, ubah konfigurasi `DATABASES` di file `backend/settings.py`.
- Data default (25 gejala, 7 penyakit, 30 rules CF, 3 pakar) sudah digenerate.
- Terdapat akun admin default dengan username `admin` dan password `admin`.

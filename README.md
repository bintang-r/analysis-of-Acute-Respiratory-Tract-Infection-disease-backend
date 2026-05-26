# 🫁 Sistem Pakar Diagnosis ISPA — Backend

> **Django REST Framework** · **PostgreSQL** · **Forward Chaining + Certainty Factor (MYCIN)**

Backend ini adalah **inference engine** untuk sistem pakar diagnosis awal Infeksi Saluran Pernapasan Akut (ISPA). Menggabungkan tiga metode: *Knowledge Acquisition* (dari dataset), *Forward Chaining* (filter kandidat penyakit), dan *Certainty Factor* MYCIN (hitung tingkat keyakinan diagnosis).

---

## Daftar Isi

- [Tech Stack](#tech-stack)
- [Struktur Direktori](#struktur-direktori)
- [Instalasi & Setup](#instalasi--setup)
- [Environment Variables](#environment-variables)
- [Menjalankan Server](#menjalankan-server)
- [API Specification](#api-specification)
  - [Authentication](#authentication)
  - [Consultations](#consultations)
  - [Symptoms](#symptoms)
  - [Diseases](#diseases)
  - [Rules & Training](#rules--training)
  - [Certainty Factors](#certainty-factors)
  - [Dataset](#dataset)
  - [Statistics](#statistics)
  - [Admin](#admin)
  - [Chat](#chat)
  - [Testimonials](#testimonials)
- [Response Format](#response-format)
- [Algoritma Diagnosis](#algoritma-diagnosis)
- [Menjalankan Training Ulang](#menjalankan-training-ulang)

---

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Language | Python 3.11 |
| Framework | Django 5.x |
| API | Django REST Framework 3.x |
| Auth | djangorestframework-simplejwt |
| Database | PostgreSQL 15 |
| ORM | Django ORM |
| Inference | Custom Python (Forward Chaining + CF MYCIN) |

---

## Struktur Direktori

```
analisis-penyakit-ispa-backend/
├── backend/
│   ├── settings.py          # Konfigurasi utama Django
│   └── urls.py              # URL routing utama
├── apps/
│   ├── authentication/      # User, register, login, profile
│   │   ├── models.py        # Custom User model (role: admin/user)
│   │   ├── serializers.py
│   │   └── views.py         # RegisterView, ProfileView, AdminUserListView
│   ├── consultations/       # Konsultasi pasien
│   │   ├── models.py        # Consultation, ConsultationDetail, Testimonial, Message
│   │   ├── serializers.py   # Logic trigger DiagnosisService
│   │   └── views.py         # ConsultationViewSet, StatisticsView, ChatView
│   ├── diseases/            # Katalog penyakit
│   │   └── models.py        # Disease (name, code, description, treatment_solutions)
│   ├── symptoms/            # Katalog gejala
│   │   └── models.py        # Symptom (name, code)
│   ├── rules/               # Knowledge base & inference engine
│   │   ├── models.py        # Rule, RuleSymptom, CertaintyFactor, DatasetRow
│   │   ├── services.py      # DiagnosisService (FC + CF) + recalculate_rules_and_cf()
│   │   └── views.py         # RuleViewSet, TrainSystemView, CertaintyFactorMatrixView
│   └── experts/             # Data pakar / dokter
├── manage.py
└── requirements.txt
```

---

## Instalasi & Setup

```bash
# 1. Clone repo
git clone <repository-url>
cd analisis-penyakit-ispa-backend

# 2. Buat virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Buat file .env (lihat bagian Environment Variables)

# 5. Jalankan migrasi
python manage.py migrate

# 6. Buat superuser / admin
python manage.py createsuperuser

# 7. (Opsional) Import dataset & training awal
python manage.py shell
>>> from apps.rules.services import recalculate_rules_and_cf
>>> recalculate_rules_and_cf()
```

---

## Environment Variables

Buat file `.env` di root direktori backend:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

# Database PostgreSQL
DB_NAME=ispa_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Media files
MEDIA_URL=/media/
MEDIA_ROOT=media/

# CORS (sesuaikan dengan URL frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Menjalankan Server

```bash
python manage.py runserver
# Server berjalan di http://localhost:8000
```

---

## API Specification

> **Base URL:** `http://localhost:8000/api/`
>
> **Format:** JSON
>
> **Auth Header:** `Authorization: Bearer <access_token>`

---

### Authentication

#### `POST /api/auth/register/`

Registrasi pengguna baru.

**Permission:** AllowAny

**Request Body:**
```json
{
  "username": "budi123",
  "email": "budi@email.com",
  "password": "secret123",
  "full_name": "Budi Santoso"
}
```

**Response `201 Created`:**
```json
{
  "id": 5,
  "username": "budi123",
  "email": "budi@email.com",
  "full_name": "Budi Santoso",
  "role": "user"
}
```

---

#### `POST /api/auth/login/`

Login dan dapatkan JWT token.

**Permission:** AllowAny

**Request Body:**
```json
{
  "username": "budi123",
  "password": "secret123"
}
```

**Response `200 OK`:**
```json
{
  "access": "eyJ0eXAi...",
  "refresh": "eyJ0eXAi..."
}
```

---

#### `POST /api/auth/refresh/`

Refresh access token yang sudah expired.

**Request Body:**
```json
{ "refresh": "eyJ0eXAi..." }
```

**Response `200 OK`:**
```json
{ "access": "eyJ0eXAi..." }
```

---

#### `GET /api/auth/profile/`
#### `PATCH /api/auth/profile/`

Ambil atau update profil pengguna yang sedang login.

**Permission:** IsAuthenticated

**Response `200 OK`:**
```json
{
  "id": 5,
  "username": "budi123",
  "email": "budi@email.com",
  "full_name": "Budi Santoso",
  "role": "user",
  "profile_picture": "http://localhost:8000/media/profiles/foto.jpg"
}
```

---

### Consultations

#### `POST /api/consultations/`

Buat konsultasi baru. Sistem otomatis menjalankan Forward Chaining + CF dan menyimpan hasil diagnosis.

**Permission:** IsAuthenticated

**Request Body:**
```json
{
  "age": 28,
  "details": [
    { "symptom": 3, "user_cf": 0.8 },
    { "symptom": 7, "user_cf": 0.6 },
    { "symptom": 1, "user_cf": 0.4 }
  ]
}
```

> `symptom` adalah ID dari tabel Symptom. `user_cf` adalah nilai keyakinan pasien (0.0 – 1.0).

**Response `201 Created`:**
```json
{
  "id": 12,
  "consultation_date": "2025-05-27T04:30:00Z",
  "final_diagnosis": "Faringitis",
  "confidence_result": 86.50,
  "age": 28,
  "diagnosis_results": [
    {
      "disease": "Faringitis",
      "percentage": 86.50,
      "matched_symptoms": ["Demam", "Nyeri tenggorokan", "Batuk kering"],
      "calculation_trace": [
        {
          "symptom": "Demam",
          "user_cf": 0.8,
          "expert_cf": 0.75,
          "cf_current": 0.600,
          "old_combined": 0.0,
          "new_combined": 0.600,
          "formula": "CF(Demam) = 0.8 * 0.75 = 0.600",
          "combine_formula": "CF Gabungan Awal = 0.600"
        }
      ],
      "recommendation": "Istirahat, minum banyak air, berkumur air garam hangat..."
    }
  ],
  "treatment_solutions": "...",
  "recovery_steps": "...",
  "description": "..."
}
```

---

#### `GET /api/consultations/`

Ambil daftar konsultasi pengguna yang login. Admin melihat semua konsultasi.

**Permission:** IsAuthenticated

**Response `200 OK`:**
```json
[
  {
    "id": 12,
    "consultation_date": "2025-05-27T04:30:00Z",
    "final_diagnosis": "Faringitis",
    "confidence_result": 86.50,
    "age": 28,
    "diagnosis_results": [...]
  }
]
```

---

#### `GET /api/consultations/{id}/`

Detail satu konsultasi (re-kalkulasi CF dilakukan saat ini).

---

#### `GET /api/consultations/{id}/matching_rows/`

Ambil baris-baris dataset yang paling mirip dengan konsultasi ini (untuk validasi Knowledge Acquisition).

**Response `200 OK`:**
```json
{
  "total_cases_in_dataset": 120,
  "matches": [
    {
      "row_id": 45,
      "age": 27,
      "diagnosis": "Faringitis",
      "matched_symptoms": ["Demam", "Nyeri tenggorokan"],
      "match_count": 2
    }
  ]
}
```

---

### Symptoms

#### `GET /api/symptoms/`

Ambil daftar seluruh gejala ISPA.

**Permission:** IsAuthenticated

**Response `200 OK`:**
```json
[
  { "id": 1, "code": "S01", "name": "Batuk kering" },
  { "id": 2, "code": "S02", "name": "Batuk berdahak" },
  { "id": 3, "code": "S03", "name": "Demam" },
  ...
  { "id": 16, "code": "S16", "name": "Nyeri saat menelan" }
]
```

---

#### `POST /api/symptoms/` · `PATCH /api/symptoms/{id}/` · `DELETE /api/symptoms/{id}/`

CRUD gejala (admin only).

---

### Diseases

#### `GET /api/diseases/`

Ambil katalog penyakit ISPA.

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "code": "D01",
    "name": "Rhinitis",
    "description": "Peradangan mukosa hidung...",
    "treatment_solutions": "Istirahat, antihistamin...",
    "recovery_steps": "1. Istirahat cukup..."
  }
]
```

---

#### `POST /api/diseases/` · `PATCH /api/diseases/{id}/` · `DELETE /api/diseases/{id}/`

CRUD penyakit (admin only).

---

### Rules & Training

#### `GET /api/rules/`

Lihat semua aturan inferensi (Rule beserta daftar gejalanya).

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "code": "R01",
    "disease": 1,
    "rule_symptoms": [
      { "symptom": 1 },
      { "symptom": 3 },
      { "symptom": 4 }
    ]
  }
]
```

---

#### `GET /api/rules/train/`

Trigger ulang training: membaca seluruh dataset, hitung ulang `expert_cf`, bangun ulang Rule, RuleSymptom, dan CertaintyFactor. **Operasi ini bersifat destruktif** (hapus semua data lama terlebih dahulu).

**Permission:** IsAuthenticated (Admin)

**Response `200 OK`:**
```json
{
  "status": "success",
  "message": "Training selesai. Rules dan CF berhasil diperbarui."
}
```

---

#### `GET /api/rules/matrix/`

Ambil matriks CF lengkap (penyakit × gejala). Berguna untuk visualisasi heatmap di frontend admin.

**Response `200 OK`:**
```json
{
  "symptoms": ["Batuk kering", "Demam", ...],
  "matrix": {
    "Rhinitis": { "Batuk kering": 0.45, "Demam": 0.30, ... },
    "Faringitis": { "Batuk kering": 0.80, "Demam": 0.75, ... }
  }
}
```

---

### Certainty Factors

#### `GET /api/certainty-factors/`

Ambil seluruh nilai CF per kombinasi penyakit–gejala.

**Response `200 OK`:**
```json
[
  { "id": 1, "disease": 7, "symptom": 3, "expert_cf": 0.900 },
  { "id": 2, "disease": 7, "symptom": 6, "expert_cf": 0.950 }
]
```

---

### Dataset

#### `GET /api/rules/dataset/`

Ambil data rekam medis yang digunakan untuk training (pagination tersedia).

**Query Params:** `?page=1&page_size=50`

**Response `200 OK`:**
```json
{
  "count": 5000,
  "next": "http://localhost:8000/api/rules/dataset/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "age": 25,
      "diagnosis": "Faringitis",
      "batuk_kering": 1,
      "batuk_berdahak": 0,
      "demam": 1,
      "nyeri_tenggorokan": 1,
      ...
    }
  ]
}
```

---

#### `POST /api/rules/dataset/`

Tambah satu baris data baru ke dataset.

#### `DELETE /api/rules/dataset/{id}/`

Hapus satu baris data dari dataset.

---

### Statistics

#### `GET /api/statistics/`

Statistik global aplikasi (dapat diakses tanpa login).

**Permission:** AllowAny

**Response `200 OK`:**
```json
{
  "total_patients": 128,
  "total_consultations": 345,
  "avg_confidence": 72.43,
  "disease_distribution": [
    { "name": "Faringitis", "cases": 95 },
    { "name": "Bronkitis", "cases": 72 }
  ],
  "top_symptoms": [
    { "name": "Demam", "count": 280 },
    { "name": "Batuk kering", "count": 230 }
  ],
  "accuracy_trend": [
    { "month": "Jan 2025", "accuracy": 68.5 },
    { "month": "Feb 2025", "accuracy": 71.2 }
  ],
  "consultation_trend": [
    { "month": "Jan 2025", "total": 30 }
  ],
  "recent_avatars": [
    { "name": "Budi Santoso", "avatar": "http://localhost:8000/media/..." }
  ]
}
```

---

### Admin

#### `GET /api/admin/users/`

Ambil semua pengguna reguler beserta riwayat konsultasi lengkap (termasuk `diagnosis_results` + `calculation_trace`). **Admin only.**

**Permission:** IsAuthenticated (role = admin)

**Response `200 OK`:**
```json
[
  {
    "id": 5,
    "username": "budi123",
    "email": "budi@email.com",
    "full_name": "Budi Santoso",
    "date_joined": "2025-01-15T08:00:00Z",
    "consultations_count": 3,
    "consultations": [
      {
        "id": 12,
        "consultation_date": "2025-05-27T04:30:00Z",
        "final_diagnosis": "Faringitis",
        "confidence_result": 86.50,
        "age": 28,
        "active_symptoms": ["S01", "S03", "S07"],
        "symptom_cfs": { "S01": 0.4, "S03": 0.8, "S07": 0.6 },
        "diagnosis_results": [
          {
            "disease": "Faringitis",
            "percentage": 86.50,
            "matched_symptoms": [...],
            "calculation_trace": [...]
          }
        ]
      }
    ]
  }
]
```

---

### Chat

#### `GET /api/chats/`

Ambil riwayat pesan antara pengguna dan admin.

**Admin:** tambahkan `?user_id=<id>` untuk melihat chat dengan user tertentu.

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "sender": 5,
    "sender_name": "Budi Santoso",
    "sender_role": "user",
    "receiver": 1,
    "content": "Dok, saya mau tanya...",
    "timestamp": "2025-05-27T04:30:00Z",
    "is_read": true
  }
]
```

---

#### `POST /api/chats/`

Kirim pesan baru.

**Request Body (user):**
```json
{ "content": "Saya mau bertanya..." }
```

**Request Body (admin):**
```json
{ "content": "Baik, silakan...", "receiver_id": 5 }
```

---

#### `GET /api/chats/contacts/`

Ambil daftar kontak chat (admin only) — semua pengguna yang pernah chat.

---

### Testimonials

#### `GET /api/testimonials/`

Ambil semua testimonial pengguna.

**Permission:** AllowAny

#### `POST /api/testimonials/`

Buat testimonial baru. Hanya bisa jika user sudah pernah konsultasi dan belum pernah membuat testimonial sebelumnya.

**Permission:** IsAuthenticated

---

## Response Format

### Success

```json
{
  "id": 1,
  "field": "value",
  ...
}
```

### Error

```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "field_name": ["This field is required."]
}
```

| HTTP Status | Keterangan |
|-------------|------------|
| `200 OK` | Request berhasil |
| `201 Created` | Resource berhasil dibuat |
| `400 Bad Request` | Data request tidak valid |
| `401 Unauthorized` | Token tidak ada / expired |
| `403 Forbidden` | Akses ditolak (bukan admin) |
| `404 Not Found` | Resource tidak ditemukan |
| `500 Internal Server Error` | Error di sisi server |

---

## Algoritma Diagnosis

Tiga tahap yang dijalankan setiap kali `POST /api/consultations/` dipanggil:

```
1. Knowledge Acquisition (offline — dijalankan saat training)
   expert_cf(D, S) = jumlah_kasus_D_dengan_gejala_S / total_kasus_D

2. Forward Chaining (filter)
   Penyakit D lolos jika:
   - matched_count >= 2, ATAU
   - match_ratio >= 0.50

3. Certainty Factor MYCIN (per penyakit yang lolos)
   cf_current = user_cf × expert_cf
   cf_combined = cf1 + cf2*(1-cf1)  [jika keduanya positif]
              = cf1 + cf2*(1+cf1)  [jika keduanya negatif]
              = (cf1+cf2)/(1-min(|cf1|,|cf2|))  [tanda berlawanan]
   
   Penalti gejala tidak dipilih: user_cf = -0.3
   Threshold minimal: percentage >= 35%
```

---

## Menjalankan Training Ulang

Setiap kali dataset diubah (tambah/hapus baris), jalankan training ulang agar Rules dan CertaintyFactor terupdate:

```bash
# Via API
GET /api/rules/train/

# Via Django shell
python manage.py shell
>>> from apps.rules.services import recalculate_rules_and_cf
>>> recalculate_rules_and_cf()
```

---

## License

MIT License — lihat file `LICENSE`.

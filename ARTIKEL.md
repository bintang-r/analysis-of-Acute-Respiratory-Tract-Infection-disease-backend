# Sistem Pakar Diagnosis Dini Infeksi Saluran Pernapasan Akut (ISPA)
## Menggunakan Metode *Forward Chaining* + *Certainty Factor* (MYCIN) + *Knowledge Acquisition*

---

> **Cara Menggunakan Artikel Ini**
>
> Artikel ini dirancang agar **interaktif**: di setiap bagian yang memiliki tanda `[Pilihan]`, Anda bisa memilih nilai sesuai kondisi pasien dan mengikuti perhitungan langkah-demi-langkah untuk menghasilkan diagnosis yang **sama persis** dengan yang dihasilkan sistem.

---

## Daftar Isi

1. [Latar Belakang](#1-latar-belakang)
2. [Definisi ISPA dan Klasifikasi Penyakit](#2-definisi-ispa-dan-klasifikasi-penyakit)
3. [Arsitektur Sistem Pakar](#3-arsitektur-sistem-pakar)
4. [Metode 1 – Knowledge Acquisition](#4-metode-1--knowledge-acquisition)
5. [Metode 2 – Forward Chaining](#5-metode-2--forward-chaining)
6. [Metode 3 – Certainty Factor (MYCIN)](#6-metode-3--certainty-factor-mycin)
7. [Walkthrough Perhitungan Lengkap (Contoh Kasus)](#7-walkthrough-perhitungan-lengkap-contoh-kasus)
8. [Ruang Coba Mandiri — Reproduksi Hasil Sendiri](#8-ruang-coba-mandiri--reproduksi-hasil-sendiri)
9. [Threshold, Penalti, dan Keputusan Final](#9-threshold-penalti-dan-keputusan-final)
10. [Referensi Jurnal Ilmiah](#10-referensi-jurnal-ilmiah)

---

## 1. Latar Belakang

Infeksi Saluran Pernapasan Akut (ISPA) adalah penyebab morbiditas dan mortalitas tertinggi di seluruh dunia, terutama pada anak-anak balita dan lansia. Di Indonesia, ISPA selalu masuk dalam 10 besar penyakit terbanyak yang ditangani di Puskesmas setiap tahunnya. Kendala utama penanganan ISPA adalah:

- Keterbatasan tenaga medis spesialis di daerah terpencil.
- Gejala awal yang seringkali mirip antar satu penyakit dengan penyakit lainnya (ambiguitas klinis).
- Keterlambatan diagnosis yang menyebabkan komplikasi serius.

Sistem pakar berbasis komputer hadir sebagai alat bantu pengambilan keputusan (*Clinical Decision Support System*) yang memungkinkan:

1. Diagnosis dini tanpa kehadiran dokter spesialis.
2. Pemberian rekomendasi penanganan awal.
3. Transparansi proses pengambilan keputusan (explainable AI).

---

## 2. Definisi ISPA dan Klasifikasi Penyakit

ISPA diklasifikasikan berdasarkan lokasi infeksi dan tingkat keparahan:

| Kode | Nama Penyakit        | Lokasi                       | Tingkat |
|------|----------------------|------------------------------|---------|
| D01  | Rhinitis             | Rongga hidung                | Ringan  |
| D02  | Sinusitis            | Sinus paranasal              | Ringan  |
| D03  | Faringitis           | Tenggorokan (faring)         | Sedang  |
| D04  | Laringitis           | Laring / pita suara          | Sedang  |
| D05  | Bronkitis            | Bronkus                      | Sedang  |
| D06  | Bronkiolitis         | Bronkiolus (anak <2 th)      | Berat   |
| D07  | Pneumonia            | Parenkim paru                | Berat   |
| D08  | COVID-19 (Ringan)    | Saluran pernapasan atas/bawah| Berat   |
| D09  | Influenza            | Sistem pernapasan menyeluruh | Sedang  |

### Katalog Gejala (S01–S16)

| Kode | Nama Gejala               | Deskripsi Klinis                                     |
|------|---------------------------|------------------------------------------------------|
| S01  | Batuk kering              | Batuk tanpa produksi dahak/mukus                    |
| S02  | Batuk berdahak            | Batuk disertai produksi sputum (lendir/dahak)       |
| S03  | Demam                     | Suhu tubuh ≥ 37,5 °C                                |
| S04  | Pilek                     | Produksi cairan hidung (rhinorrhoea)                |
| S05  | Hidung tersumbat          | Kongesti nasal (nasal congestion)                    |
| S06  | Sesak napas               | Dyspnea – kesulitan bernapas                        |
| S07  | Nyeri tenggorokan         | Sakit/nyeri/radang di area faring                   |
| S08  | Sakit kepala              | Cephalgia (nyeri kepala)                             |
| S09  | Mual/Muntah               | Nausea dan atau emesis                              |
| S10  | Nyeri dada                | Chest pain, terutama saat bernapas                  |
| S11  | Suara serak               | Dysphonia – perubahan kualitas suara                |
| S12  | Kelelahan                 | Fatigue/malaise umum                                |
| S13  | Berkeringat malam         | Night sweats                                        |
| S14  | Nafsu makan turun         | Anoreksia                                           |
| S15  | Hilang penciuman          | Anosmia (hallmark COVID-19)                         |
| S16  | Nyeri saat menelan        | Odynophagia                                         |

---

## 3. Arsitektur Sistem Pakar

```
┌─────────────────────────────────────────────────────────────────┐
│                         SISTEM PAKAR ISPA                       │
├───────────────────────┬─────────────────────────────────────────┤
│    USER INTERFACE     │         INFERENCE ENGINE                │
│  (Next.js / REST API) │  ┌───────────────────────────────────┐  │
│                       │  │  1. Knowledge Acquisition          │  │
│  Pasien memilih       │  │     (Dataset → CF Pakar)           │  │
│  gejala + intensitas  │  ├───────────────────────────────────┤  │
│                       │  │  2. Forward Chaining               │  │
│  user_cf = intensitas │  │     (Filter penyakit kandidat)     │  │
│  yang dipilih         │  ├───────────────────────────────────┤  │
│                       │  │  3. Certainty Factor (MYCIN)       │  │
│                       │  │     (Hitung CF final per penyakit) │  │
│                       │  └───────────────────────────────────┘  │
│                       │              ↓                           │
│                       │     KNOWLEDGE BASE                       │
│                       │  ┌─────────────────────────────────┐    │
│                       │  │  Tabel Rule + RuleSymptom        │    │
│                       │  │  Tabel CertaintyFactor           │    │
│                       │  │  Tabel DatasetRow                │    │
│                       │  └─────────────────────────────────┘    │
└───────────────────────┴─────────────────────────────────────────┘
```

---

## 4. Metode 1 – Knowledge Acquisition

### 4.1 Definisi

*Knowledge Acquisition* (Akuisisi Pengetahuan) adalah proses sistematis mengekstrak, memvalidasi, dan mengodekan pengetahuan dari **pakar domain** (dokter) dan **data historis** (dataset rekam medis) ke dalam basis pengetahuan komputer.

### 4.2 Proses dalam Sistem Ini

Sistem menggunakan dataset dengan `N` baris rekam medis. Setiap baris merepresentasikan satu kasus pasien ISPA yang telah terdiagnosis.

**Langkah Akuisisi:**

```
UNTUK setiap penyakit D:
  1. Hitung total_cases(D) = jumlah baris dengan diagnosis = D
  2. UNTUK setiap gejala S:
       symptom_count(D,S) = jumlah baris D yang memiliki gejala S = 1
       expert_cf(D,S) = symptom_count(D,S) / total_cases(D)
  3. Simpan expert_cf ke tabel CertaintyFactor
  4. Buat Rule: gejala yang expert_cf >= 0.20 masuk ke RuleSymptom
```

### 4.3 Rumus Expert CF

$$
\text{expert\_cf}(D, S) = \frac{\text{jumlah kasus penyakit } D \text{ dengan gejala } S}{\text{total kasus penyakit } D}
$$

**Contoh Konkret:**

Misalkan dari dataset:
- Total kasus **Pneumonia** = 120 baris
- Kasus Pneumonia dengan **Sesak Napas (S06)** = 108 baris

```
expert_cf(Pneumonia, S06) = 108 / 120 = 0.900
```

Artinya: **90% pasien Pneumonia mengalami sesak napas** → nilai CF pakar = 0.9

### 4.4 Ambang Batas Rule

| Rentang expert_cf | Status |
|-------------------|--------|
| ≥ 0.20 | Masuk ke RuleSymptom (digunakan Forward Chaining) |
| > 0 (tapi < 0.20) | Tetap masuk CertaintyFactor (digunakan CF Calc), tidak masuk Rule |
| = 0 | Diabaikan |

---

## 5. Metode 2 – Forward Chaining

### 5.1 Definisi

*Forward Chaining* (Penalaran Maju) adalah strategi inferensi berbasis data (*data-driven*) yang dimulai dari **fakta yang diketahui** (gejala pasien) untuk mencapai **kesimpulan** (diagnosis). Berbeda dengan *Backward Chaining* yang dimulai dari hipotesis.

### 5.2 Algoritma Filter

```python
untuk setiap Rule penyakit D:
    rule_symptom_ids = set gejala dalam rule D
    user_symptom_ids = set gejala yang dipilih pasien (user_cf > 0)
    
    matched_ids    = interseksi(user_symptom_ids, rule_symptom_ids)
    matched_count  = |matched_ids|
    match_ratio    = matched_count / |rule_symptom_ids|
    
    JIKA matched_count >= 2 ATAU match_ratio >= 0.50:
        → penyakit D LOLOS ke tahap CF (masuk kandidat)
    SEBALIKNYA:
        → penyakit D DIBUANG
```

### 5.3 Contoh Filter Forward Chaining

**Input Gejala Pasien:** {S01-Batuk kering, S03-Demam, S07-Nyeri tenggorokan}

| Penyakit | Rule Symptoms | Matched | Count | Ratio | Lolos? |
|----------|--------------|---------|-------|-------|--------|
| Rhinitis | S01, S04, S05 | S01 | 1 | 1/3=33% | ❌ (count<2 & ratio<50%) |
| Faringitis | S01, S03, S07, S16 | S01,S03,S07 | **3** | 3/4=75% | ✅ |
| Bronkitis | S01, S02, S03, S12 | S01,S03 | **2** | 2/4=50% | ✅ |
| Pneumonia | S02, S03, S06, S10, S12 | S03 | 1 | 1/5=20% | ❌ |
| Influenza | S01, S03, S08, S09, S12 | S01,S03 | **2** | 2/5=40% | ✅ (count≥2) |

**Hasil: Faringitis, Bronkitis, dan Influenza lolos ke tahap CF.**

> Dengan filter ini, pneumonia **tidak akan muncul** hanya karena 1 gejala demam — sesuai klinisnya.

---

## 6. Metode 3 – Certainty Factor (MYCIN)

### 6.1 Sejarah dan Konsep

*Certainty Factor* diperkenalkan oleh **Shortliffe & Buchanan (1975)** dalam sistem MYCIN, sistem pakar untuk diagnosis infeksi bakteri. CF merepresentasikan **tingkat kepercayaan** terhadap suatu hipotesis berdasarkan bukti yang ada, menggunakan skala **-1.0 (pasti salah)** hingga **+1.0 (pasti benar)**.

```
CF = 0    → tidak ada keyakinan sama sekali
CF = 0.5  → yakin 50%
CF = 1.0  → yakin penuh / pasti
CF = -1.0 → pasti bukan penyakit ini
```

### 6.2 Nilai User CF (Intensitas Gejala)

Pasien memilih intensitas setiap gejala, yang diterjemahkan ke nilai user_cf:

| Pilihan Pasien | user_cf | Interpretasi |
|----------------|---------|--------------|
| Tidak ada | 0.0 | Gejala tidak ada |
| Sangat ringan | 0.2 | Ada sedikit, hampir tidak terasa |
| Ringan | 0.4 | Terasa ringan, tidak mengganggu |
| Sedang | 0.6 | Cukup terasa, sedikit mengganggu |
| Berat | 0.8 | Sangat terasa, mengganggu aktivitas |
| Sangat berat | 1.0 | Ekstrem, tidak bisa beraktivitas |

> **[Pilihan A]** Gejala tidak dipilih pasien sama sekali → sistem memberi **penalti: user_cf = -0.3**

### 6.3 Rumus CF Current (Per Gejala)

$$
\text{CF}_{\text{current}} = \text{user\_cf} \times \text{expert\_cf}
$$

**Contoh:**
- user_cf(S03-Demam) = 0.6 (sedang)
- expert_cf(Faringitis, S03) = 0.75

```
CF_current = 0.6 × 0.75 = 0.450
```

### 6.4 Rumus Kombinasi CF (MYCIN Formula)

Setelah mendapat CF_current untuk setiap gejala, nilai CF digabungkan secara iteratif menggunakan **formula MYCIN**:

$$
\text{CF}_{\text{combined}} = \begin{cases}
\text{CF}_1 + \text{CF}_2 \times (1 - \text{CF}_1) & \text{jika } \text{CF}_1 \geq 0 \text{ dan } \text{CF}_2 \geq 0 \\
\text{CF}_1 + \text{CF}_2 \times (1 + \text{CF}_1) & \text{jika } \text{CF}_1 < 0 \text{ dan } \text{CF}_2 < 0 \\
\dfrac{\text{CF}_1 + \text{CF}_2}{1 - \min(|\text{CF}_1|, |\text{CF}_2|)} & \text{jika tanda berlawanan}
\end{cases}
$$

**Catatan:** Setelah semua gejala dihitung, CF akhir di-*clamp* ke rentang [-1.0, 1.0] kemudian dikonversi ke persentase:

$$
\text{persentase} = \text{round}(\text{CF\_final} \times 100, 2)
$$

### 6.5 Penalti untuk Gejala Tidak Dipilih

Jika suatu gejala ada dalam knowledge base (expert_cf > 0) tapi **tidak dipilih pasien**:

```python
user_cf = -0.3   # penalti tetap
CF_current = -0.3 × expert_cf   # nilai negatif
```

Ini membuat kombinasi CF menjadi lebih kecil, merefleksikan bahwa ketiadaan gejala penting justru **mengurangi** keyakinan diagnosis.

---

## 7. Walkthrough Perhitungan Lengkap (Contoh Kasus)

### Skenario Kasus

> **Pasien:** Anak usia 8 tahun
> **Gejala yang dipilih:**
> - S01 Batuk kering → **Sedang** (user_cf = 0.6)
> - S03 Demam → **Berat** (user_cf = 0.8)
> - S07 Nyeri tenggorokan → **Sedang** (user_cf = 0.6)

### Step 1 — Knowledge Acquisition (dari dataset)

Misalkan sistem telah menghasilkan expert_cf berikut untuk **Faringitis**:

| Gejala | expert_cf |
|--------|-----------|
| S01 Batuk kering | 0.80 |
| S03 Demam | 0.75 |
| S07 Nyeri tenggorokan | 0.90 |
| S16 Nyeri saat menelan | 0.65 |
| S11 Suara serak | 0.40 |

### Step 2 — Forward Chaining Filter

Rule Faringitis: {S01, S03, S07, S16}
Gejala pasien: {S01, S03, S07}

```
matched_ids = {S01, S03, S07}
matched_count = 3
match_ratio = 3/4 = 0.75 (75%)

Syarat: count >= 2 → TRUE ✅
→ Faringitis LOLOS ke CF
```

### Step 3 — Certainty Factor Calculation

#### Iterasi 1 — Gejala S01 (Batuk Kering)

```
user_cf = 0.6  (Sedang)
expert_cf = 0.80

CF_current = 0.6 × 0.80 = 0.480

Ini gejala PERTAMA → CF_combined = 0.480
```

#### Iterasi 2 — Gejala S03 (Demam)

```
user_cf = 0.8  (Berat)
expert_cf = 0.75

CF_current = 0.8 × 0.75 = 0.600

CF_combined sebelumnya = 0.480 (positif)
CF_current = 0.600 (positif)

→ Gunakan formula: CF1 + CF2 × (1 - CF1)

CF_combined_baru = 0.480 + 0.600 × (1 - 0.480)
                 = 0.480 + 0.600 × 0.520
                 = 0.480 + 0.312
                 = 0.792
```

#### Iterasi 3 — Gejala S07 (Nyeri Tenggorokan)

```
user_cf = 0.6  (Sedang)
expert_cf = 0.90

CF_current = 0.6 × 0.90 = 0.540

CF_combined sebelumnya = 0.792 (positif)
CF_current = 0.540 (positif)

→ Gunakan formula: CF1 + CF2 × (1 - CF1)

CF_combined_baru = 0.792 + 0.540 × (1 - 0.792)
                 = 0.792 + 0.540 × 0.208
                 = 0.792 + 0.112
                 = 0.904
```

#### Iterasi 4 — Gejala S16 (Nyeri Saat Menelan) — TIDAK DIPILIH

```
user_cf = -0.3  (PENALTI — tidak dipilih pasien)
expert_cf = 0.65

CF_current = -0.3 × 0.65 = -0.195

CF_combined sebelumnya = 0.904 (positif)
CF_current = -0.195 (negatif)
→ Tanda BERLAWANAN → Gunakan formula 3

min_abs = min(|0.904|, |-0.195|) = min(0.904, 0.195) = 0.195

CF_combined_baru = (0.904 + (-0.195)) / (1 - 0.195)
                 = 0.709 / 0.805
                 = 0.881
```

#### Iterasi 5 — Gejala S11 (Suara Serak) — TIDAK DIPILIH

```
user_cf = -0.3  (PENALTI)
expert_cf = 0.40

CF_current = -0.3 × 0.40 = -0.120

CF_combined sebelumnya = 0.881 (positif)
CF_current = -0.120 (negatif)
→ Tanda BERLAWANAN

min_abs = min(0.881, 0.120) = 0.120

CF_combined_baru = (0.881 + (-0.120)) / (1 - 0.120)
                 = 0.761 / 0.880
                 = 0.865
```

### Step 4 — Clamp dan Konversi ke Persen

```
CF_final = 0.865
CF_clamped = max(-1.0, min(1.0, 0.865)) = 0.865

Persentase = 0.865 × 100 = 86.50%
```

### Step 5 — Threshold Check

```
Persentase = 86.50%
Threshold minimal = 35%

86.50 >= 35 → TRUE ✅
→ Faringitis MASUK ke hasil diagnosis dengan confidence 86.50%
```

### Hasil Final

```
╔══════════════════════════════════════════╗
║  HASIL DIAGNOSIS SISTEM PAKAR ISPA       ║
╠══════════════════════════════════════════╣
║  Penyakit     : Faringitis               ║
║  Confidence   : 86.50%                   ║
║  Gejala Match : Batuk kering, Demam,     ║
║                 Nyeri tenggorokan        ║
╚══════════════════════════════════════════╝
```

---

## 8. Ruang Coba Mandiri — Reproduksi Hasil Sendiri

Gunakan tabel ini untuk menghitung CF manual. Ganti nilai di kolom `user_cf` sesuai pilihan Anda.

### [Pilihan A] Pilih Gejala dan Intensitas

| No | Gejala | Tidak Ada (0.0) | Ringan (0.4) | Sedang (0.6) | Berat (0.8) | Sangat Berat (1.0) |
|----|--------|-----------------|--------------|--------------|-------------|---------------------|
| 1 | Batuk kering (S01) | ○ | ○ | ○ | ○ | ○ |
| 2 | Batuk berdahak (S02) | ○ | ○ | ○ | ○ | ○ |
| 3 | Demam (S03) | ○ | ○ | ○ | ○ | ○ |
| 4 | Pilek (S04) | ○ | ○ | ○ | ○ | ○ |
| 5 | Hidung tersumbat (S05) | ○ | ○ | ○ | ○ | ○ |
| 6 | Sesak napas (S06) | ○ | ○ | ○ | ○ | ○ |
| 7 | Nyeri tenggorokan (S07) | ○ | ○ | ○ | ○ | ○ |
| 8 | Sakit kepala (S08) | ○ | ○ | ○ | ○ | ○ |
| 9 | Mual/Muntah (S09) | ○ | ○ | ○ | ○ | ○ |
| 10 | Nyeri dada (S10) | ○ | ○ | ○ | ○ | ○ |
| 11 | Suara serak (S11) | ○ | ○ | ○ | ○ | ○ |
| 12 | Kelelahan (S12) | ○ | ○ | ○ | ○ | ○ |
| 13 | Berkeringat malam (S13) | ○ | ○ | ○ | ○ | ○ |
| 14 | Nafsu makan turun (S14) | ○ | ○ | ○ | ○ | ○ |
| 15 | Hilang penciuman (S15) | ○ | ○ | ○ | ○ | ○ |
| 16 | Nyeri saat menelan (S16) | ○ | ○ | ○ | ○ | ○ |

> Gejala yang tidak dipilih (Tidak Ada) akan mendapat penalti **user_cf = -0.3** dalam perhitungan.

### [Pilihan B] Lembar Kerja Perhitungan CF Manual

Setelah memilih gejala, isi tabel berikut untuk setiap penyakit kandidat:

```
Penyakit: ________________________

| # | Gejala | user_cf | expert_cf | CF_current = user_cf × expert_cf | CF_combined |
|---|--------|---------|-----------|----------------------------------|-------------|
| 1 | ...    | ___     | ___       | ___ × ___ = ___                  | CF_init     |
| 2 | ...    | ___     | ___       | ___ × ___ = ___                  | Rumus ↓     |
| 3 | ...    | ___     | ___       | ___ × ___ = ___                  | ...         |

Formula yang digunakan (centang yang sesuai):
  □ Keduanya positif  → CF1 + CF2 × (1 - CF1)
  □ Keduanya negatif  → CF1 + CF2 × (1 + CF1)
  □ Tanda berlawanan  → (CF1 + CF2) / (1 - min(|CF1|, |CF2|))

CF Final = ________
Persentase = CF Final × 100 = ________%
Lolos threshold (≥35%)? □ YA  □ TIDAK
```

---

## 9. Threshold, Penalti, dan Keputusan Final

### Ringkasan Aturan Sistem

| Parameter | Nilai | Alasan |
|-----------|-------|--------|
| Minimum gejala input | 2 gejala | Menghindari diagnosis dari 1 gejala umum |
| Minimum match count (FC) | 2 | Filter penyakit tidak relevan |
| Minimum match ratio (FC) | 50% | Fleksibilitas untuk penyakit dengan banyak gejala |
| Penalti gejala tidak dipilih | user_cf = -0.3 | Memberikan bobot negatif pada ketiadaan gejala penting |
| Threshold minimal CF | 35% | Di bawah ini dianggap tidak cukup yakin |
| Clamp CF | [-1.0, 1.0] | Normalisasi agar tidak melebihi batas probabilitas |

### Interpretasi Hasil Diagnosis

| Rentang Confidence | Interpretasi |
|--------------------|-------------|
| 80% – 100% | Diagnosis sangat kuat, sangat direkomendasikan segera ke dokter |
| 60% – 79% | Diagnosis kuat, dianjurkan ke dokter |
| 35% – 59% | Diagnosis kemungkinan, perlu pemeriksaan lebih lanjut |
| < 35% | Di bawah threshold, tidak terdiagnosis spesifik |

### Alur Keputusan Final

```
MULAI
  │
  ▼
[Input gejala pasien]
  │
  ▼
[Forward Chaining] ──── tidak ada penyakit lolos ──→ "Belum cukup gejala"
  │
  ▼ (ada kandidat)
[CF Calculation untuk setiap kandidat]
  │
  ▼
[Filter CF >= 35%] ──── semua di bawah threshold ──→ "Tidak terdiagnosis spesifik"
  │
  ▼ (ada yang lolos)
[Sort DESC by CF]
  │
  ▼
[Tampilkan hasil + recommendation + trace]
  │
  SELESAI
```

---

## 10. Referensi Jurnal Ilmiah

Berikut adalah 20 referensi jurnal yang relevan dengan sistem pakar ISPA, Forward Chaining, Certainty Factor, dan Knowledge Acquisition (2015–2024):

---

### A. Sistem Pakar Diagnosis ISPA

**[1]** Njoo, S., Gunadi, K., & Palit, H. N. (2021). *Sistem Pakar Pendiagnosa Infeksi Saluran Pernafasan Akut (ISPA) dengan Metode Forward Chaining dan Certainty Factor*. **Jurnal Infra**, 9(2), 1–7. Universitas Kristen Petra.

**[2]** Gusmaliza, D., & Masdalipa, R. (2022). *Sistem Pakar Diagnosa Penyakit ISPA dengan Metode Forward Chaining*. **JOINTECTS: Journal of Information Technology and Computer Science**. DOI: 10.35134/jointects.

**[3]** Mandiri, P. D., Hartanti, D., & Sari, A. A. (2024). *Prototipe Sistem Pakar untuk Diagnosis Penyakit Infeksi Saluran Pernapasan (ISPA) Menggunakan Metode Certainty Factor*. **SKANIKA**, Vol. 7, No. 1. Universitas Budi Luhur.

**[4]** Hannafi, R. A., Arvio, Y., & Purwanto, Y. S. (2024). *Sistem Pakar Diagnosis Penyakit ISPA Menggunakan Metode Certainty Factor dan Forward Chaining di Puskesmas Tanjung Priok*. **Jurnal ITPLN**, Vol. 4. Institut Teknologi PLN Jakarta.

**[5]** Rilo, S. A., & Hari, S. (2023). *Diagnosis ISPA Berbasis Web dengan Metode Forward Chaining dan Certainty Factor*. **Jurnal Teknik Informatika (JEKIN)**. Rumahjurnal.or.id.

---

### B. Certainty Factor MYCIN pada Sistem Pakar Medis

**[6]** Dwiana, R., & Hidayat, N. (2021). *Sistem Pakar Menggunakan Metode Certainty Factor dalam Akurasi Identifikasi Penyakit pada Paru*. **Jurnal Sisfotek Global**, Vol. 11, No. 2. DOI: 10.38101/sisfotek.

**[7]** Wulandari, T., & Pratiwi, O. (2022). *Sistem Pakar Diagnosa Penyakit ISPA dengan Menggunakan Metode Certainty Factor Berbasis Web*. **Jurnal Teknik Informatika UNDIPA**, Vol. 3. Universitas Dipa Makassar.

**[8]** Sari, M., & Kusuma, D. (2024). *Rancang Bangun Sistem Pakar Diagnosa ISPA pada Apotek Adifarma Metode Certainty Factor*. **Jurnal Informatika dan Sistem Informasi**, Rumahjurnal.or.id.

**[9]** Fitri, A., & Munir, R. (2020). *Penerapan Metode Certainty Factor pada Sistem Pakar Diagnosis Penyakit Pernapasan Berbasis Android*. **Jurnal Teknologi Informasi Nusamandiri (JTIKP)**, Vol. 7, No. 1. STMIK Nusa Mandiri.

**[10]** Rahmadani, S., & Suherman, E. (2019). *Sistem Pakar untuk Mendiagnosis Penyakit Saluran Pernapasan Menggunakan Metode Certainty Factor*. **Jurnal Ilmiah Informatika**, Vol. 4, No. 2. Universitas Islam Indonesia (UII).

---

### C. Forward Chaining dalam Sistem Pakar

**[11]** Kurniawan, A., & Lestari, P. (2020). *Implementasi Forward Chaining pada Sistem Pakar Diagnosis Penyakit Infeksi Saluran Pernapasan*. **Jurnal Informasi dan Teknologi (JINTECH)**, Vol. 2. Universitas Malikussaleh.

**[12]** Syahputra, M., & Budiman, H. (2021). *Perbandingan Metode Forward Chaining dan Backward Chaining pada Sistem Pakar Medis*. **Jurnal Teknik Informatika Universitas Mercu Buana**, Vol. 12, No. 1.

**[13]** Indrawaty, Y., & Sanjaya, W. S. M. (2019). *Expert System for Early Detection of Acute Respiratory Tract Infections Using Forward Chaining Method*. **Journal of Physics: Conference Series**, Vol. 1280, 032034. IOP Publishing.

**[14]** Rivai, A., & Subagja, A. (2022). *Sistem Pakar Berbasis Web untuk Mendiagnosis Penyakit Saluran Pernapasan Akut Menggunakan Forward Chaining*. **Jurnal Informatika Terpadu**, Vol. 8, No. 2. Universitas Unindra.

---

### D. Knowledge Acquisition dan Basis Pengetahuan

**[15]** Pramana, D., & Wibowo, A. (2020). *Akuisisi Pengetahuan Berbasis Dataset untuk Pembangunan Sistem Pakar Penyakit Pernapasan*. **Jurnal Teknologi Rekayasa**, Vol. 5, No. 1. Universitas Amikom Yogyakarta.

**[16]** Hartono, R., & Nugroho, E. (2021). *Automatic Knowledge Acquisition from Medical Records for Respiratory Disease Diagnosis Expert System*. **International Journal of Intelligent Systems and Applications (IJISA)**, Vol. 13, No. 4. DOI: 10.5815/ijisa.

---

### E. Pneumonia, COVID-19, dan Penyakit Pernapasan Spesifik

**[17]** Yuliza, V., & Fitriyani, R. (2021). *Sistem Pakar Diagnosa Pneumonia Menggunakan Metode Certainty Factor pada Puskesmas*. **Jurnal Sistem Informasi dan Teknologi (JURSISTEKNI)**, Vol. 3, No. 1. Universitas Nusa Mandiri.

**[18]** Adiansyah, R., & Purwati, N. (2022). *Implementasi Certainty Factor untuk Deteksi Dini COVID-19 dan ISPA pada Sistem Pakar Berbasis Web*. **Jurnal Rekayasa Sistem dan Teknologi Informasi (RESTI)**, Vol. 6, No. 5. DOI: 10.29207/resti.

**[19]** Setiawan, B., & Cahyadi, D. (2023). *Pengembangan Sistem Pakar Berbasis Machine Learning untuk Klasifikasi Tingkat Keparahan ISPA*. **Jurnal Informatika dan Sistem Informasi (JISI)**, Vol. 9, No. 2. Universitas Indraprasta PGRI Jakarta.

---

### F. Referensi Metodologi Umum

**[20]** Shortliffe, E. H., & Buchanan, B. G. (1975). *A Model of Inexact Reasoning in Medicine*. **Mathematical Biosciences**, Vol. 23, pp. 351–379. Elsevier. *(Referensi fondasi orisinal teori Certainty Factor MYCIN)*

---

## Catatan Penting

> **Disclaimer Medis:**
> Hasil diagnosis dari sistem pakar ini bersifat **dini dan indikatif**. Sistem ini **bukan pengganti** pemeriksaan dan diagnosis oleh tenaga medis profesional. Gunakan hasil sebagai panduan awal sebelum berkonsultasi ke dokter atau puskesmas terdekat.

> **Transparansi Algoritma:**
> Semua perhitungan CF dapat ditelusuri kembali melalui fitur **"Lihat Perhitungan"** di dashboard admin sistem, yang menampilkan trace langkah demi langkah setiap formula yang digunakan.

---

*Dokumen ini dibuat untuk keperluan dokumentasi akademis dan teknis sistem pakar ISPA.*
*Terakhir diperbarui: Mei 2026*

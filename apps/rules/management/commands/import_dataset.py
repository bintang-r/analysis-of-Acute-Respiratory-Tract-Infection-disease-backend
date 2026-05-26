import os
import csv
from django.core.management.base import BaseCommand
from apps.symptoms.models import Symptom
from apps.diseases.models import Disease
from apps.rules.models import Rule, RuleSymptom, CertaintyFactor, DatasetRow
from apps.rules.services import recalculate_rules_and_cf

class Command(BaseCommand):
    help = 'Import symptoms, diseases, rules, and certainty factors (including age mapping) from dataset_ispa.csv'

    def handle(self, *args, **options):
        csv_path = os.path.join(os.getcwd(), 'data', 'dataset_ispa.csv')
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"CSV file not found at {csv_path}"))
            return

        self.stdout.write("Clearing existing Expert System database records...")
        DatasetRow.objects.all().delete()
        CertaintyFactor.objects.all().delete()
        RuleSymptom.objects.all().delete()
        Rule.objects.all().delete()
        Symptom.objects.all().delete()
        Disease.objects.all().delete()

        # Define symptom mapping from CSV columns
        symptom_columns = [
            'Batuk_Kering', 'Batuk_Berdahak', 'Demam', 'Pilek', 'Hidung_Tersumbat',
            'Sesak_Napas', 'Nyeri_Tenggorokan', 'Sakit_Kepala', 'Mual_Muntah',
            'Nyeri_Dada', 'Suara_Serak', 'Kelelahan', 'Berkeringat_Malam',
            'Nafsu_Makan_Turun', 'Hilang_Penciuman', 'Nyeri_Saat_Menelan'
        ]

        # Age groups categorized as symptoms for parameter symmetry
        age_categories = [
            'Umur_Anak', 'Umur_Remaja', 'Umur_Dewasa', 'Umur_Lansia'
        ]

        symptom_details = {
            'Batuk_Kering': {
                'name': 'Batuk Kering',
                'description': 'Batuk yang tidak menghasilkan lendir atau dahak, sering kali terasa gatal di tenggorokan.'
            },
            'Batuk_Berdahak': {
                'name': 'Batuk Berdahak',
                'description': 'Batuk yang menghasilkan lendir atau dahak, menandakan adanya penumpukan cairan di saluran pernapasan.'
            },
            'Demam': {
                'name': 'Demam',
                'description': 'Peningkatan suhu tubuh di atas batas normal (biasanya > 37.5°C) sebagai respon pertahanan tubuh terhadap infeksi.'
            },
            'Pilek': {
                'name': 'Pilek',
                'description': 'Kondisi di mana hidung mengeluarkan cairan encer atau kental secara terus-menerus.'
            },
            'Hidung_Tersumbat': {
                'name': 'Hidung Tersumbat',
                'description': 'Sensasi mampet atau tersumbat pada hidung akibat pelebaran pembuluh darah atau penumpukan lendir di rongga hidung.'
            },
            'Sesak_Napas': {
                'name': 'Sesak Napas',
                'description': 'Kesulitan bernapas atau napas terasa pendek, berat, dan tidak plong.'
            },
            'Nyeri_Tenggorokan': {
                'name': 'Nyeri Tenggorokan',
                'description': 'Rasa sakit, kering, gatal, atau iritasi pada tenggorokan yang sering memburuk saat berbicara atau menelan.'
            },
            'Sakit_Kepala': {
                'name': 'Sakit Kepala',
                'description': 'Rasa sakit, berdenyut, atau ketegangan di area kepala atau leher bagian atas.'
            },
            'Mual_Muntah': {
                'name': 'Mual & Muntah',
                'description': 'Perasaan tidak nyaman di lambung yang memicu keinginan kuat untuk memuntahkan isi perut.'
            },
            'Nyeri_Dada': {
                'name': 'Nyeri Dada',
                'description': 'Rasa sakit, tertekan, atau tidak nyaman di area dada yang dapat memburuk saat batuk atau menarik napas dalam.'
            },
            'Suara_Serak': {
                'name': 'Suara Serak',
                'description': 'Perubahan suara menjadi parau, lemah, berat, atau serak akibat adanya peradangan pada pita suara.'
            },
            'Kelelahan': {
                'name': 'Kelelahan (Fatigue)',
                'description': 'Rasa lelah yang sangat ekstrem, kekurangan energi, dan lemas yang tidak kunjung membaik setelah beristirahat.'
            },
            'Berkeringat_Malam': {
                'name': 'Berkeringat di Malam Hari',
                'description': 'Keluarnya keringat berlebih pada malam hari meskipun suhu ruangan terasa sejuk.'
            },
            'Nafsu_Makan_Turun': {
                'name': 'Nafsu Makan Menurun',
                'description': 'Hilangnya keinginan untuk makan secara signifikan yang dapat menyebabkan lemas dan kekurangan nutrisi.'
            },
            'Hilang_Penciuman': {
                'name': 'Hilang Penciuman (Anosmia)',
                'description': 'Ketidakmampuan atau penurunan drastis dalam mendeteksi dan mengenali bau.'
            },
            'Nyeri_Saat_Menelan': {
                'name': 'Nyeri Saat Menelan (Odinfagia)',
                'description': 'Rasa sakit atau perih di tenggorokan saat menelan makanan, minuman, maupun air liur.'
            },
            'Umur_Anak': {
                'name': 'Umur Balita & Anak (<= 12 Tahun)',
                'description': 'Kategori umur pasien di bawah atau sama dengan 12 tahun.'
            },
            'Umur_Remaja': {
                'name': 'Umur Remaja (13 - 18 Tahun)',
                'description': 'Kategori umur pasien antara 13 sampai 18 tahun.'
            },
            'Umur_Dewasa': {
                'name': 'Umur Dewasa (19 - 60 Tahun)',
                'description': 'Kategori umur pasien antara 19 sampai 60 tahun.'
            },
            'Umur_Lansia': {
                'name': 'Umur Lansia (> 60 Tahun)',
                'description': 'Kategori umur pasien di atas 60 tahun.'
            }
        }

        # Create Symptoms (symptoms 1-16 + age categories 17-20)
        symptom_objs = {}
        all_symptom_keys = symptom_columns + age_categories
        for idx, col in enumerate(all_symptom_keys, start=1):
            code = f"S{idx:02d}"
            details = symptom_details[col]
            s_obj = Symptom.objects.create(
                code=code,
                name=details['name'],
                description=details['description']
            )
            symptom_objs[col] = s_obj
            self.stdout.write(self.style.SUCCESS(f"Created Symptom parameter: {code} - {details['name']}"))

        # Define diseases with detailed metadata
        disease_metadata = {
            'Asma': {
                'code': 'P01',
                'category': 'Penyakit Paru Kronis',
                'description': 'Kondisi penyempitan dan peradangan saluran pernapasan kronis yang menyebabkan sesak napas, mengi (wheezing), dan batuk.',
                'recommendation': 'Hindari faktor pemicu serangan asma seperti debu, bulu hewan, asap, dan kelelahan. Selalu bawa inhaler ke mana pun Anda pergi dan konsultasikan secara berkala dengan dokter spesialis paru.',
                'treatment_solutions': '- Inhaler Pelega Cepat (Short-Acting Bronchodilator seperti Salbutamol atau Albuterol) digunakan segera saat serangan sesak napas terjadi.\n- Inhaler Pengontrol Harian (Kortikosteroid Inhalasi seperti Fluticasone atau Budesonide) digunakan rutin sesuai anjuran dokter untuk mencegah peradangan kronis.\n- Obat Bronkodilator Oral atau Teofilin (hanya atas resep dokter jika gejala memburuk).',
                'recovery_steps': '- Segera duduk tegak dan gunakan inhaler pelega sebanyak 1-2 isapan saat serangan terjadi, lalu usahakan tetap tenang.\n- Identifikasi dan hindari pemicu utama Anda (debu, udara dingin, asap rokok, bulu hewan).\n- Lakukan latihan pernapasan (buteyko atau pernapasan diafragma) untuk memperkuat kapasitas paru.\n- Lakukan kontrol medis berkala untuk memantau fungsi paru-paru Anda.'
            },
            'Bronkitis': {
                'code': 'P02',
                'category': 'Infeksi Saluran Napas Bawah',
                'description': 'Peradangan pada lapisan saluran bronkus yang berfungsi membawa udara ke dan dari paru-paru, sering kali ditandai dengan batuk berdahak kental.',
                'recommendation': 'Perbanyak minum cairan hangat untuk mengencerkan dahak, hindari paparan asap rokok, dan gunakan masker saat beraktivitas di luar ruangan.',
                'treatment_solutions': '- Obat Pengencer Dahak (Mukolitik seperti Ambroxol, Bromhexine, atau Acetylcysteine).\n- Obat Pereda Batuk (Ekspektoran) jika dahak sulit dikeluarkan.\n- Analgesik/Antipiretik seperti Paracetamol atau Ibuprofen untuk meredakan nyeri dada ringan dan demam.',
                'recovery_steps': '- Hirup uap air panas (terapi inhalasi uap sederhana) untuk melonggarkan saluran napas dan mengencerkan dahak.\n- Minum air putih hangat minimal 2.5 liter per hari untuk menjaga kelembapan tenggorokan.\n- Berhenti merokok dan hindari paparan asap rokok pasif sepenuhnya.\n- Istirahatkan tubuh dan hindari aktivitas fisik yang terlalu melelahkan.'
            },
            'COVID-19 Ringan': {
                'code': 'P03',
                'category': 'Infeksi Virus Akut',
                'description': 'Infeksi saluran pernapasan yang disebabkan oleh virus SARS-CoV-2 dengan gejala ringan seperti demam, batuk, kelelahan, dan anosmia tanpa sesak napas berat.',
                'recommendation': 'Lakukan isolasi mandiri di rumah dengan ventilasi baik selama minimal 10 hari, gunakan masker, rajin cuci tangan, dan pantau saturasi oksigen secara berkala.',
                'treatment_solutions': '- Multivitamin penunjang imun tubuh (Vitamin C dosis tinggi, Vitamin D3 1000-5000 IU, dan Zinc).\n- Paracetamol 500mg untuk meredakan demam tinggi dan sakit kepala/pegal linu.\n- Obat Antivirus khusus (seperti Favipiravir atau Paxlovid) jika diresepkan oleh dokter untuk kelompok berisiko tinggi.',
                'recovery_steps': '- Isolasi mandiri di kamar terpisah dengan ventilasi udara segar yang optimal.\n- Gunakan pulse oximeter untuk memantau saturasi oksigen (segera hubungi faskes jika saturasi di bawah 95%).\n- Berjemur di bawah sinar matahari pagi selama 15 menit setiap hari.\n- Tidur cukup (7-8 jam) dan minum banyak air hangat.'
            },
            'Demam Biasa': {
                'code': 'P04',
                'category': 'Infeksi Virus Saluran Napas Atas',
                'description': 'Infeksi virus ringan pada saluran pernapasan atas (common cold) yang sangat umum terjadi, memicu demam ringan, pilek, bersin, dan sakit tenggorokan.',
                'recommendation': 'Istirahat yang cukup di rumah, konsumsi makanan bergizi tinggi protein, serta penuhi kebutuhan hidrasi tubuh dengan air hangat.',
                'treatment_solutions': '- Analgesik/Antipiretik (Paracetamol atau Ibuprofen) untuk meredakan demam dan pusing.\n- Dekongestan oral (seperti Pseudoephedrine) untuk meringankan hidung tersumbat.\n- Tablet hisap antiseptik tenggorokan untuk melegakan rasa gatal.',
                'recovery_steps': '- Istirahat total (bed rest) untuk mengembalikan stamina tubuh.\n- Berkumur dengan air garam hangat (1/2 sendok teh garam dalam segelas air hangat) 2-3 kali sehari.\n- Minum sup hangat, air jahe hangat, atau teh madu hangat untuk melegakan pernapasan.\n- Hindari ruangan dengan pendingin udara (AC) yang terlalu dingin atau kering.'
            },
            'Faringitis': {
                'code': 'P05',
                'category': 'Infeksi Saluran Napas Atas',
                'description': 'Peradangan pada faring (tenggorokan) yang sering disebut radang tenggorokan, menyebabkan rasa perih dan nyeri terutama saat menelan.',
                'recommendation': 'Hindari makanan pedas, berminyak, terlalu panas/dingin, serta istirahatkan suara Anda. Berkumurlah dengan air garam hangat untuk meredakan radang.',
                'treatment_solutions': '- Obat pereda nyeri seperti Paracetamol atau Ibuprofen.\n- Tablet hisap pereda nyeri tenggorokan (Lozenges) dengan kandungan antiseptik.\n- Antibiotik (seperti Amoxicillin atau Erythromycin) HANYA jika terbukti disebabkan oleh infeksi bakteri Streptokokus melalui diagnosis dokter.',
                'recovery_steps': '- Berkumur dengan air garam hangat secara teratur untuk mengurangi bengkak di tenggorokan.\n- Minum cairan hangat dalam jumlah banyak untuk menjaga kelembapan tenggorokan.\n- Kurangi berbicara untuk sementara waktu guna meminimalkan ketegangan pada tenggorokan.\n- Jauhi makanan bertekstur kasar, pedas, berminyak, atau asam yang dapat memicu iritasi lebih parah.'
            },
            'Laringitis': {
                'code': 'P06',
                'category': 'Infeksi Saluran Napas Atas',
                'description': 'Peradangan pada laring (pita suara) yang menyebabkan suara menjadi serak, parau, bahkan hilang sepenuhnya, sering disertai batuk kering.',
                'recommendation': 'Istirahatkan pita suara Anda sepenuhnya (hindari berbicara atau berbisik) dan jaga kelembapan udara di sekitar Anda menggunakan humidifier.',
                'treatment_solutions': '- Analgesik ringan jika disertai nyeri tenggorokan.\n- Obat batuk antitusif jika batuk kering sangat mengganggu pita suara.\n- Kortikosteroid oral dalam jangka pendek (hanya diresepkan dokter pada kasus akut untuk meredakan radang pita suara dengan cepat).',
                'recovery_steps': '- Hindari berbicara sepenuhnya. Jangan berbisik, karena berbisik memberikan tekanan lebih berat pada pita suara dibandingkan berbicara biasa.\n- Hirup uap hangat atau gunakan humidifier di kamar tidur.\n- Hindari konsumsi kafein, alkohol, dan paparan asap rokok yang dapat mengeringkan pita suara.\n- Perbanyak konsumsi air putih suhu ruang.'
            },
            'Pneumonia': {
                'code': 'P07',
                'category': 'Infeksi Saluran Napas Bawah',
                'description': 'Infeksi serius yang menyebabkan kantung udara di salah satu atau kedua paru-paru meradang dan terisi cairan atau nanah, memicu sesak napas berat, batuk berdahak, dan nyeri dada.',
                'recommendation': 'Pneumonia memerlukan penanganan medis segera. Segera periksakan diri ke dokter spesialis paru atau rumah sakit terdekat untuk penanganan intensif.',
                'treatment_solutions': '- Antibiotik spesifik (seperti Azithromycin atau Levofloxacin) jika disebabkan oleh bakteri, wajib dihabiskan sesuai resep.\n- Obat Mukolitik untuk mengencerkan dahak kental.\n- Terapi oksigen tambahan jika saturasi oksigen menurun secara signifikan.',
                'recovery_steps': '- Lakukan istirahat total (bed rest) dan batasi aktivitas fisik seminimal mungkin.\n- Minum obat antibiotik/antivirus dari dokter secara teratur dan tidak boleh terputus.\n- Lakukan fisioterapi dada ringan (seperti menepuk-nepuk punggung secara perlahan) untuk membantu pengeluaran dahak.\n- Pantau saturasi oksigen dan suhu tubuh secara konstan. Segera ke IGD jika sesak napas meningkat atau kuku/bibir tampak membiru.'
            },
            'Sinusitis': {
                'code': 'P08',
                'category': 'Infeksi Saluran Napas Atas',
                'description': 'Inflamasi atau peradangan pada dinding sinus (rongga kecil berisi udara di belakang tulang pipi dan dahi) yang menyebabkan nyeri wajah, hidung tersumbat, dan sakit kepala.',
                'recommendation': 'Gunakan kompres hangat di daerah wajah, lakukan irigasi hidung dengan larutan saline, dan hindari perubahan tekanan udara mendadak.',
                'treatment_solutions': '- Semprotan hidung saline untuk membersihkan rongga hidung.\n- Dekongestan semprot hidung (seperti Oxymetazoline) untuk pemakaian maksimal 3-5 hari guna mencegah efek rebound.\n- Analgesik (Ibuprofen atau Paracetamol) untuk meredakan nyeri kepala dan wajah.\n- Antibiotik jika sinusitis berlangsung lebih dari 10 hari dan disebabkan infeksi bakteri.',
                'recovery_steps': '- Kompres hangat pada area dahi, hidung, dan mata untuk meredakan rasa sakit dan melancarkan aliran lendir.\n- Lakukan irigasi hidung dengan cairan saline steril secara mandiri dengan alat cuci hidung (neti pot).\n- Tidurlah dengan posisi kepala lebih tinggi untuk mengurangi penumpukan lendir di sinus.\n- Hirup uap hangat atau mandi air hangat.'
            },
            'Tidak ISPA': {
                'code': 'P09',
                'category': 'Kondisi Sehat',
                'description': 'Hasil analisis menunjukkan Anda tidak mengalami penyakit Infeksi Saluran Pernapasan Akut (ISPA). Gejala yang Anda rasakan mungkin merupakan reaksi alergi biasa atau kelelahan fisik.',
                'recommendation': 'Pertahankan pola hidup sehat, konsumsi makanan bergizi, berolahraga teratur, dan istirahat yang cukup untuk menjaga imunitas tubuh.',
                'treatment_solutions': '- Tidak memerlukan obat-obatan medis khusus atau antibiotik.\n- Konsumsi multivitamin harian (seperti Vitamin C atau B-Compleks) untuk menjaga stamina jika tubuh terasa agak lemas.',
                'recovery_steps': '- Jaga pola makan dengan gizi seimbang dan porsi makan teratur.\n- Tidur teratur minimal 7-8 jam per hari.\n- Cuci tangan secara teratur dengan sabun sebelum makan dan setelah beraktivitas di luar.\n- Kelola stres dengan baik melalui relaksasi atau aktivitas hobi.'
            }
        }

        # Create Diseases
        disease_objs = {}
        for d_name, d_meta in disease_metadata.items():
            d_obj = Disease.objects.create(
                code=d_meta['code'],
                name=d_name,
                category=d_meta['category'],
                description=d_meta['description'],
                recommendation=d_meta['recommendation'],
                treatment_solutions=d_meta['treatment_solutions'],
                recovery_steps=d_meta['recovery_steps']
            )
            disease_objs[d_name] = d_obj
            self.stdout.write(self.style.SUCCESS(f"Created Disease: {d_meta['code']} - {d_name}"))

        self.stdout.write("Reading CSV dataset to import training cases into database...")
        dataset_rows = []
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dataset_rows.append(DatasetRow(
                    age=int(row['Umur'].strip()),
                    batuk_kering=int(row['Batuk_Kering'].strip()),
                    batuk_berdahak=int(row['Batuk_Berdahak'].strip()),
                    demam=int(row['Demam'].strip()),
                    pilek=int(row['Pilek'].strip()),
                    hidung_tersumbat=int(row['Hidung_Tersumbat'].strip()),
                    sesak_napas=int(row['Sesak_Napas'].strip()),
                    nyeri_tenggorokan=int(row['Nyeri_Tenggorokan'].strip()),
                    sakit_kepala=int(row['Sakit_Kepala'].strip()),
                    mual_muntah=int(row['Mual_Muntah'].strip()),
                    nyeri_dada=int(row['Nyeri_Dada'].strip()),
                    suara_serak=int(row['Suara_Serak'].strip()),
                    kelelahan=int(row['Kelelahan'].strip()),
                    berkeringat_malam=int(row['Berkeringat_Malam'].strip()),
                    nafsu_makan_turun=int(row['Nafsu_Makan_Turun'].strip()),
                    hilang_penciuman=int(row['Hilang_Penciuman'].strip()),
                    nyeri_saat_menelan=int(row['Nyeri_Saat_Menelan'].strip()),
                    diagnosis=row['Diagnosis'].strip()
                ))
        DatasetRow.objects.bulk_create(dataset_rows)
        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {len(dataset_rows)} cases into DatasetRow table."))
        
        self.stdout.write("Running Rule Learning and Certainty Factor recalculation from database...")
        recalculate_rules_and_cf()
        self.stdout.write(self.style.SUCCESS("System training complete!"))

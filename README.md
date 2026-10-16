# Studi Kasus: Prakiraan Sebaran PM2.5 dengan Komputasi Paralel ala HPC

Studi kasus berdasarkan kuliah tamu **"Global Infrastructure to Address Local Challenge with HPC"**
oleh **Worawan Diaz Carballo (Thammasat University)**.

Materi membahas bagaimana HPC menjawab tantangan lokal, salah satunya **prakiraan kualitas udara PM2.5**
dengan superkomputer LANTA di Thailand. Proyek ini membuat versi kecilnya yang bisa dijalankan di laptop.

> Data dan parameter bersifat **sintetis** untuk pembelajaran, bukan prakiraan resmi.

## Hubungan dengan materi

| Konsep di materi | Implementasi di proyek ini |
|---|---|
| Tantangan lokal (PM2.5/kabut asap) | Simulasi sebaran asap dari 8 titik sumber pada grid 300 x 300 km |
| HPC untuk simulasi skala besar | Model adveksi-difusi 2D, 480 langkah waktu (24 jam) per simulasi |
| Kinerja diukur dalam FLOPS | Benchmark mencetak waktu, speedup, efisiensi, dan estimasi GFLOPS |
| Ekosistem HPC (APEC HPCI-MEM) | Dipetakan di dashboard: kebijakan, operator, fasilitas, komunitas |
| Peran *integrator* | Kode menjembatani model komputasi dengan asumsi pakar domain (angin, emisi, baku mutu) |
| Skala dari lokal ke global | Script `jalankan_slurm.sh` sebagai contoh pindah ke cluster |

## Cara kerja singkat

1. **Model**: persamaan adveksi-difusi dengan peluruhan, diselesaikan dengan skema *upwind* (NumPy).
2. **Ensemble**: 32 simulasi dengan kecepatan/arah angin dan emisi acak. Tiap anggota independen
   (*embarrassingly parallel*), sehingga mudah dibagi ke banyak inti dengan `multiprocessing`.
3. **Prakiraan**: rata-rata ensemble dan probabilitas PM2.5 melampaui 55 µg/m³ (nilai dapat diubah di `THRESHOLD`).
4. **Benchmark**: ensemble dijalankan dengan 1, 2, 4, ... proses; dihitung speedup, efisiensi, dan fraksi serial (hukum Amdahl).

## Cara menjalankan

```bash
pip install -r requirements.txt
python simulasi_pm25_hpc.py     
python buat_dashboard.py        
```
link index.html https://krbara.github.io/studi-kasus-hpc-pm25/

## Catatan penting

- **Speedup bergantung pada perangkat.** Hasilnya berbeda di tiap komputer dan tidak akan mencapai ideal karena
  ada bagian serial, biaya membuat proses, dan keterbatasan memori.
- **Estimasi GFLOPS bersifat kasar** (sekitar 20 operasi floating point per sel per langkah), hanya untuk
  membandingkan konfigurasi, bukan untuk mengklaim kinerja puncak.
- **Model disederhanakan**: tanpa kimia atmosfer, topografi, maupun data cuaca nyata. Untuk prakiraan operasional,
  parameter harus dikalibrasi dengan data pengamatan dan divalidasi oleh pakar.
- `jalankan_slurm.sh` adalah contoh umum dan belum diuji pada cluster tertentu.

## Pengembangan lanjutan

Memakai data cuaca/titik api nyata, mencoba `mpi4py` untuk banyak node, atau memindahkan perhitungan ke GPU (CuPy).

## Referensi

Kuliah tamu Worawan Diaz Carballo, Thammasat University.

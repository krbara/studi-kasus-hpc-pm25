"""
Studi Kasus: Prakiraan Sebaran PM2.5 (kabut asap) dengan Komputasi Paralel ala HPC
Berdasarkan kuliah tamu "Global Infrastructure to Address Local Challenge with HPC"
(Worawan Diaz Carballo, Thammasat University)

Ide utama (sesuai materi):
  - Tantangan lokal: prakiraan kualitas udara PM2.5 (di materi: Thailand dengan superkomputer LANTA).
  - HPC dipakai untuk simulasi berskala besar. Di sini: simulasi adveksi-difusi PM2.5 pada grid 2D.
  - Prakiraan ensemble: banyak simulasi dengan skenario angin & emisi berbeda -> probabilitas
    melampaui baku mutu. Tiap anggota ensemble independen, jadi cocok dijalankan paralel.
  - Kinerja diukur: waktu, speedup, efisiensi, dan estimasi FLOPS (satuan yang dibahas di materi).
  - Peran "integrator": menjembatani model komputasi (HPC) dengan pakar domain (lingkungan).

Catatan: data & parameter bersifat sintetis untuk pembelajaran, bukan prakiraan resmi.
"""
import json
import os
import time
from multiprocessing import Pool
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def cpu_count():
    """Jumlah inti yang benar-benar boleh dipakai (penting di cluster SLURM)."""
    return len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)


OUT = Path("output")
OUT.mkdir(exist_ok=True)

# ---- parameter model (satuan: km, jam, ug/m3) ----
N = int(os.getenv("GRID", 300))         # ukuran grid N x N (1 sel = 1 km)
STEPS = int(os.getenv("STEPS", 480))    # 480 langkah x 0,05 jam = 24 jam
MEMBERS = int(os.getenv("MEMBERS", 32)) # jumlah anggota ensemble
DX, DT = 1.0, 0.05
DIFF = 1.0          # koefisien difusi (km2/jam)
DECAY = 0.02        # pengendapan/peluruhan (1/jam)
BACKGROUND = 10.0   # konsentrasi latar
THRESHOLD = 55.0    # baku mutu harian PM2.5 (ug/m3), dapat disesuaikan
FLOP_PER_CELL_STEP = 20  # estimasi operasi floating point per sel per langkah

HOTSPOTS = np.random.default_rng(7).integers(40, N - 40, size=(8, 2))  # titik sumber asap


def simulate_member(seed):
    """Satu anggota ensemble: angin & emisi acak, lalu simulasi adveksi-difusi 24 jam."""
    rng = np.random.default_rng(seed)
    speed, theta = rng.uniform(3, 10), rng.uniform(0, 2 * np.pi)   # km/jam, arah angin
    ax, ay = speed * np.cos(theta) * DT / DX, speed * np.sin(theta) * DT / DX
    dd = DIFF * DT / DX**2

    src = np.zeros((N, N), np.float32)
    for (i, j), q in zip(HOTSPOTS, rng.lognormal(np.log(110), 0.4, len(HOTSPOTS))):
        src[i - 2:i + 3, j - 2:j + 3] = q                            # emisi ug/m3/jam

    c = np.full((N, N), BACKGROUND, np.float32)
    for _ in range(STEPS):
        dcx = c - np.roll(c, 1, 0) if ax >= 0 else np.roll(c, -1, 0) - c   # skema upwind
        dcy = c - np.roll(c, 1, 1) if ay >= 0 else np.roll(c, -1, 1) - c
        lap = np.roll(c, 1, 0) + np.roll(c, -1, 0) + np.roll(c, 1, 1) + np.roll(c, -1, 1) - 4 * c
        c = c - ax * dcx - ay * dcy + dd * lap - DECAY * DT * (c - BACKGROUND) + src * DT
        c[0, :] = c[-1, :] = c[:, 0] = c[:, -1] = BACKGROUND            # batas terbuka
    return c


def run_ensemble(workers):
    """Jalankan seluruh anggota ensemble dengan jumlah proses tertentu; kembalikan waktu & hasil."""
    seeds = range(MEMBERS)
    t0 = time.perf_counter()
    if workers == 1:
        fields = [simulate_member(s) for s in seeds]
    else:
        with Pool(workers) as pool:
            fields = pool.map(simulate_member, seeds, chunksize=1)
    return time.perf_counter() - t0, np.stack(fields)


def worker_list():
    cores = cpu_count()
    ws = [1]
    while ws[-1] * 2 <= cores:
        ws.append(ws[-1] * 2)
    if ws[-1] != cores:
        ws.append(cores)
    return ws


def benchmark():
    print(f"Grid {N}x{N}, {STEPS} langkah, {MEMBERS} anggota ensemble, {cpu_count()} inti CPU\n")
    rows, fields = [], None
    for w in worker_list():
        t, f = run_ensemble(w)
        rows.append({"proses": w, "waktu_detik": t})
        print(f"  {w:>2} proses -> {t:6.2f} detik")
        fields = f
    df = pd.DataFrame(rows)
    t1 = df.loc[0, "waktu_detik"]
    df["speedup"] = t1 / df["waktu_detik"]
    df["efisiensi_persen"] = df["speedup"] / df["proses"] * 100
    total_flop = FLOP_PER_CELL_STEP * N * N * STEPS * MEMBERS
    df["gflops"] = total_flop / df["waktu_detik"] / 1e9
    df.round(3).to_csv(OUT / "1_benchmark_paralel.csv", index=False)
    print("\n", df.round(2).to_string(index=False), "\n")
    return df, fields


def forecast(fields):
    mean = fields.mean(axis=0)
    prob = (fields > THRESHOLD).mean(axis=0)
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    im0 = ax[0].imshow(mean, cmap="magma_r", origin="lower")
    ax[0].set_title("Rata-rata ensemble PM2.5 setelah 24 jam (ug/m3)")
    plt.colorbar(im0, ax=ax[0], fraction=.046)
    im1 = ax[1].imshow(prob, cmap="PuRd", origin="lower", vmin=0, vmax=1)
    ax[1].set_title(f"Probabilitas PM2.5 > {THRESHOLD:.0f} ug/m3")
    plt.colorbar(im1, ax=ax[1], fraction=.046)
    for a in ax:
        a.scatter(HOTSPOTS[:, 1], HOTSPOTS[:, 0], c="cyan", edgecolors="k", s=40, label="Titik sumber")
        a.set_xlabel("km (timur)"); a.set_ylabel("km (utara)")
    ax[0].legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(OUT / "2_prakiraan_pm25.png", dpi=130)
    plt.close()
    return mean, prob


def plot_scaling(df):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(df.proses, df.speedup, "o-", color="crimson", label="Terukur")
    ax[0].plot(df.proses, df.proses, "--", color="gray", label="Ideal")
    ax[0].set_title("Speedup vs jumlah proses"); ax[0].set_xlabel("Proses"); ax[0].set_ylabel("Speedup (x)")
    ax[0].legend()
    ax[1].bar(df.proses.astype(str), df.efisiensi_persen, color="steelblue")
    ax[1].set_title("Efisiensi paralel (%)"); ax[1].set_xlabel("Proses"); ax[1].set_ylim(0, 110)
    plt.tight_layout()
    plt.savefig(OUT / "3_speedup_efisiensi.png", dpi=130)
    plt.close()


def main():
    df, fields = benchmark()
    mean, prob = forecast(fields)
    plot_scaling(df)

    last = df.iloc[-1]
    p = last["proses"]
    serial_frac = None
    if p > 1:  # estimasi fraksi serial dari hukum Amdahl: S = 1 / (f + (1-f)/p)
        serial_frac = max(0.0, (1 / last["speedup"] - 1 / p) / (1 - 1 / p))
    summary = {
        "grid": N, "steps": STEPS, "members": MEMBERS, "cores": cpu_count(),
        "waktu_serial": round(df.loc[0, "waktu_detik"], 2),
        "waktu_terbaik": round(df["waktu_detik"].min(), 2),
        "speedup_maks": round(df["speedup"].max(), 2),
        "gflops_maks": round(df["gflops"].max(), 2),
        "serial_fraction": None if serial_frac is None else round(serial_frac, 3),
        "threshold": THRESHOLD,
        "area_prob_ge_50": round(float((prob >= 0.5).mean() * 100), 2),
        "area_prob_ge_20": round(float((prob >= 0.2).mean() * 100), 2),
        "area_prob_gt_0": round(float((prob > 0).mean() * 100), 2),
        "pm25_maks_mean": round(float(mean.max()), 1),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print("Ringkasan:", json.dumps(summary, indent=2))
    print(f"\nSelesai. Hasil tersimpan di folder '{OUT}/'.")


if __name__ == "__main__":   # wajib di Windows agar multiprocessing berjalan benar
    main()

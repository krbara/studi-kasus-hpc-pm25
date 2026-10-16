#!/bin/bash
#SBATCH --job-name=pm25-ensemble
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32      # jumlah inti yang diminta
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%j.out

# Contoh script untuk menjalankan simulasi di cluster HPC berbasis SLURM
# (belum diuji pada cluster tertentu; sesuaikan nama partisi/modul dengan fasilitas yang dipakai).
module load python            # nama modul bergantung pada cluster
pip install --user -r requirements.txt
MEMBERS=256 python simulasi_pm25_hpc.py

"""Membuat dashboard web statis (docs/index.html) dari hasil simulasi di folder output/.
Jalankan setelah simulasi_pm25_hpc.py:  python buat_dashboard.py
"""
import base64
import json
from pathlib import Path

import pandas as pd

OUT, DOCS = Path("output"), Path("docs")
DOCS.mkdir(exist_ok=True)
(DOCS / ".nojekyll").touch()


def img(name):
    return f'<img src="data:image/png;base64,{base64.b64encode((OUT / name).read_bytes()).decode()}" alt="{name}">'


S = json.loads((OUT / "summary.json").read_text())
bench = pd.read_csv(OUT / "1_benchmark_paralel.csv").round(2)
bench.columns = ["Proses", "Waktu (dtk)", "Speedup (x)", "Efisiensi (%)", "GFLOPS"]
slurm = Path("jalankan_slurm.sh").read_text() if Path("jalankan_slurm.sh").exists() else ""

kpi = [("#5b8cff", "Anggota ensemble", S["members"]), ("#ff6fae", "Inti CPU terpakai", S["cores"]),
       ("#3ddc97", "Speedup maksimum", f'{S["speedup_maks"]}x'), ("#a78bfa", "Estimasi GFLOPS", S["gflops_maks"])]
kpi_html = "".join(f'<div class="kpi s3" style="background:{c}"><span>{k}</span><b>{v}</b></div>' for c, k, v in kpi)

eco = [("#5b8cff", "Pembuat kebijakan", "Menetapkan baku mutu & prioritas"), ("#ff6fae", "Operator HPC", "Menjalankan & merawat sistem"),
       ("#3ddc97", "Fasilitas HPC", "Laptop → cluster (SLURM)"), ("#a78bfa", "Komunitas / industri", "Pengguna prakiraan")]
eco_html = "".join(f'<div class="mini s3" style="background:{c}"><div><b>{t}</b><br><span>{d}</span></div></div>' for c, t, d in eco)

note_perf = ("Catatan: simulasi ini dijalankan pada 1 inti, sehingga speedup belum dapat diukur. Jalankan di komputer multi-inti."
             if S["cores"] == 1 else
             f'Fraksi serial hasil estimasi hukum Amdahl: {S["serial_fraction"]}. Semakin kecil, semakin baik skalabilitasnya.')

CSS = """
:root{--ink:#111;--bg:#efeaff;--blue:#5b8cff;--pink:#ff6fae;--green:#3ddc97;--purple:#a78bfa;--orange:#ff8a3d;--cyan:#5ce1e6}
*{box-sizing:border-box}
body{margin:0;height:100vh;display:flex;color:var(--ink);font-family:"Space Grotesk","Helvetica Neue",Arial,sans-serif;line-height:1.5;
background:var(--bg) radial-gradient(var(--ink) 1px,transparent 1px) 0 0/22px 22px;overflow:hidden}
aside{width:260px;flex-shrink:0;background:#fff;border-right:4px solid var(--ink);padding:22px 18px;display:flex;flex-direction:column;gap:12px;overflow-y:auto}
.logo{background:var(--ink);color:#fff;padding:12px 14px;box-shadow:5px 5px 0 var(--pink);border:3px solid var(--ink);margin-bottom:10px}
.logo b{display:block;font-size:1.05rem;text-transform:uppercase;line-height:1.2}.logo small{color:#cfcfcf;font-size:.72rem}
aside button{font:inherit;font-weight:800;text-transform:uppercase;font-size:.85rem;text-align:left;padding:11px 14px;cursor:pointer;color:var(--ink);
border:3px solid var(--ink);box-shadow:4px 4px 0 var(--ink);transition:.1s}
aside button:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--ink)}
aside button.on{transform:translate(3px,3px);box-shadow:1px 1px 0 var(--ink)}
.note{margin-top:auto;font-size:.72rem;font-weight:600;border:2px dashed var(--ink);padding:8px 10px}
main{flex:1;overflow-y:auto;padding:26px 30px}.view{display:none}.view.on{display:block}
h1{margin:0 0 4px;font-size:1.7rem;font-weight:800;text-transform:uppercase;letter-spacing:-.02em}.lead{margin:0 0 20px;font-weight:500}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:20px;align-items:start}
.s3{grid-column:span 3}.s4{grid-column:span 4}.s5{grid-column:span 5}.s6{grid-column:span 6}.s7{grid-column:span 7}.s8{grid-column:span 8}.s12{grid-column:span 12}
.kpi{border:3px solid var(--ink);box-shadow:6px 6px 0 var(--ink);padding:14px 16px}
.kpi span{display:block;font-size:.78rem;font-weight:700;text-transform:uppercase}.kpi b{font-size:2rem;font-weight:800}
.card{background:#fff;border:3px solid var(--ink);box-shadow:7px 7px 0 var(--ink);padding:16px 18px}
.card h2{margin:0 0 10px;font-size:1.05rem;font-weight:800;text-transform:uppercase}
img{width:100%;height:auto;border:3px solid var(--ink);display:block;background:#fff}
.scroll{overflow-x:auto;border:3px solid var(--ink);background:#fff}
table.tbl{border-collapse:collapse;width:100%;font-size:.85rem}
.tbl th{background:var(--ink);color:#fff;text-align:left;padding:8px 10px;text-transform:uppercase;font-size:.7rem;white-space:nowrap}
.tbl td{padding:7px 10px;border-top:2px solid var(--ink);font-weight:500}.tbl tr:nth-child(even) td{background:#f3efff}.tbl tr:hover td{background:var(--cyan)}
.stack{display:flex;flex-direction:column;gap:14px}
.mini{border:3px solid var(--ink);box-shadow:5px 5px 0 var(--ink);padding:10px 14px}.mini span{font-size:.82rem;font-weight:600}
.big{font-size:1.9rem;font-weight:800;display:block}
p.t{margin:10px 0 0;font-size:.88rem;font-weight:500}
pre{margin:0;background:var(--ink);color:#e8ffe8;padding:12px;font-size:.78rem;overflow-x:auto;border:3px solid var(--ink)}
ol{margin:0;padding-left:20px;font-weight:500}ol li{margin-bottom:6px}
@media(max-width:760px){body{flex-direction:column;height:auto;overflow:auto}aside{width:100%;flex-direction:row;flex-wrap:wrap;border-right:0;border-bottom:4px solid var(--ink)}
.logo{width:100%}.note{display:none}main{overflow:visible;padding:18px}.s3{grid-column:span 6}.s4,.s5,.s6,.s7,.s8,.s12{grid-column:span 12}}
"""
JS = """
const btns=document.querySelectorAll('aside button'),views=document.querySelectorAll('.view');
function show(v){views.forEach(x=>x.classList.toggle('on',x.id===v));btns.forEach(b=>b.classList.toggle('on',b.dataset.v===v));
document.querySelector('main').scrollTop=0;history.replaceState(null,'','#'+v);}
btns.forEach(b=>b.onclick=()=>show(b.dataset.v));
show(document.getElementById(location.hash.slice(1))?location.hash.slice(1):'ringkasan');
"""

html = f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HPC untuk Prakiraan PM2.5</title><style>{CSS}</style></head><body>
<aside><div class="logo"><b>HPC &amp; PM2.5</b><small>Prakiraan ensemble paralel</small></div>
<button data-v="ringkasan" style="background:var(--cyan)">◼ Ringkasan</button>
<button data-v="prakiraan" style="background:var(--blue)">1 · Prakiraan</button>
<button data-v="performa" style="background:var(--pink)">2 · Performa HPC</button>
<button data-v="cluster" style="background:var(--green)">3 · Menuju Cluster</button>
<div class="note">Data &amp; parameter sintetis untuk pembelajaran. Berdasarkan kuliah tamu Worawan Diaz Carballo (Thammasat University).</div></aside>
<main>
<section class="view" id="ringkasan"><h1>Ringkasan</h1>
<p class="lead">Infrastruktur komputasi global untuk tantangan lokal: prakiraan sebaran PM2.5 (kabut asap) dengan komputasi paralel.</p>
<div class="grid">{kpi_html}
<div class="card s12"><h2>Ekosistem HPC (model APEC HPCI-MEM) dalam proyek ini</h2><div class="grid" style="gap:16px">{eco_html}</div>
<p class="t"><b>Peran integrator:</b> kode ini menjembatani model komputasi (HPC) dengan pakar domain (lingkungan): angin, emisi, dan baku mutu ditentukan pakar, lalu diterjemahkan menjadi alur kerja yang berjalan paralel.</p></div></div></section>

<section class="view" id="prakiraan"><h1>1 · Prakiraan</h1>
<p class="lead">Ensemble {S["members"]} simulasi dengan skenario angin &amp; emisi berbeda menghasilkan probabilitas PM2.5 melampaui {S["threshold"]:.0f} µg/m³.</p>
<div class="grid"><div class="card s8"><h2>Peta prakiraan 24 jam</h2>{img("2_prakiraan_pm25.png")}</div>
<div class="s4 stack"><div class="mini" style="background:var(--pink)"><span class="big">{S["pm25_maks_mean"]}</span><span>µg/m³ — PM2.5 rata-rata ensemble tertinggi</span></div>
<div class="mini" style="background:var(--blue)"><span class="big">{S["area_prob_gt_0"]}%</span><span>area dengan probabilitas melampaui baku mutu &gt; 0</span></div>
<div class="mini" style="background:var(--green)"><span class="big">{S["area_prob_ge_20"]}%</span><span>area dengan probabilitas ≥ 20%</span></div></div></div></section>

<section class="view" id="performa"><h1>2 · Performa HPC</h1>
<p class="lead">Seberapa cepat simulasi bila dijalankan dengan lebih banyak proses? Kinerja diukur dengan waktu, speedup, efisiensi, dan FLOPS.</p>
<div class="grid"><div class="card s7"><h2>Speedup &amp; efisiensi</h2>{img("3_speedup_efisiensi.png")}</div>
<div class="card s5"><h2>Hasil benchmark</h2><div class="scroll">{bench.to_html(index=False, classes="tbl", border=0)}</div><p class="t">{note_perf}</p>
<p class="t">GFLOPS adalah estimasi kasar (≈20 operasi per sel per langkah waktu).</p></div></div></section>

<section class="view" id="cluster"><h1>3 · Menuju Cluster</h1>
<p class="lead">Kode yang sama dapat dipindah dari laptop ke cluster HPC.</p>
<div class="grid"><div class="card s5"><h2>Langkah</h2><ol><li>Laptop: <code>python simulasi_pm25_hpc.py</code></li>
<li>Perbesar <code>GRID</code>, <code>STEPS</code>, <code>MEMBERS</code> lewat variabel lingkungan</li><li>Kirim job ke cluster dengan <code>sbatch jalankan_slurm.sh</code></li>
<li>Ukur ulang speedup &amp; efisiensi, lalu bandingkan</li></ol></div>
<div class="card s7"><h2>jalankan_slurm.sh (contoh)</h2><pre>{slurm}</pre></div></div></section>
</main><script>{JS}</script></body></html>"""

(DOCS / "index.html").write_text(html, encoding="utf-8")
print("Dashboard dibuat: docs/index.html")

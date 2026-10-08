"""Dasbor latihan1 (versi Streamlit).
Jalankan di komputer:  pip install streamlit  &&  streamlit run streamlit_app.py
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dasbor latihan1", page_icon="📊", layout="wide")

GREEN, AMBER, RED, INK = "#0f6b5c", "#d9a441", "#a5321f", "#12202b"
SCORE = "Nilai ujian"
FACTORS = ["Jam belajar", "Jam tidur", "Kehadiran", "Jam layar", "Pengeluaran", "Kepuasan"]
GRADES = ["A (≥ 85)", "B (70–84)", "C (60–69)", "D (< 60)"]
GENDER_SCALE = alt.Scale(domain=["Perempuan", "Laki-laki"], range=[GREEN, AMBER])
GRADE_SCALE = alt.Scale(domain=GRADES, range=[GREEN, "#2f9e8f", AMBER, RED])


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(Path(__file__).parent / "latihan1.csv").rename(columns={
        "Student_ID": "ID", "Gender": "Kelamin", "Age": "Usia", "Study_Hours": "Jam belajar",
        "Sleep_Hours": "Jam tidur", "Attendance": "Kehadiran", "Exam_Score": SCORE,
        "Monthly_Spending": "Pengeluaran", "Screen_Hours": "Jam layar", "Satisfaction": "Kepuasan",
    })
    df["Kelamin"] = df["Kelamin"].replace({"F": "Perempuan", "M": "Laki-laki"})
    df["Kategori"] = pd.cut(df[SCORE], bins=[-float("inf"), 60, 70, 85, float("inf")],
                            labels=GRADES[::-1], right=False).astype(str)
    return df


def strength(r: float) -> str:
    a = abs(r)
    word = "sangat kuat" if a >= 0.9 else "kuat" if a >= 0.7 else "sedang" if a >= 0.4 else "lemah"
    return f"hubungan {word} {'searah' if r >= 0 else 'berlawanan arah'}"


df = load_data()
st.title("Dasbor kebiasaan dan nilai mahasiswa")

with st.sidebar:
    st.header("Filter")
    genders = sorted(df["Kelamin"].unique())
    ages = sorted(df["Usia"].unique())
    kelamin = st.multiselect("Jenis kelamin", genders, default=genders)
    usia = st.multiselect("Usia", ages, default=ages)

d = df[df["Kelamin"].isin(kelamin) & df["Usia"].isin(usia)]
if d.empty:
    st.warning("Tidak ada mahasiswa dengan filter ini. Pilih minimal satu jenis kelamin dan satu usia.")
    st.stop()

# --- Ringkasan ---
k = st.columns(5)
k[0].metric("Mahasiswa", len(d))
k[1].metric("Rata-rata nilai ujian", f"{d[SCORE].mean():.1f}")
k[2].metric("Rata-rata jam belajar", f"{d['Jam belajar'].mean():.1f}")
k[3].metric("Rata-rata kehadiran", f"{d['Kehadiran'].mean():.1f}%")
k[4].metric("Rata-rata kepuasan", f"{d['Kepuasan'].mean():.1f} / 10")

# --- Baris 1: diagram sebar + donat ---
left, right = st.columns([2, 1])
with left:
    st.subheader("Hubungan dengan nilai ujian")
    factor = st.selectbox("Faktor", FACTORS)
    r = d[factor].corr(d[SCORE])
    if len(d) < 3 or pd.isna(r):
        st.caption("Data terlalu sedikit untuk menghitung hubungan.")
    else:
        st.write(f"**{factor}** dan nilai ujian: r = {r:.2f}, {strength(r)}.")
    base = alt.Chart(d).encode(
        x=alt.X(factor, type="quantitative", scale=alt.Scale(zero=False)),
        y=alt.Y(SCORE, type="quantitative", scale=alt.Scale(zero=False)),
    )
    points = base.mark_circle(size=70, opacity=0.7).encode(
        color=alt.Color("Kelamin:N", scale=GENDER_SCALE), tooltip=["ID", "Kelamin", factor, SCORE])
    trend = base.transform_regression(factor, SCORE).mark_line(color=INK, strokeDash=[6, 4])
    st.altair_chart((points + trend).properties(height=320, width="container"))
    st.caption("Korelasi menunjukkan dua hal bergerak bersama, bukan bahwa satu menyebabkan yang lain.")

with right:
    st.subheader("Kategori nilai ujian")
    g = pd.DataFrame({"Kategori": GRADES, "Jumlah": [int((d["Kategori"] == x).sum()) for x in GRADES]})
    st.altair_chart(alt.Chart(g).mark_arc(innerRadius=60).encode(
        theta="Jumlah:Q", color=alt.Color("Kategori:N", scale=GRADE_SCALE, sort=GRADES),
        tooltip=["Kategori", "Jumlah"]).properties(height=300, width="container"))

# --- Baris 2: sebaran + kekuatan hubungan ---
left, right = st.columns([2, 1])
with left:
    st.subheader("Sebaran nilai ujian")
    st.altair_chart(alt.Chart(d).mark_bar(color=GREEN).encode(
        x=alt.X(f"{SCORE}:Q", bin=alt.Bin(step=10, extent=[40, 100]), title=SCORE),
        y=alt.Y("count():Q", title="Jumlah mahasiswa")).properties(height=280, width="container"))

with right:
    st.subheader("Kekuatan hubungan dengan nilai")
    cr = pd.DataFrame({"Faktor": FACTORS, "r": [d[f].corr(d[SCORE]) for f in FACTORS]}).dropna()
    cr = cr.reindex(cr["r"].abs().sort_values(ascending=False).index)
    st.altair_chart(alt.Chart(cr).mark_bar().encode(
        x=alt.X("r:Q", scale=alt.Scale(domain=[-1, 1]), title="Korelasi (r)"),
        y=alt.Y("Faktor:N", sort=cr["Faktor"].tolist(), title=None),
        color=alt.condition(alt.datum.r > 0, alt.value(GREEN), alt.value(RED)),
        tooltip=["Faktor", alt.Tooltip("r:Q", format=".2f")]).properties(height=280, width="container"))

# --- Baris 3: per usia + per jenis kelamin ---
left, right = st.columns([2, 1])
with left:
    st.subheader("Rata-rata nilai ujian per usia")
    dg = df[df["Kelamin"].isin(kelamin)]  # filter usia tidak dipakai agar semua usia tetap terlihat
    am = dg.groupby("Usia", as_index=False)[SCORE].mean().round(1)
    bars = alt.Chart(am).encode(x=alt.X("Usia:O", title="Usia (tahun)", axis=alt.Axis(labelAngle=0)),
                                y=alt.Y(f"{SCORE}:Q", scale=alt.Scale(domain=[0, 100])))
    st.altair_chart((bars.mark_bar(color=GREEN) + bars.mark_text(dy=-8, fontWeight="bold").encode(text=f"{SCORE}:Q"))
                    .properties(height=280, width="container"))

with right:
    st.subheader("Perbandingan jenis kelamin")
    metrics = [SCORE, "Jam belajar", "Jam tidur", "Kehadiran", "Kepuasan"]
    da = df[df["Usia"].isin(usia)]  # filter kelamin tidak dipakai agar keduanya tetap dibandingkan
    gm = (da.groupby("Kelamin")[metrics].mean().round(1).reset_index()
          .melt(id_vars="Kelamin", var_name="Ukuran", value_name="Rata_rata"))
    st.altair_chart(alt.Chart(gm).mark_bar().encode(
        x=alt.X("Kelamin:N", title=None, axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y("Rata_rata:Q", title=None),
        color=alt.Color("Kelamin:N", scale=GENDER_SCALE),
        tooltip=["Kelamin", "Ukuran", "Rata_rata"],
    ).properties(width=60, height=150).facet(column=alt.Column("Ukuran:N", sort=metrics, title=None))
     .resolve_scale(y="independent"))
    st.caption("Selisihnya muncul bersama selisih jam belajar, tidur, dan kehadiran, jadi tidak bisa "
               "dibaca sebagai akibat dari jenis kelamin saja.")

# --- Tabel ---
st.subheader("Data mahasiswa")
cari = st.text_input("Cari ID mahasiswa")
t = d if not cari.strip() else d[d["ID"].astype(str).str.contains(cari.strip(), regex=False)]
st.dataframe(t.drop(columns="Kategori"), hide_index=True)

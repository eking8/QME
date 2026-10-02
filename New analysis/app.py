import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import linprog
from sklearn.preprocessing import MinMaxScaler


st.set_page_config(
    page_title="Sapientia Observatory · DEA cost-efficiency",
    page_icon="🎓",
    layout="wide",
)

if "run_dea" not in st.session_state:
    st.session_state.run_dea = False


# =========================

# THEME

# =========================

BURGUNDY = "#822433"   # ← Sapienza brand colour, shared with the slide deck
ROSE = "#C9A3AB"       # ← non-frontier series; low-chroma so the frontier reads first
INK = "#2B2326"
GRID = "rgba(128,128,128,0.18)"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&display=swap');

    .block-container {{ padding-top: 3rem; max-width: 1400px; }}

    h1, h2, h3 {{ font-family: 'Source Serif 4', Georgia, serif !important; letter-spacing: -0.01em; }}

    /* ← both selectors: Streamlit renamed the metric test-id between versions */
    div[data-testid="stMetric"], div[data-testid="metric-container"] {{
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 10px;
        padding: 14px 16px;
    }}

    .hero {{
        background: {BURGUNDY};
        color: #fff;
        border-radius: 14px;
        padding: 22px 28px 20px;
        margin-bottom: 1.2rem;
    }}
    .hero .t {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.85rem; font-weight: 600; line-height: 1.15; }}
    .hero .s {{ margin-top: .4rem; opacity: .88; font-size: .98rem; max-width: 78ch; }}

    .peer {{
        display: inline-block;
        border: 1px solid rgba(130,36,51,0.35);
        border-radius: 999px;
        padding: 2px 10px;
        margin: 2px 4px 2px 0;
        font-size: .88rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def style_fig(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def eur(x):
    return f"€{x:,.0f}"


def eur_m(x):
    return f"€{x / 1e6:,.1f}m"


def fmt_num(v):
    if pd.isna(v):
        return "–"
    return f"{v:,.0f}" if float(v).is_integer() or abs(v) >= 100 else f"{v:,.2f}"  # ← counts as integers, scores and ratios keep decimals


# =========================

# DEA FUNCTION

# =========================

def dea_vrs(df, inputs, outputs):

    # ← copy=True: pandas copy-on-write can return a read-only view, which breaks the in-place imputation below
    X = df[inputs].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float, copy=True)
    Y = df[outputs].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float, copy=True)

    for j in range(X.shape[1]):
        col = X[:, j]
        col[np.isnan(col)] = np.nanmedian(col)
        X[:, j] = col

    for j in range(Y.shape[1]):
        col = Y[:, j]
        col[np.isnan(col)] = np.nanmedian(col)
        Y[:, j] = col

    n = X.shape[0]
    scores = []
    lambdas = []

    for i in range(n):

        x0 = X[i]
        y0 = Y[i]

        m = n

        c = np.zeros(m + 1)
        c[-1] = 1

        A_ub = []
        b_ub = []

        for k in range(X.shape[1]):
            A_ub.append(list(X[:, k]) + [-x0[k]])
            b_ub.append(0)

        for r in range(Y.shape[1]):
            A_ub.append(list(-Y[:, r]) + [0])
            b_ub.append(-y0[r])

        A_eq = [[1] * m + [0]]
        b_eq = [1]

        bounds = [(0, None)] * m + [(0, 1)]

        res = linprog(
            c,
            A_ub=np.array(A_ub),
            b_ub=np.array(b_ub),
            A_eq=np.array(A_eq),
            b_eq=np.array(b_eq),
            bounds=bounds,
            method="highs"
        )

        if res.success:
            scores.append(res.x[-1])
            lambdas.append(res.x[:-1])  # ← peer weights λ; used for the benchmark view in the explorer
        else:
            scores.append(np.nan)
            lambdas.append(np.full(n, np.nan))

    return np.array(scores), np.vstack(lambdas)


# =========================

# LOAD DATA

# =========================

BASE_DIR = Path(__file__).resolve().parent  # ← read CSVs next to app.py, whatever folder you launch from


@st.cache_data
def load_data():
    return {
        "UI": pd.read_csv(BASE_DIR / "UI_final.csv"),
        "THE": pd.read_csv(BASE_DIR / "THE_final.csv"),
    }


@st.cache_data(show_spinner="Solving one linear programme per university…")
def run_dea(dataset, inputs, outputs):
    # ← cached on the specification, so switching tabs or universities does not re-solve the LPs
    df = load_data()[dataset]

    df_scaled = df.copy()
    scale_cols = [c for c in inputs if c in df.columns]
    scaler = MinMaxScaler()
    df_scaled[scale_cols] = scaler.fit_transform(df_scaled[scale_cols])

    return dea_vrs(df_scaled, list(inputs), list(outputs))


DATA = load_data()

# =========================

# INPUT GROUPS

# =========================

all_inputs = ['STAFF | INTERNAL TEACHING STAFF', 'STAFF | AVERAGE AGE OF INTERNAL TEACHING STAFF', 'STAFF | FULL PROFESSORS', 'STAFF | AVERAGE AGE OF FULL PROFESSORS ', 'STAFF | ASSOCIATE PROFESSOR ', 'STAFF | AVERAGE AGE OF ASSOCIATE PROFESSORS', 'STAFF | TENURED RESEARCHERS', 'STAFF | AVERAGE AGE OF TENURED RESEARCHERS', 'STAFF | FIXED-TERM RESEARCHERS', 'STAFF | AVERAGE AGE OF FIXED-TERM RESEARCHERS', 'STAFF | RESEARCH FELLOWS', 'STAFF | AVERAGE AGE OF RESEARCH FELLOWS', 'STAFF | EXECUTIVE TECHNICAL ADMINISTRATIVE STAFF', 'STAFF | COLLABORATORS IN RESEARCH ACTIVITIES', 'STAFF | INTERNAL TEACHING STAFF AND RESEARCH FELLOWS', 'STAFF | NON-ACADEMIC STAFF', 'STAFF | UNIVERSITY STAFF', 'STAFF | ADJUNCT FACULTY', 'STUDENT LIFECYCLE | NUMBER OF FIRST-YEAR ENTRANCE', 'STUDENT LIFECYCLE | NUMBER OF FIRST-TIME ENTRANCE', 'STUDENT LIFECYCLE | NUMBER OF ENROLLED STUDENTS', 'STUDENT LIFECYCLE | NUMBER OF FIRST-YEAR ENROLLED STUDENTS', 'STUDENT LIFECYCLE | NUMBER OF REGULAR STUDENTS', 'STUDENT LIFECYCLE | PERCENTAGE OF STUDENTS ENROLLED IN THE SECOND YEAR IN THE SAME DEGREE PROGRAMME', 'STUDENT LIFECYCLE | PERCENTAGE OF INACTIVE STUDENTS', 'STUDENT LIFECYCLE | NUMBER OF GRADUATES', 'STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES WITHIN THE STANDARD DURATION OF THE DEGREE PROGRAMME', 'STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES WITHIN ONE YEAR BEYOND THE STANDARD DURATION OF THE DEGREE PROGRAMME', 'STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES SATISFIED WITH THE DEGREE PROGRAMMES', 'STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES EMPLOYED ONE YEAR AFTER GRADUATION ', 'STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES EMPLOYED THREE YEARS AFTER GRADUATION', 'STUDENT LIFECYCLE | STUDENT-STAFF RATIO', 'STUDENT LIFECYCLE | CREDITS OBTAINED ABROAD', 'STUDENT LIFECYCLE | PROPORTION OF STUDENTS WHO COMPLETED CURRICULAR INTERNSHIPS OR RECOGNISED WORK ACTIVITIES', 'STUDENT LIFECYCLE | PROPORTION OF STUDENTS WHO USED CAREER/JOB PLACEMENT SERVICES', 'POST LAUREAM EDUCATION | STUDENTS ENROLLED IN PHD PROGRAMMES', 'POST LAUREAM EDUCATION | PERCENTAGE OF DOCTORAL CANDIDATES RECEIVING A SCHOLARSHIP', 'POST LAUREAM EDUCATION | PHDS AWARDED', 'POST LAUREAM EDUCATION | AVERAGE AGE OF PHD GRADUATES', 'POST LAUREAM EDUCATION | STUDENTS ENROLLED IN SPECIALISATION PROGRAMMES ', 'POST LAUREAM EDUCATION | STUDENTS ENROLLED IN FIRST-LEVEL MASTER’S PROGRAMMES', 'POST LAUREAM EDUCATION | STUDENTS ENROLLED IN SECOND-LEVEL MASTER’S PROGRAMMES', 'POST LAUREAM EDUCATION | SPECIALISATION DIPLOMAS AWARDED', 'POST LAUREAM EDUCATION | FIRST-LEVEL MASTER’S DEGREES AWARDED', 'POST LAUREAM EDUCATION | SECOND-LEVEL MASTER’S DEGREES AWARDED', 'ECONOMIC AND FINANCIAL | STUDENT CONTRIBUTION REVENUE', 'ECONOMIC AND FINANCIAL | AVERAGE TOTAL TUITION FEE FOR ENROLLED UNDERGRADUATE STUDENTS', 'ECONOMIC AND FINANCIAL | TOTAL REVENUES', 'ECONOMIC AND FINANCIAL | CURRENT REVENUES', 'ECONOMIC AND FINANCIAL | TEACHING ACTIVITIES REVENUES', 'ECONOMIC AND FINANCIAL | PUBLIC REVENUES', 'ECONOMIC AND FINANCIAL | REVENUES FROM THE EUROPEAN UNION AND REST OF THE WORLD', 'ECONOMIC AND FINANCIAL | REVENUES FROM PRIVATE SOCIAL INSTITUTIONS', 'ECONOMIC AND FINANCIAL | REVENUES FROM ENTERPRISES', 'ECONOMIC AND FINANCIAL | TOTAL EXPENDITURES', 'ECONOMIC AND FINANCIAL | CURRENT EXPENDITURES', 'ECONOMIC AND FINANCIAL | PURCHASE OF GOODS AND SERVICES', 'ECONOMIC AND FINANCIAL | NET BALANCE', 'ECONOMIC AND FINANCIAL | NET EQUITY', 'ECONOMIC AND FINANCIAL | NET ECONOMIC RESULT', 'ECONOMIC AND FINANCIAL | OPERATING REVENUES', 'ECONOMIC AND FINANCIAL | OPERATING REVENUES: OWN REVENUES', 'ECONOMIC AND FINANCIAL | OPERATING REVENUES: CONTRIBUTIONS', 'ECONOMIC AND FINANCIAL | OPERATING REVENUES: OTHER REVENUES', 'ECONOMIC AND FINANCIAL | OPERATING COSTS', 'ECONOMIC AND FINANCIAL | OPERATING COSTS: PERSONNEL', 'ECONOMIC AND FINANCIAL | OPERATING COSTS: CURRENT MANAGEMENT', 'ECONOMIC AND FINANCIAL | OPERATING COSTS: DEPRECIATION AND WRITE-DOWNS', 'ECONOMIC AND FINANCIAL | OPERATING COSTS: OTHER', 'ECONOMIC AND FINANCIAL | OPERATING RESULT', 'ECONOMIC AND FINANCIAL | OWN REVENUES FROM TEACHING', 'ECONOMIC AND FINANCIAL | TEACHING REVENUES: DEGREE PROGRAMMES', "ECONOMIC AND FINANCIAL | TEACHING REVENUES: MASTER'S PROGRAMMES", 'ECONOMIC AND FINANCIAL | TEACHING REVENUES: POST-DEGREE PROGRAMMES', 'ECONOMIC AND FINANCIAL | TEACHING REVENUES: STATE EXAMINATIONS, ADMINISTRATIVE FEES AND OTHER', 'ECONOMIC AND FINANCIAL | TEACHING REVENUES: OTHER COURSES', 'ECONOMIC AND FINANCIAL | OWN REVENUES FROM RESEARCH', 'ECONOMIC AND FINANCIAL | INDEBTEDNESS INDEX (IDEB)', 'ECONOMIC AND FINANCIAL | ECONOMIC AND FINANCIAL SUSTAINABILITY INDEX', 'ECONOMIC AND FINANCIAL | FFO (ANVUR)', 'ECONOMIC AND FINANCIAL | FFO (DM)', 'ECONOMIC AND FINANCIAL | BASE FUNDING QUOTA', 'ECONOMIC AND FINANCIAL | PERFORMANCE-BASED FUNDING QUOTA', 'ECONOMIC AND FINANCIAL | EQUALISATION INTERVENTIONS', 'ECONOMIC AND FINANCIAL | EXTRAORDINARY FUNDING PLANS', 'ECONOMIC AND FINANCIAL | STANDARD COST PER STUDENT', 'RESEARCH | HIGHLY CITED RESEARCHERS ', 'RESEARCH | ARTICLES PUBLISHED IN NATURE AND SCIENCE ']

DEFAULT_INPUTS = [
    "STAFF | INTERNAL TEACHING STAFF",
    "STAFF | RESEARCH FELLOWS",
    "STAFF | NON-ACADEMIC STAFF",
    "STAFF | ADJUNCT FACULTY",
]

DOMAIN_LABELS = {
    "STAFF": "Staff",
    "STUDENT LIFECYCLE": "Students",
    "POST LAUREAM EDUCATION": "Post-lauream",
    "ECONOMIC AND FINANCIAL": "Finance",
    "RESEARCH": "Research",
}

ACRONYMS = {"phd": "PhD", "phds": "PhDs", "ffo": "FFO", "anvur": "ANVUR", "dm": "DM", "ideb": "IDEB", "european union": "European Union"}

OUTPUT_LABELS = {
    "GLOBAL": "Overall GreenMetric score (GLOBAL)",
    "SI": "Campus setting (SI)",
    "EC": "Energy efficiency (EC)",
    "WS": "Waste treatment (WS)",
    "WR": "Water usage (WR)",
    "TR": "Campus transit (TR)",
    "ED": "Research & education (ED)",
    "OVERALL": "Overall THE Impact score (OVERALL)",
}


def label(col):
    # ← display-only label; the raw column name is still what the model uses
    domain, _, name = col.partition("|")
    name = name.strip().lower().capitalize()
    name = re.sub(
        r"\b(phds|phd|ffo|anvur|dm|ideb|european union)\b",
        lambda m: ACRONYMS[m.group(0)],
        name,
    )
    return f"{DOMAIN_LABELS.get(domain.strip(), domain.strip().title())} · {name}"


# =========================

# COST PROXIES

# =========================

def normalize(col):
    return col.replace(" ", "").replace("’", "'").upper().strip()

cost_per_unit = {
    # ======================
    # STAFF - AGE VARIABLES
    # ======================
    "STAFF | AVERAGE AGE OF INTERNAL TEACHING STAFF": 0,
    "STAFF | AVERAGE AGE OF FULL PROFESSORS": 0,
    "STAFF | AVERAGE AGE OF ASSOCIATE PROFESSORS": 0,
    "STAFF | AVERAGE AGE OF TENURED RESEARCHERS": 0,
    "STAFF | AVERAGE AGE OF FIXED-TERM RESEARCHERS": 0,
    "STAFF | AVERAGE AGE OF RESEARCH FELLOWS": 0,

    # ======================
    # STAFF - COUNTS (UPDATED PROXIES)
    # ======================
    "STAFF | INTERNAL TEACHING STAFF": 70000,  # blended teaching academic labour
    "STAFF | FULL PROFESSORS": 95000,  # ← Table 3 of the report; previously missing, so costed at 0
    "STAFF | ASSOCIATE PROFESSOR": 75000,  # ← Table 3
    "STAFF | FIXED-TERM RESEARCHERS": 45000,  # ← Table 3 (RTD)
    "STAFF | RESEARCH FELLOWS": 45000,
    "STAFF | EXECUTIVE TECHNICAL ADMINISTRATIVE STAFF": 38000,
    "STAFF | COLLABORATORS IN RESEARCH ACTIVITIES": 40000,
    "STAFF | INTERNAL TEACHING STAFF AND RESEARCH FELLOWS": 60000,  # blended composite
    "STAFF | NON-ACADEMIC STAFF": 38000,
    "STAFF | ADJUNCT FACULTY": 8000,

    # ======================
    # STUDENTS (UPDATED OECD/EUROSTAT MIDPOINT)
    # ======================
    "STUDENT LIFECYCLE | NUMBER OF FIRST-YEAR ENTRANCE": 10000,
    "STUDENT LIFECYCLE | NUMBER OF FIRST-TIME ENTRANCE": 10000,
    "STUDENT LIFECYCLE | NUMBER OF ENROLLED STUDENTS": 10000,  # ← Table 3
    "STUDENT LIFECYCLE | NUMBER OF FIRST-YEAR ENROLLED STUDENTS": 10000,
    "STUDENT LIFECYCLE | NUMBER OF REGULAR STUDENTS": 10000,

    # ======================
    # STUDENT PERCENTAGES
    # ======================
    "STUDENT LIFECYCLE | PERCENTAGE OF STUDENTS ENROLLED IN THE SECOND YEAR IN THE SAME DEGREE PROGRAMME": 0,
    "STUDENT LIFECYCLE | PERCENTAGE OF INACTIVE STUDENTS": 0,
    "STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES WITHIN THE STANDARD DURATION OF THE DEGREE PROGRAMME": 0,
    "STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES WITHIN ONE YEAR BEYOND THE STANDARD DURATION OF THE DEGREE PROGRAMME": 0,
    "STUDENT LIFECYCLE | PERCENTAGE OF GRADUATES EMPLOYED THREE YEARS AFTER GRADUATION": 0,

    # ======================
    # MOBILITY / CAREERS
    # ======================
    "STUDENT LIFECYCLE | CREDITS OBTAINED ABROAD": 3000,
    "STUDENT LIFECYCLE | PROPORTION OF STUDENTS WHO COMPLETED CURRICULAR INTERNSHIPS OR RECOGNISED WORK ACTIVITIES": 1000,
    "STUDENT LIFECYCLE | PROPORTION OF STUDENTS WHO USED CAREER/JOB PLACEMENT SERVICES": 500,

    # ======================
    # POST LAUREAM EDUCATION (UPDATED)
    # ======================
    "POST LAUREAM EDUCATION | STUDENTS ENROLLED IN PHD PROGRAMMES": 22000,  # ← Table 3
    "POST LAUREAM EDUCATION | PERCENTAGE OF DOCTORAL CANDIDATES RECEIVING A SCHOLARSHIP": 0,
    "POST LAUREAM EDUCATION | AVERAGE AGE OF PHD GRADUATES": 0,

    "POST LAUREAM EDUCATION | STUDENTS ENROLLED IN SPECIALISATION PROGRAMMES": 4000,
    "POST LAUREAM EDUCATION | STUDENTS ENROLLED IN FIRST-LEVEL MASTER’S PROGRAMMES": 3000,
    "POST LAUREAM EDUCATION | STUDENTS ENROLLED IN SECOND-LEVEL MASTER’S PROGRAMMES": 4000,
    "POST LAUREAM EDUCATION | SPECIALISATION DIPLOMAS AWARDED": 4000,

    # ======================
    # FINANCIAL VARIABLES (NO CHANGE)
    # ======================
    "ECONOMIC AND FINANCIAL | STUDENT CONTRIBUTION REVENUE": 1,
    "ECONOMIC AND FINANCIAL | AVERAGE TOTAL TUITION FEE FOR ENROLLED UNDERGRADUATE STUDENTS": 1,
    "ECONOMIC AND FINANCIAL | TOTAL REVENUES": 1,
    "ECONOMIC AND FINANCIAL | CURRENT REVENUES": 1,
    "ECONOMIC AND FINANCIAL | TEACHING ACTIVITIES REVENUES": 1,
    "ECONOMIC AND FINANCIAL | PUBLIC REVENUES": 1,
    "ECONOMIC AND FINANCIAL | REVENUES FROM THE EUROPEAN UNION AND REST OF THE WORLD": 1,
    "ECONOMIC AND FINANCIAL | REVENUES FROM PRIVATE SOCIAL INSTITUTIONS": 1,
    "ECONOMIC AND FINANCIAL | REVENUES FROM ENTERPRISES": 1,
    "ECONOMIC AND FINANCIAL | TOTAL EXPENDITURES": 1,
    "ECONOMIC AND FINANCIAL | CURRENT EXPENDITURES": 1,
    "ECONOMIC AND FINANCIAL | PURCHASE OF GOODS AND SERVICES": 1,
    "ECONOMIC AND FINANCIAL | OPERATING REVENUES": 1,
    "ECONOMIC AND FINANCIAL | OPERATING REVENUES: OWN REVENUES": 1,
    "ECONOMIC AND FINANCIAL | OPERATING REVENUES: CONTRIBUTIONS": 1,
    "ECONOMIC AND FINANCIAL | OPERATING REVENUES: OTHER REVENUES": 1,
    "ECONOMIC AND FINANCIAL | OPERATING COSTS": 1,
    "ECONOMIC AND FINANCIAL | OPERATING COSTS: PERSONNEL": 1,
    "ECONOMIC AND FINANCIAL | OPERATING COSTS: CURRENT MANAGEMENT": 1,
    "ECONOMIC AND FINANCIAL | OPERATING COSTS: DEPRECIATION AND WRITE-DOWNS": 1,
    "ECONOMIC AND FINANCIAL | OPERATING COSTS: OTHER": 1,
    "ECONOMIC AND FINANCIAL | OWN REVENUES FROM TEACHING": 1,
    "ECONOMIC AND FINANCIAL | TEACHING REVENUES: DEGREE PROGRAMMES": 1,
    "ECONOMIC AND FINANCIAL | TEACHING REVENUES: MASTER'S PROGRAMMES": 1,
    "ECONOMIC AND FINANCIAL | TEACHING REVENUES: POST-DEGREE PROGRAMMES": 1,
    "ECONOMIC AND FINANCIAL | TEACHING REVENUES: STATE EXAMINATIONS, ADMINISTRATIVE FEES AND OTHER": 1,
    "ECONOMIC AND FINANCIAL | TEACHING REVENUES: OTHER COURSES": 1,
    "ECONOMIC AND FINANCIAL | OWN REVENUES FROM RESEARCH": 1,
    "ECONOMIC AND FINANCIAL | FFO (ANVUR)": 1,
    "ECONOMIC AND FINANCIAL | FFO (DM)": 1,
    "ECONOMIC AND FINANCIAL | BASE FUNDING QUOTA": 1,
    "ECONOMIC AND FINANCIAL | PERFORMANCE-BASED FUNDING QUOTA": 1,
    "ECONOMIC AND FINANCIAL | EQUALISATION INTERVENTIONS": 1,
    "ECONOMIC AND FINANCIAL | EXTRAORDINARY FUNDING PLANS": 1,
    "ECONOMIC AND FINANCIAL | STANDARD COST PER STUDENT": 1,

    # ======================
    # RATIOS / NON-RESOURCE VARIABLES
    # ======================
    "ECONOMIC AND FINANCIAL | NET BALANCE": 0,
    "ECONOMIC AND FINANCIAL | NET EQUITY": 0,
    "ECONOMIC AND FINANCIAL | NET ECONOMIC RESULT": 0,
    "ECONOMIC AND FINANCIAL | OPERATING RESULT": 0,
    "ECONOMIC AND FINANCIAL | INDEBTEDNESS INDEX (IDEB)": 0,
    "ECONOMIC AND FINANCIAL | ECONOMIC AND FINANCIAL SUSTAINABILITY INDEX": 0
}
cost_dict_norm = {normalize(k): v for k, v in cost_per_unit.items()}


def default_cost(col):
    # ← normalised lookup: several dataset columns carry trailing spaces, which silently costed them at 0 before
    return float(cost_dict_norm.get(normalize(col), 0))


def compute_cost(df, inputs, unit_costs):
    values = df[inputs].apply(pd.to_numeric, errors="coerce").fillna(0)
    return values * pd.Series(unit_costs)  # ← per-input cost matrix; row sums give TOTAL_COST


# =========================

# SIDEBAR

# =========================

st.sidebar.title("DEA dashboard")

dataset = st.sidebar.radio(
    "Output ranking",
    ["UI", "THE"],
    format_func=lambda d: {
        "UI": f"UI GreenMetric ({len(DATA['UI'])} universities)",
        "THE": f"THE Impact Rankings ({len(DATA['THE'])} universities)",
    }[d],
)

df = DATA[dataset].copy()

if dataset == "UI":
    output_options = [c for c in ["GLOBAL", "SI", "EC", "WS", "WR", "TR", "ED"] if c in df.columns]
else:
    output_options = ["OVERALL"]

st.sidebar.markdown(
    """
    **Workflow**

    1. Select inputs and outputs
    2. Check the diagnostics
    3. Adjust cost proxies if needed
    4. Run DEA and explore the tabs

    Input-oriented VRS DEA, solved with HiGHS. Inputs are min–max scaled; costs use the raw values.
    """
)

# =========================

# HEADER

# =========================

st.markdown(
    """
    <div class="hero">
      <div class="t">Sustainability efficiency of Italian universities</div>
      <div class="s">Sapientia Observatory extension. DEA efficiency against UI GreenMetric and THE Impact
      Rankings, with a cost layer that expresses inefficiency in euros.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================

# INPUTS

# =========================

st.subheader("Model specification")

input_options = [c for c in all_inputs if c in df.columns]  # ← only offer variables the chosen dataset actually has

c_in, c_out = st.columns([3, 2])

with c_in:
    selected_inputs = st.multiselect(
        "Inputs (resources)",
        input_options,
        default=[c for c in DEFAULT_INPUTS if c in input_options],
        format_func=label,
        placeholder="Search by name, e.g. professors, revenues…",
    )

with c_out:
    selected_outputs = st.multiselect(
        "Outputs (sustainability performance)",
        output_options,
        default=[output_options[0]],
        format_func=lambda o: OUTPUT_LABELS.get(o, o),
    )

# =========================

# DEA VALIDITY CHECK

# =========================

n_dmus = len(df)

n_vars = (
    len(selected_inputs)
    + len(selected_outputs)
)

ratio = n_dmus / max(n_vars, 1)

d1, d2, d3, d4 = st.columns([1, 1, 1, 2])

d1.metric("Universities (DMUs)", n_dmus)
d2.metric("Variables", n_vars)
d3.metric("DMUs per variable", round(ratio, 2))

with d4:
    st.write("")
    if ratio < 3:
        st.error("Too many variables selected. DEA discrimination likely poor.")
    elif ratio < 5:
        st.warning("Weak DEA specification.")
    elif ratio < 10:
        st.info("Acceptable DEA specification.")
    else:
        st.success("Strong DEA specification.")

with st.expander("How to interpret DEA diagnostics"):
    st.markdown(
    """
    DEA performs best when the number of universities (DMUs) is large
    relative to the number of inputs and outputs.

    - Higher ratios improve discrimination.
    - Low ratios may result in too many universities appearing efficient.
    - Ratios above 10 are generally considered strong.
    """
    )

with st.expander("Cost assumptions (€ per unit per year)"):
    st.caption(
        "Defaults are the proxies documented in Section 3.5 of the report. "
        "Edit a value to test an alternative assumption; DEA scores are unaffected, only costs and savings change."
    )
    spec_key = hashlib.md5("|".join(selected_inputs).encode()).hexdigest()[:10]  # ← new editor per input set, so rows never misalign
    cost_table = pd.DataFrame({
        "Input": [label(c) for c in selected_inputs],
        "Unit cost (€/year)": [default_cost(c) for c in selected_inputs],
    })
    edited = st.data_editor(
        cost_table,
        hide_index=True,
        disabled=["Input"],
        key=f"costs_{dataset}_{spec_key}",
        column_config={
            "Unit cost (€/year)": st.column_config.NumberColumn(min_value=0, step=500, format="€%d"),
        },
    )
    unit_costs = dict(zip(selected_inputs, edited["Unit cost (€/year)"].fillna(0).astype(float)))

with st.expander("Cost-benefit analysis disclaimer"):
    st.markdown(
    """
    Cost estimates are intended as approximate proxies for resources consumed
    by a university.

    - Staff variables use estimated annual employment costs.
    - Student variables use estimated expenditure per student.
    - Research variables use estimated support costs.
    - Financial variables already measured in euros are treated directly.
    - Ratios, percentages, ages and performance indicators are assigned
      zero cost because they do not represent resource consumption.

    Results should therefore be interpreted as a comparative efficiency
    assessment rather than an exact accounting valuation.
    """
    )

if st.button("Run DEA", type="primary"):
    st.session_state.run_dea = True

if not st.session_state.run_dea:
    st.caption("The default specification reproduces the results reported in the paper. Press Run DEA to start.")
    st.stop()

if len(selected_inputs) == 0:
    st.error("Select at least one input.")
    st.stop()

if len(selected_outputs) == 0:
    st.error("Select at least one output.")
    st.stop()

# =========================

# RUN DEA

# =========================

scores, lambdas = run_dea(dataset, tuple(selected_inputs), tuple(selected_outputs))

cost_matrix = compute_cost(df, selected_inputs, unit_costs)

results = pd.DataFrame({
    "UNIVERSITY_ID": df["UNIVERSITY_ID"].values,
    "DEA": scores,
    "TOTAL_COST": cost_matrix.sum(axis=1).values,
    "_pos": np.arange(len(df)),  # ← original row position, so λ and raw inputs can be looked up after sorting
})

results["DEA_R"] = results["DEA"].round(6)  # ← comparison copy: solver noise (1 − 1e-9) otherwise breaks frontier ties; raw DEA kept for euro figures

results["POTENTIAL_SAVINGS"] = (results["TOTAL_COST"] * (1 - results["DEA"])).clip(lower=0)

results["DEA_per_cost"] = np.where(
    results["TOTAL_COST"] > 0,
    results["DEA"] / results["TOTAL_COST"],
    np.nan
)


def band(s):
    if s >= 0.999:
        return "Efficient frontier"
    if s >= 0.9:
        return "Highly efficient"
    if s >= 0.8:
        return "Good efficiency"
    if s >= 0.7:
        return "Moderate inefficiency"
    return "Significant improvement potential"


results["Band"] = results["DEA"].apply(band)
results["Frontier"] = np.where(results["DEA"] >= 0.999, "Frontier", "Non-frontier")

results = results.sort_values("DEA", ascending=False).reset_index(drop=True)  # ← raw order, so the ranking matches the report figures
results["Rank"] = results.index + 1
results["Percentile"] = results["DEA_R"].rank(pct=True) * 100

mean_cost = results["TOTAL_COST"].mean()
mean_dea = results["DEA"].mean()
upper = results["DEA"] >= mean_dea
left = results["TOTAL_COST"] <= mean_cost
results["Quadrant"] = np.select(
    [upper & left, upper & ~left, ~upper & left],
    ["Best value for money", "Resource intensive", "Limited outputs"],
    default="Greatest potential",
)

efficient_count = (results["DEA"] >= 0.999).sum()
no_cost = results["TOTAL_COST"].sum() == 0

# =========================

# HEADLINE METRICS

# =========================

st.divider()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Average DEA", f"{mean_dea:.3f}")
m2.metric("Median DEA", f"{results['DEA'].median():.3f}")
m3.metric("Frontier universities", f"{efficient_count} of {len(results)}")
m4.metric("Average estimated cost", "n/a" if no_cost else eur_m(mean_cost))

if no_cost:
    st.info("The selected inputs carry no cost proxy, so cost and savings views are empty. Add a staff, student or financial input.")

# =========================
# OUTPUTS
# =========================

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "🏆 Rankings",
    "💰 Cost analysis",
    "🎓 University explorer",
])

with tab1:

    g1, g2 = st.columns([2, 1])

    with g1:
        fig = px.histogram(
            results,
            x="DEA",
            nbins=20,
            marginal="box",
            opacity=0.95,
            color_discrete_sequence=[BURGUNDY],
            title="Distribution of university efficiency scores",
        )
        fig.update_traces(marker_line_color="white", marker_line_width=1, selector=dict(type="histogram"))
        fig.add_vline(x=1, line_dash="dash", line_color=INK)
        fig.add_annotation(  # ← one label; add_vline's own annotation repeats on the marginal subplot
            x=1, xref="x", y=1, yref="y domain",
            text="Efficiency frontier", showarrow=False, xanchor="right", yanchor="bottom",
        )
        fig.update_xaxes(range=[-0.02, 1.06], title_text="")
        fig.update_layout(xaxis_title_text="DEA score")  # ← title on the main axis only, not the marginal box
        fig.update_yaxes(title="Universities", selector=dict(anchor="x"))
        st.plotly_chart(style_fig(fig, 430))

    with g2:
        st.markdown("#### Executive summary")
        best = results[results["DEA"] >= 0.999]
        cheapest = best.loc[best["TOTAL_COST"].idxmin(), "UNIVERSITY_ID"] if len(best) and not no_cost else None
        st.markdown(
            f"""
- Average DEA score: **{mean_dea:.3f}** (median {results['DEA'].median():.3f})
- **{efficient_count}** universities define the efficiency frontier.
{f"- Lowest-cost frontier university: **{cheapest}**" if cheapest else ""}
- **{(results['DEA'] < 0.4).sum()}** universities score below 0.4.
- Institutions below the frontier may have opportunities to improve
resource utilisation while maintaining output levels.
            """
        )
        st.caption(
            "A concentration near 1.0 suggests many institutions perform close to best practice. "
            "A wide spread indicates substantial differences in efficiency. "
            "Multiple peaks may indicate groups operating under different conditions."
        )

    st.markdown("#### DEA results")
    table = results.assign(
        COST_M=results["TOTAL_COST"] / 1e6,
        SAVE_M=results["POTENTIAL_SAVINGS"] / 1e6,
        DEA_PER_M=results["DEA_per_cost"] * 1e6,  # ← DEA per €m reads better than per €
    )
    st.dataframe(
        table[["Rank", "UNIVERSITY_ID", "DEA", "Band", "COST_M", "SAVE_M", "DEA_PER_M"]],
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn(width="small"),
            "UNIVERSITY_ID": "University",
            "DEA": st.column_config.ProgressColumn("DEA score", min_value=0, max_value=1, format="%.3f"),
            "Band": "Interpretation",
            "COST_M": st.column_config.NumberColumn("Estimated cost (€m)", format="%.1f"),
            "SAVE_M": st.column_config.NumberColumn("Potential savings (€m)", format="%.1f"),
            "DEA_PER_M": st.column_config.NumberColumn("DEA per €m", format="%.4f"),
        },
    )

    with st.expander("DEA score interpretation"):
        st.markdown(
        """
        | DEA Score | Interpretation |
        |-----------|---------------|
        | 1.00 | Efficient frontier (best practice institution) |
        | 0.90 - 0.99 | Highly efficient |
        | 0.80 - 0.89 | Good efficiency |
        | 0.70 - 0.79 | Moderate inefficiency |
        | < 0.70 | Significant improvement potential |

        **Example**

        A DEA score of **0.80** suggests that a university could theoretically
        produce the same outputs using approximately **80% of its current inputs**
        if it operated as efficiently as the best-performing institutions.
        """
        )

with tab2:

    frontier = results[results["DEA"] >= 0.999]
    followers = results[results["DEA"] < 0.999].head(3)

    r1, r2 = st.columns([1, 2])

    with r1:
        st.markdown("#### Frontier universities")
        st.caption("Tied at DEA = 1.000; these are the benchmarks for everyone else.")  # ← ties, so no medals: their order is arbitrary
        st.markdown(
            "".join(f'<span class="peer">{u}</span>' for u in frontier["UNIVERSITY_ID"]),
            unsafe_allow_html=True,
        )
        st.markdown("#### Closest followers")
        for row in followers.itertuples():
            st.markdown(f"**{row.UNIVERSITY_ID}**: DEA {row.DEA:.3f}")

    with r2:
        top20 = results.head(20)

        fig2 = px.bar(
            top20,
            x="DEA",
            y="UNIVERSITY_ID",
            orientation="h",
            color="Frontier",
            color_discrete_map={"Frontier": BURGUNDY, "Non-frontier": ROSE},
            title=f"Top {len(top20)} universities",
        )
        fig2.update_traces(texttemplate="%{x:.3f}", textposition="outside", cliponaxis=False)
        fig2.update_layout(
            yaxis=dict(categoryorder="array", categoryarray=top20["UNIVERSITY_ID"].tolist()[::-1], title=""),  # ← highest at the top
            xaxis=dict(range=[0, 1.12], title="DEA score"),
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
        )
        st.plotly_chart(style_fig(fig2, 640))

    st.caption(
        "Institutions at the top represent benchmark organisations that less efficient universities may compare themselves against."
    )

with tab3:

    if no_cost:
        st.info("No cost proxies apply to the selected inputs.")
    else:
        plot_df = results.assign(COST_M=results["TOTAL_COST"] / 1e6)

        fig3 = px.scatter(
            plot_df,
            x="COST_M",
            y="DEA",
            color="Frontier",
            size="DEA",
            size_max=18,
            color_discrete_map={"Frontier": BURGUNDY, "Non-frontier": ROSE},
            hover_name="UNIVERSITY_ID",
            hover_data={"COST_M": ":,.1f", "DEA": ":.3f", "Frontier": False, "Quadrant": True},
            labels={"COST_M": "Estimated total cost (€m)", "DEA": "DEA score"},
            title="Estimated cost against DEA efficiency",
        )
        fig3.add_vline(x=mean_cost / 1e6, line_dash="dash", line_color=INK, opacity=0.6)
        fig3.add_hline(y=mean_dea, line_dash="dash", line_color=INK, opacity=0.6)
        for text, x, y, xa, ya in [  # ← quadrant names drawn on the chart so the caption isn't needed to read it
            ("Best value for money", 0.01, 0.99, "left", "top"),
            ("Resource intensive", 0.99, 0.99, "right", "top"),
            ("Limited outputs", 0.01, 0.01, "left", "bottom"),
            ("Greatest potential for improvement", 0.99, 0.01, "right", "bottom"),
        ]:
            fig3.add_annotation(
                x=x, y=y, xref="x domain", yref="y domain", text=text, showarrow=False,
                xanchor=xa, yanchor=ya, font=dict(size=12, color="gray"),
            )
        fig3.update_yaxes(range=[-0.05, 1.2])  # ← headroom so the upper quadrant labels clear the frontier markers
        fig3.update_layout(legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"))
        st.plotly_chart(style_fig(fig3, 480))

        q = results["Quadrant"].value_counts()
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Best value for money", int(q.get("Best value for money", 0)), help="High efficiency, low cost")
        q2.metric("Resource intensive", int(q.get("Resource intensive", 0)), help="High efficiency, high cost")
        q3.metric("Limited outputs", int(q.get("Limited outputs", 0)), help="Low efficiency, low cost")
        q4.metric("Greatest potential", int(q.get("Greatest potential", 0)), help="Low efficiency, high cost")

        st.caption(
            "Dashed lines mark the sample means of cost and DEA. High cost in the upper-right quadrant "
            "may reflect scale or mission complexity rather than waste."
        )

        st.markdown("#### Universities with highest savings potential")

        top_savers = results.sort_values("POTENTIAL_SAVINGS", ascending=False).head(10)

        s1, s2 = st.columns([3, 2])

        with s1:
            fig_save = px.bar(
                top_savers.assign(SAVE_M=top_savers["POTENTIAL_SAVINGS"] / 1e6),
                x="SAVE_M",
                y="UNIVERSITY_ID",
                orientation="h",
                color_discrete_sequence=[BURGUNDY],
                labels={"SAVE_M": "Potential savings (€m)", "UNIVERSITY_ID": ""},
                title="Estimated cost savings potential (top 10)",
            )
            fig_save.update_traces(texttemplate="€%{x:,.0f}m", textposition="outside", cliponaxis=False)
            fig_save.update_layout(
                yaxis=dict(categoryorder="array", categoryarray=top_savers["UNIVERSITY_ID"].tolist()[::-1]),
                xaxis=dict(range=[0, top_savers["POTENTIAL_SAVINGS"].max() / 1e6 * 1.15]),  # ← headroom for the outside labels
            )
            st.plotly_chart(style_fig(fig_save, 460))

        with s2:
            st.dataframe(
                top_savers[["UNIVERSITY_ID", "DEA", "TOTAL_COST", "POTENTIAL_SAVINGS"]].assign(
                    TOTAL_COST=lambda d: d["TOTAL_COST"] / 1e6,
                    POTENTIAL_SAVINGS=lambda d: d["POTENTIAL_SAVINGS"] / 1e6,
                ),
                hide_index=True,
                column_config={
                    "UNIVERSITY_ID": "University",
                    "DEA": st.column_config.NumberColumn("DEA", format="%.3f"),
                    "TOTAL_COST": st.column_config.NumberColumn("Cost (€m)", format="%.1f"),
                    "POTENTIAL_SAVINGS": st.column_config.NumberColumn("Savings (€m)", format="%.1f"),
                },
            )
            st.caption(
                "Savings = estimated cost × (1 − DEA). A benchmarking gap, not a budget-cut recommendation."
            )

        st.markdown("#### Efficiency frontier")
        st.dataframe(
            frontier[["UNIVERSITY_ID", "DEA", "TOTAL_COST"]].assign(TOTAL_COST=lambda d: d["TOTAL_COST"] / 1e6),
            hide_index=True,
            column_config={
                "UNIVERSITY_ID": "University",
                "DEA": st.column_config.NumberColumn("DEA", format="%.3f"),
                "TOTAL_COST": st.column_config.NumberColumn("Estimated cost (€m)", format="%.1f"),
            },
        )

with tab4:

    selected_uni = st.selectbox(
        "University",
        results["UNIVERSITY_ID"].tolist(),
        key=f"selected_uni_{dataset}",  # ← per dataset: the THE sample is smaller, so a stored choice could vanish
    )

    selected_row = results[results["UNIVERSITY_ID"] == selected_uni].iloc[0]
    uni_score = selected_row["DEA"]
    pos = int(selected_row["_pos"])

    higher = (results["DEA_R"] > selected_row["DEA_R"]).sum()
    lower = (results["DEA_R"] < selected_row["DEA_R"]).sum()

    e1, e2 = st.columns([1, 1])

    with e1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=uni_score,
            number={'valueformat': '.3f'},
            gauge={
                'axis': {'range': [0, 1]},
                'bar': {'color': INK, 'thickness': 0.28},
                'steps': [
                    {'range': [0, 0.7], 'color': '#ffcccc'},
                    {'range': [0.7, 0.8], 'color': '#ffe5b4'},
                    {'range': [0.8, 0.9], 'color': '#fff4a3'},
                    {'range': [0.9, 1], 'color': '#c7f5c7'}
                ],
                'threshold': {
                    'line': {'width': 4},
                    'value': 1
                }
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=30, r=30, t=50, b=10), title="DEA efficiency score")
        st.plotly_chart(fig_gauge)

    with e2:
        st.markdown(f"### {selected_uni}")
        st.markdown(f"**{band(uni_score)}**")
        st.markdown(
            f"Outperforms **{lower}** universities and is outperformed by **{higher}**."
        )

        k1, k2, k3 = st.columns(3)
        k1.metric("DEA score", f"{uni_score:.3f}")
        k2.metric("Rank", f"{int(selected_row['Rank'])} of {len(results)}")
        k3.metric("Percentile", f"{selected_row['Percentile']:.0f}%")

        percentile = selected_row["Percentile"]
        st.progress(percentile / 100)
        if percentile >= 90:
            st.success("Top 10% of universities")
        elif percentile >= 75:
            st.info("Top quartile")
        elif percentile >= 50:
            st.warning("Above median")
        else:
            st.error("Below median")

    # =========================
    # SAVINGS INTERPRETATION
    # =========================

    st.divider()

    savings = selected_row["POTENTIAL_SAVINGS"]
    cost = selected_row["TOTAL_COST"]
    savings_pct = max(0.0, (1 - uni_score) * 100)

    f1, f2 = st.columns([1, 1])

    with f1:
        st.markdown("#### 💰 Cost efficiency insight")
        c1, c2 = st.columns(2)
        c1.metric("Estimated cost", eur(cost))
        c2.metric("Estimated inefficiency cost", eur(savings))
        st.markdown(
            f"""
Relative to the DEA efficiency frontier, this university may be operating with approximately
**{savings_pct:.1f}% excess resource usage** on the selected inputs.

If it reached the frontier (DEA = 1.0), it could *theoretically* reduce resource usage by up to
**{eur(savings)} annually**. This is not a budget cut recommendation, but a **benchmarking gap estimate**
showing potential reallocation efficiency.
            """
        )

    with f2:
        st.markdown("#### Estimated cost by input")
        breakdown = cost_matrix.iloc[pos]
        breakdown = breakdown[breakdown > 0].sort_values()
        if breakdown.empty:
            st.caption("None of the selected inputs carries a cost proxy.")
        else:
            fig_b = px.bar(
                x=breakdown.values / 1e6,
                y=[label(c) for c in breakdown.index],
                orientation="h",
                color_discrete_sequence=[BURGUNDY],
                labels={"x": "€m per year", "y": ""},
            )
            fig_b.update_traces(texttemplate="€%{x:,.1f}m", textposition="outside", cliponaxis=False)
            fig_b.update_xaxes(range=[0, breakdown.max() / 1e6 * 1.25])  # ← headroom for the outside labels
            st.plotly_chart(style_fig(fig_b, 60 + 48 * len(breakdown)))

    # =========================
    # BENCHMARK
    # =========================

    st.divider()
    st.markdown("#### Benchmark university")

    lam = lambdas[pos]
    uid = df["UNIVERSITY_ID"].values
    peers = sorted(
        [(uid[j], lam[j]) for j in range(len(lam)) if j != pos and np.isfinite(lam[j]) and lam[j] > 1e-6],
        key=lambda t: -t[1],
    )

    if uni_score >= 0.999:
        st.caption("This university is on the frontier, so it acts as its own benchmark. Pick any comparator below.")
    elif peers:
        st.caption(
            "DEA reference set: the frontier universities whose weighted combination (λ) forms this university's benchmark."
        )
        st.markdown(
            "".join(f'<span class="peer">{p} · λ = {w:.2f}</span>' for p, w in peers),
            unsafe_allow_html=True,
        )

    others = [u for u in results["UNIVERSITY_ID"] if u != selected_uni]
    default_bench = peers[0][0] if peers else others[0]  # ← default to the dominant DEA peer, not simply the top-ranked row

    bench_uni = st.selectbox(
        "Compare against",
        others,
        index=others.index(default_bench),
        key=f"bench_{dataset}_{selected_uni}",  # ← keyed on the selection so the default follows the university
    )

    bench_row = results[results["UNIVERSITY_ID"] == bench_uni].iloc[0]
    bpos = int(bench_row["_pos"])

    raw = df[selected_inputs + selected_outputs].apply(pd.to_numeric, errors="coerce")

    comp = pd.DataFrame(
        {
            selected_uni: [f"{uni_score:.3f}", eur(cost)]
            + [fmt_num(v) for v in raw.iloc[pos]],
            bench_uni: [f"{bench_row['DEA']:.3f}", eur(bench_row['TOTAL_COST'])]
            + [fmt_num(v) for v in raw.iloc[bpos]],
        },
        index=["DEA score", "Estimated cost"]
        + [label(c) for c in selected_inputs]
        + [OUTPUT_LABELS.get(o, o) for o in selected_outputs],
    )
    st.dataframe(comp)
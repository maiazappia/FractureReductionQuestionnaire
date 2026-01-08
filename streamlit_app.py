# app.py
import streamlit as st
import csv
import os
import re
from datetime import datetime
import uuid

APP_VERSION = "forms-saved-values-v1"
st.set_page_config(page_title="Questionnaire — Fracture Reduction", layout="centered")
st.write("APP_VERSION:", APP_VERSION)

# --- CONFIG ---
PARAMETERS = [
    "Time taken (total procedure)",
    "Accuracy of fragment positioning (translational error vs reference)",
    "Accuracy of fragment rotation (rotational error vs reference)",
    "Number of moves (how many fragment manipulations)",
    "Order of fragment movements (efficient sequencing)",
]
RESPONSES_CSV = "submissions_new.csv"

# --- helper: safe keys for session_state ---
def key_for(prefix: str, label: str) -> str:
    safe = re.sub(r'\W+', '_', label).strip('_').lower()
    return f"{prefix}{safe}"

# --- session_state initialization (only if missing) ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "error" not in st.session_state:
    st.session_state.error = ""

# initialize widget keys only if missing (do not overwrite saved copies)
for p in PARAMETERS:
    rk = key_for("rank_", p)
    pk = key_for("points_", p)
    lk = key_for("likert_", p)
    if rk not in st.session_state:
        st.session_state[rk] = 1
    if pk not in st.session_state:
        st.session_state[pk] = 0
    if lk not in st.session_state:
        st.session_state[lk] = 4

# --- CSV saving ---
def save_submission_to_csv(results):
    file_exists = os.path.isfile(RESPONSES_CSV)
    write_header = not file_exists or os.path.getsize(RESPONSES_CSV) == 0
    with open(RESPONSES_CSV, mode="a", newline="", encoding="utf-8") as f:
        fieldnames = ["submission_id", "timestamp_utc", "parameter_label", "rank", "points", "likert"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        submission_id = str(uuid.uuid4())
        ts = datetime.utcnow().isoformat() + "Z"
        for r in results:
            row = {
                "submission_id": submission_id,
                "timestamp_utc": ts,
                "parameter_label": r["parameter_label"],
                "rank": r["rank"],
                "points": r["points"],
                "likert": r["likert"],
            }
            writer.writerow(row)

# --- helpers / navigation ---
def reset_all():
    for p in PARAMETERS:
        for prefix in ("rank_", "points_", "likert_"):
            key = key_for(prefix, p)
            if key in st.session_state:
                del st.session_state[key]
    # remove saved snapshots if any
    for k in ("saved_ranks", "saved_points"):
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.submitted = False
    st.session_state.error = ""
    st.session_state.page = "home"
    # re-init defaults
    for p in PARAMETERS:
        st.session_state[key_for("rank_", p)] = 1
        st.session_state[key_for("points_", p)] = 0
        st.session_state[key_for("likert_", p)] = 4

def validate_ranks(ranks):
    if any(v is None for v in ranks):
        return "Please assign all rankings (1-5)."
    if len(set(ranks)) != len(ranks):
        return "Rankings must be unique: assign 1..5 without repetitions."
    if set(ranks) != set([1,2,3,4,5]):
        return "Rankings must cover exactly the values 1,2,3,4,5."
    return None

def validate_points(points):
    try:
        pints = [int(x) for x in points]
    except Exception:
        return "Error in points: use valid integers."
    total = sum(pints)
    if total != 100:
        return f"The sum of points must be 100 (now: {total})."
    return None

# --- PAGES USING FORMS (BUT SAVE VALUES EXPLICITLY) ---
def show_home():
    st.title("Critical parameters in virtual fracture reduction")
    st.write(
        "This research project aims to develop software for training orthopaedic residents in tibial plateau and calcaneal fracture reduction through a virtual, simulation-based approach. We aim to identify how expert orthopaedic surgeons weight different performance parameters. The results will be used to build a performance score and to prioritize which metrics matter most. Your answers are anonymous and will be aggregated. The questionnaire takes a few minutes. Thank you for your participation!"
    )
    st.markdown("---")
    if st.button("Start"):
        st.session_state.page = "ranking"

def show_ranking():
    st.header("Ranking task")
    st.write("Rank the parameters from 1 (most important) to 5 (least important) for inclusion and weight in a performance score measuring a surgeon’s quality of fracture reduction.")
    st.write("Parameters:")
    for p in PARAMETERS:
        st.write(f"- {p}")

    with st.form(key="ranking_form"):
        # Use widget keys as before; when submitted save explicitly to saved_ranks
        for p in PARAMETERS:
            st.selectbox(label=p, options=[1,2,3,4,5], key=key_for("rank_", p))
        submitted = st.form_submit_button("Next")
        if submitted:
            ranks = {p: int(st.session_state.get(key_for("rank_", p))) for p in PARAMETERS}
            err = validate_ranks(list(ranks.values()))
            if err:
                st.session_state.error = err
            else:
                st.session_state["saved_ranks"] = ranks  # <--- crucial: persist snapshot
                st.session_state.error = ""
                st.session_state.page = "points"
                print("DEBUG: saved_ranks:", st.session_state["saved_ranks"])

    if st.session_state.error:
        st.error(st.session_state.error)

def show_points():
    st.header("Points allocation")
    st.write("Now, distribute 100 points across the five parameters to indicate their relative importance for the performance score. (Total must be 100.)")

    with st.form(key="points_form"):
        for p in PARAMETERS:
            st.number_input(
                label=p,
                min_value=0,
                max_value=100,
                step=1,
                format="%d",
                key=key_for("points_", p)
            )
        total_points = sum(int(st.session_state.get(key_for("points_", p), 0)) for p in PARAMETERS)
        st.info(f"Current total points: {total_points}")
        submitted = st.form_submit_button("Next")
        if submitted:
            points_map = {p: int(st.session_state.get(key_for("points_", p), 0)) for p in PARAMETERS}
            err = validate_points(list(points_map.values()))
            if err:
                st.session_state.error = err
            else:
                st.session_state["saved_points"] = points_map  # <--- persist snapshot of points
                st.session_state.error = ""
                st.session_state.page = "likert"
                print("DEBUG: saved_points:", st.session_state["saved_points"])

    if st.session_state.error:
        st.error(st.session_state.error)

def show_likert():
    st.header("Likert ratings")
    st.write("For each parameter, indicate how important it is to include it in a performance score (1 = Not important, 7 = Extremely important).")

    with st.form(key="likert_form"):
        for p in PARAMETERS:
            st.slider(
                label=p,
                min_value=1,
                max_value=7,
                step=1,
                key=key_for("likert_", p)
            )
        submitted = st.form_submit_button("Submit responses")
        if submitted:
            # Build snapshot using saved values if available, otherwise fallback to current widget keys
            snapshot = {}
            for p in PARAMETERS:
                rank_val = None
                points_val = None
                # prefer saved snapshots (these are the values user submitted in previous forms)
                if "saved_ranks" in st.session_state:
                    rank_val = st.session_state["saved_ranks"].get(p)
                else:
                    rank_val = st.session_state.get(key_for("rank_", p))
                if "saved_points" in st.session_state:
                    points_val = st.session_state["saved_points"].get(p)
                else:
                    points_val = st.session_state.get(key_for("points_", p), 0)

                likert_val = st.session_state.get(key_for("likert_", p))
                snapshot[p] = {
                    "rank_key": key_for("rank_", p),
                    "points_key": key_for("points_", p),
                    "likert_key": key_for("likert_", p),
                    "rank_value": rank_val,
                    "points_value": points_val,
                    "likert_value": likert_val,
                }

            # validate likerts present
            if any(v["likert_value"] is None for v in snapshot.values()):
                st.session_state.error = "Please complete all Likert ratings."
            else:
                # prepare results ensuring we convert saved values to int
                results = []
                try:
                    for p in PARAMETERS:
                        results.append({
                            "parameter_label": p,
                            "rank": int(snapshot[p]["rank_value"]),
                            "points": int(snapshot[p]["points_value"]),
                            "likert": int(snapshot[p]["likert_value"]),
                        })
                except Exception as e:
                    st.session_state.error = f"Error preparing results: {e}"
                    st.error(st.session_state.error)
                    return

                # save
                try:
                    save_submission_to_csv(results)
                except Exception as e:
                    st.session_state.error = f"Failed to save submission: {e}"
                    st.error(st.session_state.error)
                    return

                st.session_state.results = results
                st.session_state.submitted = True
                st.session_state.error = ""
                st.session_state.page = "results"

    if st.session_state.error:
        st.error(st.session_state.error)

def show_results():
    st.success("Thank you — your responses have been recorded.")
    if "results" in st.session_state:
        st.write("Your submitted values:")
        st.table(st.session_state.results)

def show_admin():
    st.header("Admin — All responses")
    if not os.path.isfile(RESPONSES_CSV):
        st.info("No submissions yet.")
        return

    rows = []
    with open(RESPONSES_CSV, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        st.info("No submissions yet.")
        return

    st.write(f"Total rows: {len(rows)}")
    st.dataframe(rows)
    with open(RESPONSES_CSV, mode="rb") as f:
        csv_bytes = f.read()
    st.download_button("Download all responses (CSV)", data=csv_bytes, file_name=RESPONSES_CSV, mime="text/csv")

# --- Router ---
query_params = st.query_params
is_admin_mode = query_params.get("admin", ["0"])[0] == "1"

if is_admin_mode:
    show_admin()
else:
    if st.session_state.page == "home":
        show_home()
    elif st.session_state.page == "ranking":
        show_ranking()
    elif st.session_state.page == "points":
        show_points()
    elif st.session_state.page == "likert":
        show_likert()
    elif st.session_state.page == "results":
        if st.session_state.submitted:
            show_results()
        else:
            st.info("No results submitted yet. Go back to the previous page to complete the questionnaire.")
            if st.button("Return to questionnaire"):
                st.session_state.page = "ranking"

# Note: persistence on cloud may require DB or Google Sheets; local file may be ephemeral in some hosts.

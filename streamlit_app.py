import streamlit as st
import io
import csv
import os
from datetime import datetime
import uuid

st.set_page_config(page_title="Questionnaire — Fracture Reduction", layout="centered")

# PARAMETERS (using exact labels from your text)
PARAMETERS = [
    "Time taken (total procedure)",
    "Accuracy of fragment positioning (translational error vs reference)",
    "Accuracy of fragment rotation (rotational error vs reference)",
    "Number of moves (how many fragment manipulations)",
    "Order of fragment movements (efficient sequencing)",
]

# CSV file for storing submissions
RESPONSES_CSV = "submissions.csv"

# init session state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "error" not in st.session_state:
    st.session_state.error = ""

# initialize inputs if missing
for p in PARAMETERS:
    rank_key = f"rank_{p}"
    points_key = f"points_{p}"
    likert_key = f"likert_{p}"
    if rank_key not in st.session_state:
        st.session_state[rank_key] = 1
    if points_key not in st.session_state:
        st.session_state[points_key] = 0.0
    if likert_key not in st.session_state:
        st.session_state[likert_key] = 4

def save_submission_to_csv(results):
    """
    Append a submission to RESPONSES_CSV.
    Each row contains: submission_id, timestamp_utc, parameter_label, rank, points, likert
    """
    file_exists = os.path.isfile(RESPONSES_CSV)
    write_header = not file_exists or os.path.getsize(RESPONSES_CSV) == 0

    with open(RESPONSES_CSV, mode="a", newline="", encoding="utf-8") as f:
        fieldnames = ["submission_id", "timestamp_utc", "parameter_label", "rank", "points", "likert"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        submission_id = str(uuid.uuid4())
        ts = datetime.utcnow().isoformat()
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

def go_to(page):
    st.session_state.page = page

def reset_all():
    for p in PARAMETERS:
        for prefix in ("rank_", "points_", "likert_"):
            key = prefix + p
            if key in st.session_state:
                del st.session_state[key]
    st.session_state.submitted = False
    st.session_state.error = ""
    st.session_state.page = "home"

def validate_and_next_from_ranking():
    # validate ranks unique and cover 1..5
    ranks = [st.session_state.get(f"rank_{p}") for p in PARAMETERS]
    if any(v is None for v in ranks):
        st.session_state.error = "Please assign all rankings (1-5)."
        return
    if len(set(ranks)) != len(ranks):
        st.session_state.error = "Rankings must be unique: assign 1, 2, 3, 4, 5 without repetitions."
        return
    if set(ranks) != set([1,2,3,4,5]):
        st.session_state.error = "Rankings must cover exactly the values 1,2,3,4,5."
        return
    st.session_state.error = ""
    st.session_state.page = "points"

def validate_and_next_from_points():
    points = [st.session_state.get(f"points_{p}", 0) for p in PARAMETERS]
    try:
        total = sum(float(p) for p in points)
    except Exception:
        st.session_state.error = "Error in points: use valid numbers."
        return
    if int(round(total)) != 100:
        st.session_state.error = f"The sum of points must be 100 (now: {total})."
        return
    st.session_state.error = ""
    st.session_state.page = "likert"

def submit_from_likert():
    likerts = [st.session_state.get(f"likert_{p}") for p in PARAMETERS]
    if any(v is None for v in likerts):
        st.session_state.error = "Please complete all Likert ratings."
        return
    # prepare results and mark submitted
    results = []
    for p in PARAMETERS:
        results.append({
            "parameter_label": p,
            "rank": int(st.session_state.get(f"rank_{p}")),
            "points": float(st.session_state.get(f"points_{p}")),
            "likert": int(st.session_state.get(f"likert_{p}")),
        })

    # SAVE to CSV (central storage)
    try:
        save_submission_to_csv(results)
    except Exception as e:
        st.session_state.error = f"Failed to save submission: {e}"
        return

    st.session_state.results = results
    st.session_state.submitted = True
    st.session_state.error = ""
    st.session_state.page = "results"

# --- Pages ---

def show_home():
    st.title("Critical parameters in virtual fracture reduction")
    st.write(
        "This research project aims to develop software for training orthopaedic residents in tibial plateau and calcaneal fracture reduction through a virtual, simulation-based approach. We aim to identify how expert orthopaedic surgeons weight different performance parameters. The results will be used to build a performance score and to prioritize which metrics matter most. Your answers are anonymous and will be aggregated. The questionnaire takes a few minutes. Thank you for your participation!"
    )
    st.markdown("---")
    st.button("Start", on_click=lambda: st.session_state.update(page="ranking"))

def show_ranking():
    st.header("Ranking task")
    st.write("Rank the parameters from 1 (most important) to 5 (least important) for inclusion and weight in a performance score measuring a surgeon’s quality of fracture reduction.")
    st.write("Parameters:")
    for p in PARAMETERS:
        st.write(f"- {p}")

    # layout the selectboxes
    for p in PARAMETERS:
        st.selectbox(
            label=p,
            options=[1,2,3,4,5],
            key=f"rank_{p}"
        )

    st.markdown("---")
    st.button("Next", on_click=validate_and_next_from_ranking)

    if st.session_state.error:
        st.error(st.session_state.error)

def show_points():
    st.header("Points allocation")
    st.write("Now, distribute 100 points across the five parameters to indicate their relative importance for the performance score. (Total must be 100.)")

    for p in PARAMETERS:
        st.number_input(
            label=p,
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key=f"points_{p}"
        )

    total_points = sum(st.session_state.get(f"points_{p}", 0) for p in PARAMETERS)
    st.info(f"Current total points: {total_points}")

    st.markdown("---")
    st.button("Next", on_click=validate_and_next_from_points)

    if st.session_state.error:
        st.error(st.session_state.error)

def show_likert():
    st.header("Likert ratings")
    st.write("For each parameter, indicate how important it is to include it in a performance score (1 = Not important, 7 = Extremely important).")
    
    for p in PARAMETERS:
        st.slider(
            label=p,
            min_value=1,
            max_value=7,
            step=1,
            key=f"likert_{p}"
        )

    st.markdown("---")
    st.button("Submit responses", on_click=submit_from_likert)

    if st.session_state.error:
        st.error(st.session_state.error)

def show_results():
    st.success("Thank you — your responses have been recorded.")
    
def show_admin():
    """
    Admin view: requires query param ?admin=1
    Displays all submissions and allows download of submissions.csv
    """
    st.header("Admin — All responses")
    if not os.path.isfile(RESPONSES_CSV):
        st.info("No submissions yet.")
        return

    # read CSV
    rows = []
    with open(RESPONSES_CSV, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        st.info("No submissions yet.")
        return

    # show basic stats
    st.write(f"Total rows: {len(rows)}")
    # display table (Streamlit will render a nice table)
    st.dataframe(rows)

    # download button (raw file)
    with open(RESPONSES_CSV, mode="rb") as f:
        csv_bytes = f.read()
    st.download_button("Download all responses (CSV)", data=csv_bytes, file_name=RESPONSES_CSV, mime="text/csv")

# Router (with admin access via query param ?admin=1)
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
            st.button("Return to questionnaire", on_click=lambda: st.session_state.update(page="ranking"))

# Short note for operator (shown in console only)
# If you deploy on a cloud service, note that local filesystem may be ephemeral.
# For persistent, multi-user deployments prefer Google Sheets / a database.

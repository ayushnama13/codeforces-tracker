import streamlit as st
import pandas as pd
import plotly.express as px
from revision_store import (
    load_revision_problems,
    add_revision_by_id,
    remove_revision_problem,
    load_hidden_problems,
    hide_problem,
)



from config import HANDLE, FOCUS_TAGS
from data import fetch_submissions, preprocess


st.set_page_config(page_title="CF Analyzer", layout="wide")
st.title("Codeforces Profile Analyzer")
st.caption("Complete analytics • Weakness detection • Training guidance")

# ---------- DATA ----------


@st.cache_data
def load_data():
    subs = fetch_submissions(HANDLE)
    return preprocess(subs)


(
    df,
    verdicts,
    monthly,
    attempts,
    ac,
    contest_tag,
    practice_tag,
    problem_history,
) = load_data()

# ---------- METRICS ----------

c1, c2, c3 = st.columns(3)
c1.metric("Problems Solved", len(df))
c2.metric("Average Rating", int(df["rating"].mean()))
c3.metric("Max Rating", int(df["rating"].max()))

st.divider()

# ---------- RATING DISTRIBUTION ----------

st.plotly_chart(
    px.histogram(df, x="rating", title="Overall Rating Distribution"),
    use_container_width=True,
)

# ---------- FOCUS TAG OVERVIEW ----------

tags_exploded = df.explode("tags")

focus_df = (
    tags_exploded[tags_exploded["tags"].isin(FOCUS_TAGS)]["tags"]
    .value_counts()
    .reindex(FOCUS_TAGS, fill_value=0)
    .reset_index()
)
focus_df.columns = ["Tag", "Solved"]

st.plotly_chart(
    px.bar(
        focus_df,
        x="Tag",
        y="Solved",
        title="Focus Tags – Problems Solved",
        text="Solved",
    ),
    use_container_width=True,
)

# ---------- TAG → RATING ----------

st.subheader("Tag-wise Rating Breakdown")
selected_tag = st.selectbox("Select focus tag", FOCUS_TAGS)

tag_df = tags_exploded[tags_exploded["tags"] == selected_tag]
rating_df = tag_df["rating"].value_counts().sort_index().reset_index()
rating_df.columns = ["Rating", "Solved"]

st.plotly_chart(
    px.bar(
        rating_df,
        x="Rating",
        y="Solved",
        title=f"{selected_tag.upper()} – Rating Distribution",
        text="Solved",
    ),
    use_container_width=True,
)

# ---------- REVISION MODE ----------

st.subheader("Revision Mode (Tag-wise)")

all_tags = sorted({t for p in problem_history.values() for t in p["tags"]})
rev_tag = st.selectbox("Select a tag to revise", all_tags)

rows = []
hidden = load_hidden_problems()

st.markdown("### Problems to Revise")

for idx, p in enumerate(problem_history.values()):
    if rev_tag not in p["tags"]:
        continue

    if (p["contestId"], p["index"]) in hidden:
        continue

    col1, col2, col3, col4, col5 = st.columns([4, 1, 2, 2, 1])

    with col1:
        st.markdown(
            f"<a href='https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}' "
            f"target='_blank'>{p['name']}</a>",
            unsafe_allow_html=True,
        )

    with col2:
        st.write(p["rating"])

    with col3:
        st.write(f"{p['contestId']}{p['index']}")

    with col4:
        st.write(p["last_solved"].strftime("%Y-%m-%d"))

    with col5:
        if st.button(
            "Hide",
            key=f"hide_auto_{p['contestId']}_{p['index']}_{idx}",
        ):
            hide_problem(p["contestId"], p["index"])
            st.experimental_rerun()


rev_df = pd.DataFrame(
    rows,
    columns=[
        "Problem Name",
        "Rating",
        "Problem ID",
        "First Solved On",
        "Last Solved On",
    ],
).sort_values("First Solved On")

st.markdown(rev_df.to_html(escape=False, index=False), unsafe_allow_html=True)


# ================= MANUAL REVISION BACKLOG ================= #

st.subheader("Revision Backlog (Manual)")

with st.expander("➕ Add problem by ID (e.g. 1784D)"):
    prob_id = st.text_input("Problem ID", placeholder="1784D")

    if st.button("Add to Revision List"):
        try:
            add_revision_by_id(prob_id.strip())
            st.success(f"{prob_id} added to revision list")
        except Exception as e:
            st.error(str(e))

# ---------- VIEW REVISION BACKLOG ----------

st.subheader("Your Revision Problems")

revision_problems = load_revision_problems()
rev_df = pd.DataFrame(revision_problems)

if rev_df.empty:
    st.info("No revision problems added yet.")
else:
    # convert last_solved to datetime
    rev_df["last_solved"] = pd.to_datetime(rev_df["last_solved"])

    # ---------- FILTERS ----------
    filter_mode = st.selectbox(
        "Filter revision problems by",
        ["None", "Tag", "Rating"],
    )

    if filter_mode == "Tag":
        all_tags = sorted({t for tags in rev_df["tags"] for t in tags})
        selected_tag = st.selectbox("Select tag", all_tags)
        rev_df = rev_df[rev_df["tags"].apply(lambda x: selected_tag in x)]

    elif filter_mode == "Rating":
        min_r, max_r = st.slider(
            "Rating range",
            0,
            3500,
            (800, 1600),
            step=100,
        )
        rev_df = rev_df[(rev_df["rating"] >= min_r) & (rev_df["rating"] <= max_r)]

    # ---------- SORT (NEWEST ON TOP) ----------
    rev_df = rev_df.sort_values("last_solved", ascending=False)

    # ---------- CLICKABLE LINKS ----------
    rev_df["Problem"] = rev_df.apply(
        lambda r: (f"<a href='{r['url']}' target='_blank'>{r['name']}</a>"),
        axis=1,
    )

    display_df = rev_df[["Problem", "rating", "tags", "last_solved"]]

    st.markdown("### Revision Problems List")

    for _, row in rev_df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([4, 1, 2, 2, 1])

        with col1:
            st.markdown(
                f"<a href='{row['url']}' target='_blank'>{row['name']}</a>",
                unsafe_allow_html=True,
            )

        with col2:
            st.write(row["rating"])

        with col3:
            st.write(", ".join(row["tags"]))

        with col4:
            st.write(row["last_solved"].strftime("%Y-%m-%d"))

        with col5:
            if st.button(
                "Remove",
                key=f"remove_{row['contestId']}_{row['index']}_{_}",
            ):

                remove_revision_problem(row["contestId"], row["index"])
                st.experimental_rerun()


# ---------- MONTHLY PROGRESS ----------

st.subheader("Monthly Solving Progress")

monthly_df = pd.DataFrame(
    {"Month": monthly.keys(), "Solved": monthly.values()}
).sort_values("Month")

st.plotly_chart(
    px.line(
        monthly_df,
        x="Month",
        y="Solved",
        markers=True,
        title="Monthly Problems Solved",
    ),
    use_container_width=True,
)
# ---------- VERDICT DISTRIBUTION ----------

st.subheader("Submission Verdict Distribution")

verdict_df = pd.DataFrame({"Verdict": verdicts.keys(), "Count": verdicts.values()})

st.plotly_chart(
    px.bar(
        verdict_df,
        x="Verdict",
        y="Count",
        text="Count",
        title="Verdict Distribution",
    ),
    use_container_width=True,
)
# ---------- CONTEST vs PRACTICE ----------

st.subheader("Contest vs Practice Solves")

cp_df = pd.DataFrame(
    {
        "Tag": FOCUS_TAGS,
        "Contest": [contest_tag[t] for t in FOCUS_TAGS],
        "Practice": [practice_tag[t] for t in FOCUS_TAGS],
    }
)

st.dataframe(cp_df, use_container_width=True)

st.plotly_chart(
    px.bar(
        cp_df,
        x="Tag",
        y=["Contest", "Practice"],
        barmode="group",
        title="Contest vs Practice (Tag-wise)",
    ),
    use_container_width=True,
)
# ---------- WEAK TAG DETECTION ----------

st.subheader("Weak Tag Detection")

weak_rows = []
for tag in FOCUS_TAGS:
    if attempts[tag] >= 10:
        ratio = ac[tag] / attempts[tag]
        weak_rows.append([tag, attempts[tag], ac[tag], round(ratio, 2)])

weak_df = pd.DataFrame(
    weak_rows,
    columns=["Tag", "Attempts", "Solved", "AC Ratio"],
).sort_values("AC Ratio")

st.dataframe(weak_df, use_container_width=True)

st.plotly_chart(
    px.bar(
        weak_df,
        x="Tag",
        y="AC Ratio",
        text="AC Ratio",
        title="Weak Tags (Lower AC Ratio = Weaker)",
    ),
    use_container_width=True,
)
# ---------- DIFFICULTY HEATMAP ----------

st.subheader("Difficulty Heatmap (Tag × Rating)")

heat_rows = []
for _, row in df.iterrows():
    for tag in row["tags"]:
        if tag in FOCUS_TAGS:
            heat_rows.append([tag, row["rating"]])

heat_df = pd.DataFrame(heat_rows, columns=["Tag", "Rating"])
heat_df["Count"] = 1
heat_df = heat_df.groupby(["Tag", "Rating"]).count().reset_index()

st.plotly_chart(
    px.density_heatmap(
        heat_df,
        x="Rating",
        y="Tag",
        z="Count",
        color_continuous_scale="Blues",
        title="Tag × Rating Heatmap",
    ),
    use_container_width=True,
)

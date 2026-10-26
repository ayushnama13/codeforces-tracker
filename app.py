import pandas as pd
import plotly.express as px
import streamlit as st

from config import FOCUS_TAGS, HANDLE
from data import fetch_submissions, preprocess
from revision_store import (
    add_revision_by_id,
    hide_problem,
    load_hidden_problems,
    load_revision_problems,
    remove_revision_problem,
)

st.set_page_config(page_title="CF Analyzer", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {
        background: #fff; border: 1px solid #d0d7de; border-radius: 10px;
        padding: 14px 18px;
    }
    [data-testid="stMetricLabel"] {color: #656d76;}
    [data-testid="stVerticalBlockBorderWrapper"] {background: #fff; border-radius: 10px;}
    h1 {font-size: 1.8rem !important;}
    h3 {font-size: 1.05rem !important; margin-bottom: 0 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

CHART_H = 340


def style(fig, height=CHART_H):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        title_font_size=15,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def card(fig):
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch")


# ---------- SIDEBAR ----------

with st.sidebar:
    st.header("Settings")
    handle = st.text_input("Codeforces handle", HANDLE, key="handle").strip() or HANDLE
    if st.button("Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.subheader("Heatmap filters")
    n_contests = st.number_input("Last N contests", min_value=1, value=100, step=10)

# ---------- DATA ----------


@st.cache_data(ttl=600)
def load_data(handle):
    return preprocess(fetch_submissions(handle))


@st.cache_data
def load_all_problems():
    return pd.read_csv("codeforces_all_problems.csv")


try:
    (
        df,
        verdicts,
        monthly,
        attempts,
        ac,
        contest_tag,
        practice_tag,
        problem_history,
    ) = load_data(handle)
except Exception as e:
    st.error(f"Could not load data for '{handle}': {e}")
    st.stop()

if df.empty:
    st.warning(f"No solved problems found for '{handle}'.")
    st.stop()

all_probs = load_all_problems()
all_probs = all_probs[
    (all_probs["phase"] == "FINISHED") & all_probs["rating"].notna()
].copy()
all_probs["letter"] = all_probs["problemIndex"].str[0]
all_probs["rating"] = all_probs["rating"].astype(int)

with st.sidebar:
    divs = st.multiselect(
        "Divisions",
        sorted(all_probs["division"].unique()),
        default=["Div2", "Div1+Div2", "Div3", "Div4", "Educational"],
    )

# ---------- HEADER ----------

st.title("Codeforces Profile Analyzer")
st.caption(f"**{handle}** · analytics · weakness detection · training guidance")

rated = df["rating"].dropna()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Problems solved", len(df))
m2.metric("Average rating", int(rated.mean()) if len(rated) else 0)
m3.metric("Max rating", int(rated.max()) if len(rated) else 0)
m4.metric("Contests tracked", len(all_probs["contestId"].unique()))

tab_over, tab_heat, tab_rev, tab_perf = st.tabs(
    ["Overview", "Heatmaps", "Revision", "Performance"]
)

tags_exploded = df.explode("tags")

# ---------- OVERVIEW ----------

with tab_over:
    c1, c2 = st.columns(2)
    with c1:
        card(
            style(
                px.histogram(
                    df, x="rating", nbins=30, title="Rating distribution"
                )
            )
        )
    with c2:
        focus_df = (
            tags_exploded[tags_exploded["tags"].isin(FOCUS_TAGS)]["tags"]
            .value_counts()
            .reindex(FOCUS_TAGS, fill_value=0)
            .reset_index()
        )
        focus_df.columns = ["Tag", "Solved"]
        card(
            style(
                px.bar(
                    focus_df,
                    x="Solved",
                    y="Tag",
                    orientation="h",
                    text="Solved",
                    title="Focus tags solved",
                ).update_yaxes(autorange="reversed")
            )
        )

    c3, c4 = st.columns(2)
    with c3:
        monthly_df = pd.DataFrame(
            {"Month": list(monthly.keys()), "Solved": list(monthly.values())}
        ).sort_values("Month")
        card(
            style(
                px.line(
                    monthly_df,
                    x="Month",
                    y="Solved",
                    markers=True,
                    title="Monthly problems solved",
                )
            )
        )
    with c4:
        verdict_df = pd.DataFrame(
            {"Verdict": list(verdicts.keys()), "Count": list(verdicts.values())}
        ).sort_values("Count", ascending=False)
        card(
            style(
                px.bar(
                    verdict_df,
                    x="Verdict",
                    y="Count",
                    text="Count",
                    title="Verdict distribution",
                )
            )
        )

    with st.container(border=True):
        st.markdown("### Tag-wise rating breakdown")
        selected_tag = st.selectbox("Focus tag", FOCUS_TAGS)
        rating_df = (
            tags_exploded[tags_exploded["tags"] == selected_tag]["rating"]
            .value_counts()
            .sort_index()
            .reset_index()
        )
        rating_df.columns = ["Rating", "Solved"]
        st.plotly_chart(
            style(
                px.bar(
                    rating_df,
                    x="Rating",
                    y="Solved",
                    text="Solved",
                    title=f"{selected_tag.title()} – rating distribution",
                ),
                height=300,
            ),
            width="stretch",
        )

# ---------- HEATMAPS ----------

with tab_heat:
    pool = all_probs[all_probs["division"].isin(divs)]
    recent_ids = (
        pool.drop_duplicates("contestId")
        .sort_values("startTime", ascending=False)
        .head(int(n_contests))["contestId"]
    )
    recent = pool[pool["contestId"].isin(recent_ids)]
    st.caption(
        f"Last {int(n_contests)} contests in selected divisions "
        f"({recent['contestId'].nunique()} contests, {len(recent)} rated problems). "
        "Change N and divisions in the sidebar."
    )

    if recent.empty:
        st.info("No problems match the current filters.")
    else:
        letter_grid = pd.crosstab(recent["letter"], recent["rating"])
        card(
            style(
                px.imshow(
                    letter_grid,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Blues",
                    labels=dict(x="Rating", y="Problem letter", color="Count"),
                    title="Problem letter × rating",
                ),
                height=max(320, 32 * len(letter_grid) + 120),
            )
        )

        tag_rows = (
            recent.assign(tag=recent["tags"].str.split(";"))
            .explode("tag")
            .dropna(subset=["tag"])
            .reset_index(drop=True)
        )
        tag_grid = pd.crosstab(tag_rows["tag"], tag_rows["rating"])
        card(
            style(
                px.imshow(
                    tag_grid,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Blues",
                    labels=dict(x="Rating", y="Tag", color="Count"),
                    title="Tag × rating",
                ),
                height=max(400, 24 * len(tag_grid) + 120),
            )
        )

    heat_rows = [
        [tag, row["rating"]]
        for _, row in df.iterrows()
        if pd.notna(row["rating"])
        for tag in row["tags"]
        if tag in FOCUS_TAGS
    ]
    if heat_rows:
        mine = pd.crosstab(
            pd.DataFrame(heat_rows, columns=["Tag", "Rating"])["Tag"],
            pd.DataFrame(heat_rows, columns=["Tag", "Rating"])["Rating"],
        )
        card(
            style(
                px.imshow(
                    mine,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Greens",
                    labels=dict(x="Rating", y="Tag", color="Solved"),
                    title=f"Your solves: focus tag × rating ({handle})",
                ),
                height=max(360, 30 * len(mine) + 120),
            )
        )

# ---------- REVISION ----------

with tab_rev:
    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.markdown("### Revise by tag")
            all_tags = sorted({t for p in problem_history.values() for t in p["tags"]})
            rev_tag = st.selectbox("Tag", all_tags)
            hidden = load_hidden_problems()
            items = [
                p
                for p in problem_history.values()
                if rev_tag in p["tags"] and (p["contestId"], p["index"]) not in hidden
            ]
            items.sort(key=lambda p: p["last_solved"])
            st.caption(f"{len(items)} problems, oldest solve first")

            with st.container(height=520, border=False):
                for i, p in enumerate(items):
                    a, b, c = st.columns([5, 2, 1])
                    a.markdown(
                        f"[{p['contestId']}{p['index']} · {p['name']}]"
                        f"(https://codeforces.com/contest/{p['contestId']}/problem/{p['index']})"
                    )
                    b.caption(
                        f"{p['rating'] or '—'} · {p['last_solved'].strftime('%Y-%m-%d')}"
                    )
                    if c.button(
                        "Hide",
                        key=f"hide_{p['contestId']}_{p['index']}_{i}",
                    ):
                        hide_problem(p["contestId"], p["index"])
                        st.rerun()

    with right:
        with st.container(border=True):
            st.markdown("### Manual backlog")
            with st.form("add_problem", clear_on_submit=True):
                pc1, pc2 = st.columns([3, 1])
                prob_id = pc1.text_input(
                    "Problem ID", placeholder="1784D", label_visibility="collapsed"
                )
                submitted = pc2.form_submit_button("Add", width="stretch")
            if submitted:
                try:
                    add_revision_by_id(prob_id.strip())
                    st.success(f"{prob_id.strip()} added")
                except Exception as e:
                    st.error(str(e))

            rev_df = pd.DataFrame(load_revision_problems())
            if rev_df.empty:
                st.info("No revision problems added yet.")
            else:
                rev_df["last_solved"] = pd.to_datetime(rev_df["last_solved"])
                mode = st.radio(
                    "Filter", ["None", "Tag", "Rating"], horizontal=True
                )
                if mode == "Tag":
                    tags_avail = sorted({t for ts in rev_df["tags"] for t in ts})
                    sel = st.selectbox("Tag", tags_avail, key="backlog_tag")
                    rev_df = rev_df[rev_df["tags"].apply(lambda x: sel in x)]
                elif mode == "Rating":
                    lo, hi = st.slider("Rating range", 0, 3500, (800, 1600), step=100)
                    rev_df = rev_df[(rev_df["rating"] >= lo) & (rev_df["rating"] <= hi)]

                rev_df = rev_df.sort_values("last_solved", ascending=False)
                st.caption(f"{len(rev_df)} problems, newest first")
                with st.container(height=400, border=False):
                    for i, (_, row) in enumerate(rev_df.iterrows()):
                        a, b, c = st.columns([5, 2, 1])
                        a.markdown(f"[{row['name']}]({row['url']})")
                        b.caption(f"{row['rating']} · {row['last_solved']:%Y-%m-%d}")
                        if c.button(
                            "Remove",
                            key=f"remove_{row['contestId']}_{row['index']}_{i}",
                        ):
                            remove_revision_problem(row["contestId"], row["index"])
                            st.rerun()

# ---------- PERFORMANCE ----------

with tab_perf:
    cp_df = pd.DataFrame(
        {
            "Tag": FOCUS_TAGS,
            "Contest": [contest_tag[t] for t in FOCUS_TAGS],
            "Practice": [practice_tag[t] for t in FOCUS_TAGS],
        }
    )
    card(
        style(
            px.bar(
                cp_df,
                x="Tag",
                y=["Contest", "Practice"],
                barmode="group",
                title="Contest vs practice solves by tag",
            )
        )
    )

    weak_rows = [
        [t, attempts[t], ac[t], round(ac[t] / attempts[t], 2)]
        for t in FOCUS_TAGS
        if attempts[t] >= 10
    ]
    weak_df = pd.DataFrame(
        weak_rows, columns=["Tag", "Attempts", "Solved", "AC Ratio"]
    ).sort_values("AC Ratio")

    w1, w2 = st.columns([2, 3])
    with w1:
        with st.container(border=True):
            st.markdown("### Weak tag detection")
            st.dataframe(weak_df, hide_index=True, width="stretch")
    with w2:
        card(
            style(
                px.bar(
                    weak_df,
                    x="AC Ratio",
                    y="Tag",
                    orientation="h",
                    text="AC Ratio",
                    title="AC ratio (lower = weaker)",
                )
            )
        )

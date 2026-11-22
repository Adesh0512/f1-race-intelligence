import os
import sys
from datetime import date
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import xgboost as xgb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "06_classification_algorithm"))
from db_utils import apply_f1_theme, get_plotly_theme, page_header, PURPLE, GREEN, INK, GRAPHITE, RULE, SURFACE, DISPLAY_FONT
from feature_engineering import ENGINEERED_FEATURE_COLS as FEATURES
from improved_classifier import softmax_race_probabilities
import future_race as fr

apply_f1_theme()
st.markdown(f"""<style>
.podium {{ display: flex; gap: 12px; align-items: flex-end; margin: 4px 0 14px 0; }}
.podium .step {{ flex: 1; background: {SURFACE}; border: 1px solid {RULE}; border-radius: 12px; padding: 14px 16px; }}
.podium .p1 {{ border: 2px solid {PURPLE}; padding-top: 26px; }}
.podium .pos {{ font-family: {DISPLAY_FONT}; color: {GRAPHITE}; font-size: .85rem; }}
.podium .name {{ font-family: {DISPLAY_FONT}; color: {INK}; font-size: 1.35rem; font-weight: 700; line-height: 1.15; }}
.podium .team {{ color: {GRAPHITE}; font-size: .85rem; }}
.podium .pct {{ font-family: {DISPLAY_FONT}; font-size: 1.9rem; font-weight: 700; color: {INK}; }}
.podium .p1 .pct {{ color: {PURPLE}; }}
.race-banner {{ display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; align-items: flex-end;
  border-left: 4px solid {PURPLE}; padding: 6px 0 6px 16px; margin: 18px 0 14px 0; }}
.race-banner .lbl {{ color: {GRAPHITE}; font-size: .85rem; }}
.race-banner .big {{ font-family: {DISPLAY_FONT}; color: {INK}; font-size: 2rem; font-weight: 700; line-height: 1.1; }}
.race-banner .sub {{ color: {INK}; font-size: .95rem; }}
.race-banner .right {{ text-align: right; }}
</style>""", unsafe_allow_html=True)


@st.cache_resource
def champion():
    """Same data, split and settings as the champion in 06_classification_algorithm/improved_classifier.py."""
    df = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
    train = df[df["season"] < 2022]
    model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15, subsample=0.85,
                              colsample_bytree=0.85, random_state=42, eval_metric="logloss")
    model.fit(train[FEATURES].fillna(0), train["target_is_win"].astype(int))
    return model, df[df["season"] >= 2022].copy()


def predict(model, rows):
    """Per-driver win probability, normalised with the champion's race softmax so the race sums to 100%."""
    raw = model.predict_proba(rows[FEATURES].fillna(0))[:, 1]
    return softmax_race_probabilities(raw, [0] * len(rows)) * 100


@st.cache_resource
def forecaster():
    """History to the latest race, the champion retrained on all of it, and the projected starting line-up."""
    history, dob = fr.load_history()
    history = fr.add_recent_features(history, dob)
    lineup = fr.latest_lineup(history)
    lineup["grid_position"] = fr.projected_grid(history, lineup)
    return history, dob, fr.full_history_model(history), lineup.sort_values("grid_position").reset_index(drop=True)


history, dob, model, projection = forecaster()
last = history[history["race_date"] == history["race_date"].max()]
last_win = last[last["target_is_win"] == 1].iloc[0]
cal = fr.upcoming_calendar()
page_header('Dashboard 2', 'Supervised learning', 'Race predictor',
            f"Who wins the next Grand Prix? Predicted from every race up to the {int(last_win['season'])} "
            f"{last_win['race_name']} ({pd.Timestamp(last_win['race_date']):%d %b}). Change any parameter and the forecast updates instantly.")

live, record, past = st.tabs(["Next race forecast", "Track record", "Check a past race"])

with live:
    # races to forecast: the rest of the calendar, then "what if the next race were at another 2026 track"
    nxt = cal.iloc[0]
    options = [dict(label=f"{r.race_name}, {r.race_date:%d %b}", race=r.race_name,
                    track=r.circuit_name, circuit_id=r.circuit_id, date=r.race_date) for r in cal.itertuples()]
    options += [dict(label=f"What-if: next race at {r.circuit_name}", race=f"What-if at {r.circuit_name}", track=r.circuit_name,
                     circuit_id=r.circuit_id, date=nxt["race_date"])
                for r in fr.what_if_venues(history).itertuples() if r.circuit_id not in set(cal["circuit_id"])]
    labels = [o["label"] for o in options]
    names = dict(zip(projection["driver_id"], projection["driver_name"]))
    by_name = {n: d for d, n in names.items()}  # widgets hold names; the engine works on driver ids
    teams = projection.drop_duplicates("constructor_id").set_index("constructor_name")["constructor_id"].sort_index()
    v = st.session_state.get("rp_reset", 0)

    banner_slot = st.empty()  # filled once the race is picked, but shown above the controls
    with st.container(border=True):
        a, b = st.columns(2)
        o = options[labels.index(a.selectbox("Grand Prix to predict", labels, key=f"rp_race_{v}"))]
        pole = by_name[b.selectbox("Pole position", list(projection["driver_name"]), key=f"rp_pole_{v}",
                                   help="Qualifying is on Saturday. Until then the grid follows each driver's average start over his last 5 races.")]
        lineup = fr.move_to_grid(projection, pole, 1)
        base_feats = fr.race_features(history, dob, lineup, o["circuit_id"], o["date"])
        favourite = fr.forecast(history, dob, model, lineup, o["circuit_id"], o["date"]).iloc[0]["driver_name"]
        st.markdown("**Adjust one driver's parameters**")
        c1, c2, c3 = st.columns(3)
        drivers = list(projection["driver_name"])
        focus = by_name[c1.selectbox("Driver", drivers, index=drivers.index(favourite), key=f"rp_driver_{v}")]
        mine = base_feats.set_index("driver_id").loc[focus]
        k = f"{v}_{focus}_{pole}_{o['circuit_id']}"
        team = c2.selectbox("Team", list(teams.index), index=list(teams.index).index(mine["constructor_name"]), key=f"rp_team_{k}")
        slot = c3.slider("Starting position", 1, len(lineup), int(mine["grid_position"]), key=f"rp_grid_{k}")
        c4, c5, c6 = st.columns(3, vertical_alignment="center")
        form = c4.slider("Avg finish, last 5 races", 1.0, float(len(lineup)), float(round(mine["driver_rolling_finish_5"], 1)),
                         0.1, key=f"rp_form_{k}", help="Lower is better. Starts at his real last 5 races.")
        beat = c5.toggle("Beat teammate in qualifying", bool(mine["ahead_of_teammate_grid"]), key=f"rp_beat_{k}")
        if c6.button("Reset all parameters", width="stretch"):
            st.session_state["rp_reset"] = v + 1
            st.rerun()

    scenario = fr.move_to_team(fr.move_to_grid(lineup, focus, slot), focus, teams[team], team)
    result = fr.forecast(history, dob, model, scenario, o["circuit_id"], o["date"],
                         {focus: {"driver_rolling_finish_5": form, "ahead_of_teammate_grid": int(beat)}})
    baseline = fr.forecast(history, dob, model, projection, o["circuit_id"], o["date"]).set_index("driver_id")["win_probability"]
    result["change"] = result["win_probability"] - result["driver_id"].map(baseline)


    days = (pd.Timestamp(o["date"]).date() - date.today()).days
    with banner_slot:
        st.markdown(f"""<div class="race-banner">
            <div><div class="lbl">{"Next race" if o["race"] == nxt["race_name"] else "Scenario" if o["race"].startswith("What-if") else "Upcoming race"}</div>
                 <div class="big">{o["race"]}</div>
                 <div class="sub">{o["track"]} · {pd.Timestamp(o["date"]):%A %d %B %Y}{f" · in {days} days" if days > 0 else ""}</div></div>
            <div class="right"><div class="lbl">Last race</div>
                 <div class="sub">{last_win["race_name"]}, {pd.Timestamp(last_win["race_date"]):%d %b}: won by <b>{last_win["driver_name"]}</b></div></div>
            </div>""", unsafe_allow_html=True)
    top = result.head(3)
    step = lambda r, cls, pos: (f'<div class="step {cls}"><div class="pos">{pos}</div><div class="name">{r.driver_name}</div>'
                                f'<div class="team">{r.constructor_name} · starts P{int(r.grid_position)}</div>'
                                f'<div class="pct">{r.win_probability:.1f}%</div><div class="team">chance to win</div></div>')
    st.markdown('<div class="podium">' + step(top.iloc[1], "p2", "2nd favourite") + step(top.iloc[0], "p1", "Predicted winner")
                + step(top.iloc[2], "p3", "3rd favourite") + "</div>", unsafe_allow_html=True)

    def why(r):
        track = (f"averages P{r.circuit_avg_finish:.1f} at this track ({int(r.circuit_experience)} start{'s' * (r.circuit_experience != 1)})"
                 if r.circuit_experience else "has never raced at this track")
        return (f"**{r.driver_name}** starts P{int(r.grid_position)}, averaged P{r.driver_rolling_finish_5:.1f} over his "
                f"last 5 races, {r.constructor_name} scored {r.constructor_rolling_points_10:.1f} points per race over its last 10, "
                f"and he {track}.")

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        chart = result.head(10).iloc[::-1]
        colour = np.where(chart["rank"] == 1, "Predicted winner", np.where(chart["driver_id"] == focus, "Driver you adjusted", "Other drivers"))
        fig = px.bar(chart, x="win_probability", y="driver_name", orientation="h", text="win_probability", color=colour,
                     color_discrete_map={"Predicted winner": PURPLE, "Driver you adjusted": GREEN, "Other drivers": "#B8BEC7"},
                     title="Chance to win, top 10")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False).update_layout(
            xaxis_title="Chance to win (%)", yaxis_title=None, showlegend=False, height=430,
            xaxis_range=[0, chart["win_probability"].max() * 1.2])
        fig.update_yaxes(categoryorder="array", categoryarray=chart["driver_name"].tolist())  # keep probability order across colours
        st.plotly_chart(get_plotly_theme(fig), width="stretch")
        st.caption("Purple: predicted winner. Green: the driver whose parameters you adjusted.")
    with right:
        st.markdown("**Why the model ranks them this way**")
        for r in top.itertuples():
            st.markdown(why(r))
        me = result.set_index("driver_id").loc[focus]
        if int(me["rank"]) > 3:
            st.markdown(why(next(result[result["driver_id"] == focus].itertuples())))
        st.caption(f"{names[focus]}: {me['win_probability']:.1f}% chance, predicted P{int(me['rank'])}"
                   + (f" ({me['change']:+.1f} points vs. the default forecast)." if abs(me["change"]) >= 0.05 else "."))

    st.markdown("**Full predicted order and the parameters behind it**")
    table = result.assign(career_win_rate=result["career_win_rate"] * 100)[
        ["rank", "driver_name", "constructor_name", "grid_position", "win_probability", "change", "driver_rolling_finish_5",
         "constructor_rolling_points_10", "circuit_experience", "career_win_rate"]].round(1)
    table.columns = ["Predicted", "Driver", "Team", "Starts", "Win chance %", "Change vs default", "Avg finish, last 5",
                     "Team points per race, last 10", "Starts at this track", "Career win %"]
    if table["Change vs default"].abs().max() < 0.05:  # nothing adjusted yet
        table = table.drop(columns="Change vs default")
    st.dataframe(table, width="stretch", hide_index=True)
    st.caption("How it works: the history is f1.zip (1994–2024) plus every race since, from the public Jolpica-F1 API. For each driver the "
               f"model rebuilds {len(FEATURES)} parameters from his record before the race (starting position, recent form, team form, "
               "record at this track, career, age, teammate battle). The champion XGBoost classifier, retrained on all races, scores them "
               "and a race softmax makes the chances add up to 100%.")

with record:
    test = pd.read_csv(os.path.join(ROOT, "06_classification_algorithm", "real_world_test.csv"))
    hold = pd.read_csv(os.path.join(ROOT, "08_performance_metrics", "partition_metrics.csv")).iloc[-1]
    a, b, c = st.columns(3)
    a.metric("Holdout 2022–2024 (unseen)", f"{int(hold['top1_hits'])} / {int(hold['total_gps'])}", f"{hold['top1_winner_hit_pct']:.0f}% winners called", delta_color="off")
    b.metric(f"Real world {test['season'].min()}–{test['season'].max()}", f"{test['model_correct'].sum()} / {len(test)}",
             f"{test['model_correct'].mean():.0%} called before the race", delta_color="off")
    c.metric("Pole-sitter, same races", f"{test['pole_correct'].sum()} / {len(test)}", f"{test['pole_correct'].mean():.0%}", delta_color="off")
    by = test.groupby("season")[["model_correct", "pole_correct"]].sum().reset_index().melt(id_vars="season", var_name="who", value_name="wins_called")
    by["who"] = by["who"].map({"model_correct": "Model", "pole_correct": "Pole-sitter"})
    fig = px.bar(by, x="season", y="wins_called", color="who", barmode="group", text="wins_called",
                 color_discrete_map={"Model": PURPLE, "Pole-sitter": "#B8BEC7"}, title="Winners called per season (races since 2024)")
    st.plotly_chart(get_plotly_theme(fig.update_layout(xaxis_type="category", legend_title_text="")), width="stretch")
    st.caption("The model trained on 1994–2024 only, then called every later race before it happened. In 2025–26 qualifying decided most "
               "races and the 2026 rule change made older form a weaker guide, so pole position alone was about as strong a signal.")
    st.dataframe(test.sort_values(["season", "round"], ascending=False), width="stretch", hide_index=True, height=360)

with past:
    model, holdout = champion()
    races = holdout.drop_duplicates("race_id").sort_values(["season", "round"])

    a, b = st.columns([1, 3])
    season = a.selectbox("Season", sorted(races["season"].unique(), reverse=True))
    in_season = races[races["season"] == season]
    rid = b.selectbox("Grand Prix", in_season["race_id"], format_func=lambda r: in_season.loc[in_season["race_id"] == r, "race_name"].iat[0])
    race = holdout[holdout["race_id"] == rid].sort_values("grid_position").reset_index(drop=True)
    race_name = f"{season} {race['race_name'].iat[0]}"

    EDIT = {"grid_position": "Grid slot", "driver_rolling_finish_5": "Avg finish, last 5 races",
            "driver_rolling_points_5": "Avg points, last 5 races", "constructor_rolling_points_10": "Team avg points, last 10",
            "ahead_of_teammate_grid": "Out-qualified teammate"}
    st.markdown(f"#### What-if inputs for the {race_name}")
    st.caption("These are the real pre-race values. Edit any cell (for example give a driver pole position) and the prediction "
               "below updates. The other 11 features stay as they were before the race.")
    key = f"edit_{rid}_{st.session_state.get('reset', 0)}"
    shown = race[["driver_name", "constructor_name"] + list(EDIT)].rename(columns={"driver_name": "Driver", "constructor_name": "Team", **EDIT})
    shown["Out-qualified teammate"] = shown["Out-qualified teammate"].astype(bool)
    edited = st.data_editor(
        shown, key=key, hide_index=True, width="stretch", disabled=["Driver", "Team"],
        column_config={"Grid slot": st.column_config.NumberColumn(min_value=1, max_value=26, step=1),
                       "Avg finish, last 5 races": st.column_config.NumberColumn(min_value=1.0, max_value=26.0, step=0.1, format="%.1f"),
                       "Avg points, last 5 races": st.column_config.NumberColumn(min_value=0.0, max_value=26.0, step=0.1, format="%.1f"),
                       "Team avg points, last 10": st.column_config.NumberColumn(min_value=0.0, max_value=44.0, step=0.1, format="%.1f")})
    if st.button("Reset to the real pre-race values"):
        st.session_state["reset"] = st.session_state.get("reset", 0) + 1
        st.rerun()

    scenario = race.copy()
    for f, label in EDIT.items():
        scenario[f] = edited[label].astype(float).values
    scenario["grid_vs_form_gap"] = scenario["grid_position"] - scenario["driver_rolling_finish_5"]  # derived feature follows the edits

    base = predict(model, race)
    new = predict(model, scenario)
    out = pd.DataFrame({"Driver": race["driver_name"], "Team": race["constructor_name"], "Grid": scenario["grid_position"].astype(int),
                        "Win probability %": new.round(1), "Change vs real inputs": (new - base).round(1),
                        "Actual finish": race["target_finish_position"].astype(int)}).sort_values("Win probability %", ascending=False)
    changed = not np.allclose(new, base)

    fav, actual = out.iloc[0], race.loc[race["target_is_win"] == 1, "driver_name"].iat[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Predicted winner", fav["Driver"], f"{fav['Win probability %']:.1f}% chance", delta_color="off")
    c2.metric("Actual winner", actual, f"started P{int(race.loc[race['target_is_win'] == 1, 'grid_position'].iat[0])}", delta_color="off")
    c3.metric("Model's pick (real inputs)", race["driver_name"].iat[int(np.argmax(base))],
              "correct" if race["driver_name"].iat[int(np.argmax(base))] == actual else "missed", delta_color="off")
    c4.metric("Inputs", "Edited" if changed else "Real", "what-if scenario" if changed else "as before the race", delta_color="off")

    top = out.head(10).iloc[::-1]
    fig = px.bar(top, x="Win probability %", y="Driver", orientation="h", text="Win probability %",
                 color=np.where(top["Driver"] == actual, "Actual winner", "Other"),
                 color_discrete_map={"Actual winner": GREEN, "Other": PURPLE},
                 title=f"{race_name}: predicted win probability, top 10" + (" (what-if)" if changed else ""))
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False).update_layout(yaxis_title=None, legend_title_text="")
    st.plotly_chart(get_plotly_theme(fig), width="stretch")
    st.dataframe(out, width="stretch", hide_index=True)

    with st.expander("How the prediction is made"):
        st.markdown(f"""
        1. The champion **cost-sensitive XGBoost** (100 trees, depth 4, `scale_pos_weight = 15`) is trained on 1994–2021 only,
           so every 2022–2024 race here is genuinely unseen.
        2. It scores each driver from **{len(FEATURES)} pre-race features**: grid slot, recent driver and team form, circuit record,
           career numbers and the teammate qualifying battle.
        3. A **race softmax** (temperature 0.8) turns the scores into probabilities that add up to 100% for the race.
        4. The predicted winner is the driver with the highest probability. Over the 68 races it picks the real winner in 40.
        """)

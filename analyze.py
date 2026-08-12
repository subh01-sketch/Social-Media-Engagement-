"""
analyze.py
Reads instagram_posts.csv and produces:
  - analysis.json  (all aggregates used by the dashboard website)
  - posts_enriched.csv (same raw data + engagement_rate, ready for Power BI)
"""

import json
import pandas as pd
import numpy as np

df = pd.read_csv("instagram_posts.csv")

DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ---- Hour buckets (3-hour blocks) for a readable heatmap ----
def hour_block(h):
    starts = [0, 3, 6, 9, 12, 15, 18, 21]
    labels = ["12-3am", "3-6am", "6-9am", "9am-12pm", "12-3pm", "3-6pm", "6-9pm", "9pm-12am"]
    for i in range(len(starts) - 1, -1, -1):
        if h >= starts[i]:
            return labels[i]
    return labels[0]

BLOCK_ORDER = ["12-3am", "3-6am", "6-9am", "9am-12pm", "12-3pm", "3-6pm", "6-9pm", "9pm-12am"]

df["hour_block"] = df["hour"].apply(hour_block)

# ---- Heatmap: avg engagement rate by day_of_week x hour_block ----
heat = df.groupby(["day_of_week", "hour_block"])["engagement_rate"].mean().reset_index()
heatmap = []
for dow in DOW_ORDER:
    row = []
    for block in BLOCK_ORDER:
        match = heat[(heat.day_of_week == dow) & (heat.hour_block == block)]
        row.append(round(float(match.engagement_rate.iloc[0]), 4) if len(match) else None)
    heatmap.append({"day": dow, "values": row})

# ---- Best posting windows (top 5 day+block combos by avg ER, min 2 posts) ----
counts = df.groupby(["day_of_week", "hour_block"]).size().reset_index(name="n")
merged = heat.merge(counts, on=["day_of_week", "hour_block"])
merged = merged[merged.n >= 2].sort_values("engagement_rate", ascending=False)
best_windows = [
    {"day": r.day_of_week, "block": r.hour_block, "avg_engagement_rate": round(float(r.engagement_rate), 4)}
    for r in merged.head(5).itertuples()
]

# ---- Content type performance ----
ct = df.groupby("content_type").agg(
    posts=("post_id", "count"),
    avg_impressions=("impressions", "mean"),
    avg_reach=("reach", "mean"),
    avg_likes=("likes", "mean"),
    avg_comments=("comments", "mean"),
    avg_shares_saves=("shares_saves", "mean"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_follows_gained=("follows_gained", "mean"),
).reset_index().sort_values("avg_engagement_rate", ascending=False)
content_performance = ct.round(3).to_dict(orient="records")

# ---- Theme performance ----
th = df.groupby("theme").agg(
    posts=("post_id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_comments=("comments", "mean"),
).reset_index().sort_values("avg_engagement_rate", ascending=False)
theme_performance = th.round(3).to_dict(orient="records")

# ---- Daily trend (for a line chart) ----
daily = df.groupby("date").agg(
    impressions=("impressions", "sum"),
    likes=("likes", "sum"),
    comments=("comments", "sum"),
    shares_saves=("shares_saves", "sum"),
    engagement_rate=("engagement_rate", "mean"),
).reset_index().sort_values("date")
daily_trend = daily.round(3).to_dict(orient="records")

# ---- Top 5 posts ----
top_posts = (df.sort_values("engagement_rate", ascending=False)
             .head(5)[["post_id", "date", "content_type", "theme", "engagement_rate",
                        "likes", "comments", "shares_saves", "impressions"]]
             .round(3).to_dict(orient="records"))

# ---- Headline KPIs ----
kpis = {
    "total_posts": int(len(df)),
    "total_impressions": int(df.impressions.sum()),
    "total_reach": int(df.reach.sum()),
    "total_likes": int(df.likes.sum()),
    "total_comments": int(df.comments.sum()),
    "total_shares_saves": int(df.shares_saves.sum()),
    "avg_engagement_rate": round(float(df.engagement_rate.mean()), 4),
    "total_follows_gained": int(df.follows_gained.sum()),
}

# ---- Recommendations (generated from the actual numbers above) ----
def pluralize(name):
    if name.endswith("y"):
        return name[:-1] + "ies"
    return name + "s"

top_content = content_performance[0]["content_type"]
top_theme = theme_performance[0]["theme"]
top_window = best_windows[0]
low_content = min(content_performance, key=lambda r: r["avg_engagement_rate"])

recommendations = [
    f"Post more {pluralize(top_content)}: they average a {content_performance[0]['avg_engagement_rate']*100:.1f}% "
    f"engagement rate, the highest of any format in this dataset.",
    f"Your strongest window is {top_window['day']} between {top_window['block']}, averaging "
    f"{top_window['avg_engagement_rate']*100:.1f}% engagement — prioritize publishing here.",
    f"\"{top_theme}\" content out-performs other themes on comments and engagement rate; lean into it "
    f"in your content calendar.",
    f"{pluralize(low_content['content_type'])} underperform ({low_content['avg_engagement_rate']*100:.1f}% ER) — "
    f"use them for supplementary/behind-the-scenes content rather than key launches.",
    "Treat the three other windows in 'best_windows' as a secondary rotation to test consistency "
    "of the pattern before locking in a permanent schedule.",
]

analysis = {
    "kpis": kpis,
    "heatmap": {"days": DOW_ORDER, "blocks": BLOCK_ORDER, "rows": heatmap},
    "best_windows": best_windows,
    "content_performance": content_performance,
    "theme_performance": theme_performance,
    "daily_trend": daily_trend,
    "top_posts": top_posts,
    "recommendations": recommendations,
}

with open("analysis.json", "w") as f:
    json.dump(analysis, f, indent=2)

df.to_csv("posts_enriched.csv", index=False)
print("Wrote analysis.json and posts_enriched.csv")
print(json.dumps(kpis, indent=2))

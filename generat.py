"""
generate_data.py
Creates a synthetic-but-realistic Instagram post performance dataset.
Swap this out with a real export (Meta Business Suite / Graph API) once you
have one -- the analyze.py script downstream expects the same columns.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)

N_DAYS = 90
POSTS_PER_DAY_RANGE = (1, 4)
CONTENT_TYPES = ["Reel", "Carousel", "Single Image", "Story"]
CONTENT_WEIGHTS = [0.35, 0.30, 0.20, 0.15]
THEMES = ["Behind the Scenes", "Product/Feature", "Tutorial/How-To",
          "UGC/Testimonial", "Meme/Trend", "Announcement", "Q&A"]

START_DATE = datetime.now() - timedelta(days=N_DAYS)

# base follower count that grows slowly over the window, drives impressions
BASE_FOLLOWERS = 42000
FOLLOWER_GROWTH_PER_DAY = 18

# Hour-of-day engagement multiplier (0-23). Peaks late morning & evening.
HOUR_CURVE = np.array([
    0.3, 0.2, 0.2, 0.2, 0.2, 0.3, 0.5, 0.7,      # 0-7
    0.9, 1.1, 1.3, 1.5, 1.4, 1.2, 1.0, 0.9,      # 8-15
    1.0, 1.2, 1.5, 1.8, 1.9, 1.6, 1.1, 0.6        # 16-23
])

# Day-of-week multiplier: Mon=0 ... Sun=6. Weekends + midweek evenings up.
DOW_CURVE = np.array([0.9, 1.0, 1.15, 1.2, 1.1, 1.35, 1.25])  # Mon..Sun

CONTENT_BASE_REACH = {
    "Reel": 1.9, "Carousel": 1.3, "Single Image": 1.0, "Story": 0.6
}
CONTENT_ENGAGEMENT_BIAS = {
    # multiplier on (likes, comments, shares/saves) beyond reach effect
    "Reel": (1.1, 0.9, 1.6),
    "Carousel": (1.0, 1.4, 1.3),
    "Single Image": (1.0, 1.0, 0.8),
    "Story": (0.6, 0.4, 0.5),
}

rows = []
post_id = 1000

for day in range(N_DAYS):
    date = START_DATE + timedelta(days=day)
    dow = date.weekday()
    followers_today = BASE_FOLLOWERS + FOLLOWER_GROWTH_PER_DAY * day
    n_posts = rng.integers(POSTS_PER_DAY_RANGE[0], POSTS_PER_DAY_RANGE[1] + 1)

    for _ in range(n_posts):
        hour = rng.integers(6, 24)
        content_type = rng.choice(CONTENT_TYPES, p=CONTENT_WEIGHTS)
        theme = rng.choice(THEMES)

        time_mult = HOUR_CURVE[hour] * DOW_CURVE[dow]
        reach_mult = CONTENT_BASE_REACH[content_type]
        like_bias, comment_bias, share_bias = CONTENT_ENGAGEMENT_BIAS[content_type]

        # impressions: base reach off follower count, seasonal noise
        base_impressions = followers_today * 0.18 * reach_mult
        impressions = max(50, rng.normal(base_impressions * time_mult, base_impressions * 0.25))

        reach = impressions * rng.uniform(0.72, 0.9)

        # engagement rate baseline ~3-9%, shaped by time-of-post and content type
        base_er = rng.uniform(0.03, 0.07) * time_mult
        likes = max(0, rng.normal(reach * base_er * 0.75 * like_bias, reach * 0.01))
        comments = max(0, rng.normal(reach * base_er * 0.06 * comment_bias, reach * 0.003))
        shares_saves = max(0, rng.normal(reach * base_er * 0.18 * share_bias, reach * 0.005))
        follows_gained = max(0, rng.normal(reach * 0.0015 * reach_mult, reach * 0.0004))

        rows.append({
            "post_id": post_id,
            "date": date.strftime("%Y-%m-%d"),
            "day_of_week": date.strftime("%A"),
            "hour": int(hour),
            "content_type": content_type,
            "theme": theme,
            "impressions": int(impressions),
            "reach": int(reach),
            "likes": int(likes),
            "comments": int(comments),
            "shares_saves": int(shares_saves),
            "follows_gained": int(follows_gained),
        })
        post_id += 1

df = pd.DataFrame(rows)
df["engagement_rate"] = ((df["likes"] + df["comments"] + df["shares_saves"])
                          / df["impressions"]).round(4)

df.to_csv("instagram_posts.csv", index=False)
print(f"Generated {len(df)} posts -> instagram_posts.csv")
print(df.head())

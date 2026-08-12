# Social-Media-Engagement-
# Power BI Setup Guide — Instagram Engagement Dashboard

This uses `posts_enriched.csv` (one row per post). Power BI Desktop isn't
available in this environment, so this is a ready-to-follow setup for you
to build it on your own machine in ~15 minutes.

## 1. Load the data
1. Power BI Desktop → **Get Data → Text/CSV** → select `posts_enriched.csv`.
2. In Power Query, confirm types: `date` → Date, `hour` → Whole Number,
   `engagement_rate` → Decimal Number (already computed for you).
3. Add a **Date table** (Modeling → New Table):
   ```
   DateTable = CALENDAR(MIN(posts_enriched[date]), MAX(posts_enriched[date]))
   ```
   Mark it as a date table and relate it to `posts_enriched[date]`.

## 2. Core DAX measures
```
Total Impressions   = SUM(posts_enriched[impressions])
Total Reach         = SUM(posts_enriched[reach])
Total Likes         = SUM(posts_enriched[likes])
Total Comments      = SUM(posts_enriched[comments])
Total Shares/Saves  = SUM(posts_enriched[shares_saves])

Avg Engagement Rate =
    AVERAGE(posts_enriched[engagement_rate])

Engagement Rate (weighted) =
    DIVIDE(
        SUM(posts_enriched[likes]) + SUM(posts_enriched[comments]) + SUM(posts_enriched[shares_saves]),
        SUM(posts_enriched[impressions])
    )

Follows per 1K Impressions =
    DIVIDE(SUM(posts_enriched[follows_gained]), SUM(posts_enriched[impressions])) * 1000
```

## 3. Recommended visuals
| Visual | Fields | Notes |
|---|---|---|
| Matrix (heatmap) | Rows: `day_of_week`, Columns: `hour`, Values: `Avg Engagement Rate` | Apply conditional formatting (color scale) to recreate the best-time heatmap |
| Clustered bar | Axis: `content_type`, Values: `Avg Engagement Rate` | Sort descending |
| Line chart | Axis: `date`, Values: `Engagement Rate (weighted)` | Add a trend line |
| Donut | `content_type` by `Total Impressions` | Share of reach by format |
| Table | Top 10 by `engagement_rate` | Post-level detail |
| Card visuals | KPIs from section 2 | Top strip of the report page |

## 4. Slicers
Add slicers for `content_type`, `theme`, and the date table so stakeholders
can filter the whole report by format or time period.

## 5. Refreshing with real data
Replace `posts_enriched.csv` with an export from:
- **Meta Business Suite** → Insights → Export, or
- **Instagram Graph API** (`/{ig-user-id}/media` + `/insights` fields:
  `impressions, reach, likes, comments, saved, shares`) for Business/Creator
  accounts you manage.

Keep the same column names and Power BI's existing measures, relationships,
and visuals will keep working without changes — just hit Refresh.

> Note: Instagram's terms of service prohibit scraping public profiles or
> feeds. For real data, use the official Graph API (requires a
> Business/Creator account you administer) or an export from Meta Business
> Suite rather than a scraper.

WITH us_rate AS (
    SELECT
	  obs_date,
	  value AS fed_funds
	FROM observations
	WHERE indicator_id = 3
),
il_rate AS (
    SELECT
	  obs_date,
	  value AS boi_rate
	FROM observations
	WHERE indicator_id = 6
)
SELECT
  us_rate.obs_date,
  fed_funds,
  boi_rate,
  ROUND(fed_funds - boi_rate, 2) AS rate_differential
FROM us_rate
JOIN il_rate ON us_rate.obs_date = il_rate.obs_date
ORDER BY us_rate.obs_date;
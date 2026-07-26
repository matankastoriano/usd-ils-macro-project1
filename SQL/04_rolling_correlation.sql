WITH monthly_fx AS (
	SELECT
	  date_trunc('month', obs_date) ::date AS month,
	  ROUND(AVG(value), 4) AS avg_fx
	FROM
	  observations
	WHERE indicator_id = 7
	GROUP BY date_trunc('month', obs_date)::date
	ORDER BY month
), 
us_rate AS (
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
),
diff AS (
    SELECT
        us_rate.obs_date AS month,
        ROUND(fed_funds - boi_rate, 2) AS rate_differential
    FROM us_rate
    JOIN il_rate ON us_rate.obs_date = il_rate.obs_date
)
SELECT
  monthly_fx.month,
  avg_fx,
  rate_differential,
  ROUND(CORR(avg_fx, rate_differential) OVER (ORDER BY monthly_fx.month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)::numeric, 3) AS rolling_corr_12m
FROM monthly_fx
JOIN diff ON monthly_fx.month = diff.month
ORDER BY monthly_fx.month;
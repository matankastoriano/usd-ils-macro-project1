SELECT
  obs_date,
  value AS usd_ils,
  ROUND(AVG(value) OVER(ORDER BY obs_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 4) AS thirty_avg,
  ROUND(AVG(value) OVER(ORDER BY obs_date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW), 4) AS ninety_avg,
  ROUND(STDDEV(value) OVER(ORDER BY obs_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 4) AS thirty_volatility
FROM observations
WHERE indicator_id = 7
ORDER BY obs_date

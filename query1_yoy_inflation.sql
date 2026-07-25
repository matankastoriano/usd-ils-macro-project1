SELECT 
  obs_date,
  indicator_id,
  value,
  LAG(value, 12) OVER(PARTITION BY indicator_id ORDER BY obs_date) AS cpi_year_ago,
  ROUND(100 * (value - LAG(value, 12) OVER(PARTITION BY indicator_id ORDER BY obs_date)) / 
  LAG(value, 12) OVER(PARTITION BY indicator_id ORDER BY obs_date), 2) AS yoy_inflation_pct
FROM observations
WHERE indicator_id IN (1, 5) 
ORDER BY indicator_id, obs_date;
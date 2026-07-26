-- USD/ILS Macro Database Schema
-- Normalized design: countries + indicators (dimensions) -> observations (fact table)

CREATE TABLE countries (
    country_id  SERIAL PRIMARY KEY,
    iso_code    CHAR(3) UNIQUE NOT NULL,
    name        TEXT NOT NULL
);

CREATE TABLE indicators (
    indicator_id  SERIAL PRIMARY KEY,
    code          TEXT UNIQUE NOT NULL,
    name          TEXT NOT NULL,
    country_id    INT REFERENCES countries(country_id),
    frequency     TEXT NOT NULL CHECK (frequency IN ('daily', 'monthly')),
    units         TEXT,
    source        TEXT NOT NULL
);

CREATE TABLE observations (
    indicator_id  INT NOT NULL REFERENCES indicators(indicator_id),
    obs_date      DATE NOT NULL,
    value         NUMERIC NOT NULL,
    PRIMARY KEY (indicator_id, obs_date)
);

CREATE INDEX idx_obs_date ON observations (obs_date);

-- Seed data: countries
INSERT INTO countries (iso_code, name) VALUES
    ('USA', 'United States'),
    ('ISR', 'Israel');

-- Seed data: indicator catalog
INSERT INTO indicators (code, name, country_id, frequency, units, source) VALUES
    ('CPIAUCSL',     'US CPI (all urban consumers)',   (SELECT country_id FROM countries WHERE iso_code='USA'), 'monthly', 'index 1982-84=100', 'FRED'),
    ('CPILFESL',     'US core CPI (ex food & energy)',  (SELECT country_id FROM countries WHERE iso_code='USA'), 'monthly', 'index 1982-84=100', 'FRED'),
    ('FEDFUNDS',     'Effective federal funds rate',    (SELECT country_id FROM countries WHERE iso_code='USA'), 'monthly', 'percent', 'FRED'),
    ('DGS10',        'US 10-year Treasury yield',       (SELECT country_id FROM countries WHERE iso_code='USA'), 'daily',   'percent', 'FRED'),
    ('ISR_CPI',      'Israel CPI (all items)',          (SELECT country_id FROM countries WHERE iso_code='ISR'), 'monthly', 'index',   'FRED (OECD)'),
    ('BOI_RATE',     'Bank of Israel policy rate',      (SELECT country_id FROM countries WHERE iso_code='ISR'), 'monthly', 'percent', 'FRED (OECD)'),
    ('USDILS_DAILY', 'USD/ILS spot exchange rate',      NULL,                                                    'daily',   'ILS per USD', 'yfinance');
-- Initiale Provider-Daten
INSERT INTO providers (name, display_name, country_code, currency, is_active) VALUES
('aWATTar', 'aWATTar', 'DE', 'EUR', true),
('Tibber', 'Tibber', 'DE', 'EUR', true),
('ENTSO-E', 'ENTSO-E', 'DE', 'EUR', true)
ON CONFLICT (name) DO NOTHING;

-- Index für bessere Performance
CREATE INDEX IF NOT EXISTS idx_electric_prices_timestamp ON electric_prices(timestamp);
CREATE INDEX IF NOT EXISTS idx_electric_prices_provider_timestamp ON electric_prices(provider_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_electric_prices_start_end_time ON electric_prices(start_time, end_time);

-- Beispiel Alert für günstige Preise
INSERT INTO price_alerts (name, provider_id, threshold_price, alert_type, is_active, time_window_hours, min_duration_minutes)
SELECT 'Günstige Preise unter 20ct/kWh', p.id, 20.0, 'below', true, 24, 60
FROM providers p
WHERE p.name = 'aWATTar'
ON CONFLICT DO NOTHING;
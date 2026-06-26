-- Bronze layer DDL (see forge-docs/warehouse.md)
-- Apply: mysql -h 127.0.0.1 -P 3309 -u root -p < ingest/sql/warehouse.sql

CREATE DATABASE IF NOT EXISTS forge_bronze
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS forge_bronze.ingest_run (
  run_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  source         VARCHAR(32)     NOT NULL,
  dataset        VARCHAR(64)     NOT NULL,
  status         ENUM('running','success','failed') NOT NULL DEFAULT 'running',
  started_at     DATETIME(6)     NOT NULL,
  finished_at    DATETIME(6)     NULL,
  row_count      BIGINT UNSIGNED NULL,
  params_json    JSON            NULL,
  error_message  TEXT            NULL,
  PRIMARY KEY (run_id),
  KEY idx_ingest_run_dataset_started (dataset, started_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS forge_bronze.yfinance_equity_eod (
  run_id         BIGINT UNSIGNED NOT NULL,
  yf_ticker      VARCHAR(24)     NOT NULL,
  trade_date     DATE            NOT NULL,
  open           DECIMAL(18,6)   NULL,
  high           DECIMAL(18,6)   NULL,
  low            DECIMAL(18,6)   NULL,
  close          DECIMAL(18,6)   NULL,
  adj_close      DECIMAL(18,6)   NULL,
  volume         BIGINT UNSIGNED NULL,
  dividends      DECIMAL(18,8)   NOT NULL DEFAULT 0,
  stock_splits   DECIMAL(18,8)   NOT NULL DEFAULT 0,
  ingested_at    DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (run_id, yf_ticker, trade_date),
  KEY idx_yf_ticker_date (yf_ticker, trade_date),
  CONSTRAINT fk_bronze_eod_run
    FOREIGN KEY (run_id) REFERENCES forge_bronze.ingest_run (run_id)
) ENGINE=InnoDB;

-- S&P 500 universe (refreshed from FMP via ingest/sp500_constituents.py)
CREATE TABLE IF NOT EXISTS forge_bronze.sp500_constituent (
  symbol         VARCHAR(24)     NOT NULL COMMENT 'FMP symbol',
  yf_ticker      VARCHAR(24)     NOT NULL COMMENT 'yfinance symbol',
  name           VARCHAR(256)    NULL,
  sector         VARCHAR(128)    NULL,
  sub_sector     VARCHAR(128)    NULL,
  refreshed_at   DATETIME(6)     NOT NULL,
  PRIMARY KEY (symbol),
  KEY idx_sp500_yf_ticker (yf_ticker)
) ENGINE=InnoDB;

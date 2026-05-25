CREATE DATABASE IF NOT EXISTS stock_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE stock_db;

CREATE TABLE IF NOT EXISTS stock_master (
    stock_id VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    market_type VARCHAR(20) NOT NULL DEFAULT '上市',
    industry VARCHAR(100) NULL,
    is_active TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS daily_price (
    stock_id VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(12,4) NULL,
    high_price DECIMAL(12,4) NULL,
    low_price DECIMAL(12,4) NULL,
    close_price DECIMAL(12,4) NULL,
    price_change DECIMAL(12,4) NULL,
    volume BIGINT NULL,
    turnover_amount BIGINT NULL,
    transaction_count BIGINT NULL,
    data_source VARCHAR(30) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_id, trade_date),
    INDEX idx_daily_trade_date (trade_date),
    INDEX idx_daily_stock_id (stock_id),
    CONSTRAINT fk_daily_stock
        FOREIGN KEY (stock_id)
        REFERENCES stock_master(stock_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_features (
    stock_id VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    close_price DECIMAL(12,4) NULL,
    return_1d DECIMAL(12,6) NULL,
    return_3d DECIMAL(12,6) NULL,
    return_5d DECIMAL(12,6) NULL,
    ma3 DECIMAL(12,4) NULL,
    ma5 DECIMAL(12,4) NULL,
    ma10 DECIMAL(12,4) NULL,
    volume_ma3 DECIMAL(20,4) NULL,
    volume_ma5 DECIMAL(20,4) NULL,
    volume_change_3d DECIMAL(12,6) NULL,
    volume_change_5d DECIMAL(12,6) NULL,
    rsi7 DECIMAL(12,6) NULL,
    rsi14 DECIMAL(12,6) NULL,
    volatility_3d DECIMAL(12,6) NULL,
    volatility_5d DECIMAL(12,6) NULL,
    price_position_14d DECIMAL(12,6) NULL,
    label_next_day_up TINYINT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_id, trade_date),
    INDEX idx_features_trade_date (trade_date),
    INDEX idx_features_label (label_next_day_up),
    CONSTRAINT fk_features_stock
        FOREIGN KEY (stock_id)
        REFERENCES stock_master(stock_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS prediction_top20 (
    id BIGINT NOT NULL AUTO_INCREMENT,
    prediction_date DATE NOT NULL,
    target_date DATE NOT NULL,
    rank_no INT NOT NULL,
    stock_id VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    predicted_up_prob DECIMAL(12,8) NOT NULL,
    score DECIMAL(12,8) NOT NULL,
    close_price DECIMAL(12,4) NULL,
    return_1d DECIMAL(12,6) NULL,
    return_3d DECIMAL(12,6) NULL,
    return_5d DECIMAL(12,6) NULL,
    ma3 DECIMAL(12,4) NULL,
    ma5 DECIMAL(12,4) NULL,
    ma10 DECIMAL(12,4) NULL,
    rsi7 DECIMAL(12,6) NULL,
    rsi14 DECIMAL(12,6) NULL,
    volume_change_3d DECIMAL(12,6) NULL,
    volume_change_5d DECIMAL(12,6) NULL,
    data_source VARCHAR(30) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_prediction_rank (prediction_date, target_date, rank_no),
    INDEX idx_prediction_date (prediction_date),
    INDEX idx_prediction_stock (stock_id),
    CONSTRAINT fk_prediction_stock
        FOREIGN KEY (stock_id)
        REFERENCES stock_master(stock_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_status (
    id BIGINT NOT NULL AUTO_INCREMENT,
    status_date DATE NOT NULL,
    collected_days INT NOT NULL DEFAULT 0,
    stock_count INT NOT NULL DEFAULT 0,
    daily_price_rows INT NOT NULL DEFAULT 0,
    feature_rows INT NOT NULL DEFAULT 0,
    is_ready_for_prediction TINYINT NOT NULL DEFAULT 0,
    message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_status_date (status_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS model_run_log (
    id BIGINT NOT NULL AUTO_INCREMENT,
    run_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    run_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) NULL,
    status VARCHAR(30) NOT NULL,
    message TEXT NULL,
    total_stocks INT NULL,
    total_rows INT NULL,
    success_count INT NULL,
    fail_count INT NULL,
    top20_win_rate DECIMAL(12,6) NULL,
    average_next_day_return DECIMAL(12,6) NULL,
    notes TEXT NULL,
    PRIMARY KEY (id),
    INDEX idx_model_run_time (run_time),
    INDEX idx_model_run_type (run_type),
    INDEX idx_model_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS backtest_result (
    id BIGINT NOT NULL AUTO_INCREMENT,
    test_date DATE NOT NULL,
    target_date DATE NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    top_n INT NOT NULL,
    win_count INT NULL,
    lose_count INT NULL,
    win_rate DECIMAL(12,6) NULL,
    average_return DECIMAL(12,6) NULL,
    best_return DECIMAL(12,6) NULL,
    worst_return DECIMAL(12,6) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_backtest_date (test_date),
    INDEX idx_backtest_model (model_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS api_request_log (
    id BIGINT NOT NULL AUTO_INCREMENT,
    request_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    api_name VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    dataset VARCHAR(100) NULL,
    stock_id VARCHAR(20) NULL,
    status_code INT NULL,
    success TINYINT NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    retry_after INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_api_request_time (request_time),
    INDEX idx_api_name (api_name),
    INDEX idx_api_stock (stock_id),
    INDEX idx_api_success (success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS improvement_suggestions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    evidence TEXT NULL,
    suggested_action TEXT NOT NULL,
    action_command TEXT NULL,
    is_done TINYINT NOT NULL DEFAULT 0,
    done_at DATETIME NULL,
    PRIMARY KEY (id),
    INDEX idx_improvement_done (is_done),
    INDEX idx_improvement_severity (severity),
    INDEX idx_improvement_issue_type (issue_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS self_improvement_actions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(100) NOT NULL,
    action_description TEXT NOT NULL,
    action_command TEXT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    result_message TEXT NULL,
    PRIMARY KEY (id),
    INDEX idx_action_status (status),
    INDEX idx_action_type (action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

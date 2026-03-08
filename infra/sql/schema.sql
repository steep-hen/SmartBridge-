-- AI Financial Advisor Database Schema
-- PostgreSQL DDL for production and development environments
-- Supports UUID primary keys and comprehensive data tracking

-- ============================================================================
-- 1. USERS TABLE - Core user accounts
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================================
-- 2. FINANCIAL_SUMMARY TABLE - Monthly financial snapshots per user
-- ============================================================================
CREATE TABLE IF NOT EXISTS financial_summary (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_income DECIMAL(15, 2) NOT NULL DEFAULT 0,
    total_expenses DECIMAL(15, 2) NOT NULL DEFAULT 0,
    total_savings DECIMAL(15, 2) NOT NULL DEFAULT 0,
    total_investments DECIMAL(15, 2) NOT NULL DEFAULT 0,
    net_worth DECIMAL(15, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(user_id, year, month)
);

CREATE INDEX idx_financial_summary_user_id ON financial_summary(user_id);
CREATE INDEX idx_financial_summary_year_month ON financial_summary(year, month);

-- ============================================================================
-- 3. TRANSACTIONS TABLE - Individual transaction records
-- ============================================================================
CREATE TABLE IF NOT EXISTS transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    merchant_name VARCHAR(255),
    transaction_type VARCHAR(20) NOT NULL, -- 'INCOME', 'EXPENSE', 'INVESTMENT'
    payment_method VARCHAR(50), -- 'CASH', 'CARD', 'TRANSFER', 'UPI', 'CHEQUE'
    is_recurring BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);

-- ============================================================================
-- 4. GOALS TABLE - Financial goals per user
-- ============================================================================
CREATE TABLE IF NOT EXISTS goals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_name VARCHAR(255) NOT NULL,
    description TEXT,
    target_amount DECIMAL(15, 2) NOT NULL,
    current_amount DECIMAL(15, 2) DEFAULT 0,
    target_date DATE NOT NULL,
    goal_type VARCHAR(50) NOT NULL, -- 'SAVINGS', 'INVESTMENT', 'DEBT_PAYOFF', 'EDUCATION', 'HOME', 'RETIREMENT'
    priority VARCHAR(20) DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH'
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'ON_TRACK', 'AT_RISK', 'COMPLETED', 'ABANDONED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_target_date ON goals(target_date);

-- ============================================================================
-- 5. HOLDINGS TABLE - Current investment holdings
-- ============================================================================
CREATE TABLE IF NOT EXISTS holdings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    quantity DECIMAL(15, 4) NOT NULL,
    average_cost DECIMAL(15, 2) NOT NULL,
    current_value DECIMAL(15, 2) NOT NULL,
    asset_type VARCHAR(50) NOT NULL, -- 'EQUITY', 'MUTUAL_FUND', 'BOND', 'CRYPTO', 'COMMODITY', 'OTHER'
    purchase_date DATE NOT NULL,
    last_updated DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_holdings_user_id ON holdings(user_id);
CREATE INDEX idx_holdings_ticker ON holdings(ticker);
CREATE INDEX idx_holdings_asset_type ON holdings(asset_type);

-- ============================================================================
-- 6. MARKET_PRICES TABLE - Historical market prices for reference
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_prices (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    price_date DATE NOT NULL,
    open_price DECIMAL(15, 4) NOT NULL,
    close_price DECIMAL(15, 4) NOT NULL,
    high_price DECIMAL(15, 4) NOT NULL,
    low_price DECIMAL(15, 4) NOT NULL,
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(ticker, price_date)
);

CREATE INDEX idx_market_prices_ticker ON market_prices(ticker);
CREATE INDEX idx_market_prices_date ON market_prices(price_date);
CREATE INDEX idx_market_prices_ticker_date ON market_prices(ticker, price_date);

-- ============================================================================
-- 7. CONSENT_LOG TABLE - Track user consent for data usage
-- ============================================================================
CREATE TABLE IF NOT EXISTS consent_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL, -- 'ANALYTICS', 'MARKETING', 'DATA_SHARING', 'THIRD_PARTY'
    given BOOLEAN NOT NULL,
    consent_date TIMESTAMP NOT NULL,
    expiry_date TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_consent_log_user_id ON consent_log(user_id);
CREATE INDEX idx_consent_log_type ON consent_log(consent_type);

-- ============================================================================
-- 8. AUDIT_LOG TABLE - Track all data modifications
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    operation VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_log_operation ON audit_log(operation);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- ============================================================================
-- CONSTRAINTS AND VALIDATIONS
-- ============================================================================

-- Financial Summary Constraints
ALTER TABLE financial_summary
ADD CONSTRAINT chk_financial_summary_amounts
CHECK (total_income >= 0 AND total_expenses >= 0 AND total_savings >= 0 AND total_investments >= 0);

-- Transactions Constraints
ALTER TABLE transactions
ADD CONSTRAINT chk_transaction_amount
CHECK (amount > 0);

-- Goals Constraints
ALTER TABLE goals
ADD CONSTRAINT chk_goals_amounts
CHECK (target_amount > 0 AND current_amount >= 0 AND current_amount <= target_amount);

-- Holdings Constraints
ALTER TABLE holdings
ADD CONSTRAINT chk_holdings_quantities
CHECK (quantity > 0 AND average_cost > 0 AND current_value >= 0);

-- Market Prices Constraints
ALTER TABLE market_prices
ADD CONSTRAINT chk_market_prices
CHECK (open_price > 0 AND close_price > 0 AND high_price >= low_price);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- User Financial Overview
CREATE OR REPLACE VIEW v_user_financial_overview AS
SELECT
    u.id,
    u.email,
    u.name,
    fs.year,
    fs.month,
    fs.total_income,
    fs.total_expenses,
    fs.total_savings,
    fs.net_worth,
    (fs.total_savings / NULLIF(fs.total_income, 0)) * 100 as savings_rate_pct
FROM users u
LEFT JOIN financial_summary fs ON u.id = fs.user_id
ORDER BY u.id, fs.year DESC, fs.month DESC;

-- User Transaction Summary by Category
CREATE OR REPLACE VIEW v_transaction_summary_by_category AS
SELECT
    user_id,
    category,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM transactions
GROUP BY user_id, category;

-- User Goal Progress
CREATE OR REPLACE VIEW v_goal_progress AS
SELECT
    id,
    user_id,
    goal_name,
    target_amount,
    current_amount,
    target_date,
    ROUND(((current_amount / NULLIF(target_amount, 0)) * 100)::NUMERIC, 2) as progress_pct,
    CASE
        WHEN current_amount >= target_amount THEN 'COMPLETED'
        WHEN (target_date - CURRENT_DATE) < 30 THEN 'URGENT'
        WHEN current_amount / NULLIF(target_amount, 0) < 0.5 THEN 'AT_RISK'
        ELSE 'ON_TRACK'
    END as goal_status
FROM goals;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Tables Created: 8 (users, financial_summary, transactions, goals, holdings, market_prices, consent_log, audit_log)
-- Primary Keys: UUID with auto-generation
-- Foreign Keys: Referential integrity with ON DELETE CASCADE for user records
-- Indexes: Strategic placement on frequently queried columns
-- Views: 3 common queries pre-built for analytics
-- Constraints: Data validation at database level
-- ============================================================================

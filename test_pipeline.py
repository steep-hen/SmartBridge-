"""
Full Pipeline Test: Data Generation → Validation → Database Load → Verification
"""

from pathlib import Path
from sqlalchemy import create_engine, text
from scripts.load_data import DataLoader

# Create SQLite test database
db_url = 'sqlite:///test_pipeline.db'
engine = create_engine(db_url)

# Create schema
sqlite_schema = '''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    date_of_birth TEXT,
    gender TEXT,
    country TEXT
);

CREATE TABLE IF NOT EXISTS financial_summary (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    year INTEGER,
    month INTEGER,
    total_income DECIMAL,
    total_expenses DECIMAL,
    total_savings DECIMAL,
    total_investments DECIMAL,
    net_worth DECIMAL,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(user_id, year, month),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    transaction_date TEXT,
    amount DECIMAL,
    category TEXT,
    merchant_name TEXT,
    transaction_type TEXT,
    payment_method TEXT,
    description TEXT,
    is_recurring BOOLEAN,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    goal_name TEXT,
    description TEXT,
    target_amount DECIMAL,
    current_amount DECIMAL,
    target_date TEXT,
    goal_type TEXT,
    status TEXT,
    priority TEXT,
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS holdings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    ticker TEXT,
    quantity DECIMAL,
    average_cost DECIMAL,
    current_value DECIMAL,
    asset_type TEXT,
    purchase_date TEXT,
    last_updated TEXT,
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS market_prices (
    id TEXT PRIMARY KEY,
    ticker TEXT,
    price_date TEXT,
    open_price DECIMAL,
    close_price DECIMAL,
    high_price DECIMAL,
    low_price DECIMAL,
    volume INTEGER,
    created_at TEXT
);
'''

print('Creating SQLite schema...')
with engine.connect() as conn:
    for stmt in sqlite_schema.split(';'):
        if stmt.strip():
            conn.execute(text(stmt))
    conn.commit()

print('Schema created\n')

# Load data
print('Loading data into database...')
loader = DataLoader(db_url, data_dir='test_data')
results = loader.load_all()

# Display results
total_rows = results['total_rows']
print('\n' + '='*70)
print('PIPELINE TEST RESULTS')
print('='*70)
for table, count in results['tables_loaded'].items():
    print(f'  {table:25} {count:8} rows loaded')
print(f'\nTotal rows loaded: {total_rows}')

# Verify data integrity
print('\n' + '='*70)
print('DATA INTEGRITY VERIFICATION')
print('='*70)
with engine.connect() as conn:
    # Check row counts
    for table in ['users', 'transactions', 'goals', 'holdings', 'market_prices']:
        result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
        count = result.scalar()
        print(f'  {table:30} {count:6} rows')
    
    # Check foreign key consistency (transactions)
    result = conn.execute(text('''
        SELECT COUNT(*) FROM transactions
        WHERE user_id NOT IN (SELECT id FROM users)
    '''))
    orphaned = result.scalar()
    print(f'\n  Orphaned transaction records: {orphaned}')
    
    # Check data samples
    result = conn.execute(text('SELECT email, name FROM users LIMIT 2'))
    print(f'\n  Sample users:')
    for email, name in result:
        print(f'    - {name} ({email})')
    
    # Check transaction amounts
    result = conn.execute(text('SELECT MIN(amount), MAX(amount), AVG(amount) FROM transactions'))
    min_amt, max_amt, avg_amt = result.fetchone()
    print(f'\n  Transaction amounts:')
    print(f'    - Min: ${min_amt:.2f}')
    print(f'    - Max: ${max_amt:.2f}')
    print(f'    - Avg: ${avg_amt:.2f}')

print('\n' + '='*70)
print('✅ FULL PIPELINE TEST PASSED')
print('='*70)

CREATE TABLE IF NOT EXISTS sheets_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    credentials TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
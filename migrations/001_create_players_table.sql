CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    photo_url VARCHAR(255),
    team_logo VARCHAR(255),
    price FLOAT,
    form FLOAT,
    points_per_match FLOAT,
    gw20_points INTEGER,
    total_points INTEGER,
    total_bonus INTEGER,
    ict_index FLOAT,
    selected_by_percent FLOAT,
    last_updated DATETIME
);
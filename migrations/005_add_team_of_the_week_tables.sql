CREATE TABLE IF NOT EXISTS team_of_the_week (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gameweek INTEGER NOT NULL,
    total_points INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_of_the_week_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_of_the_week_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(20) NOT NULL,
    team VARCHAR(50) NOT NULL,
    points INTEGER NOT NULL,
    photo_url VARCHAR(255),
    team_logo VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_of_the_week_id) REFERENCES team_of_the_week(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gameweek ON team_of_the_week(gameweek);
CREATE INDEX IF NOT EXISTS idx_team_players ON team_of_the_week_players(team_of_the_week_id);
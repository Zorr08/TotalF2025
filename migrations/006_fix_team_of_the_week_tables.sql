-- Create new tables with updated schema
CREATE TABLE IF NOT EXISTS team_of_the_week_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gameweek INTEGER NOT NULL,
    total_points INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_of_the_week_players_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_of_the_week_id INTEGER,
    player_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(20) NOT NULL,
    team VARCHAR(50) NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    photo_url VARCHAR(255),
    team_logo VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_of_the_week_id) REFERENCES team_of_the_week_new(id) ON DELETE CASCADE
);

-- Copy data from old tables to new ones
INSERT OR IGNORE INTO team_of_the_week_new (id, gameweek, total_points, created_at, updated_at)
SELECT id, gameweek, total_points, created_at, updated_at FROM team_of_the_week;

INSERT OR IGNORE INTO team_of_the_week_players_new (id, team_of_the_week_id, player_id, name, position, team, points, photo_url, team_logo, created_at, updated_at)
SELECT id, team_of_the_week_id, player_id, name, position, team, points, photo_url, team_logo, created_at, updated_at FROM team_of_the_week_players;

-- Drop old tables
DROP TABLE IF EXISTS team_of_the_week_players;
DROP TABLE IF EXISTS team_of_the_week;

-- Rename new tables to original names
ALTER TABLE team_of_the_week_new RENAME TO team_of_the_week;
ALTER TABLE team_of_the_week_players_new RENAME TO team_of_the_week_players;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_gameweek ON team_of_the_week(gameweek);
CREATE INDEX IF NOT EXISTS idx_team_players ON team_of_the_week_players(team_of_the_week_id);
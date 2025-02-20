-- Create new table with updated schema
CREATE TABLE players_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    photo_url VARCHAR(255),
    team_logo VARCHAR(255),
    price FLOAT,
    form FLOAT,
    points_per_match FLOAT,
    total_points INTEGER,
    total_bonus INTEGER,
    ict_index FLOAT,
    selected_by_percent FLOAT,
    last_updated DATETIME
);

-- Copy data from old table to new one
INSERT INTO players_new (
    id, name, photo_url, team_logo, price, form, 
    points_per_match, total_points, total_bonus, 
    ict_index, selected_by_percent, last_updated
)
SELECT 
    id, name, photo_url, team_logo, price, form, 
    points_per_match, total_points, total_bonus, 
    ict_index, selected_by_percent, last_updated
FROM players;

-- Drop old table
DROP TABLE players;

-- Rename new table to original name
ALTER TABLE players_new RENAME TO players;
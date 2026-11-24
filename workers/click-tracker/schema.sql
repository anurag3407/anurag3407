CREATE TABLE IF NOT EXISTS clicks (
  key TEXT PRIMARY KEY,
  count INTEGER NOT NULL
);

INSERT OR IGNORE INTO clicks (key, count) VALUES ('github_profile', 4789);

CREATE TABLE IF NOT EXISTS task_store (
    task_id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'processing',
    flow TEXT DEFAULT '',
    phases JSONB DEFAULT '{}',
    result JSONB,
    error TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_store_status ON task_store(status);

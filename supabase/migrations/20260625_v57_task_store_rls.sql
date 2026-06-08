ALTER TABLE task_store ENABLE ROW LEVEL SECURITY;

-- Grant permissions to service_role (used by backend)
GRANT ALL ON TABLE task_store TO service_role;
GRANT ALL ON TABLE task_store TO postgres;

-- Allow full access for service_role
CREATE POLICY "service_role_all" ON task_store
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow anon to read and insert (for future client-side tasks)
GRANT SELECT, INSERT ON TABLE task_store TO anon;
GRANT SELECT, INSERT ON TABLE task_store TO authenticated;

CREATE POLICY "anon_insert" ON task_store
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "anon_select" ON task_store
    FOR SELECT
    TO anon
    USING (true);

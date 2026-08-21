import unittest

from app.config import Settings


class SettingsTests(unittest.TestCase):
    def test_normalizes_postgrest_base_url_for_supabase_client(self):
        settings = Settings(supabase_url="https://example.supabase.co/rest/v1/")
        self.assertEqual(settings.supabase_url, "https://example.supabase.co")

    def test_preserves_project_base_url(self):
        settings = Settings(supabase_url="https://example.supabase.co")
        self.assertEqual(settings.supabase_url, "https://example.supabase.co")


if __name__ == "__main__":
    unittest.main()

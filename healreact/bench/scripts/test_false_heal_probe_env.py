import os
import tempfile
import unittest
from pathlib import Path

from false_heal_probe import load_project_dotenv


class TestFalseHealProbeEnv(unittest.TestCase):
    def test_load_project_dotenv_loads_env_file_without_overriding_existing_values(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / ".env"
            env_path.write_text(
                "HEALREACT_DOTENV_TEST_LOADED=from_file\n"
                "HEALREACT_DOTENV_TEST_EXISTING=from_file\n"
            )

            old_loaded = os.environ.pop("HEALREACT_DOTENV_TEST_LOADED", None)
            old_existing = os.environ.get("HEALREACT_DOTENV_TEST_EXISTING")
            os.environ["HEALREACT_DOTENV_TEST_EXISTING"] = "already_set"
            try:
                self.assertTrue(load_project_dotenv(env_path))
                self.assertEqual(os.environ["HEALREACT_DOTENV_TEST_LOADED"], "from_file")
                self.assertEqual(os.environ["HEALREACT_DOTENV_TEST_EXISTING"], "already_set")
            finally:
                os.environ.pop("HEALREACT_DOTENV_TEST_LOADED", None)
                if old_loaded is not None:
                    os.environ["HEALREACT_DOTENV_TEST_LOADED"] = old_loaded
                if old_existing is None:
                    os.environ.pop("HEALREACT_DOTENV_TEST_EXISTING", None)
                else:
                    os.environ["HEALREACT_DOTENV_TEST_EXISTING"] = old_existing


if __name__ == "__main__":
    unittest.main()

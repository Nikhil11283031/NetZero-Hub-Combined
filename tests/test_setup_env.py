import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('setup_env', ROOT / 'scripts/setup_env.py')
setup_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_env)


class SetupEnvironmentTests(unittest.TestCase):
    def test_existing_database_passwords_and_accounts_survive_repeated_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'env.example').write_text((ROOT / 'env.example').read_text())
            (root / '.env').write_text('MYSQL_PASSWORD=keep-this-db-password\nMYSQL_ROOT_PASSWORD=keep-this-root\nDEMO_RESIDENT_PASSWORD=my-existing-password\n')
            setup_env.configure(root)
            first = (root / '.env').read_text()
            self.assertIn('MYSQL_PASSWORD=keep-this-db-password\n', first)
            self.assertIn('MYSQL_ROOT_PASSWORD=keep-this-root\n', first)
            self.assertIn('DEMO_RESIDENT_PASSWORD=my-existing-password\n', first)
            self.assertNotIn('=CHANGE-ME-', first)
            self.assertRegex(first, r'NZ_INTERNAL_TOKEN=[a-f0-9]{64}')
            setup_env.configure(root)
            self.assertEqual((root / '.env').read_text(), first)

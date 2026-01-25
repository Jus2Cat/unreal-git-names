import unittest
import subprocess
import os
import sys
import re
import glob

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT_PATH = os.path.join(PROJECT_ROOT, 'scripts', 'get_actor_name.py')
TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')


def discover_version_folders():
    """Find all UE version folders (pattern: X_Y where X and Y are digits)."""
    folders = {}
    for entry in os.listdir(TESTS_DIR):
        if re.match(r'^\d+_\d+$', entry):
            folder_path = os.path.join(TESTS_DIR, entry)
            if os.path.isdir(folder_path):
                # Find all .uasset files in this folder
                uassets = glob.glob(os.path.join(folder_path, '*.uasset'))
                if uassets:
                    folders[entry] = uassets
    return folders


def discover_test_assets():
    """Build list of all test assets from version folders."""
    assets = []
    for version, files in discover_version_folders().items():
        for filepath in files:
            assets.append({
                'version': version,
                'path': filepath,
                'filename': os.path.basename(filepath),
            })
    return assets


TEST_ASSETS = discover_test_assets()

class TestGetActorNameCLI(unittest.TestCase):

    def run_script(self, args):
        """Helper to run the script and capture output."""
        cmd = [sys.executable, SCRIPT_PATH] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result

    def test_parsing_all_assets(self):
        """Test that all discovered assets parse successfully."""
        self.assertTrue(TEST_ASSETS, "No test assets found in version folders")
        for asset in TEST_ASSETS:
            with self.subTest(version=asset['version'], file=asset['filename']):
                result = self.run_script([asset['path']])
                self.assertEqual(result.returncode, 0)
                output = result.stdout.strip()
                self.assertTrue(output, f"Empty output for {asset['filename']}")
                # Output should be printable text (the label)
                self.assertTrue(output.isprintable(), f"Non-printable output: {output}")

    def test_show_type_valid_labels(self):
        """Test --show-type returns valid label types (ActorLabel or FolderLabel)."""
        valid_types = {'ActorLabel', 'FolderLabel', 'Label'}
        for asset in TEST_ASSETS:
            with self.subTest(version=asset['version'], file=asset['filename']):
                result = self.run_script([asset['path'], "--show-type"])
                self.assertEqual(result.returncode, 0)
                output = result.stdout.strip()
                # Should contain [SomeLabel] format
                self.assertIn("|", output)
                match = re.search(r'\[(\w+)\]', output)
                self.assertIsNotNone(match, f"No [Type] found in: {output}")
                self.assertIn(match.group(1), valid_types)

    def test_show_path_absolute(self):
        """Test --show-path outputs absolute paths."""
        for asset in TEST_ASSETS:
            with self.subTest(version=asset['version'], file=asset['filename']):
                result = self.run_script([asset['path'], "--show-path"])
                self.assertEqual(result.returncode, 0)
                output = result.stdout.strip()
                self.assertIn("|", output)
                # Path should be absolute (contains drive letter on Windows or starts with /)
                self.assertTrue(
                    os.path.abspath(asset['path']) in output or
                    asset['path'] in output,
                    f"Path not found in output: {output}"
                )

    def test_all_flags_format(self):
        """Test combined --show-path --show-type output format."""
        for asset in TEST_ASSETS:
            with self.subTest(version=asset['version'], file=asset['filename']):
                result = self.run_script([asset['path'], "--show-path", "--show-type"])
                self.assertEqual(result.returncode, 0)
                output = result.stdout.strip()
                # Should have exactly 2 separators: path | [type] | name
                self.assertEqual(output.count("|"), 2, f"Wrong format: {output}")

    def test_recursive_scan_versions(self):
        """Test scanning each version directory."""
        for version, files in discover_version_folders().items():
            version_dir = os.path.join(TESTS_DIR, version)
            with self.subTest(version=version):
                result = self.run_script([version_dir])
                self.assertEqual(result.returncode, 0)
                # Should output at least as many lines as files
                output_lines = [l for l in result.stdout.strip().split('\n') if l]
                self.assertGreaterEqual(
                    len(output_lines), len(files),
                    f"Expected {len(files)} results, got {len(output_lines)}"
                )

    def test_missing_file(self):
        """Test behavior when file does not exist."""
        missing_path = os.path.join(PROJECT_ROOT, 'non_existent_file.uasset')
        result = self.run_script([missing_path])
        self.assertIn("Error: Path not found", result.stderr)

    def test_no_test_assets_warning(self):
        """Ensure test assets exist (informational)."""
        versions = discover_version_folders()
        print(f"\nDiscovered {len(versions)} version folders:")
        for version, files in sorted(versions.items()):
            print(f"  {version}: {len(files)} file(s)")
        self.assertTrue(versions, "No version folders found! Add folders like 5_3/, 5_4/ with .uasset files")

if __name__ == '__main__':
    unittest.main()

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "booth_checker"))

from fbx_diff import build_fbx_path_list, calculate_fbx_diff


class FbxDiffTests(unittest.TestCase):
    def test_same_basename_with_new_hash_is_reported_as_changed(self):
        previous_fbx = {"old_package/model.fbx": "aaaaaaaa11111111"}
        current_fbx = {"new_package/model.fbx": "bbbbbbbb22222222"}

        added, changed, deleted = calculate_fbx_diff(previous_fbx, current_fbx)

        self.assertEqual(added, [])
        self.assertEqual(deleted, [])
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0]["basename"], "model.fbx")
        self.assertEqual(changed[0]["previous_hash"], "aaaaaaaa11111111")
        self.assertEqual(changed[0]["current_hash"], "bbbbbbbb22222222")

        path_list = build_fbx_path_list(added, changed, deleted)
        self.assertEqual(path_list, [
            {
                "line_str": (
                    "model.fbx {from old_package/model.fbx -> new_package/model.fbx} "
                    "[aaaaaaaa -> bbbbbbbb]"
                ),
                "status": 3,
            }
        ])

    def test_duplicate_basenames_keep_unchanged_entries_out_of_diff(self):
        previous_fbx = {
            "pack_a/model.fbx": "samehash00",
            "pack_b/model.fbx": "oldhash11",
        }
        current_fbx = {
            "pack_a/model.fbx": "samehash00",
            "pack_c/model.fbx": "newhash22",
        }

        added, changed, deleted = calculate_fbx_diff(previous_fbx, current_fbx)

        self.assertEqual(added, [])
        self.assertEqual(deleted, [])
        self.assertEqual(
            changed,
            [
                {
                    "basename": "model.fbx",
                    "previous_hash": "oldhash11",
                    "current_hash": "newhash22",
                    "previous_path": "pack_b/model.fbx",
                    "current_path": "pack_c/model.fbx",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()

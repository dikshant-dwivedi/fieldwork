import json
from pathlib import Path
import tempfile
import unittest

from manual_config import ParticipantConfig, load_config


class ManualConfigTests(unittest.TestCase):
    def test_loads_a_visible_name_to_mac_address_book(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alice.json"
            path.write_text(json.dumps({
                "name": "Alice",
                "peers": {"Bob": "02:00:00:00:00:02"},
            }))

            self.assertEqual(
                load_config(str(path)),
                ParticipantConfig("Alice", {"Bob": "02:00:00:00:00:02"}),
            )

    def test_rejects_a_participant_in_its_own_peer_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alice.json"
            path.write_text(json.dumps({
                "name": "Alice",
                "peers": {"Alice": "02:00:00:00:00:01"},
            }))

            with self.assertRaisesRegex(ValueError, "must not list itself"):
                load_config(str(path))


if __name__ == "__main__":
    unittest.main()

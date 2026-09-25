import unittest

from ethernet import mac_to_bytes
from peer_directory import PeerDirectory


class PeerDirectoryTests(unittest.TestCase):
    def test_resolves_one_announced_name(self):
        directory = PeerDirectory(timeout=7)
        bob = mac_to_bytes("02:00:00:00:00:02")
        directory.observe("Bob", bob, now=10)

        self.assertEqual(directory.resolve("Bob", now=12), bob)

    def test_refuses_a_duplicate_name(self):
        directory = PeerDirectory(timeout=7)
        directory.observe("Bob", mac_to_bytes("02:00:00:00:00:02"), now=10)
        directory.observe("Bob", mac_to_bytes("02:00:00:00:00:09"), now=11)

        with self.assertRaisesRegex(ValueError, "ambiguous"):
            directory.resolve("Bob", now=12)

    def test_expires_a_peer_after_missing_announcements(self):
        directory = PeerDirectory(timeout=7)
        directory.observe("Carol", mac_to_bytes("02:00:00:00:00:03"), now=10)

        with self.assertRaisesRegex(ValueError, "unavailable"):
            directory.resolve("Carol", now=18)


if __name__ == "__main__":
    unittest.main()

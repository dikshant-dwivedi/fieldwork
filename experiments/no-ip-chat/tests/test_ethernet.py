import unittest

from ethernet import (
    ReceivedFrame,
    build_frame,
    format_mac,
    mac_to_bytes,
    parse_frame,
)


class EthernetFrameTests(unittest.TestCase):
    def test_builds_and_parses_a_padded_frame(self):
        alice = mac_to_bytes("02:00:00:00:00:01")
        bob = mac_to_bytes("02:00:00:00:00:02")

        encoded = build_frame(alice, bob, "hello from Alice")

        self.assertEqual(len(encoded), 60)
        self.assertEqual(
            parse_frame(encoded),
            ReceivedFrame(bob, alice, "hello from Alice"),
        )

    def test_formats_a_mac_address(self):
        self.assertEqual(
            format_mac(bytes((2, 0, 0, 0, 0, 1))),
            "02:00:00:00:00:01",
        )

    def test_rejects_the_wrong_ether_type(self):
        alice = mac_to_bytes("02:00:00:00:00:01")
        bob = mac_to_bytes("02:00:00:00:00:02")
        encoded = bytearray(build_frame(alice, bob, "hello"))
        encoded[12:14] = bytes.fromhex("0800")

        with self.assertRaisesRegex(ValueError, "unexpected EtherType"):
            parse_frame(bytes(encoded))


if __name__ == "__main__":
    unittest.main()

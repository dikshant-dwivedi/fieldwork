import unittest

from chat_protocol import ChatMessage, Hello, decode_packet, encode_packet


class ChatProtocolTests(unittest.TestCase):
    def test_hello_round_trip_ignores_ethernet_padding(self):
        payload = encode_packet(Hello("Alice")).ljust(46, b"\x00")
        self.assertEqual(decode_packet(payload), Hello("Alice"))

    def test_chat_round_trip_ignores_ethernet_padding(self):
        original = ChatMessage("Bob", "Hello Alice")
        payload = encode_packet(original).ljust(46, b"\x00")
        self.assertEqual(decode_packet(payload), original)

    def test_rejects_another_protocol_version(self):
        payload = bytearray(encode_packet(Hello("Alice")))
        payload[0:4] = b"NIP9"
        with self.assertRaisesRegex(ValueError, "checkpoint 5"):
            decode_packet(bytes(payload))


if __name__ == "__main__":
    unittest.main()

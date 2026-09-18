import unittest

from chat_protocol import ChatMessage, decode_message, encode_message


class ChatProtocolTests(unittest.TestCase):
    def test_round_trip_ignores_ethernet_padding(self):
        original = ChatMessage("Alice", "Hello Bob")
        padded_payload = encode_message(original).ljust(46, b"\x00")

        self.assertEqual(decode_message(padded_payload), original)

    def test_rejects_another_protocol_version(self):
        payload = bytearray(encode_message(ChatMessage("Alice", "Hello")))
        payload[0:4] = b"NIP9"

        with self.assertRaisesRegex(ValueError, "checkpoint 2"):
            decode_message(bytes(payload))


if __name__ == "__main__":
    unittest.main()

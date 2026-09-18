"""Unit tests for JieLi RCSP protocol."""

import unittest
from jlab_controller.protocol.jieli_rcsp import (
    JieLiPacket,
    JieLiEncoder,
    VOICE_MODE_DENOISE,
    VOICE_MODE_TRANSPARENT,
    VOICE_MODE_CLOSE,
    EQ_MODE_SIGNATURE,
    EQ_MODE_BALANCED,
    EQ_MODE_BASS_BOOST,
    EQ_MODE_CUSTOM,
)


class TestJieLiRCSP(unittest.TestCase):
    def test_voice_mode_encoding(self):
        pkt = JieLiEncoder.build_set_voice_mode(VOICE_MODE_DENOISE, awareness_level=75)
        raw = pkt.encode()
        self.assertTrue(raw.startswith(bytes([0xFE, 0xDC, 0xBA])))
        self.assertTrue(raw.endswith(bytes([0xEF])))
        self.assertEqual(raw[4], 0x08)  # SetSysInfo opcode
        
        # Decode test
        decoded, consumed = JieLiPacket.decode(raw)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.op_code, 0x08)
        self.assertEqual(consumed, len(raw))

    def test_eq_preset_encoding(self):
        gains = [1.0, 1.0, 0.0, -2.0, -3.0, -4.0, -4.0, -2.0, -1.0, -2.0]
        pkt = JieLiEncoder.build_set_eq(EQ_MODE_SIGNATURE, gains)
        raw = pkt.encode()
        self.assertTrue(raw.startswith(bytes([0xFE, 0xDC, 0xBA])))
        self.assertTrue(raw.endswith(bytes([0xEF])))
        
        decoded, consumed = JieLiPacket.decode(raw)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.op_code, 0x08)

    def test_query_commands(self):
        battery_pkt = JieLiEncoder.build_get_battery()
        self.assertEqual(battery_pkt.op_code, 0x07)
        
        vm_pkt = JieLiEncoder.build_get_current_voice_mode()
        self.assertEqual(vm_pkt.op_code, 0x07)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for JLab RACE protocol packets, PEQ encoders, and ANC modes."""

import unittest
from jlab_controller.constants import AncMode, EqPreset, RaceId, RaceType
from jlab_controller.protocol.anc import AncEncoder
from jlab_controller.protocol.mmi import MmiEncoder
from jlab_controller.protocol.peq import PeqEncoder
from jlab_controller.protocol.race_packet import RacePacket

class TestRaceProtocol(unittest.TestCase):
    def test_packet_encode_decode(self):
        # Create a sample packet
        pkt = RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.GET_BATTERY,
            payload=b"",
        )
        encoded = pkt.encode()
        self.assertEqual(encoded[0], 0x05)
        self.assertEqual(encoded[1], 0x5A)

        # Decode packet
        decoded_pkt, consumed = RacePacket.decode(encoded)
        self.assertIsNotNone(decoded_pkt)
        self.assertEqual(consumed, len(encoded))
        self.assertEqual(decoded_pkt.race_id, RaceId.GET_BATTERY)
        self.assertEqual(decoded_pkt.race_type, RaceType.CMD_NEED_RESP)

    def test_eq_preset_command(self):
        # Setting Signature EQ (preset 1)
        pkt = PeqEncoder.build_set_eq_preset(EqPreset.SIGNATURE)
        encoded = pkt.encode()
        self.assertEqual(pkt.race_id, RaceId.HOSTAUDIO_MMI_SET_ENUM)
        self.assertEqual(encoded, bytes([0x05, 0x5A, 0x05, 0x00, 0x00, 0x09, 0x00, 0x00, 0x01]))

    def test_eq_indication_parsing(self):
        # Indication from headset when tapped to switch to Bass Boost (preset 3)
        # Expected from hardware: 05 5D 06 00 01 09 00 00 00 03
        raw_indication = bytes([0x05, 0x5D, 0x06, 0x00, 0x01, 0x09, 0x00, 0x00, 0x00, 0x03])
        pkt, consumed = RacePacket.decode(raw_indication)
        self.assertIsNotNone(pkt)
        self.assertEqual(consumed, len(raw_indication))
        preset_idx = PeqEncoder.parse_eq_indication(pkt)
        self.assertEqual(preset_idx, 3)

    def test_anc_commands(self):
        # ANC ON
        pkt_on = AncEncoder.build_set_anc_on(1)
        self.assertEqual(pkt_on.race_id, RaceId.MMI_ANC_CONTROL)
        self.assertEqual(pkt_on.payload, bytes([0x00, 0x0A, 0x01, 0x01]))

        # ANC OFF
        pkt_off = AncEncoder.build_set_anc_off()
        self.assertEqual(pkt_off.race_id, RaceId.MMI_ANC_CONTROL)
        self.assertEqual(pkt_off.payload, bytes([0x00, 0x0B, 0x01]))

        # Be Aware
        pkt_aware = AncEncoder.build_set_be_aware(9)
        self.assertEqual(pkt_aware.payload, bytes([0x00, 0x0A, 0x09, 0x01]))

        # Set Awareness Gain (75%)
        pkt_gain = AncEncoder.build_set_awareness_gain(75)
        self.assertEqual(pkt_gain.payload, bytes([0x00, 0x0F, 75, 0, 0x01]))

if __name__ == "__main__":
    unittest.main()

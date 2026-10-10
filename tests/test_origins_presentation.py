"""Inspector exposes mapped traits without normalizing unusual inventory data."""
import unittest

from koei_editor.games.origins import origins_parser as backend
from koei_editor.games.origins.origins_presentation import OriginsPresentation
from koei_editor.games.origins import origins_weapons as weapons
from tests.test_origins_parser import fixture


class OriginsInspectionTests(unittest.TestCase):
    def test_inventory_inspection_preserves_unknown_traits_and_reserved_records(self):
        from koei_editor.games.origins import origins_codec
        raw = fixture(29)
        envelope = origins_codec.decode(raw, 'slot')
        payload = bytearray(envelope.payload)
        base = weapons.BASES[29]
        for index in range(weapons.SERIALIZED_COUNT):
            offset = base + index * weapons.RECORD_SIZE
            payload[offset:offset + 2] = b'\xff\xff'
        offset = base + 849 * weapons.RECORD_SIZE
        payload[offset:offset + 2] = (299).to_bytes(2, 'little')
        payload[offset + 2] = 120
        payload[offset + 3:offset + 15] = b'\xff\xff' * 6
        payload[offset + 15:offset + 21] = bytes((255, 2, 3, 4, 5, 6))
        reserved = base + 850 * weapons.RECORD_SIZE
        payload[reserved:reserved + 2] = b'\x00\x00'
        document = backend.decode(origins_codec.encode(bytes(payload), envelope.seed, 'slot'))
        table = OriginsPresentation(backend, 'origins').inspection_tables(document)[0]
        self.assertEqual(len(table.rows), 1)
        self.assertEqual(table.rows[0][:3], (850, 299, 120))
        self.assertIn('65535', table.rows[0][3])
        self.assertEqual(table.rows[0][4], '255, 2, 3, 4, 5, 6')
        self.assertEqual(table.rows[0][5], 'Inspection only')
        self.assertEqual(backend.serialize(document, {}), document.raw)


if __name__ == '__main__':
    unittest.main()

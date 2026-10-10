"""Nonfinite compatibility fields survive verified writes without trusting mutations."""
import hashlib
import math
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from koei_editor.games.dw3.models import Change, SaveError, fields
from koei_editor.games.dw3.save_codec import decrypt, encrypt
from koei_editor.games.dw3.save_parser import parse_bytes, read_save
from koei_editor.games.dw3.save_writer import serialize
from test_weapon_rolls import edited_fixture_bytes

FIXTURE = ROOT / "work/original-upload/GameStatusData.sav"


def fstring(value):
    raw = value.encode("utf-8") + b"\0"
    return struct.pack("<i", len(raw)) + raw


@unittest.skipUnless(FIXTURE.exists(), "The supplied workspace copy is required.")
class NaNPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_hash = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        original = read_save(FIXTURE)
        time = fields(original.records("WeaponDataArray")[0])["GetTime"]
        # Deliberately use distinct noncanonical NaN payloads in both float widths.
        cls.nan64 = struct.pack("<Q", 0x7FF8000000000042)
        cls.nan32 = struct.pack("<I", 0x7FC00042)
        raw = edited_fixture_bytes(original, [(time, cls.nan64)])
        plain = bytearray(decrypt(raw))
        size = struct.unpack_from(">I", plain)[0]
        plain = plain[:4 + size]
        offset = len(plain) - 4 - len(fstring("None"))
        tag = (fstring("UnrecognizedNaNFloat") + fstring("FloatProperty") +
               struct.pack("<iiB", 0, 4, 0) + cls.nan32)
        plain[offset:offset] = tag
        struct.pack_into(">I", plain, 0, len(plain) - 4)
        plain.extend(bytes((-len(plain)) % 16))
        cls.raw = encrypt(bytes(plain))

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == cls.source_hash

    def document(self):
        return parse_bytes(self.raw)

    def assert_nan_payloads(self, document):
        time = fields(document.records("WeaponDataArray")[0])["GetTime"]
        extra = document.properties["UnrecognizedNaNFloat"]
        self.assertTrue(math.isnan(time["value"]))
        self.assertTrue(math.isnan(extra["value"]))
        self.assertEqual(document.plaintext[time["data_offset"]:time["data_offset"] + 8], self.nan64)
        self.assertEqual(document.plaintext[extra["data_offset"]:extra["data_offset"] + 4], self.nan32)

    def test_noop_preserves_both_nan_payloads_and_audit(self):
        document = self.document()
        self.assert_nan_payloads(document)
        raw, audit = serialize(document)
        self.assertEqual(raw, self.raw)
        self.assertEqual(audit["plaintext_changes"], [])
        self.assertEqual(audit["changed_aes_blocks"], [])
        self.assertEqual(audit["source_sha256"], audit["output_sha256"])

    def test_unrelated_scalar_edit_preserves_nan_bytes(self):
        document = self.document()
        point = fields(document.records("PCSaveDataArray")[0])["SPoint"]
        target = 99998 if point["value"] == 99999 else 99999
        raw, audit = serialize(document, [Change("officer", 0, "SPoint", target)])
        reread = parse_bytes(raw)
        self.assert_nan_payloads(reread)
        expected = bytearray(document.plaintext)
        expected[point["data_offset"]:point["data_offset"] + 4] = struct.pack("<i", target)
        self.assertEqual(reread.plaintext, bytes(expected))
        self.assertEqual(len(audit["plaintext_changes"]), 1)
        self.assertEqual(audit["plaintext_changes"][0]["offset"], point["data_offset"])
        self.assertFalse(audit["resized"])

    def test_nan_does_not_bypass_graph_mutation_guard(self):
        mutations = {
            "timestamp value": lambda d: fields(d.records("WeaponDataArray")[0])["GetTime"].update(value=0.0),
            "offset": lambda d: fields(d.records("WeaponDataArray")[0])["GetTime"].update(data_offset=0),
            "type": lambda d: d.properties["UnrecognizedNaNFloat"].update(type="IntProperty"),
            "numeric scalar type": lambda d: fields(d.records("PCSaveDataArray")[0])["SPoint"].update(
                value=float(fields(d.records("PCSaveDataArray")[0])["SPoint"]["value"])),
            "bool equals integer": lambda d: d.properties["UnrecognizedNaNFloat"].update(array_index=False),
            "structure": lambda d: d.properties["CanUseCharaArray"]["value"].update(values=tuple(
                d.properties["CanUseCharaArray"]["value"]["values"])),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                document = self.document()
                mutate(document)
                with self.assertRaisesRegex(SaveError, "bytes or offsets changed"):
                    serialize(document)

    def test_plaintext_mutation_is_still_refused(self):
        document = self.document()
        plain = bytearray(document.plaintext)
        prop = document.properties["UnrecognizedNaNFloat"]
        plain[prop["data_offset"]] ^= 1
        document.plaintext = bytes(plain)
        with self.assertRaisesRegex(SaveError, "bytes or offsets changed"):
            serialize(document)


if __name__ == "__main__":
    unittest.main()

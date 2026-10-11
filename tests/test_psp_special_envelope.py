"""Procedural malformed-envelope checks and optional submitted-file observations."""
from dataclasses import asdict
import os
from pathlib import Path
import struct
import unittest
import zipfile

from koei_editor.research.psp_special.envelope import (
    EnvelopeError, PROFILES, inspect_envelope,
)


def procedural_sfo(profile):
    secure_files = bytearray(3168)
    secure_files[:9] = b'DATA.BIN\0'
    secure_files[13:29] = bytes(range(1, 17))
    fields = (
        (b'CATEGORY', 0x0204, b'MS\0', 4),
        (b'PARENTAL_LEVEL', 0x0404, struct.pack('<I', 2), 4),
        (b'SAVEDATA_DETAIL', 0x0204, b'PRIVATE_PLAYER_TEXT\0', 1024),
        (b'SAVEDATA_DIRECTORY', 0x0204, profile.directory.encode() + b'\0', 64),
        (b'SAVEDATA_FILE_LIST', 0x0004, bytes(secure_files), 3168),
        (b'SAVEDATA_PARAMS', 0x0004, b'\x41' + bytes(range(1, 128)), 128),
        (b'SAVEDATA_TITLE', 0x0204, b'PRIVATE_PLAYER_TITLE\0', 128),
        (b'TITLE', 0x0204, profile.title.encode('utf-8') + b'\0', 128),
    )
    keys = bytearray()
    values = bytearray()
    index = bytearray()
    positions = {}
    for name, kind, value, capacity in fields:
        positions[name] = (len(index) + 20, len(values))
        index += struct.pack('<HHIII', len(keys), kind, len(value), capacity, len(values))
        keys += name + b'\0'
        values += value + b'\xa5' * (capacity - len(value))
    keys_start = 20 + len(index)
    data_start = (keys_start + len(keys) + 3) // 4 * 4
    raw = bytearray(struct.pack('<4sIIII', b'\x00PSF', 0x101,
                                keys_start, data_start, len(fields)))
    raw += index + keys
    raw += bytes(data_start - len(raw))
    raw += values
    raw += bytes(4912 - len(raw))
    positions = {name: (entry, data_start + value)
                 for name, (entry, value) in positions.items()}
    return bytes(raw), positions


class PSPEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.profile = PROFILES[0]
        self.sfo, self.positions = procedural_sfo(self.profile)
        self.data = bytes(self.profile.data_size)

    def inspect(self, sfo=None, data=None, profile=None):
        return inspect_envelope(profile or self.profile.id,
                                self.sfo if sfo is None else sfo,
                                self.data if data is None else data)

    def rejects(self, raw):
        with self.assertRaises(EnvelopeError) as error:
            self.inspect(raw)
        self.assertNotIn('PRIVATE_PLAYER', str(error.exception))

    def mutate_index(self, field, offset, encoding, value):
        raw = bytearray(self.sfo)
        struct.pack_into(encoding, raw, self.positions[field][0] + offset, value)
        return bytes(raw)

    def test_all_observed_profiles_have_explicit_unverified_results(self):
        for profile in PROFILES:
            with self.subTest(profile=profile.id):
                raw, _ = procedural_sfo(profile)
                before = raw
                result = inspect_envelope(profile.id, raw, bytes(profile.data_size))
                self.assertEqual(result.profile_id, profile.id)
                self.assertEqual(result.encrypted_file_size, profile.data_size)
                self.assertFalse(result.envelope_authenticated)
                self.assertFalse(result.payload_layout_verified)
                self.assertEqual(raw, before)
                self.assertNotIn('PRIVATE_PLAYER', repr(asdict(result)))

    def test_bad_magic_version_length_and_index_count(self):
        for data in (b'', self.sfo[:-1], self.sfo + b'\0'):
            self.rejects(data)
        for offset, value in ((0, 0), (4, 0x102), (16, 0), (16, 65), (16, 10000)):
            raw = bytearray(self.sfo)
            struct.pack_into('<I', raw, offset, value)
            self.rejects(bytes(raw))

    def test_index_key_and_data_regions_must_be_ordered_and_bounded(self):
        for offset, value in ((8, 0), (8, 4912), (12, 0), (12, 5000), (12, 148)):
            raw = bytearray(self.sfo)
            struct.pack_into('<I', raw, offset, value)
            self.rejects(bytes(raw))
        for offset, kind, value in ((0, '<H', 65535), (2, '<H', 999),
                                    (4, '<I', 5), (8, '<I', 5000),
                                    (12, '<I', 1), (12, '<I', 5000)):
            self.rejects(self.mutate_index(b'CATEGORY', offset, kind, value))

    def test_duplicate_keys_overlapping_values_and_unterminated_keys(self):
        raw = bytearray(self.sfo)
        struct.pack_into('<H', raw, 36, 0)
        self.rejects(bytes(raw))
        first_value = self.positions[b'CATEGORY'][1]
        other_value = self.positions[b'PARENTAL_LEVEL'][1]
        self.rejects(self.mutate_index(b'PARENTAL_LEVEL', 12, '<I',
                                      other_value - first_value - 4))
        raw = bytearray(self.sfo)
        keys, values = struct.unpack_from('<II', raw, 8)
        raw[keys:values] = b'A' * (values - keys)
        self.rejects(bytes(raw))

    def test_foreign_category_directory_title_and_selected_profile(self):
        for field in (b'CATEGORY', b'SAVEDATA_DIRECTORY', b'TITLE'):
            raw = bytearray(self.sfo)
            raw[self.positions[field][1]] ^= 1
            self.rejects(bytes(raw))
        for profile in ('unknown', PROFILES[1].id, PROFILES[2].id):
            with self.assertRaises(EnvelopeError):
                self.inspect(profile=profile)

    def test_sfo_string_type_length_and_termination(self):
        self.rejects(self.mutate_index(b'CATEGORY', 2, '<H', 0x0004))
        self.rejects(self.mutate_index(b'CATEGORY', 4, '<I', 0))
        raw = bytearray(self.sfo)
        raw[self.positions[b'CATEGORY'][1] + 2] = 1
        self.rejects(bytes(raw))
        self.rejects(self.mutate_index(b'PARENTAL_LEVEL', 4, '<I', 3))

    def test_secure_flag_and_parameter_type_length(self):
        for flag in (0, 1, 0x21, 0x42, 0xFF):
            raw = bytearray(self.sfo)
            raw[self.positions[b'SAVEDATA_PARAMS'][1]] = flag
            self.rejects(bytes(raw))
        self.rejects(self.mutate_index(b'SAVEDATA_PARAMS', 4, '<I', 127))
        self.rejects(self.mutate_index(b'SAVEDATA_PARAMS', 2, '<H', 0x0204))

    def test_secure_file_list_bounds_duplicates_foreign_names_and_missing_mac(self):
        self.rejects(self.mutate_index(b'SAVEDATA_FILE_LIST', 4, '<I', 3167))
        start = self.positions[b'SAVEDATA_FILE_LIST'][1]
        for edit in ('duplicate', 'foreign', 'empty', 'missing_mac', 'bad_name_tail', 'no_nul'):
            raw = bytearray(self.sfo)
            if edit == 'duplicate':
                raw[start + 32:start + 64] = raw[start:start + 32]
            elif edit == 'foreign':
                raw[start] = ord('X')
            elif edit == 'empty':
                raw[start:start + 32] = bytes(32)
            elif edit == 'missing_mac':
                raw[start + 13:start + 29] = bytes(16)
            elif edit == 'bad_name_tail':
                raw[start + 12] = 1
            else:
                raw[start:start + 13] = b'A' * 13
            with self.subTest(edit=edit):
                self.rejects(bytes(raw))

    def test_secure_file_padding_cannot_substitute_for_declared_mac(self):
        # Native PspSavedataFileList is filename[13], hash[16], pad[3].
        # Nonzero reserved bytes must not make an absent stored MAC present.
        start = self.positions[b'SAVEDATA_FILE_LIST'][1]
        raw = bytearray(self.sfo)
        raw[start + 13:start + 29] = bytes(16)
        raw[start + 29:start + 32] = b'\x51\x52\x53'
        self.rejects(bytes(raw))

    def test_first_native_mac_byte_and_unknown_padding_are_preserved(self):
        start = self.positions[b'SAVEDATA_FILE_LIST'][1]
        raw = bytearray(self.sfo)
        raw[start + 13:start + 32] = b'\x01' + bytes(18)
        before = bytes(raw)
        result = self.inspect(before)
        self.assertFalse(result.envelope_authenticated)
        self.assertEqual(bytes(raw), before)
        raw[start + 29:start + 32] = b'\x91\x92\x93'
        padded = bytes(raw)
        self.assertEqual(self.inspect(padded), result)
        self.assertEqual(bytes(raw), padded)

    def test_encrypted_data_length_and_metadata_do_not_authenticate_payload(self):
        for data in (b'', self.data[:-1], self.data + b'\0'):
            with self.assertRaises(EnvelopeError):
                self.inspect(data=data)
        # Transport crypto is intentionally absent; same-length corruption
        # cannot be detected and must never acquire an authenticated label.
        changed = bytearray(self.data)
        changed[123] = 255
        result = self.inspect(data=bytes(changed))
        self.assertFalse(result.envelope_authenticated)
        self.assertFalse(result.payload_layout_verified)

    def test_unknown_player_metadata_is_never_exposed(self):
        raw = bytearray(self.sfo)
        raw[self.positions[b'SAVEDATA_DETAIL'][1]] = 255
        result = self.inspect(bytes(raw))
        self.assertEqual(set(asdict(result)), {
            'profile_id', 'product_title', 'savedata_directory', 'secure_filename',
            'encrypted_file_size', 'sfo_size', 'secure_flag',
            'envelope_authenticated', 'payload_layout_verified',
        })
        self.assertNotIn('PRIVATE_PLAYER', repr(result))


class OptionalSubmittedEnvelopeTests(unittest.TestCase):
    def check_zip(self, profile, variable):
        configured = os.environ.get(variable)
        if not configured:
            self.skipTest(f'{variable} not configured; no submitted reference observed')
        path = Path(configured)
        original = path.read_bytes()
        with zipfile.ZipFile(path) as archive:
            required = (profile.directory + '/PARAM.SFO', profile.directory + '/DATA.BIN')
            contents = []
            for name, expected_size in zip(required, (4912, profile.data_size)):
                matches = [item for item in archive.infolist() if item.filename == name]
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0].file_size, expected_size)
                contents.append(archive.read(matches[0]))
        result = inspect_envelope(profile.id, *contents)
        self.assertFalse(result.envelope_authenticated)
        self.assertFalse(result.payload_layout_verified)
        self.assertEqual(path.read_bytes(), original)

    def test_dw6_submitted_reference(self):
        self.check_zip(PROFILES[0], 'DW6_SPECIAL_PSP_ENVELOPE_ZIP')

    def test_dw7_submitted_reference(self):
        self.check_zip(PROFILES[1], 'DW7_SPECIAL_PSP_ENVELOPE_ZIP')

    def test_sw3z_submitted_reference(self):
        self.check_zip(PROFILES[2], 'SW3Z_SPECIAL_PSP_ENVELOPE_ZIP')


if __name__ == '__main__':
    unittest.main()

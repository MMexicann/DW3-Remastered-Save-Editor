"""Published AES vectors and provider lifetime checks, on native CNG or portable development crypto."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from save_codec import CNG_AES, encrypt, decrypt


class AesProviderTests(unittest.TestCase):
    def test_nist_aes256_cbc_multiblock_vector_and_iv_preservation(self):
        key = bytes.fromhex('603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4')
        iv = bytes.fromhex('000102030405060708090a0b0c0d0e0f')
        plain = bytes.fromhex('6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e51')
        expected = bytes.fromhex('f58c4c04d6e5f1ba779eabfb5f7bfbd69cfc4e967edb808d679f777bc6702c7d')
        with CNG_AES('CBC') as aes:
            self.assertEqual(aes.transform(plain, key, direction='encrypt', iv=iv), expected)
            self.assertEqual(aes.transform(expected, key, direction='decrypt', iv=iv), plain)
        self.assertEqual(iv.hex(), '000102030405060708090a0b0c0d0e0f')

    def test_closed_provider_and_invalid_parameters_are_rejected(self):
        aes = CNG_AES('ECB')
        aes.close()
        aes.close()
        with self.assertRaises(RuntimeError):
            aes.transform(bytes(16), bytes(32), direction='encrypt')
        with CNG_AES('CBC') as aes:
            for data, key, iv, direction in ((b'bad', bytes(32), bytes(16), 'encrypt'),
                                             (bytes(16), b'bad', bytes(16), 'encrypt'),
                                             (bytes(16), bytes(32), None, 'decrypt'),
                                             (bytes(16), bytes(32), bytes(16), 'invalid')):
                with self.assertRaises(ValueError):
                    aes.transform(data, key, direction=direction, iv=iv)

    def test_dw3_envelope_rejects_wrong_game_and_corrupt_padding(self):
        for raw in (b'', b'x', bytes(32), b'Origins reference data'):
            with self.assertRaises(ValueError):
                decrypt(raw)
        with self.assertRaises(ValueError):
            encrypt(bytes(32))


if __name__ == '__main__':
    unittest.main()

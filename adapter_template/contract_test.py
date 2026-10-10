"""Rename to tests/test_new_game_contract.py after qualifying and registering."""
import unittest
from tests.scalar_contract import ScalarContractTests


class NewGameContractTests(ScalarContractTests, unittest.TestCase):
    game_id = 'new_game_pc'
    # Declare only native integrity bytes inside decoded payload, if applicable:
    payload_integrity_offsets = frozenset()

    @staticmethod
    def fixture_bytes():
        # Import your independently constructed procedural fixture, or read an
        # explicitly configured private COPY. Never read a live save directory.
        raise NotImplementedError('Supply a qualified fixture with occupied editable records.')

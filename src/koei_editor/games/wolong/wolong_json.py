"""Bounded JSON parsing with exact mapped scalar token spans.

Own implementation: preserve native JSON spelling, whitespace and unknown data
instead of reserializing the complete object. Duplicate keys fail closed.
"""
import json
import math
import re

from koei_editor.games.dw3.models import SaveError

NUMBER = re.compile(rb'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')


def parse(data):
    if type(data) is not bytes or not 0 < len(data) <= 8 * 1024 * 1024:
        raise SaveError('Invalid bounded Wo Long JSON body.')
    position, nodes = 0, 0
    spans = {}

    def whitespace():
        nonlocal position
        while position < len(data) and data[position] in b' \t\r\n':
            position += 1

    def string():
        nonlocal position
        start = position
        position += 1
        while position < len(data):
            if data[position] == 92:
                position += 2
            elif data[position] == 34:
                position += 1
                try:
                    return json.loads(data[start:position].decode('utf-8'))
                except (ValueError, UnicodeError) as error:
                    raise SaveError('Invalid Wo Long JSON string.') from error
            else:
                position += 1
        raise SaveError('Truncated Wo Long JSON string.')

    def value(path, depth):
        nonlocal position, nodes
        nodes += 1
        if depth > 64 or nodes > 600_000:
            raise SaveError('Wo Long JSON nesting or record budget exceeded.')
        whitespace()
        if position >= len(data):
            raise SaveError('Truncated Wo Long JSON value.')
        start = position
        ch = data[position]
        if ch == 34:
            result = string()
            if (len(path) == 5 and path[:2] == ('UIData', 'ui_battleset_slot_data_info')
                    and path[3:] == ('UiBattleSetSlotInfo', 'str')):
                spans[path] = (start, position)
            return result
        if ch in (123, 91):
            is_object = ch == 123
            result = {} if is_object else []
            end = 125 if is_object else 93
            position += 1
            whitespace()
            if position < len(data) and data[position] == end:
                position += 1
                return result
            while True:
                whitespace()
                if is_object:
                    if position >= len(data) or data[position] != 34:
                        raise SaveError('Invalid Wo Long JSON object key.')
                    key = string()
                    if key in result:
                        raise SaveError('Duplicate Wo Long JSON keys are unsupported.')
                    whitespace()
                    if position >= len(data) or data[position] != 58:
                        raise SaveError('Missing Wo Long JSON colon.')
                    position += 1
                else:
                    key = len(result)
                item = value(path + (key,), depth + 1)
                if is_object:
                    result[key] = item
                else:
                    result.append(item)
                whitespace()
                if position >= len(data):
                    raise SaveError('Truncated Wo Long JSON container.')
                delimiter = data[position]
                position += 1
                if delimiter == end:
                    return result
                if delimiter != 44:
                    raise SaveError('Invalid Wo Long JSON separator.')
        for literal, result in ((b'true', True), (b'false', False), (b'null', None)):
            if data.startswith(literal, position):
                position += len(literal)
                return result
        match = NUMBER.match(data, position)
        if not match:
            raise SaveError('Invalid Wo Long JSON number or literal.')
        position = match.end()
        token = data[start:position]
        result = json.loads(token)
        if isinstance(result, float) and not math.isfinite(result):
            raise SaveError('Nonfinite Wo Long JSON values are unsupported.')
        # Only existing integer balances and stack quantities need byte spans.
        if (type(result) is int and
                (path in (('PlayerData', 'sen'), ('PlayerData', 'senki'), ('PlayerData', 'bukun'))
                 or (len(path) == 5 and path[0] == 'PossessionItemData'
                     and path[1] in ('possession_items', 'storage_items')
                     and path[3:] == ('ItemObjectData', 'num')))):
            spans[path] = (start, position)
        return result

    result = value((), 0)
    whitespace()
    if position != len(data):
        raise SaveError('Trailing Wo Long JSON data is unsupported.')
    return result, spans

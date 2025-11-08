import random
import re
import string
import sys
from typing import Iterator, List, Optional
from ...models.fei import FEIEvent
from ..interfaces import IParser


class RedisParser(IParser):
    """
    Acts as the all-in-one specialist for Redis. It uses a custom parser that
    understands the MONITOR format's specific argument splitting rules and
    treats all argument content as raw strings.
    """
    _LOG_LINE_REGEX = re.compile(r'^(\S+)\s+\[([^\]]+)\]\s+(.*)$')
    _OPERATION_SEMANTICS = {
        "SET":     ["CREATE", "UPDATE"],
        "HMSET":   ["CREATE", "UPDATE"],
        "GET":     ["READ"],
        "HGETALL": ["READ"],
        "ZADD":    ["CREATE", "UPDATE"],
        "DEL":     ["DELETE"],
        "CLIENT":  ["READ"],
    }
    _DEFAULT_SEMANTIC_TYPE = ["READ"]

    def __init__(self, timestamp_granularity: int):
        self.timestamp_granularity = timestamp_granularity

    def _parse_command_args(self, command_str: str) -> List[str]:
        """
        Parses a raw command string by splitting arguments only when a
        double-quote is followed by a space, treating content as raw.
        """
        args = []
        current_arg = ""
        in_quotes = False
        i = 0
        while i < len(command_str):
            char = command_str[i]

            if not in_quotes:
                if char == '"':
                    in_quotes = True
                i += 1
                continue

            if char == '"' and (i + 1 == len(command_str) or (command_str[i+1].isspace() and command_str[i+2] == '"')):
                in_quotes = False
                args.append(current_arg)
                current_arg = ""
            else:
                current_arg += char
            i += 1
        return args

    def _parse_line_to_fei(self, line: str) -> Optional[FEIEvent]:
        match = self._LOG_LINE_REGEX.match(line.strip())
        if not match:
            return None

        try:
            timestamp_str, client_id, command_str = match.groups()
            timestamp = round(float(timestamp_str), self.timestamp_granularity)
            
            all_args = self._parse_command_args(command_str)
            if not all_args:
                return None

            op_type = all_args[0].upper()
            
            target, raw_args_list = self._dispatch_args(op_type, all_args)
            
            semantic_type = self._OPERATION_SEMANTICS.get(op_type, self._DEFAULT_SEMANTIC_TYPE)
            
            if op_type == "CLIENT":
                return None

            return FEIEvent(
                timestamp=timestamp,
                client_id=client_id,
                op_type=op_type,
                semantic_type=semantic_type,
                target=target,
                additional_data={'raw_args': raw_args_list}
            )
        except (ValueError, IndexError, Exception) as e:
            print(f"[WARN] Error parsing line '{line.strip()}': {e}", file=sys.stderr)
            return None

    def _dispatch_args(self, op_type, all_args):
        target = all_args[1] if len(all_args) > 1 else ""
        raw_args = all_args[2:]
        return target, raw_args

    def format(self, event: FEIEvent) -> str:
        def escape_arg(arg: str) -> str:
            return f'"{arg}"'

        command_parts = [escape_arg(event["op_type"]), escape_arg(event["target"])]
        raw_args = event['additional_data'].get('raw_args', [])
        for arg in raw_args:
            command_parts.append(escape_arg(str(arg)))
        
        full_command = ' '.join(command_parts)
        
        return f"{event['timestamp']:.{self.timestamp_granularity}f} [{event['client_id']}] {full_command}"

    def generate_args(self, op_type: str, target: str, available_pool: List[str]) -> List[str]:
        """Generates realistic synthetic arguments for Redis commands."""
        if op_type == "HMSET":
            num_fields = random.randint(1, 10)
            fields = [f"field{j}" for j in range(num_fields)]
            values = [self._generate_thrash_string(50) for _ in range(num_fields)]
            return [item for pair in zip(fields, values) for item in pair]
        elif op_type == "SET":
            return [self._generate_thrash_string(100)]
        elif op_type == "ZADD":
            if not available_pool:
                return []
            member = random.choice(available_pool)
            score = f"{random.uniform(-1e9, 1e9):.8E}"
            return [score, member]
        return []

    def _generate_thrash_string(self, length: int) -> str:
        """Generates a random string, allowing all characters."""
        chars = string.ascii_letters + string.digits + string.punctuation + ' '
        return ''.join(random.choice(chars) for _ in range(length)).replace('"', "'").replace(' ', '_')

    def parse(self, file_path: str) -> Iterator[FEIEvent]:
        """Reads a log file and yields a stream of FEIEvent objects."""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                event = self._parse_line_to_fei(line)
                if event:
                    yield event
                else:
                    print(f"[WARN] Line {line_num} was skipped due to parsing error.", file=sys.stderr)
import re
import sys
from datetime import datetime
from typing import Iterator, List, Dict, Any, Tuple
from multiprocessing import Pool, cpu_count

from ...models.fei import FEIEvent
from ..interfaces import IParser

LOG_PATTERN = re.compile(
    r'^(\S+) \S+ \S+ \[(.*?)\] "(.*?) (.*?) (.*?)" (\d{3}) (\S+) "(.*?)" "(.*?)" "(.*?)"$'
)

def _parse_chunk_worker(chunk_data: Tuple[List[str], int, int]) -> List[FEIEvent]:
    lines, granularity, start_line_idx = chunk_data
    parsed_events = []

    date_fmt = "%d/%b/%Y:%H:%M:%S %z"

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        match = LOG_PATTERN.match(line)
        if match:
            try:
                groups = match.groups()

                ip = groups[0]
                dt_str = groups[1]
                method = groups[2]
                url = groups[3]
                protocol = groups[4]
                status = groups[5]
                size = groups[6]
                referer = groups[7]
                user_agent = groups[8]
                extra_field = groups[9]

                dt_obj = datetime.strptime(dt_str, date_fmt)
                timestamp = round(dt_obj.timestamp(), granularity)

                semantic_type = ["READ"]
                if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
                    semantic_type = ["UPDATE"]

                event = FEIEvent(
                    timestamp=timestamp,
                    client_id=ip,
                    op_type=method.upper(),
                    semantic_type=semantic_type,
                    target=url,
                    additional_data={
                        "protocol": protocol,
                        "status": status,
                        "size": size,
                        "referer": referer,
                        "user_agent": user_agent,
                        "extra": extra_field,
                        "raw_date": dt_str
                    }
                )
                parsed_events.append(event)
            except Exception:
                continue

    return parsed_events

class HttpParser(IParser):
    def __init__(self, timestamp_granularity: int = 6, chunk_size: int = 20000):
        self.timestamp_granularity = timestamp_granularity
        self.chunk_size = chunk_size
        self.baseline_epoch: float = 0.0

    def parse(self, file_path: str) -> Iterator[FEIEvent]:
        num_workers = max(1, cpu_count() - 1)
        pool = Pool(processes=num_workers)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                chunk = []
                line_count = 0

                def chunk_generator():
                    nonlocal chunk, line_count
                    for line in f:
                        chunk.append(line)
                        if len(chunk) >= self.chunk_size:
                            yield (chunk, self.timestamp_granularity, line_count)
                            line_count += len(chunk)
                            chunk = []
                    if chunk:
                        yield (chunk, self.timestamp_granularity, line_count)

                is_first = True
                for batch_result in pool.imap(_parse_chunk_worker, chunk_generator()):
                    for event in batch_result:
                        if is_first:
                            self.baseline_epoch = event["timestamp"]
                            is_first = False
                        yield event

        except KeyboardInterrupt:
            pool.terminate()
            raise
        finally:
            pool.close()
            pool.join()

    def format(self, event: FEIEvent) -> str:
        data = event.get("additional_data", {})
        raw_date = data.get("raw_date")

        if not raw_date:
            absolute_epoch = self.baseline_epoch + event["timestamp"]

            dt = datetime.fromtimestamp(absolute_epoch)
            raw_date = dt.strftime("%d/%b/%Y:%H:%M:%S +0000")

        return (
            f'{event["client_id"]} - - [{raw_date}] '
            f'"{event["op_type"]} {event["target"]} {data.get("protocol", "HTTP/1.1")}" '
            f'{data.get("status", 200)} {data.get("size", "-")} '
            f'"{data.get("referer", "-")}" "{data.get("user_agent", "-")}" "{data.get("extra", "-")}"'
        )

    def generate_args(self, op_type: str, target: str, available_pool: List[str]) -> List[str]:
        return ["Mozilla/5.0 (Synthetic Defigium Client)"]

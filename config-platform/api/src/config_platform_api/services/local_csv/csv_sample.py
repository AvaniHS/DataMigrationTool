"""CSV header sampling for local and staged file connections."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from config_platform_api.connectors.base import ConnectorValidationError

SAMPLE_BYTES = 65_536


def read_csv_column_names(path: Path, parse_options: dict[str, str | int]) -> list[str]:
    delimiter = str(parse_options.get("delimiter", ","))
    quotechar = str(parse_options.get("quote", '"'))
    encoding = str(parse_options.get("encoding", "utf-8"))
    header_row = int(parse_options.get("header_row", 1))
    if header_row < 1:
        raise ConnectorValidationError("header_row must be at least 1.")

    try:
        with path.open("r", encoding=encoding, newline="") as handle:
            sample = handle.read(SAMPLE_BYTES)
    except OSError as exc:
        raise ConnectorValidationError(f"Unable to read CSV file: {exc}") from exc

    if not sample.strip():
        raise ConnectorValidationError("CSV file is empty.")

    reader = csv.reader(
        io.StringIO(sample),
        delimiter=delimiter,
        quotechar=quotechar,
    )
    for row_index, row in enumerate(reader, start=1):
        if row_index == header_row:
            columns = [cell.strip() for cell in row if cell.strip()]
            if not columns:
                raise ConnectorValidationError("CSV header row is empty.")
            return columns

    raise ConnectorValidationError(f"CSV file does not contain header row {header_row}.")

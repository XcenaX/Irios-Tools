from __future__ import annotations

import argparse
from pathlib import Path
import sys

DEFAULT_RECEIPTS_NAME = "пост.xls"
DEFAULT_SALES_NAME = "реал.xls"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Собирает отчёт 'Недостающие оригиналы документов' и может запускать desktop-приложение."
    )
    parser.add_argument("--receipts", default=DEFAULT_RECEIPTS_NAME)
    parser.add_argument("--sales", default=DEFAULT_SALES_NAME)
    parser.add_argument("--output", default="")
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--license-key", default="")
    return parser.parse_args()


def run_gui() -> None:
    from desktop_app.app.main import run as run_desktop_app

    run_desktop_app()


def run_cli(args: argparse.Namespace) -> None:
    from desktop_app.app.context import build_context

    context = build_context(include_ui=False)
    if args.license_key:
        context.license_service.activate(args.license_key)

    receipts = Path(args.receipts)
    sales = Path(args.sales)
    output = Path(args.output) if args.output else None
    result = context.report_run_service.run_missing_originals(receipts, sales, output)
    print(f"Готово: {result.output_file}")
    print(
        "Строк в отчёте: "
        f"поступления {result.receipts_count}, "
        f"реализации {result.sales_count}, "
        f"всего {result.total_count}"
    )


def main() -> None:
    args = parse_args()
    cli_args_used = any(
        value in sys.argv[1:] for value in ("--receipts", "--sales", "--output", "--license-key")
    )
    if args.gui or not cli_args_used:
        run_gui()
        return
    run_cli(args)


if __name__ == "__main__":
    main()

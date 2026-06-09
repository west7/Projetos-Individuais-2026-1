import argparse
from pathlib import Path

from .catalog import Catalog
from .ingest import ingest_sources
from .parsing import parse_documents
from .process import process_documents
from .sources import selected_sources

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = BASE_DIR / "data" / "catalog.db"
DEFAULT_PDF_DIR = BASE_DIR / "data" / "pdfs"


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta e ingestao de PDFs de RI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Coleta PDFs das fontes configuradas.")
    ingest_parser.add_argument("--company", choices=["all", "mrv", "pacaembu"], default="all")
    ingest_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    ingest_parser.add_argument("--output-dir", type=Path, default=DEFAULT_PDF_DIR)
    ingest_parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de novos downloads.")

    list_parser = subparsers.add_parser("list-documents", help="Lista documentos catalogados.")
    list_parser.add_argument("--db", type=Path, default=DEFAULT_DB)

    parse_parser = subparsers.add_parser("parse-documents", help="Extrai texto dos PDFs catalogados.")
    parse_parser.add_argument("--company", choices=["all", "mrv", "pacaembu"], default="all")
    parse_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parse_parser.add_argument("--limit", type=int, default=None)

    process_parser = subparsers.add_parser("process-mock", help="Simula extracao via LLM e salva metricas.")
    process_parser.add_argument("--company", choices=["all", "mrv", "pacaembu"], default="all")
    process_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    process_parser.add_argument("--limit", type=int, default=None)

    process_real_parser = subparsers.add_parser("process", help="Processa documentos com mock ou Gemini.")
    process_real_parser.add_argument("--extractor", choices=["mock", "gemini"], default="mock")
    process_real_parser.add_argument("--company", choices=["all", "mrv", "pacaembu"], default="all")
    process_real_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    process_real_parser.add_argument("--limit", type=int, default=None)

    metrics_parser = subparsers.add_parser("list-metrics", help="Lista metricas extraidas.")
    metrics_parser.add_argument("--db", type=Path, default=DEFAULT_DB)

    args = parser.parse_args()

    if args.command == "ingest":
        stats = ingest_sources(selected_sources(args.company), args.db, args.output_dir, args.limit)
        print(
            "Ingestao concluida: "
            f"{stats['discovered']} descobertos, "
            f"{stats['downloaded']} baixados, "
            f"{stats['skipped']} ignorados, "
            f"{stats['failed']} falharam."
        )
        return

    if args.command == "list-documents":
        catalog = Catalog(args.db)
        try:
            rows = catalog.list_documents()
        finally:
            catalog.close()

        if not rows:
            print("Nenhum documento catalogado.")
            return

        for row in rows:
            period = _format_period(row["year"], row["quarter"])
            print(f"{row['company']} | {period} | {row['status']} | {row['document_title']}")

    if args.command == "parse-documents":
        company = None if args.company == "all" else args.company
        stats = parse_documents(args.db, company=company, limit=args.limit)
        print(
            "Parsing concluido: "
            f"{stats['documents']} documentos parseados, {stats['failed']} falharam."
        )
        return

    if args.command == "process-mock":
        company = None if args.company == "all" else args.company
        stats = process_documents(args.db, company=company, limit=args.limit, extractor_name="mock")
        print(
            "Processamento mock concluido: "
            f"{stats['documents']} documentos, {stats['metrics']} metricas, {stats['failed']} falharam."
        )
        return

    if args.command == "process":
        company = None if args.company == "all" else args.company
        stats = process_documents(args.db, company=company, limit=args.limit, extractor_name=args.extractor)
        print(
            "Processamento concluido: "
            f"{stats['documents']} documentos, "
            f"{stats['metrics']} metricas, "
            f"{stats['parsed']} parseados sob demanda, "
            f"{stats['failed']} falharam."
        )
        return

    if args.command == "list-metrics":
        catalog = Catalog(args.db)
        try:
            rows = catalog.list_metrics()
        finally:
            catalog.close()

        if not rows:
            print("Nenhuma metrica extraida.")
            return

        for row in rows:
            period = _format_period(row["year"], row["quarter"])
            print(
                f"{row['company']} | {period} | {row['metric_name']} | "
                f"{row['value']} {row['unit']} | {row['extractor_name']}"
            )


def _format_period(year: int | None, quarter: int | None) -> str:
    if year and quarter:
        return f"{quarter}T{str(year)[-2:]}"
    return "periodo desconhecido"


if __name__ == "__main__":
    main()

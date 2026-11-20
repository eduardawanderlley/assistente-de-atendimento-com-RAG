"""CLI de ingestão — rode manualmente após alterar a base de conhecimento.

Uso:
    python scripts/ingest.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.deps import Pipeline
from src.config import get_settings
from src.ingestion.indexer import ingest


def main() -> None:
    pipeline = Pipeline(get_settings())
    n = ingest(pipeline.settings, pipeline.vectorstore, pipeline.embedder)
    print(f"Ingestão concluída: {n} chunks indexados em '{pipeline.settings.chroma_dir}'.")


if __name__ == "__main__":
    main()

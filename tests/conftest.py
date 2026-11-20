"""Fixtures compartilhadas dos testes."""
import pytest

from src.ingestion.document import Document


@pytest.fixture
def sample_document() -> Document:
    texto = (
        "# Check-in\n\n"
        "O check-in abre 3 horas antes do embarque.\n\n"
        "## Bagagem\n\n"
        "Bagagem de mão limitada a 10 kg.\n\n"
        "Excedentes são cobrados por quilograma adicional na tarifa cheia."
    )
    return Document(
        content=texto,
        metadata={"source": "exemplo.md", "type": "md"},
    )

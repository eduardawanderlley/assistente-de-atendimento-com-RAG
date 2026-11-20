"""Carregadores de arquivos da base de conhecimento (PDF, HTML, Markdown, TXT)."""
from pathlib import Path

from bs4 import BeautifulSoup

from .document import Document

SUPPORTED_EXTENSIONS = {".pdf", ".html", ".htm", ".md", ".txt"}


def load_file(path: Path) -> Document:
    """Dispacha o arquivo para o carregador correto conforme a extensão."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _load_pdf(path)
    if ext in {".html", ".htm"}:
        return _load_html(path)
    if ext in {".md", ".txt"}:
        return _load_text(path)
    raise ValueError(f"Formato não suportado: {ext}")


def load_directory(directory: Path) -> list[Document]:
    """Carrega recursivamente todos os arquivos suportados de um diretório."""
    documents = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(load_file(path))
    if not documents:
        raise FileNotFoundError(f"Nenhum arquivo suportado encontrado em {directory}")
    return documents


def _load_pdf(path: Path) -> Document:
    """Extrai texto página a página com pypdf, mantendo o número da página nos metadados."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    content = "\n\n".join(pages)
    return Document(
        content=content,
        metadata={"source": path.name, "type": "pdf", "pages": len(reader.pages)},
    )


def _load_html(path: Path) -> Document:
    """Remove tags e scripts com BeautifulSoup, preservando o texto legível."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else path.stem
    return Document(
        content=soup.get_text(separator="\n", strip=True),
        metadata={"source": path.name, "type": "html", "title": title},
    )


def _load_text(path: Path) -> Document:
    """Carrega arquivos Markdown/TXT puros."""
    return Document(
        content=path.read_text(encoding="utf-8"),
        metadata={"source": path.name, "type": path.suffix.lower().lstrip(".")},
    )

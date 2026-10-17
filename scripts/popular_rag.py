import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.rag import RAGManager


def carregar_literatura() -> None:
    literatura_dir = Path(settings.literatura_path)
    if not literatura_dir.exists():
        print(f"Diretório {literatura_dir} não encontrado — crie a pasta e adicione arquivos .txt.")
        return

    documentos = []
    for arquivo in sorted(literatura_dir.glob("*.txt")):
        texto = arquivo.read_text(encoding="utf-8")
        for i in range(0, len(texto), 1000):
            documentos.append({
                "id": f"{arquivo.name}_{i}",
                "texto": texto[i:i + 1000],
                "metadata": {"source": arquivo.name},
            })

    if not documentos:
        print("Nenhum arquivo .txt de literatura encontrado.")
        return

    RAGManager().indexar_literatura(documentos)
    print(f"Indexados {len(documentos)} chunks de literatura.")


if __name__ == "__main__":
    carregar_literatura()

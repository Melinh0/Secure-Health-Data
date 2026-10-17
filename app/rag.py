import logging
from typing import Any

import chromadb

from .config import settings

logger = logging.getLogger(__name__)


class RAGManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.literatura_collection = self.client.get_or_create_collection(name="literatura_psiquiatrica")
        self.paciente_collection = self.client.get_or_create_collection(name="paciente_anotacoes")

    def indexar_literatura(self, documentos: list[dict[str, Any]]) -> None:
        if not documentos:
            return
        try:
            self.literatura_collection.upsert(
                ids=[d["id"] for d in documentos],
                documents=[d["texto"] for d in documentos],
                metadatas=[d.get("metadata", {}) for d in documentos],
            )
        except Exception as erro:
            logger.warning("Falha ao indexar literatura: %s", erro)

    def indexar_anotacoes_paciente(self, paciente_id: int, anotacoes: list[dict[str, Any]]) -> None:
        if not anotacoes:
            return
        ids = [f"pac_{paciente_id}_anot_{i}" for i in range(len(anotacoes))]
        metadatas = [
            {
                "paciente_id": paciente_id,
                "data": a["data"].isoformat() if hasattr(a["data"], "isoformat") else str(a["data"]),
                "tipo": a.get("tipo", ""),
            }
            for a in anotacoes
        ]
        try:
            self.paciente_collection.upsert(
                ids=ids,
                documents=[a["texto"] for a in anotacoes],
                metadatas=metadatas,
            )
        except Exception as erro:
            logger.warning("Falha ao indexar anotações: %s", erro)

    def recuperar_literatura(self, query: str, top_k: int = 5) -> list[str]:
        try:
            resultados = self.literatura_collection.query(query_texts=[query], n_results=top_k)
            return resultados["documents"][0] if resultados["documents"] else []
        except Exception as erro:
            logger.warning("Falha na busca de literatura: %s", erro)
            return []

    def recuperar_anotacoes_paciente(self, paciente_id: int, query: str, top_k: int = 3) -> list[str]:
        try:
            resultados = self.paciente_collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"paciente_id": paciente_id},
            )
            return resultados["documents"][0] if resultados["documents"] else []
        except Exception as erro:
            logger.warning("Falha na busca de anotações: %s", erro)
            return []

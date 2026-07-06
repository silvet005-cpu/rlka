"""
vectorstore.py — Generacion de embeddings e indexacion en FAISS.

Responsabilidad (ver Documentacion_Tecnica seccion 3; ADR-002;
tarjeta de Trello "3 - Indexacion"):

1. Convertir cada chunk de texto en un embedding (vector numerico).
2. Indexar esos vectores en FAISS para busqueda por similitud.
3. Guardar junto a cada vector su metadata (source, categoria, pagina,
   contenido original) para poder recuperarla despues de una busqueda.

Regla critica (explicita en la descripcion de la tarjeta): el MISMO
modelo de embeddings debe usarse tanto para indexar los documentos
como para convertir la pregunta del usuario en un vector — vectores
generados por modelos distintos no son comparables entre si. Por eso
este modulo expone una unica funcion get_embedding_model(), que
tambien debe usarse desde agent.py al procesar cada pregunta.

Modelo elegido: sentence-transformers "paraphrase-multilingual-MiniLM-L12-v2"
— corre localmente, sin necesidad de API key ni conexion a un proveedor de
IA externo. IMPORTANTE: se eligio especificamente esta variante
multilingue (no "all-MiniLM-L6-v2", que es principalmente para ingles)
tras un diagnostico real: con el modelo solo-ingles, el chunk que
contenia la respuesta correcta en español obtenia una similitud mas
baja (0.42-0.46) que chunks irrelevantes (0.49-0.53) — el modelo no
diferenciaba bien el significado en español. Con el modelo
multilingue, la calidad de busqueda en español mejora sustancialmente.
"""

import os
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "vectorstore.faiss"
METADATA_PATH = "vectorstore_metadata.pkl"

_model = None  # cache: el modelo solo se carga una vez por ejecucion


def get_embedding_model() -> SentenceTransformer:
    """
    Devuelve la instancia del modelo de embeddings, cargandolo una sola
    vez. IMPORTANTE: esta es la unica funcion que debe usarse para
    generar embeddings en todo el proyecto (aqui y en agent.py), para
    garantizar que documentos y preguntas usen siempre el mismo modelo.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def build_vectorstore(chunks: list[dict]) -> tuple[faiss.Index, list[dict]]:
    """
    Genera embeddings para una lista de chunks y los indexa en FAISS.

    Args:
        chunks: lista de dicts con al menos la clave "content" (texto
            del chunk). Las demas claves (source, category, page) se
            conservan como metadata asociada a cada vector.

    Returns:
        Tupla (indice_faiss, metadata), donde metadata es la lista de
        chunks original, en el mismo orden que los vectores del indice
        (la posicion i del indice corresponde a metadata[i]).
    """
    model = get_embedding_model()

    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    # Normalizar los vectores para poder usar similitud por producto
    # interno (equivalente a similitud coseno) en vez de distancia L2.
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # IP = Inner Product (similitud coseno tras normalizar)
    index.add(embeddings)

    return index, chunks


def save_vectorstore(index: faiss.Index, metadata: list[dict], index_path: str = INDEX_PATH, metadata_path: str = METADATA_PATH) -> None:
    """Guarda el indice FAISS y su metadata asociada en disco."""
    faiss.write_index(index, index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)


def load_vectorstore(index_path: str = INDEX_PATH, metadata_path: str = METADATA_PATH) -> tuple[faiss.Index, list[dict]]:
    """Carga un indice FAISS y su metadata previamente guardados."""
    index = faiss.read_index(index_path)
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def search(query: str, index: faiss.Index, metadata: list[dict], top_k: int = 4, category: str | None = None) -> list[dict]:
    """
    Busca los chunks mas relevantes para una pregunta, usando el MISMO
    modelo de embeddings con el que se indexaron los documentos.

    Args:
        query: la pregunta del usuario.
        index: el indice FAISS ya construido.
        metadata: la lista de metadata correspondiente al indice.
        top_k: cuantos chunks relevantes devolver.
        category: si se especifica (ej. "Garantía", "Recursos Humanos"),
            restringe la busqueda solo a chunks de esa categoria antes
            de calcular similitud semantica (filtrado por metadatos,
            tarjeta "4 - Camada de recuperacion").

    Returns:
        Lista de chunks (con su metadata) ordenados de mas a menos
        relevante.
    """
    model = get_embedding_model()

    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)

    # Si se pide filtrar por categoria, buscamos entre mas candidatos
    # de los necesarios (top_k * 5) para no quedarnos sin resultados
    # despues de descartar los que no son de esa categoria.
    search_k = top_k * 5 if category else top_k
    search_k = min(search_k, index.ntotal)

    scores, indices = index.search(query_embedding, search_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = metadata[idx].copy()

        if category and chunk.get("category") != category:
            continue

        chunk["similarity_score"] = float(score)
        results.append(chunk)

        if len(results) >= top_k:
            break

    return results


def assemble_context(results: list[dict]) -> str:
    """
    Convierte los chunks recuperados en un bloque de texto formateado,
    listo para insertarse en el prompt del LLM. Cada fragmento incluye
    su fuente y pagina, para que el modelo pueda citarlas en la
    respuesta (ver seccion 11 de Documentacion_Tecnica, dialogos de
    RoofKA).

    Args:
        results: lista de chunks devueltos por search().

    Returns:
        Texto formateado con todos los fragmentos, listo para el prompt.
        Si no hay resultados, devuelve una cadena vacia (senal para que
        agent.py active el fallback de "no tengo esa informacion").
    """
    if not results:
        return ""

    bloques = []
    for r in results:
        bloques.append(
            f"[Fuente: {r['source']}, página {r['page']}]\n{r['content']}"
        )

    return "\n\n---\n\n".join(bloques)


if __name__ == "__main__":
    from ingest import load_and_chunk_documents

    print("Generando chunks desde los PDFs...")
    chunks = load_and_chunk_documents()
    print(f"{len(chunks)} chunks listos para indexar.\n")

    print("Generando embeddings e indexando en FAISS...")
    index, metadata = build_vectorstore(chunks)
    print(f"Indice construido con {index.ntotal} vectores.\n")

    save_vectorstore(index, metadata)
    print(f"Indice guardado en '{INDEX_PATH}' y metadata en '{METADATA_PATH}'.\n")

    # Prueba rapida de busqueda
    test_query = "¿Cuánto dura la garantía de un techo completo?"
    print(f"--- Prueba de busqueda ---\nPregunta: {test_query}\n")
    results = search(test_query, index, metadata, top_k=3)
    for i, r in enumerate(results, start=1):
        print(f"{i}. [{r['source']} - pág. {r['page']}] (similitud: {r['similarity_score']:.3f})")
        print(f"   {r['content'][:150]}...\n")

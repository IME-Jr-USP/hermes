from pathlib import Path

BATCH_SIZE = 20

LOG_DIR = Path("./logs")
LOG_PATH = LOG_DIR / "app.log"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DEVICE = "cpu"
EMBEDDING_NORMALIZE = True  # para similaridade por cosseno

DB_PATH = Path("./chroma_db")
DB_COLLECTION_NAME = "disciplinas_jupiterweb"
DB_DISTANCE_METRIC = "cosine"

DISCIPLINA_DOCUMENT_CHAVES = [
    "ementa",
    "conteudo programatico",
    "objetivos",
    "bibliografia",
    "bibliografia basica",
    "bibliografia complementar",
]

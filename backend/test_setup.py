import git
import chromadb
from sentence_transformers import SentenceTransformer

print("GitPython works:", git.__version__ if hasattr(git, '__version__') else "OK")
print("ChromaDB works:", chromadb.__version__)
print("Sentence Transformers imported OK")
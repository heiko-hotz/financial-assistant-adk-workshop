
import chromadb
import glob
import os

# Get the directory where THIS script is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Setup local persistent database
# Store in module_02/rag_agent/demo_rag_db
db_path = os.path.join(base_dir, "rag_agent", "demo_rag_db")
os.makedirs(db_path, exist_ok=True)

client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(name="demo_docs")

# 2. Read all .txt files in the SAME directory as this script
file_search_path = os.path.join(base_dir, "*.txt")
file_paths = glob.glob(file_search_path)
documents = []
ids = []

if not file_paths:
    print("❌ No .txt files found! Make sure you are running this in the folder with your text files.")
else:
    print(f"📄 Found {len(file_paths)} files: {file_paths}")

    for i, file_path in enumerate(file_paths):
        with open(file_path, "r") as f:
            content = f.read()
            documents.append(content)
            ids.append(f"doc_{i}") # Simple ID generation
            print(f"   - Loaded: {file_path}")

    # 3. Add to Chroma (Embeddings are handled automatically by default)
    if documents:
        collection.add(documents=documents, ids=ids)
        print(f"✅ Successfully ingested {len(documents)} files into ./demo_rag_db")
        print("Peek at the data:", collection.peek())
    else:
        print("⚠️ No documents to ingest.")

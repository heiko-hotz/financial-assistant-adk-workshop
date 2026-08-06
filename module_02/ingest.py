
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
collection_name = "demo_docs"

# 2. Read all .txt files in the SAME directory as this script
file_search_path = os.path.join(base_dir, "*.txt")
file_paths = sorted(glob.glob(file_search_path))
documents = []
ids = []

if not file_paths:
    print("❌ No .txt files found! Make sure you are running this in the folder with your text files.")
else:
    print(f"📄 Found {len(file_paths)} files: {file_paths}")

    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            documents.append(content)
            ids.append(os.path.basename(file_path))
            print(f"   - Loaded: {file_path}")

    # 3. Rebuild the collection so removed or renamed files cannot remain searchable
    if documents:
        existing_collection_names = {
            item.name if hasattr(item, "name") else str(item)
            for item in client.list_collections()
        }
        if collection_name in existing_collection_names:
            client.delete_collection(name=collection_name)
            print(f"🗑️ Replaced existing '{collection_name}' collection.")

        collection = client.create_collection(name=collection_name)
        collection.add(documents=documents, ids=ids)
        print(
            f"✅ Successfully ingested {len(documents)} files into "
            f"'{collection_name}' in ./demo_rag_db"
        )
        print(f"   IDs: {ids}")
        print("Peek at the data:", collection.peek())
    else:
        print("⚠️ No documents to ingest.")

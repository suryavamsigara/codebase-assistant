from indexing.walker import RepoWalker
from indexing.chunker import CodeChunker
from indexing.embeddings import Embedder

walker = RepoWalker("tmp/r1", "r1")
chunker = CodeChunker()


def main():
    all_chunks = []
    for file_data in walker.walk():
        print(f"Processing: {file_data['file_path']}")

        with open(file_data['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        chunks = chunker.chunk_python(code, file_data['file_path'])

        # for chunk in chunks:
        #     print(f"\nName: {chunk['name']}\nBody: {chunk['body']}\n===================================\n")

        for chunk in chunks:
            chunk['repo_name'] = file_data['repo_name']
            chunk['full_file_path'] = file_data['file_path']
            # Add git author, last_modified
        
        all_chunks.extend(chunks)
        print(f"  Found {len(chunks)} chunks from this file. Total so far: {len(all_chunks)}")
        # embed(chunks)

    embedder = Embedder(chunks=all_chunks)
    embedder.embed_chunks(all_chunks)
    embedder.save("db")
    embedder.load("db")
    print("======================")
    print(embedder.search("backward propagation for matrix multiplication"))
    print("======================")
    print(embedder.search("to deposit money"))
    print("======================")
    print(embedder.search("How to build computation order?"))
    print("======================")
    print(embedder.search("compute n factorial recursively"))



if __name__ == "__main__":
    main()

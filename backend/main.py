from walker import RepoWalker
from chunker import CodeChunker
from embeddings import Embedder

walker = RepoWalker("tmp/r1", "r1")
chunker = CodeChunker()


def main():
    for file_data in walker.walk():
        print(f"Processing: {file_data['file_path']}")

        with open(file_data['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        chunks = chunker.chunk_python(code, file_data['file_path'])

        # for chunk in chunks:
        #     print(f"\nName: {chunk['name']}\nBody: {chunk['body']}\n===================================\n")

        # for chunk in chunks: update chunk by adding repo name, last modified, git author, full file path (file_data[file_path])
        # embed(chunks)

    embedder = Embedder(chunks=chunks)
    embedder.embed_chunks(chunks)
    embedder.save("db")
    embedder.load("db")
    print("======================")
    print(embedder.search("convert string to integer safely"))
    print("======================")
    print(embedder.search("remove duplicate items from list"))
    print("======================")
    print(embedder.search("sorting algorithm"))
    print("======================")
    print(embedder.search("compute n factorial recursively"))



if __name__ == "__main__":
    main()

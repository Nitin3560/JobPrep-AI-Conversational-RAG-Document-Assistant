Requirements 

1. When a user uploads a file the system should immediately process it, extract the text, split it into chunks and embed it into the index. Upload is completed once the embedding is done of new chunks.

2. The pipeline should always run in order, upload then extract then chunk then embed then retrieve. Retrieval should not run until the document is fully indexed.

3. If retrieval fails or returns nothing useful the system should show an error and stop. The chat should not continue with empty or weak results.

4. If the same file is uploaded more than once the system should not re-save or re-embed the same content. Deduplication should happen at both the file level and the chunk level.

5. Each chunk should get a deterministic ID based on the source document and its text content. The ID should stay consistent across storage and the index so retrieved results can always be traced back.

6. The system should store chunk text separately from the vector index. The chunk file should be human readable and the index should only be used for search.
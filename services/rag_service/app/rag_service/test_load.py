import llama_cpp

llm = llama_cpp.Llama(model_path="/app/rag_service/model.gguf", embedding=True)

embeddings = llm.create_embedding("Hello, world!")

print("Эмбеддинг размерности:", len(embeddings))
print("Пример значений:", embeddings[:10])
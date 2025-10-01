from langchain_ollama import ChatOllama

prompt = """You are a helpful assistant that answers questions about programming and technology. Tell me about AI"""

model = ChatOllama(model="llama3.1:8b")

response = model.invoke(prompt)

print(response)

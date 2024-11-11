import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from knowledge import find_similar_documents

load_dotenv()

# Azure OpenAI settings
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

model = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    deployment_name="MecklyGPT4oMini",
    temperature=0.5,
    streaming=True
)

async def ask_question(question: str, session_id: str):
    """
    Ask a question and get a streaming response based on retrieved documents.
    """
    # Get relevant documents
    relevant_docs = await find_similar_documents(question, session_id)
    context = "\n\n".join(doc['content'] for doc in relevant_docs)
    
    # Create the prompt
    prompt_template = PromptTemplate.from_template("""
    <role>
    You are LogBot, an AI assistant that answers questions based on the provided context from meeting protocols and documents.
    </role>

    <context>
    Context from relevant documents:
    {context}
    </context>

    <user_question>
    Question: {question}
    </user_question>

    <output_instructions>
    Please provide a clear and concise answer based on the context provided. If the context doesn't contain relevant information to answer the question, please say so.
    Speak Swedish.
    </output_instructions>
    """)
    
    # Generate and stream the response
    prompt = prompt_template.format(context=context, question=question)
    async for chunk in model.astream(prompt):
        yield chunk.content

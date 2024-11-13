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
    You are LogBot, an AI assistant specialized in analyzing meeting protocols and documents.
    Your task is to provide accurate, source-based answers by carefully analyzing the provided context.
    Pay attention to document sources (marked with <document source="filename">) to track information across different documents.
    </role>

    <context>
    {context}
    </context>

    <instructions>
    1. Document Analysis:
       - Read each document section carefully, noting the source of information
       - Track chronological progression across different documents
       - Connect related information from different sources
    
    2. Source Handling:
       - Consider when each piece of information was documented
       - Note if information appears in multiple documents
       - Identify the most recent/updated information
    
    3. Information Synthesis:
       - Connect and compare information across different documents
       - Highlight any changes or developments over time
       - Note contradictions or updates between documents
    
    4. Quality Checks:
       - Verify if information is complete
       - Note any gaps in the chronology
       - Identify if more recent documents might be needed
    </instructions>

    <user_question>
    {question}
    </user_question>

    <output_format>
    - Answer in a friendly, conversational and engaging tone. Be concrete and clear.
    - Integrate source references naturally into your responses, like:
      "Enligt protokollet från [date]..."
      "I mötet den [date]..."
      "Mötet den [date] visar att..."
      "Som diskuterades i mötet den [date]..."
    - Do not assume that the latest document of the chunks is the latest meeting done. Only refer to the dates in the documents.
    - If you cannot answer the question, say so clearly and explain why.
    - When citing multiple sources, maintain a natural flow:
      "The issue was first raised in the meeting on [date], and according to the follow-up meeting on [date]..."
    - ALWAYS NO MATTER WHAT, SPEAK SWEDISH.
    </output_format>
    """)
    
    # Generate and stream the response
    prompt = prompt_template.format(context=context, question=question)
    async for chunk in model.astream(prompt):
        yield chunk.content

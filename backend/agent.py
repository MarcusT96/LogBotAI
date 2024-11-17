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
AZURE_OPENAI_MINI_ENDPOINT = os.getenv("AZURE_OPENAI_MINI_ENDPOINT")
# Initialize the LLM models
chat_model = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    deployment_name="gpt-4o-meckly",
    temperature=0.5,
    streaming=True
)

query_optimizer = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_MINI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    deployment_name="MecklyGPT4oMini",
    temperature=0.3
)

async def optimize_query(query: str) -> str:
    """
    Use LLM to optimize the query for semantic search
    """
    prompt = f"""
    <role>
    You are LogBot's Query Optimizer. Your task is to convert questions into 5 key search phrases
    that would appear in meeting minutes, focusing on the most essential terms and concepts.
    </role>

    <user_question>
    {query}
    </user_question>

    <instructions>
    1. Extract only the most essential search terms
    2. Create 5 alternative phrasings
    3. Use formal protocol language
    </instructions>

    <output_format>
    Return exactly 5 comma-separated phrases that capture the core search intent.
    </output_format>

    <example>
    Question: "Hur har Trafikverket planerat att minska bullernivåerna längs järnvägen?"
    Answer: trafikverket bullerdämpande åtgärder, åtgärdsplan järnvägsbuller, bullernivåer järnväg
    </example>
    """

    response = await query_optimizer.ainvoke(prompt)
    return response.content.strip()

async def ask_question(question: str, session_id: str):
    """
    Ask a question and get a streaming response based on retrieved documents.
    """
    # Optimize the query first
    optimized_query = await optimize_query(question)
    
    # Get relevant documents using optimized query
    relevant_docs = await find_similar_documents(optimized_query, session_id)
    context = "\n\n".join(doc['content'] for doc in relevant_docs)
    
    # Create the prompt
    prompt_template = PromptTemplate.from_template("""
    <role>
    You are LogBot, an AI assistant specialized in analyzing meeting protocols and documents.
    Your task is to provide accurate, source-based answers by carefully analyzing the provided context.
    For questions without direct evidence in the documents, be honest and provide a brief response.
    </role>

    <user_question>
    {question}
    </user_question>

    <context>
    {context}
    </context>

    <instructions>
    1. Response Strategy:
       IF SPECIFIC QUESTION WITH EVIDENCE:
       - Provide detailed answer with dates and facts
       - Use chronological order
       - Cite specific meetings
       
       IF BROAD ANALYSIS OR LIMITED EVIDENCE:
       - Summarize key themes briefly
       - State clearly what information is available
       - Keep response short and focused
       
       IF NO RELEVANT EVIDENCE:
       - State honestly that information is not in the protocols
       - Keep response to 1-2 sentences
       - Don't speculate
    
    2. Source Citations:
       - Use natural date formats: "i mötet den 5:e mars..."
       - Never show filenames
       - Group related information by date
    
    3. Quality Standards:
       - Write in Swedish
       - Be direct and honest about limitations
       - Keep responses focused and relevant
       - Use clear, professional language
    </instructions>

    <response_examples>
    GOOD RESPONSES:
    
    For specific questions with evidence:
    "I mötet den 5:e mars diskuterades denna fråga specifikt, där man beslutade att..."
    
    For broad questions with limited evidence:
    "I protokollen nämns detta område kortfattat. De huvudsakliga punkterna är: [1]..., [2]..."
    
    For questions without evidence:
    "Denna fråga behandlas inte i de tillgängliga protokollen."
    
    BAD RESPONSES (NEVER USE):
    - Spekulativa svar utan källhänvisning
    - Långa svar när information saknas
    - Filnamn eller tekniska datumformat
    </response_examples>
    """)
    
    # Generate and stream the response
    prompt = prompt_template.format(context=context, question=question)
    async for chunk in chat_model.astream(prompt):
        yield chunk.content

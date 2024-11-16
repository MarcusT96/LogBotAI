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
    You are LogBot's Query Optimizer. Your task is to convert questions into 3 key search phrases
    that would appear in meeting minutes, focusing on the most essential terms and concepts.
    </role>

    <user_question>
    {query}
    </user_question>

    <instructions>
    1. Extract only the most essential search terms
    2. Create  3 alternative phrasings
    3. Use formal protocol language
    </instructions>

    <output_format>
    Return exactly 3 comma-separated phrases that capture the core search intent.
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
    Extract dates from document sources and refer to them naturally in your responses.
    Never show the full filename in your response.
    </role>

    <user_question>
    {question}
    </user_question>

    <context>
    {context}
    </context>

    <instructions>
    1. Chronological Organization:
       - Sort information by date before responding
       - Present events in chronological order
       - Use natural, conversational date references
       - Keep a clear timeline of events
    
    2. Source Citations:
       - Use these natural date formats:
         * "i mötet den 5:e mars..."
         * "vid mötet den 12:e mars..."
         * "detta följdes upp den 19:e mars..."
         * "senare, den 26:e mars..."
       - Never use YYYY-MM-DD format
       - Never show filenames
    
    3. Timeline Clarity:
       - Start with earliest date
       - Use natural transitions between dates
       - Group related information by date
       - Keep the narrative flowing naturally
    
    4. Quality Guidelines:
       - Write in Swedish
       - Use a conversational, clear tone
       - Make dates easy to read and understand
       - Maintain a natural chronological flow
    </instructions>

    <output_format>
    Structure your response naturally:
    1. Use conversational date formats
    2. Keep chronological order of the dates
    3. Make it easy to read
    
    CORRECT EXAMPLES:
    "I mötet den 5:e mars diskuterades först...
    Vid mötet den 12:e mars rapporterades att...
    Detta följdes upp den 19:e mars när...
    Slutligen, den 26:e mars konstaterades att..."
    
    INCORRECT EXAMPLES (NEVER USE):
    "I mötet den 2024-03-05..."
    "(Motesprotokoll_2024-03-05.docx)"
    "Den 5/3-2024..."
    </output_format>
    """)
    
    # Generate and stream the response
    prompt = prompt_template.format(context=context, question=question)
    async for chunk in chat_model.astream(prompt):
        yield chunk.content

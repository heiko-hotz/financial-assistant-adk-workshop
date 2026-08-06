import os
from dotenv import load_dotenv

# Load .env.local from project root (2 dirs up from this file)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
env_path = os.path.join(project_root, ".env.local")
load_dotenv(env_path)

if "GOOGLE_API_KEY" not in os.environ:
    print(f"⚠️ Warning: GOOGLE_API_KEY not found in {env_path}")

from google.adk.agents import Agent
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StdioServerParameters

# Calculate absolute path to the database to ensure it works from any CWD
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_rag_db")

# Define the Chroma Tool connection
# This spins up a local MCP server that talks to your "./demo_rag_db" folder
# We use 'uvx' to run the chroma-mcp server without global installation
chroma_tool = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uvx", 
            args=[
                "chroma-mcp", 
                "--client-type", "persistent",
                "--data-dir", db_dir, # Use absolute path
            ],
        )
    )
)

 # Create the Agent
root_agent = Agent(
    model='gemini-3.5-flash-lite',
    name='rag_agent',
    instruction="""You are a RAG Analyst. 
    Use the `chroma_query_documents` (or similar) tool to answer questions based on the user's document collection.
    The collection name is 'demo_docs'.
    If you find relevant info, summarize it concisely.
    """,
    tools=[chroma_tool]
)

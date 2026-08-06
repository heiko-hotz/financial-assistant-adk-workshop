
import os
from dotenv import load_dotenv
from typing import Annotated
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# 1. Load Environment Variables
# Load .env.local from project root (2 dirs up from this file)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
env_path = os.path.join(project_root, ".env.local")
load_dotenv(env_path)

if "GOOGLE_API_KEY" not in os.environ:
    print(f"⚠️ Warning: GOOGLE_API_KEY not found in {env_path}")

# 2. Define Tools
def get_stock_price(
    ticker: Annotated[str, "The stock ticker symbol (e.g. LUMR, AAPL)"]
) -> float:
    """Fetches the current stock price for a given ticker."""
    print(f"   [Tool] Fetching price for {ticker}...")
    
    # Simulation logic
    mock_prices = {
        "LUMR": 245.50,
        "AAPL": 180.00,
        "GOOG": 140.00
    }
    return mock_prices.get(ticker.upper(), 100.00)

stock_tool = FunctionTool(get_stock_price)

# 3. Define Agent
# Named 'root_agent' for ADK compatibility
root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="financial_assistant",
    tools=[stock_tool],
    instruction=(
        "You are a helpful Financial Assistant for Lumenridge Financial Group employees. "
        "Use your tools to find stock prices when asked. "
        "Always explain your analysis in a professional tone."
    )
)

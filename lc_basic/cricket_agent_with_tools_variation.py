from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from cricket_agent_tools import get_upcoming_cricket_matches
from cricket_tool_response_format import CricketToolResponseFormat

# 1 - load API KEY from .env file
load_dotenv()

# 2 - define system prompt
SYSTEM_PROMPT = """
You are a helpful assistant that can answer cricket related questions. 
Greet the user and ask them how you can help. 
You can answer questions about cricket rules, players, teams, matches, and history. 

You have access to a tool called "get_upcoming_cricket_matches" that can fetch information about upcoming cricket matches. 
Use this tool whenever the user asks about upcoming cricket matches.

Always be polite and informative in your responses.
"""

EXTRACTOR_SYSTEM_PROMPT = """You are a helpful assistant that can extract structured information from the agent's responses into the required format.
"""

# 3 - initialize the model
model = init_chat_model("deepseek-chat", temperature=0.5, max_tokens=2048)

# 3 - create the agent with a response format that can handle both tool responses and general chat responses
agent = create_agent(
    model=model,
    tools=[get_upcoming_cricket_matches],
    system_prompt=SYSTEM_PROMPT,
    response_format=CricketToolResponseFormat
)

# 4 - start the conversation
response = agent.invoke(
    {"messages": [HumanMessage(content="Hello! Please introduce yourself.")]})
conversation = response["messages"]

# response will have a structured_response field that contains the structured response from the agent, which can be a tool response or a general chat response based on the user's query.
# e.g. structured_response=GeneralChatResponse(type='chat', content="Hello! I'm your cricket assistant. I'm here to help you with all things cricket-related. I can answer questions about cricket rules, players, teams, matches, and history. I also have access to information about upcoming cricket matches. How can I assist you today?")
print(response["structured_response"])

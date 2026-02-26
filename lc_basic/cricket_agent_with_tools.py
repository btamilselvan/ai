## This is an example of a cricket agent that can answer cricket related questions and also has access to a tool that can fetch information about upcoming cricket matches. 
# The agent uses a response format that can handle both general chat responses and tool responses. 
# We also use a separate model instance with structured output to extract the structured response from the agent's response.

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

# 3 - create the agent
agent = create_agent(
    model=model,
    tools=[get_upcoming_cricket_matches],
    system_prompt=SYSTEM_PROMPT
)

# 4 - start the conversation
response = agent.invoke(
    {"messages": [HumanMessage(content="Hello! Please introduce yourself.")]})
conversation = response["messages"]

# print the text version of the agent's response
print("Agent: ", conversation[-1].content)

# 4.1 (use a separate model instance with structured output for extracting the structured response from the agent's response)
extractor = model.with_structured_output(CricketToolResponseFormat)
## the extractor_response will have the structured_response field.
## e.g. extractor response will be "structured_response=GeneralChatResponse(type='chat', content="Hello! I'm your cricket assistant, here to help you with all things cricket! I can answer questions about cricket rules, players, teams, matches, history, and more. I also have access to information about upcoming cricket matches.\n\nHow can I help you today? Are you interested in learning about cricket rules, specific players or teams, match results, or perhaps you'd like to know about upcoming matches?")"
extractor_response = extractor.invoke([SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT),
                                        AIMessage(content=conversation[-1].content)])
print("Structured Response: ", extractor_response)
structured_response = extractor_response.structured_response
# use the 'type' to determine if it's a tool response or a general chat response
print("Structured Response Type: ", structured_response.type)

# 5 - conversation loop
number_of_questions = 2
for i in range(number_of_questions):
    human_message = input("Human: ")
    conversation.append(HumanMessage(content=human_message))
    response = agent.invoke({"messages": conversation})
    agent_response = response["messages"][-1].content
    print("Agent: ", agent_response)
    conversation.append(AIMessage(content=agent_response))
    
    # format the agent's response into the structured format using the extractor
    extractor_response = extractor.invoke([SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT),
                                        AIMessage(content=conversation[-1].content)])
    print("Structured Response: ", extractor_response)
    structured_response = extractor_response.structured_response
    # use the 'type' to determine if it's a tool response or a general chat response
    print("Structured Response Type: ", structured_response.type)


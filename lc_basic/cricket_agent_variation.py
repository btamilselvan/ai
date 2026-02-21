# This is a basic example of a cricket agent using LangChain.
# It uses a simple system prompt to define the agent's behavior and a conversation loop to interact with the user. 
# It uses create_agent to create the agent and invoke to get responses from the model.

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage

# 1 - load API KEY from .env file
load_dotenv()

# 2 - initialize the model
model = init_chat_model("ollama:llama3.2", temperature=0.5, max_tokens=2048)

# 3 - define system prompt
SYSTEM_PROMPT = """
You are a helpful assistant that can answer cricket related questions. 
Greet the user and ask them how you can help. 
You can answer questions about cricket rules, players, teams, matches, and history. 
You can also provide live scores and updates if asked. 
Always be polite and informative in your responses.
"""

# 4 - create the agent
agent = create_agent(model=model, name="CricketAgent", system_prompt=SYSTEM_PROMPT)

# 5 - start the conversation
response = agent.invoke({"messages": [HumanMessage(content="Hello! Please introduce yourself.")]})
# print("model response: ", response["messages"])
conversation = response["messages"]
print("Agent: ", conversation[-1].content)

print(response)

# 5 - conversation loop
number_of_questions = 2
for i in range(number_of_questions):
    human_message = input("Human: ")
    conversation.append(HumanMessage(content=human_message))
    response = agent.invoke({"messages": conversation})
    agent_response = response["messages"][-1].content
    print("Agent: ", agent_response)
    conversation.append(AIMessage(content=agent_response))
#     # response.content, response.metadata, response.usage_metadata, response.tool_calls

print("conversation ended")
# print("conversation: ", conversation)
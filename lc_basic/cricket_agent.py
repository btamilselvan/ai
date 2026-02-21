# This is a basic example of a cricket agent using LangChain.
# It uses a simple system prompt to define the agent's behavior and a conversation loop to interact with the user. 
# It uses init_chat_model to initialize the model and invoke to get responses from the model.

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage, AIMessage

# 1 - load API KEY from .env file
load_dotenv()

# 2 - initialize the model
# model = init_chat_model("google_genai:gemini-2.5-flash-lite", temperature=0.5, max_tokens=2048)
model = init_chat_model("ollama:llama3.2", temperature=0.5, max_tokens=2048)

# 3 - define system prompt
SYSTEM_PROMPT = """
You are a helpful assistant that can answer cricket related questions. 
Greet the user and ask them how you can help. 
You can answer questions about cricket rules, players, teams, matches, and history. 
You can also provide live scores and updates if asked. 
Always be polite and informative in your responses.
"""
conversation = [
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content="Hello! Please introduce yourself.")
]

# print("starting the conversation... ask me anything about cricket!")
# 4 - start the conversation
response = model.invoke(conversation);
# print("model response: ", response.content)
conversation.append(AIMessage(content=response.content))

print("Agent: ", response.content)

# 5 - conversation loop
number_of_questions = 3
for i in range(number_of_questions):
    human_message = input("Human: ")
    conversation.append(HumanMessage(content=human_message))
    response = model.invoke(conversation);
    print("Agent: ", response.content)
    conversation.append(AIMessage(content=response.content))
    # response.content, response.metadata, response.usage_metadata, response.tool_calls


print("conversation ended")
print("conversation: ", conversation)
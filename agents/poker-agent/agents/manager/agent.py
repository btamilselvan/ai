from openai import OpenAI
from dotenv import load_dotenv
from state.app_state import AppState

load_dotenv()

client = OpenAI(model="gemma4:e4b", temperature=0.7)


def call_llm(app_state: AppState) -> AppState:
    # call the LLM with the app_state and get the response
    
    response = client.chat.completions.create(
        context="You are a poker agent that helps users play poker by providing suggestions and advice based on the current game state. You can analyze the user's hand, the community cards, and the actions of other players to give recommendations on whether to fold, call, or raise. You can also provide insights on the strength of the user's hand and potential winning combinations.",
        model="gemma4:e4b",
        temperature=0.7,
        messages=app_state.messages
    )
    # update the app_state with the response
    app_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
    return app_state
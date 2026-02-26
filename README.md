# ai

- Pydantic BaseModel is the primary tool for Data Validation.
- When we create a class that inherits from BaseModel, Pydantic performs "parsing" rather than just type checking. It will try to convert data to the correct type (e.g., turning the string "123" into the integer 123) and validate it against our rules.

### Framework comparision

| Feature            | LangChain                                           | LangGraph                                             | CrewAI                                                     |
|--------------------|-----------------------------------------------------|-------------------------------------------------------|------------------------------------------------------------|
| Architectural Role | Foundational Library (The "Swiss Army Knife")       | State Machine / Orchestrator (The "Brainstem")        | Multi-Agent Coordinator (The "Manager")                    |
| Built On Top Of    | Direct LLM / Provider SDKs                          | LangChain (specifically LCEL)                         | LangChain (historically) & Pydantic                        |
| Logic Model        | Linear Chains (DAGs): A → B → C                     | Cyclic Graphs: Loops, branches, and retries           | Role-Based Teams: Tasks, Roles, and Backstories            |
| State Management   | Minimal (Basic memory buffers)                      | High (Persistence): Uses Checkpoints to save/resume   | Context-Based: Shares "Context" objects between agents     |
| Workflow Style     | Explicit (You define every step)                    | Low-level (You define Nodes & Edges)                  | Declarative (You define the Goal, it figures out the How)  |
| Human-in-the-Loop  | Difficult (Requires custom code)                    | Native: Built-in "Interrupt" nodes for approval       | Simple: via human_input=Trueparameter                      |
| Execution          | Sequential                                          | Parallel & Stateful                                   | Sequential, Hierarchical, or Asynchronous                  |
| Best Use Case      | Simple RAG, Chatbots                                | Enterprise apps, coding agents, self-correcting loops | Creative writing, research teams, business processes       |
| Primary Goal       | Connecting LLMs to data/tools                       | Complex, looping workflows                            | Multi-agent collaboration                                  |
| Complexity         | Medium                                              | High (Steep learning curve)                           | Low (Very Easy)                                            |
| Control            | Modular                                             | Total Control (Architectural)                         | "Hands-off" (Managerial)                                   |
| Best Analogy       | A Swiss Army Knife: A tool for every specific task. | A Flowchart: If A happens, do B; then repeat C.       | A Company: Different roles working toward a goal.          |

## Tools

Tools are callable functions with well-defined inputs and outputs that get passed to a chat model. The model decides when to invoke a tool based on the conversation context, and what input arguments to provide.

### Access Context
Tools can access runtime information through the ToolRuntime parameter.

#### ToolRuntime Componenets
| Component     | Description                                                                                                   | Use case                                            |
|---------------|---------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| State         | Short-term memory - mutable data that exists for the current conversation (messages, counters, custom fields) | Access conversation history, track tool call counts |
| Context       | Immutable configuration passed at invocation time (user IDs, session info)                                    | Personalize responses based on user identity        |
| Store         | Long-term memory - persistent data that survives across conversations                                         | Save user preferences, maintain knowledge base      |
| Stream Writer | Emit real-time updates during tool execution                                                                  | Show progress for long-running operations           |
| Config        | RunnableConfig for the execution                                                                              | Access callbacks, tags, and metadata                |
| Tool Call ID  | Unique identifier for the current tool invocation                                                             | Correlate tool calls for logs and model invocations |


## LangGraph

LangGraph is very low-level, and focused entirely on ```agent orchestration```. LangGraph provides low-level supporting infrastructure for any long-running, ```stateful``` workflow or agent.

### ReAct
The ReAct pattern (short for Reasoning + Acting) is the architectural standard for building AI agents that don't just talk, but actually do work.

Before ReAct, LLMs were like students who shouted out an answer immediately without showing their work. ReAct forces the AI to slow down and use a "Thought-Action-Observation" loop.

#### Three stpes of ReAct
When we give a ReAct agent a task (like "What is the square root of the current temperature in NYC?"), it follows this cycle:

- Thought - The AI writes down its internal reasoning. "I first need to find the temperature in NYC, then I will calculate the square root."
- Action - The AI chooses a tool to call. get_weather(city="NYC")
- Observation - The AI "sees" the tool result. "The temperature is 16 degrees."

#### Why ReAct better
- Reduced Hallucination: Instead of guessing a fact (like the weather), the agent is forced to use a tool to get the ground truth.
- Multi-step Logic: It can break a complex request into a sequence of smaller tasks.
- Self-Correction: If a tool returns an error (e.g., "City not found"), the AI can "Reason" about the error and try a different search term.

#### How ReAct fits in LangGrapgh
- ```llm_call``` node: This is where the Thought and Action happen. The LLM generates the "Thought" (internal monologue) and the "Tool Call" (Action).
- ```tool_node```: This provides the Observation. It runs the math and feeds the result back into the message history.
- ```should_continue```: This is the "Exit Logic." It looks at the LLM's last message and asks: "Is there an 'Action' here? If yes, go to the Tool Node. If no, we are done."

### Graph API
- Graph - workflow made of nodes and edges (graphical representation)
- Nodes - steps (it can be a function, an agent or a tool)
- Edges - rules that decide which node runs next
- State - shared data between the nodes (e.g. storing user's favorite cricket team, messages, etc) (nodes receive the current state and returns the updated state) (TypeDict)

### Workflow

Define a state -> Write node functions -> connect nodes with edges -> fianl graph (invoke the grpah)

### Thinking in LangGraph
Step 1: Map out your workflow as discrete steps
Step 2: Identify what each step needs to do
    - A step can be, LLM Step, Data Step, Action Step, User Input Step
Step 3: Design your state
    - Keep state raw, format prompts on-demand
Step 4: Build your nodes

### Error handling
| Error Type                                                      | Who Fixes It       | Strategy                           | When to Use                                       |
|-----------------------------------------------------------------|--------------------|------------------------------------|---------------------------------------------------|
| Transient errors (network issues, rate limits)                  | System (automatic) | Retry policy                       | Temporary failures that usually resolve on retry  |
| LLM-recoverable errors (tool failures, parsing issues)          | LLM                | Store error in state and loop back | LLM can see the error and adjust its approach     |
| User-fixable errors (missing information, unclear instructions) | Human              | Pause with interrupt()             | Need user input to proceed                        |
| Unexpected errors                                               | Developer          | Let them bubble up                 | Unknown issues that need debugging                |

### Interrupt and Resuming

When you call interrupt, here’s what happens:
Graph execution gets suspended at the exact point where interrupt is called
State is saved using the checkpointer so execution can be resumed later, In production, this should be a persistent checkpointer (e.g. backed by a database)
Value is returned to the caller under __interrupt__; it can be any JSON-serializable value (string, object, array, etc.)
Graph waits indefinitely until you resume execution with a response
Response is passed back into the node when you resume, becoming the return value of the interrupt() call

Key points about resuming:
You must use the same thread ID when resuming that was used when the interrupt occurred
The value passed to Command(resume=...) becomes the return value of the interrupt call
The node restarts from the beginning of the node where the interrupt was called when resumed, so any code before the interrupt runs again
You can pass any JSON-serializable value as the resume value

### Functional API

### Memory Overview
### Short-term memory


## Workspace setup
- create venv ```python3 -m venv myaienv```
- active venv ```source myaienv/bin/activate```
- deactivate venv ```deactivate```
- install packages included in requirements.tx ``` pip3 install -r lc_requirements.txt ```
- list all installed packages ```pip list```
- add all installed packages to requirements.txt - ``` pip freeze > requirements.txt ```

## Ollama

- Run locally (install ollama and download the model(s))


## References
- chatgpt model comparision - https://developers.openai.com/api/docs/models/compare
- ollama langchain integration - https://docs.langchain.com/oss/python/integrations/chat/ollama
- Providers list - https://docs.langchain.com/oss/python/integrations/providers/overview
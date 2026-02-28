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

#### Interrupts - best practices
- Do not enclose interrupt calls in try catch block
- Do not perform non-idempotent operations before interrupt
- Do not return complex values in interrupt calls
- Do not conditionally skip interrupt calls within a node

### Functional API

### Memory Overview
### Short-term memory
Short-term memory (thread-level persistence) enables agents to track multi-turn conversations.
- Use ```checkpoint``` to add short-term memory. it is backed by InMemorySaver, PostgresSaver, MongoDBSaver, RedisSaver

- Short-term memory can be managed by "Trim Messages", "Delete Messages", "Summarize Messages"

### Long-term memory
Use long-term memory to store user-specific or application-specific data across conversations.
- Can be implemented using "InMemoryStore", "PostgresStore", "RedisStore"

### Subgraphs

## Workspace setup
- create venv ```python3 -m venv myaienv```
- active venv ```source myaienv/bin/activate```
- deactivate venv ```deactivate```
- install packages included in requirements.tx ``` pip3 install -r lc_requirements.txt ```
- list all installed packages ```pip list```
- add all installed packages to requirements.txt - ``` pip freeze > requirements.txt ```

## Ollama

- Run locally (install ollama and download the model(s))

## LangSmith App
### Local dev
- Install langgraph-cli and "langgraph-cli[inmem]"
- pip install langgraph-cli "langgraph-cli[inmem]"
- Run, ```langgraph dev```
- When you import functions from one module to another (e.g. agent.py imports tools and nodes), make sure to use the full module path in the import statement. For example, 

``` cricket_agent/agent.py -> import functions from utils/nodes.py and utils/tools.py
    from cricket_agent.utils.state import MyAppState
    from cricket_agent.utils.nodes import llm_node, tool_tode, planner_node
```

## MCP (Model Context Protocol)

The MCP Server (the wrapper) acts as a specialized adapter. It is often developed by the community or the API providers themselves to bridge the gap between "LLM-speak" (JSON-RPC) and "API-speak" (REST/HTTP).

- In the MCP world, "Server" refers to the role in the JSON-RPC relationship, not necessarily where the code lives.

### The Wrapper's Role

Whether local or remote, the MCP wrapper is the piece that "knows" the API. It contains the logic to:

- ```Authenticate``` with the underlying APIs

- ```Map Tools``` - e.g. Take a high-level tool like get_upcoming_matches and translate it into the specific URL https://cricket-live-data.p.rapidapi.com/fixtures.

- ```Format Data``` - e.g Strip out the 1,000 lines of raw JSON the API returns and give the LLM just the 5 lines of cricket scores it actually asked for.

### Who Develops the Wrapper
This is currently a mix of three groups:

- The API Providers: Some (like Google or Slack) are releasing "Official" MCP servers.

- The AI Platforms: Anthropic and OpenAI maintain "Reference" servers for things like Google Drive or GitHub.

- The Community: Enthusiasts on platforms like Smithery.ai or Glama.ai write wrappers for popular APIs (like the RapidAPI Cricket ones) so that other developers don't have to start from scratch.

### The Two Ways to "Connect"

| Feature        | Local (stdio) Transport                                                 | Remote (HTTP/SSE) Transport                                      |
|----------------|-------------------------------------------------------------------------|------------------------------------------------------------------|
| Analogy        | A Pipe. Like cat file | grep.                                           | A Socket. Like curl https://api...                               |
| Who starts it? | The Client (Your Agent) spawns it as a subprocess.                      | The Provider (RapidAPI) keeps it running 24/7.                   |
| Connection     | stdin / stdout                                                          | HTTP POST + Server-Sent Events                                   |
| Use Case       | Most current GitHub/NPM MCP servers (the ones you find on Smithery.ai). | Enterprise/Cloud services (like a hosted DB or specialized API). |

### The "Big Three" of MCP Connectivity

| Connection Method      | What it is    | How it works                                                                  | Analogy                                            |
|------------------------|---------------|-------------------------------------------------------------------------------|----------------------------------------------------|
| 1. Stdio (Local)       | Child Process | Agent spawns the server on your PC. They talk via system pipes.               | A personal translator sitting in your room.        |
| 2. SSE / HTTP (Remote) | Web Service   | Agent connects directly to a URL over the internet.                           | Calling a translator over the phone.               |
| 3. mcp-remote (Bridge) | The Hybrid    | Agent spawns a tiny local process (mcp-remote) which then calls a remote URL. | Hiring a local guy to call the translator for you. |


### Comparing the "Chain of Command"

| Feature      | Local (Stdio) Mode                              | Remote (SSE) Mode                             |
|--------------|-------------------------------------------------|-----------------------------------------------|
| Architecture | Parent-Child Process. Your agent is the parent. | Client-Server. Your agent is a web client.    |
| Transport    | stdin / stdout pipes.                           | HTTP POST + Server-Sent Events.               |
| Lifecycle    | Spawned on demand. Killed when agent stops.     | Always-on. Lives independently in the cloud.  |
| Security     | Isolated to your machine. No network exposed.   | Requires HTTPS, API keys, or JWT tokens.      |
| Latency      | Near-zero. No network overhead.                 | Network-dependent. (Approx. 20–100ms).        |
| Best For     | IDEs, local CLI tools, secure local databases.  | SaaS, Mobile apps, shared team data sources.  |

| Mode          | Transport    | Mechanism                                              | Use Case                                        |
|---------------|--------------|--------------------------------------------------------|-------------------------------------------------|
| Local (Stdio) | stdin/stdout | The Agent spawns the MCP Server as a local subprocess. | Local development and CLI-based tools.          |
| Remote (SSE)  | HTTP/SSE     | The Agent connects to an existing remote URL.          | Production web/mobile apps and shared services. |


| Model         | The Chain                                               | Where the "Logic" Lives                                               |
|---------------|---------------------------------------------------------|-----------------------------------------------------------------------|
| Local (Stdio) | Agent → Local Wrapper (on your PC) → RapidAPI (Cloud)   | The wrapper logic is running on your machine as a child process.      |
| Remote (SSE)  | Agent → Remote Wrapper (on a Server) → RapidAPI (Cloud) | The wrapper logic is running on a web server, which you call via URL. |


### Stdio Mode

In Stdio mode, the "Server" is really just a local process that your agent (the Host) manages. It’s like having a dedicated translator sitting in the same room as you, rather than calling one in a different country.

In Stdio mode, the MCP Server is a local subprocess of the Agent. This ensures low-latency, secure communication via system pipes without the need for network configuration or open ports.

- The Chain: Your Agent <—(Stdio/JSON-RPC)—> Local MCP Wrapper <—(HTTP/REST)—> Remote Cricket API.
- Both the MCP Client (your agent) and the MCP Server run on the same host machine.

#### How it works

Our LangGraph Agent (the Host) spawns the MCP Server as a local child process.

The Communication: Instead of HTTP requests over the internet, the Agent and the MCP Server talk by "typing" to each other through system pipes (stdin/stdout).

The Logic: This local translator sits on the host machine, receives high-level commands from the Agent, and then makes the traditional REST API calls to the remote Cricket data source.

#### The Parent-Child Process Model
When you run your LangGraph application, it acts as the Parent Process. When it reaches the line of code that initializes the MCP connection:

- The Spawn: Your Agent (Parent) tells the OS to start a new Child Process (the MCP Server).

- The Pipes: The OS creates two "pipes" (unidirectional data channels) between them:

    -   Stdin: The Parent writes to the Child's input.

    -   Stdout: The Child writes to the Parent's output.

- The Handshake: They immediately begin "typing" JSON-RPC messages to each other through these pipes to negotiate capabilities.

#### how to handle a "Zombie Process"
- what happens if your Agent crashes but the local MCP Server stays running—and how to prevent it?

### SSE Mode

- The "Translator" (MCP server) is moved to the cloud.
- The Chain: Your Agent <—(HTTP/SSE)—> Remote MCP Wrapper <—(Internal)—> Cricket Data.

Unlike Stdio, where communication is a simple two-way pipe, SSE is traditionally unidirectional (Server → Client). To achieve the bidirectional communication MCP requires, it uses two distinct channels:

- The "Get" Channel (SSE): The Agent (Client) opens a long-lived HTTP GET request to the MCP Server. The server uses this to push messages (tool results, logs, or notifications) to the agent.

- The "Post" Channel (HTTP): When the Agent wants to send a command (like tools/call), it sends a standard HTTP POST request to a specific endpoint provided by the server during the handshake.

### Code sample

```
async def runit():
    server_params = StdioServerParameters(
        command="npx",
        args=[
            "mcp-remote",
            "https://mcp.rapidapi.com",
            "--header",
            "x-api-host: cricbuzz-cricket.p.rapidapi.com",
            "--header",
            f"x-api-key: {os.getenv("RAPIDAPI_API_KEY")}",
        ]
    )
    
    async with stdio_client(server_params) as (read, write):
        global agent
        global model_with_tools
        global tool_node_remote
        
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await load_mcp_tools(session)
            print("mcp tools loaded..")
            
            tool_node_remote = ToolNode(mcp_tools)

```

#### Breakdown of the Logic
##### The Connection Parameters (server_params)
This block defines how to talk to the remote server.
- ```command="npx"```: It uses Node.js's package runner to execute a tool.
- ```mcp-remote```: This is the specific MCP inspector/proxy tool. This is the "Bridge Utility." Its job is to talk Stdio to your Python script and HTTPS/SSE to RapidAPI.
- ```https://mcp.rapidapi.com```: This is the gateway URL.
- ```Headers```: It passes the RapidAPI credentials (host and key) so the remote server knows who is making the request.

##### The Communication Tunnel (stdio_client)
``` async with stdio_client(server_params) as (read, write):```

This opens a "pipe" between your Python script and the npx process.
- read: Where Python listens for data coming back from the API.
- write: Where Python sends commands (like "Get me the score for match X").

##### Session Initialization

``` 
async with ClientSession(read, write) as session:
    await session.initialize()
```
The client and the remote server perform a "handshake." They agree on versioning and capabilities before any data is exchanged.
This line actually spawns the npx mcp-remote process. It creates two "pipes" (read and write) so your Python script can send and receive data from that subprocess.

##### Tool Discovery and Integration
- ```session.initialize()```: This is the Handshake. Your script says "Hello" to the remote server, and the server replies with its version and capabilities.
- ```load_mcp_tools(session)```: This asks the remote server: "What functions do you have available?" The server might respond with "get_live_score," "get_player_stats," etc. Discovery step.
- ```ToolNode(mcp_tools)```: It takes those remote functions and packages them into a format that a LangGraph AI agent can understand and call automatically.

##### Summary
1) Spawn a process to talk to RapidAPI.
2) Establish a secure communication session.
3) Fetch the definitions of all available cricket tools.
4) Register those tools into a ToolNode so your AI agent can decide when to use them.

## References
- chatgpt model comparision - https://developers.openai.com/api/docs/models/compare
- ollama langchain integration - https://docs.langchain.com/oss/python/integrations/chat/ollama
- Providers list - https://docs.langchain.com/oss/python/integrations/providers/overview
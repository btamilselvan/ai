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
# Tiny Backspace

# **Introduction**

---

Let's build a trivial version of Backspace — a sandboxed coding agent that can create PRs!

In this project, we will build a service that takes in:

- `Your Public Github Repo Url`  - i.e (https://github.com/daytonaio/daytona)
- `Coding Prompt`  - i.e (Add a sign on page to the app)

And automatically creates a pull request with the implemented changes.

This is effectively exploring the core technology behind autonomous coding agents and we'll build it with modern tooling for safety and observability.

# **Project Spec**

---

Make a **streaming API** either in Python or Typescript

*For example…*

- **Python**: FastAPI with Server-Sent Events
- **TypeScript**: Next.js API with Server-Sent Events

**Endpoint**: `POST /code` that immediately starts streaming the coding process via Server-Sent Events

- Takes in two inputs:
    - `repoUrl`: the URL of a public repo on Github
    - `prompt`: a textual command describing what code changes to make
- Streams real-time updates showing:
    - Repo cloning progress
    - Agent analysis and planning
    - Code changes being made
    - Git operations and PR creation
    - Final result with PR URL
- It then:
    - Clones the repo into a secure sandbox environment
    - Runs a coding agent of your choice to implement the requested changes
    - Creates a pull request with the implemented changes
    - Returns the PR URL and a summary of changes made
- **Focus Areas**: Don't get bogged down with the agent implementation - focus on the surrounding infrastructure like sandboxing and PR creation

*You may face some trouble getting the agent to make PRs for you from the sandbox. Thus, it’s completely fine if you make a PR on one of your own public GitHub repositories and use your PAT for authentication. The agent can make PRs under your name.*

### **Bonus Points:**

- Real-time telemetry through OpenTelemetry or observability tools like LangSmith that shows the agent's thinking process

# **Using AI Tools**

Please please use Cursor, Claude Code or any other AI tools to help you code.

This project is designed to measure how effectively you can "just figure it out" and ship infrastructure that works.

*At Backspace, we are vibe coders at heart*

# Tips

- feel free to use Claude Code or Codex as your built-in coding agent
- Some good sandbox providers are [Modal](https://modal.com/docs/guide/sandbox), [Daytona](https://www.daytona.io/docs/) & [E2B](https://e2b.dev/)

# **Example Input/Output:**

---

**Input:**

- Public repo: `https://github.com/example/simple-api`
- Prompt: `"Add input validation to all POST endpoints and return proper error messages"`

**Expected Output (Server-Sent Events stream):**

```markdown

data: {"type": "Tool: Read", "filepath": "app.py"}

data: {"type": "Tool: Read", "filepath": "requirements.txt"}

data: {"type": "AI Message", "message": "Found 3 POST endpoints: /users, /posts, /comments. Need to add Pydantic for validation."}

data: {"type": "Tool: Edit", "filepath": "models.py", "old_str": "", "new_str": "from pydantic import BaseModel\n\nclass UserCreate(BaseModel):\n    name: str\n    email: str"}

data: {"type": "Tool: Edit", "filepath": "app.py", "old_str": "@app.post('/users')\ndef create_user(user_data: dict):", "new_str": "@app.post('/users')\ndef create_user(user_data: UserCreate):"}

data: {"type": "Tool: Edit", "filepath": "requirements.txt", "old_str": "fastapi==0.68.0", "new_str": "fastapi==0.68.0\npydantic==1.8.2"}
data: {"type": "Tool: Bash", "command": "git checkout -b feature/add-input-validation", "output": "Switched to a new branch 'feature/add-input-validation'"}

data: {"type": "Tool: Bash", "command": "git add .", "output": ""}

data: {"type": "Tool: Bash", "command": "git commit -m 'Add input validation to POST endpoints'", "output": "[feature/add-input-validation abc123] Add input validation to POST endpoints"}

data: {"type": "Tool: Bash", "command": "git push origin feature/add-input-validation", "output": "To https://github.com/example/simple-api.git"}

data: {"type": "Tool: Bash", "command": "gh pr create --title 'Add input validation to POST endpoints' --body 'Added Pydantic models for validation and proper error handling'", "output": "https://github.com/example/simple-api/pull/123"}

```

**The created PR should contain:**

- Proper code changes that address the prompt
- A clear PR description explaining what was changed and why

*The above output is a very rough example. Stream as you wish! Whatever makes the most sense to you and is most appropriate.*

# **Deliverables**

---

Please send the following to [tawsif@backspace.run](mailto:tawsif@backspace.run) with the subject "[Name]: Coding Agent Takehome Submission":

- Repo link on Github
- A README with:
    - How to hit the public URL
    - How to run it locally on our machines
    - Which coding agent approach you chose and why
- Demo video (optional but encouraged) showing the full flow from API call to PR creation

# **Other Notes**

---

- Please write code quality that you would deem "good"
    - Moving fast is impressive, but so is writing code that's maintainable and secure
    - We aren't asking for production-quality code, but the architecture should make sense
- **Security is important** - since you're running arbitrary code, proper sandboxing is critical
- **Think about observability** - we want to see what the agent is thinking/doing in real-time. Even if you don’t trace your logs to an external observability tool, show some logging statements.

Don't hesitate to reach out to [tawsif@backspace.run](mailto:tawsif@backspace.run) if you have any questions!

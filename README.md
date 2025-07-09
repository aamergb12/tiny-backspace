# Tiny Backspace AI Coding Agent

A production-grade AI coding agent that generates complete project structures using Claude's native tools API. Built with FastAPI, Modal cloud sandboxing, and enterprise-level observability.

## 🚀 Key Features

### **Tools-Based Architecture**
- Uses Claude 3.5 Sonnet's native Tools API for direct file execution
- Multi-turn conversations for complex project generation
- Context-aware file creation based on project type

### **Context-Aware Generation**
- **Web Development**: Creates `auth.py`, `routes.py`, `models.py` for APIs
- **Data Science**: Generates `model.py`, `training.py`, `preprocessing.py` for ML projects
- **Frontend**: Builds `components.jsx`, `utils.js`, `styles.css` for React apps
- **DevOps**: Produces `docker_manager.py`, `logger.py`, `config.py` for tools

### **Enterprise Observability**
- LangSmith-style telemetry with OpenTelemetry
- Real-time AI decision tracking and confidence scoring
- File quality analysis and code complexity metrics
- End-to-end session monitoring with detailed traces

### **Secure Cloud Execution**
- Modal cloud sandboxing for isolated code execution
- Ephemeral containers with pre-installed development tools
- Automatic cleanup and no local environment pollution

### **Professional Output**
- Comprehensive README generation with setup instructions
- Production-ready code with proper error handling
- Automatic GitHub PR creation with detailed descriptions
- Professional commit messages and documentation

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI        │    │   Claude 3.5    │
│   (React/Next)  │───▶│   Backend        │───▶│   Sonnet        │
│                 │    │                  │    │   Tools API     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Modal Cloud    │    │   Enhanced      │
                       │   Sandboxing     │    │   Telemetry     │
                       │                  │    │   (OpenTelemetry)│
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   GitHub         │
                       │   Integration    │
                       │   (CLI + API)    │
                       └──────────────────┘
```

## 🛠️ Tech Stack

### **Backend**
- **FastAPI**: High-performance API with automatic docs
- **Claude 3.5 Sonnet**: Latest tools-capable AI model
- **Modal**: Cloud sandboxing and container orchestration
- **OpenTelemetry**: Enterprise observability and tracing

### **AI Integration**
- **Anthropic SDK**: Official Python client for Claude API
- **Tools API**: Native tool execution (not function calling)
- **Multi-turn Conversations**: Context-aware file generation

### **Infrastructure**
- **GitHub CLI**: Reliable git operations and PR creation
- **Docker**: Containerized execution environment
- **Server-Sent Events**: Real-time progress streaming

## 📦 Installation

### **Prerequisites**
- Python 3.9+
- Node.js 18+ (for frontend)
- Modal account and CLI setup
- GitHub personal access token
- Anthropic API key

### **Backend Setup**
```bash
# Clone the repository
git clone https://github.com/yourusername/tiny-backspace.git
cd tiny-backspace

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your_claude_api_key
# GITHUB_TOKEN=your_github_token
```

### **Modal Setup**
```bash
# Install Modal CLI
pip install modal

# Authenticate with Modal
modal token new

# Verify setup
modal app list
```

### **Frontend Setup**
```bash
cd frontend
npm install
npm run build
```

## 🚀 Usage

### **Start the Backend**
```bash
python3 main.py
```
The API will be available at `http://localhost:8002`

### **Start Frontend (Development)**
```bash
cd frontend
npm run dev
```
Frontend available at `http://localhost:5173`

### **API Usage**
```bash
curl -X POST http://localhost:8002/code \
  -H "Content-Type: application/json" \
  -d '{
    "repoUrl": "https://github.com/username/repo",
    "prompt": "Create a FastAPI authentication system"
  }'
```

## 🎯 Example Prompts

### **Web Development**
```
Create a FastAPI web application with user authentication
Build a Flask blog application with admin panel
Create a React dashboard with charts and user management
```

### **Data Science**
```
Create a Python machine learning project for image classification
Build a data analysis pipeline for customer segmentation
Create a neural network for sentiment analysis
```

### **DevOps & Tools**
```
Create a CLI tool for managing Docker containers
Build a monitoring system for server health with alerts
Create a deployment automation script with logging
```

## 📊 Telemetry & Observability

### **LangSmith-Style Traces**
```
🔍 LANGSMITH TRACE: claude_tool_execution
⏱️  Duration: 1834.50ms | Status: ✅ SUCCESS
📊 Context:
   🧠 claude.tool_name: create_file
   🧠 claude.file_path: auth.py
   🛠️  tools.success: True
```

### **Tracked Metrics**
- **AI Decision Making**: Confidence scores, reasoning quality
- **Tool Execution**: Success rates, timing, error handling
- **File Quality**: Lines of code, documentation coverage, complexity
- **Session Performance**: End-to-end duration, PR creation success

## 🔧 Configuration

### **Environment Variables**
```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key_here
GITHUB_TOKEN=your_github_personal_access_token

# Optional
MAX_TOKENS=4000
MODAL_APP_NAME=tiny-backspace-agent
LOG_LEVEL=INFO
```

### **Modal Configuration**
The agent automatically creates Modal apps and manages container lifecycle. Configuration is handled in `sandbox.py`.

## 🏢 Production Deployment

### **Docker Deployment**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### **Environment Setup**
- Configure secrets management for API keys
- Set up monitoring and alerting
- Configure rate limiting for Claude API
- Set up backup authentication methods

## 🔐 Security

### **API Key Management**
- Environment variables for all secrets
- No API keys in code or logs
- Modal handles container isolation

### **Sandbox Security**
- Ephemeral containers prevent persistence attacks
- Isolated file systems per request
- Automatic cleanup after execution

### **GitHub Integration**
- Personal access tokens with minimal required scopes
- Repository-specific permissions
- Audit logging for all git operations

## 📈 Performance

### **Benchmarks**
- **Average Session Duration**: 15-30 seconds
- **File Generation**: 2-5 files per request
- **API Response Time**: <2 seconds for simple requests
- **Claude API Calls**: 2-4 per session (multi-turn)

### **Scaling**
- Modal provides automatic horizontal scaling
- Each request runs in isolated container
- No shared state between sessions
- Concurrent request handling

## 🐛 Troubleshooting

### **Common Issues**

**Modal Authentication Failed**
```bash
modal token new
modal app list  # Verify connection
```

**Claude API Rate Limits**
- Monitor usage in Anthropic console
- Implement exponential backoff
- Consider upgrading API tier

**GitHub Permission Denied**
- Verify token has repo write permissions
- Check repository access settings
- Ensure token hasn't expired

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude 3.5 Sonnet and Tools API
- **Modal** for cloud sandboxing infrastructure
- **OpenTelemetry** for observability standards
- **FastAPI** for the excellent Python web framework

## 📞 Support

For questions or support:
- Create an issue in this repository
- Check the troubleshooting section above
- Review the API documentation at `/docs` when running locally

---

**Built with ❤️ for the future of AI-powered development**
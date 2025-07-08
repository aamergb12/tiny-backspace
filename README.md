# Tiny Backspace - AI Coding Agent

This is my take-home for Backspace, I focused on strong infra, streaming feedback, and secure sandboxing. The agent is Claude-powered, but I built everything around it to make the whole system reliable and clear. I’ve included everything below, how it works, how to run it, and why I chose this setup.


A streaming API that automatically creates GitHub pull requests using Claude AI and secure Modal cloud sandboxes.

## 🚀 Features

- **Claude AI Integration**: Intelligent code analysis and generation using Anthropic's Claude 3 Sonnet
- **Modal Cloud Sandboxes**: Secure, ephemeral execution environments in the cloud
- **Real-time Streaming**: Server-Sent Events for live updates during the coding process
- **GitHub Integration**: Automatic PR creation with enhanced descriptions
- **OpenTelemetry**: Comprehensive observability and telemetry tracking
- **Fallback Support**: Local sandbox fallback when cloud services are unavailable

## 🏗️ Architecture

- **FastAPI**: Streaming REST API with Server-Sent Events
- **Modal**: Cloud-based secure sandbox execution
- **Claude AI**: Intelligent code analysis and generation
- **GitHub API**: Automated pull request creation
- **OpenTelemetry**: Distributed tracing and observability

## 🛠️ Setup

### Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **GitHub Token**: Personal Access Token with repo permissions
3. **Anthropic API Key**: Claude AI access key

### Environment Variables

Create a `.env` file:

```bash
# GitHub Token for PR creation
GITHUB_TOKEN=your_github_personal_access_token

# Modal Configuration
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret

# Claude AI API Key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd tiny-backspace

# Install dependencies
pip install -r requirements.txt

# Set up Modal authentication
modal token new

# Run the application
python main.py
```

## 📡 API Usage

### Endpoint: `POST /code`

Send a JSON request to create an automated PR:

```bash
curl -X POST "http://localhost:8002/code" \
  -H "Content-Type: application/json" \
  -d '{
    "repoUrl": "https://github.com/username/repo",
    "prompt": "Add error handling to all functions"
  }'
```

### Response Format

The API streams Server-Sent Events with real-time updates:

```
data: {"type": "status", "message": "Initializing Claude-powered coding agent..."}

data: {"type": "sandbox", "message": "Creating Modal cloud sandbox..."}

data: {"type": "ai_analysis", "message": "Claude analyzing project structure..."}

data: {"type": "planned_change", "change": {...}}

data: {"type": "implementation", "message": "Implementing Claude-generated changes..."}

data: {"type": "completion", "message": "Process completed successfully!"}
```

## 🧠 AI Integration

### Claude AI Capabilities

- **Codebase Analysis**: Intelligent project structure analysis
- **Change Planning**: Smart code modification strategies
- **Code Generation**: Production-ready code creation
- **Error Handling**: Robust fallback mechanisms

### Example AI-Generated Changes

```python
# Claude can generate sophisticated code like:
class ErrorHandler:
    def __init__(self, service_name: str = "TinyBackspace"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
    
    def log_error(self, error: Exception, context: str = "Unknown"):
        # Comprehensive error logging implementation
        pass
```

## 🔒 Security & Sandboxing

### Modal Cloud Sandboxes

- **Isolation**: Each coding session runs in a separate, ephemeral container
- **Security**: No persistent storage, automatic cleanup
- **Scalability**: Cloud-native execution with automatic resource management
- **Observability**: Full telemetry and logging

### Fallback: Local Sandboxes

- Automatic fallback to local execution when Modal is unavailable
- Secure temporary directory isolation
- Process-level sandboxing

## 📊 Observability

### OpenTelemetry Integration

- **Distributed Tracing**: Track the entire coding workflow
- **Performance Metrics**: Monitor execution times and success rates
- **Error Tracking**: Comprehensive error logging and analysis
- **AI Decision Tracking**: Trace Claude's reasoning process

### Telemetry Features

```python
# Automatic tracing of key operations
telemetry.trace_analysis_phase(files_found, analysis_result)
telemetry.trace_planning_phase(changes)
telemetry.trace_implementation_phase(file_path, change_type, success)
telemetry.trace_git_operations("create_pr", branch_name, success)
```

## 🧪 Testing

### Local Testing

```bash
# Start the server
python main.py

# Test with a simple request
curl -X POST "http://localhost:8002/code" \
  -H "Content-Type: application/json" \
  -d '{
    "repoUrl": "https://github.com/yourusername/test-repo",
    "prompt": "Add a hello world function"
  }'
```

### Health Check

```bash
curl http://localhost:8002/health
# Response: {"status": "healthy"}
```

## 🚀 Deployment

### Public URL Access

Deploy to your preferred platform:

- **Railway**: Connect GitHub repo, set environment variables
- **Render**: Deploy from GitHub with automatic builds
- **Modal**: Deploy the entire application on Modal infrastructure
- **AWS/GCP/Azure**: Container deployment

### Environment Configuration

Ensure all environment variables are properly set in your deployment platform.

## 🎯 Why This Approach?

### Technology Choices

1. **Modal over E2B/Local**: Superior security, scalability, and ease of use
2. **Claude AI**: Most sophisticated code understanding and generation
3. **FastAPI**: Best-in-class async performance for streaming
4. **OpenTelemetry**: Industry-standard observability

### AI Agent Strategy

- **Focus on Infrastructure**: Robust sandboxing and PR creation over complex agent logic
- **Claude Integration**: Leverage best-in-class AI rather than building from scratch
- **Real-time Feedback**: Stream everything for transparency and debugging
- **Production Ready**: Error handling, fallbacks, and observability

## 📝 Implementation Notes

### Code Quality

- **Type Hints**: Full typing for better maintainability
- **Error Handling**: Comprehensive exception handling with graceful degradation
- **Async/Await**: Proper async patterns for performance
- **Separation of Concerns**: Clean architecture with distinct responsibilities

### Security Considerations

- **Token Management**: Secure GitHub token handling
- **Sandbox Isolation**: Proper isolation between coding sessions
- **Input Validation**: Proper validation of repository URLs and prompts
- **Rate Limiting**: Protection against abuse (can be added)

## 🔮 Future Enhancements

- **Multi-language Support**: Expand beyond Python
- **Advanced AI Models**: Integration with multiple AI providers
- **Collaboration Features**: Multi-user coding sessions
- **Advanced Git Operations**: Merge conflict resolution, rebasing
- **Custom Templates**: Pre-defined coding patterns and templates

---

**Built with ❤️ for the Backspace team**

*This project demonstrates modern AI-powered infrastructure with production-ready observability and security.*
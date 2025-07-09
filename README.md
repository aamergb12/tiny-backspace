# Tiny Backspace Coding Agent Submission

**Submitted by:** Aamer  
**Email:** [agbelhamidi@gmail.com]  
**Repository:** https://github.com/[aamergb12]/tiny-backspace

I chose a tools based approach using Claude's native Tools API after Tawsif said that was the industry standard.

The main difference I found is Claude directly executes file creation operations rather than just generating suggestions. With the Tools API, Claude can analyze codebases, create multiple files, and keep the same context across operations, overall it was more reliable then text parsing and allowed the agent to make complex projects.

I used Claude 3.5 Sonnet with Modal cloud containers for secure execution. The agent creates multiple files, including professional documentation, and auto creates GitHub pull requests.

## 🌐 Public URL

**Frontend:** Currently running locally at `http://localhost:5173`  
**Backend API:** Currently running locally at `http://localhost:8002`

*Note: For production deployment, the frontend can be deployed to Vercel/Netlify and backend to Railway/Render.*

## 🏃‍♂️ How to Run Locally

### Prerequisites
- Python 3.9+
- Node.js 20+
- Anthropic API key
- GitHub personal access token
- Modal account (for cloud sandboxing)

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/[your-username]/tiny-backspace
cd tiny-backspace

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add:
# ANTHROPIC_API_KEY=your_anthropic_api_key
# GITHUB_TOKEN=your_github_personal_access_token

# Set up Modal (for cloud sandboxing)
pip install modal
modal token new

# Start the backend
python3 main.py
```
Backend will run on `http://localhost:8002`

### Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
Frontend will run on `http://localhost:5173`

### Usage
1. Open `http://localhost:5173` in your browser
2. Enter a GitHub repository URL
3. Enter a prompt describing what you want to build
4. Watch the real-time progress as the AI agent generates code
5. Check GitHub for the automatically created pull request

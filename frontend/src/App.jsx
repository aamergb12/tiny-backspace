import { useState, useRef, useEffect } from "react";

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [prompt, setPrompt] = useState("");
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState('idle');
  const [prUrl, setPrUrl] = useState('');
  const logsEndRef = useRef(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const addLog = (type, message, timestamp = new Date().toLocaleTimeString()) => {
    setLogs(prev => [...prev, { 
      id: Date.now() + Math.random(), 
      type, 
      message, 
      timestamp 
    }]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!repoUrl || !prompt || isRunning) return;

    setIsRunning(true);
    setStatus('running');
    setLogs([]);
    setPrUrl('');
    
    addLog('status', '🚀 Initializing Tiny Backspace AI Agent...');

    try {
      const response = await fetch("http://localhost:8002/code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repoUrl, prompt }),
      });

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              addLog(data.type, data.message);

              if (data.pr_url) {
                setPrUrl(data.pr_url);
              }

              if (data.type === 'completion') {
                setStatus('success');
                addLog('success', '🎉 AI coding session completed successfully!');
              } else if (data.type === 'error') {
                setStatus('error');
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      addLog('error', `❌ Connection failed: ${error.message}`);
      setStatus('error');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative">
      {/* Floating decorative elements */}
      <div className="absolute top-20 left-20 text-purple-400 text-4xl opacity-20 animate-pulse">⭐</div>
      <div className="absolute top-40 right-32 text-blue-400 text-3xl opacity-30 animate-bounce">🌟</div>
      <div className="absolute bottom-32 left-16 text-indigo-400 text-5xl opacity-25 animate-pulse">✨</div>
      <div className="absolute bottom-20 right-20 text-purple-300 text-3xl opacity-20 animate-bounce">🌙</div>

      <div className="w-full max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-6xl md:text-8xl font-bold mb-4 title-glow flex items-center justify-center gap-4">
            <span className="text-6xl md:text-8xl">🚀</span>
            <span className="bg-gradient-to-r from-purple-400 via-blue-400 to-purple-600 bg-clip-text text-transparent">
              Tiny Backspace
            </span>
        </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            AI-powered coding agent that travels through the cosmos to analyze repositories, 
            generate intelligent code with Claude AI, and create stellar pull requests using Modal cloud sandboxes.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Main Input Panel */}
          <div className="glass-strong rounded-3xl p-8 relative overflow-hidden">
            <h2 className="text-2xl font-semibold mb-8 flex items-center gap-3">
              <span className="text-3xl">🌌</span>
              Mission Control
            </h2>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
                  <span className="text-lg">🔗</span>
                  GitHub Repository URL
                </label>
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repository"
                  className="cosmic-input w-full px-4 py-4 rounded-xl text-white placeholder-gray-400 focus:outline-none"
                  disabled={isRunning}
                />
                <p className="mt-2 text-sm text-gray-400 flex items-center gap-2">
                  <span>💫</span>
                  Must be a public GitHub repository
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
                  <span className="text-lg">💭</span>
                  AI Coding Mission
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Add error handling and logging to all functions, Create a REST API with authentication, Build a calculator with unit tests..."
                  rows={4}
                  className="cosmic-input w-full px-4 py-4 rounded-xl text-white placeholder-gray-400 focus:outline-none resize-none"
                  disabled={isRunning}
                />
                <p className="mt-2 text-sm text-gray-400 flex items-center gap-2">
                  <span>🎯</span>
                  Describe what you want the AI to implement
                </p>
              </div>

              <button
                onClick={handleSubmit}
                disabled={!repoUrl || !prompt || isRunning}
                className="cosmic-button w-full py-4 px-8 rounded-xl text-white font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
              >
                {isRunning ? (
                  <>
                    <span className="animate-spin text-2xl">🌀</span>
                    <span className="animate-pulse">AI Agent Working</span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl">🚀</span>
                    Launch AI Mission
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Live Mission Logs */}
          <div className="glass-strong rounded-3xl p-8 relative overflow-hidden">
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
              <span className="text-3xl">📡</span>
              Mission Telemetry
            </h2>

            <div className="cosmic-logs rounded-2xl p-4 h-96 overflow-y-auto font-mono text-sm">
              {logs.length === 0 ? (
                <div className="text-gray-400 text-center py-12 space-y-4">
                  <div className="text-4xl">🌌</div>
                  <div>Mission control is ready...</div>
                  <div className="text-xs opacity-60">Start a coding mission to see live telemetry data</div>
                </div>
              ) : (
                <div className="space-y-2">
                  {logs.map((log) => (
                    <div key={log.id} className="flex items-start gap-3 text-gray-300 hover:bg-white/5 rounded-lg p-2 transition-colors">
                      <span className="text-gray-500 text-xs mt-1 w-16 flex-shrink-0">
                        {log.timestamp}
                      </span>
                      <span className="break-words leading-relaxed">
                        {log.message}
                      </span>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
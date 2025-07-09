from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.sdk.resources import Resource
import json
import time
from typing import Dict, Any, Sequence, List
from datetime import datetime

# Enhanced Console Exporter with LangSmith-style formatting
class LangSmithStyleExporter(SpanExporter):
    """LangSmith-style telemetry exporter with rich context and AI-specific metrics"""
    
    def export(self, spans) -> SpanExportResult:
        for span in spans:
            duration_ms = (span.end_time - span.start_time) / 1_000_000
            
            # Better status detection
            is_successful = self._determine_span_success(span)
            status_display = '✅ SUCCESS' if is_successful else '❌ ERROR'
            
            # LangSmith-style header
            print(f"\n🔍 LANGSMITH TRACE: {span.name}")
            print(f"⏱️  Duration: {duration_ms:.2f}ms | Status: {status_display}")
            
            if span.attributes:
                print("📊 Context:")
                for key, value in span.attributes.items():
                    if key.startswith('ai.'):
                        print(f"   🤖 {key}: {value}")
                    elif key.startswith('git.'):
                        print(f"   🔧 {key}: {value}")
                    elif key.startswith('claude.'):
                        print(f"   🧠 {key}: {value}")
                    elif key.startswith('tools.'):
                        print(f"   🛠️  {key}: {value}")
                    else:
                        print(f"   📈 {key}: {value}")
            
            if span.events:
                print("📝 Events:")
                for event in span.events:
                    timestamp = datetime.fromtimestamp(event.timestamp / 1_000_000_000).strftime("%H:%M:%S.%f")[:-3]
                    print(f"   [{timestamp}] {event.name}")
                    if event.attributes:
                        for k, v in event.attributes.items():
                            print(f"      → {k}: {v}")
            
            print("─" * 60)
        return SpanExportResult.SUCCESS
    
    def _determine_span_success(self, span) -> bool:
        """Determine if a span was actually successful based on attributes"""
        # Check for explicit success indicators
        if hasattr(span, 'attributes') and span.attributes:
            # Git operations
            if span.attributes.get('git.success') is True:
                return True
            if span.attributes.get('git.success') is False:
                return False
                
            # Tool operations
            if span.attributes.get('tools.success') is True:
                return True
            if span.attributes.get('tools.success') is False:
                return False
                
            # Session operations
            if span.attributes.get('session.success') is True:
                return True
            if span.attributes.get('session.success') is False:
                return False
                
            # Claude operations with file_path (likely successful)
            if span.attributes.get('claude.file_path') and span.attributes.get('claude.file_path') != 'unknown':
                return True
                
            # Quality analysis (neutral operation, consider successful)
            if span.name == 'file_quality_analysis':
                return True
                
            # Analysis and planning phases (neutral, consider successful)
            if span.name in ['codebase_analysis', 'change_planning', 'ai_decision']:
                return True
        
        # Check OpenTelemetry status
        if hasattr(span, 'status') and span.status:
            return span.status.status_code.name == 'OK'
        
        # Default to success if no clear failure indicators
        return True
    
    def shutdown(self):
        pass

# Set up enhanced tracing
resource = Resource.create({
    "service.name": "tiny-backspace-coding-agent",
    "service.version": "2.0.0",
    "ai.framework": "claude-tools",
    "deployment.environment": "production"
})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Enhanced exporter
langsmith_exporter = LangSmithStyleExporter()
span_processor = BatchSpanProcessor(langsmith_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

class EnhancedCodingAgentTelemetry:
    """
    LangSmith-style telemetry that tracks AI reasoning, tool usage, 
    performance metrics, and decision-making processes
    """
    
    def __init__(self):
        self.tracer = trace.get_tracer("enhanced-coding-agent")
        self.current_span = None
        self.session_metrics = {}
    
    def start_coding_session(self, repo_url: str, prompt: str):
        """Start enhanced coding session with LangSmith-style context"""
        self.current_span = self.tracer.start_span(
            "ai_coding_session",
            attributes={
                "session.repo_url": repo_url,
                "session.user_prompt": prompt,
                "session.prompt_length": len(prompt),
                "ai.model": "claude-3.5-sonnet",
                "ai.framework": "anthropic-tools",
                "session.start_time": time.time(),
                "session.id": f"session_{int(time.time())}"
            }
        )
        
        # Add prompt analysis
        self.current_span.add_event("session_started", {
            "prompt_complexity": self._analyze_prompt_complexity(prompt),
            "expected_file_count": self._estimate_file_count(prompt),
            "project_type": self._detect_project_type(prompt)
        })
        
        return self.current_span
    
    def trace_claude_tool_execution(self, tool_name: str, input_data: dict, output_data: dict, duration_ms: float):
        """Track Claude's tool usage with detailed metrics"""
        with self.tracer.start_span("claude_tool_execution") as span:
            span.set_attributes({
                "claude.tool_name": tool_name,
                "claude.input_size": len(str(input_data)),
                "claude.output_size": len(str(output_data)),
                "claude.execution_time_ms": duration_ms,
                "claude.file_path": output_data.get('file_path', 'unknown'),
                "claude.content_length": len(output_data.get('content', '')),
                "tools.success": bool(output_data)
            })
            
            span.add_event("tool_executed", {
                "reasoning": output_data.get('reasoning', 'No reasoning provided'),
                "file_created": tool_name == "create_file",
                "content_preview": str(output_data.get('content', ''))[:100] + "..." if output_data.get('content') else ""
            })
    
    def trace_ai_decision_making(self, decision_point: str, context: dict, reasoning: str, confidence: float):
        """Track AI decision-making process like LangSmith"""
        with self.tracer.start_span("ai_decision") as span:
            span.set_attributes({
                "ai.decision_point": decision_point,
                "ai.reasoning_length": len(reasoning),
                "ai.confidence_score": confidence,
                "ai.context_size": len(str(context)),
                "ai.decision_timestamp": time.time()
            })
            
            span.add_event("decision_made", {
                "reasoning": reasoning,
                "context": json.dumps(context)[:500],  # Truncate for display
                "confidence_level": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
            })
    
    def trace_multi_turn_conversation(self, turn_number: int, prompt: str, response: str, tools_used: List[str]):
        """Track multi-turn Claude conversations"""
        with self.tracer.start_span("claude_conversation_turn") as span:
            span.set_attributes({
                "claude.turn_number": turn_number,
                "claude.prompt_tokens": len(prompt.split()),
                "claude.response_tokens": len(response.split()),
                "claude.tools_used_count": len(tools_used),
                "claude.tools_list": json.dumps(tools_used)
            })
            
            span.add_event("conversation_turn", {
                "turn": turn_number,
                "tools_called": tools_used,
                "response_preview": response[:200] + "..." if len(response) > 200 else response
            })
    
    def trace_performance_metrics(self, operation: str, metrics: dict):
        """Track performance metrics like LangSmith"""
        with self.tracer.start_span("performance_metrics") as span:
            span.set_attributes({
                f"perf.{operation}.duration_ms": metrics.get('duration_ms', 0),
                f"perf.{operation}.memory_mb": metrics.get('memory_mb', 0),
                f"perf.{operation}.cpu_percent": metrics.get('cpu_percent', 0),
                f"perf.{operation}.success_rate": metrics.get('success_rate', 1.0),
                "perf.operation_type": operation
            })
    
    def trace_file_generation_quality(self, file_path: str, content: str, metrics: dict):
        """Track file generation quality metrics"""
        with self.tracer.start_span("file_quality_analysis") as span:
            span.set_attributes({
                "quality.file_path": file_path,
                "quality.lines_of_code": len(content.split('\n')),
                "quality.character_count": len(content),
                "quality.has_docstrings": '"""' in content or "'''" in content,
                "quality.has_comments": '#' in content,
                "quality.complexity_score": metrics.get('complexity', 0),
                "quality.readability_score": metrics.get('readability', 0)
            })
            
            span.add_event("file_analyzed", {
                "file_type": file_path.split('.')[-1] if '.' in file_path else 'unknown',
                "content_preview": content[:150] + "..." if len(content) > 150 else content
            })
    
    def _analyze_prompt_complexity(self, prompt: str) -> str:
        """Analyze prompt complexity"""
        word_count = len(prompt.split())
        if word_count < 5:
            return "simple"
        elif word_count < 15:
            return "moderate"
        else:
            return "complex"
    
    def _estimate_file_count(self, prompt: str) -> int:
        """Estimate expected file count from prompt"""
        keywords = ['file', 'module', 'component', 'class', 'function']
        count = sum(1 for keyword in keywords if keyword in prompt.lower())
        return max(2, min(count + 2, 6))  # Between 2-6 files
    
    def trace_analysis_phase(self, files_found: list, analysis_result: dict):
        """Backward compatibility for old telemetry calls"""
        with self.tracer.start_span("codebase_analysis") as span:
            span.set_attributes({
                "analysis.files_count": len(files_found),
                "analysis.project_type": analysis_result.get("project_type", "unknown"),
                "analysis.primary_language": analysis_result.get("primary_language", "unknown")
            })
    
    def trace_planning_phase(self, planned_changes: list):
        """Backward compatibility for old telemetry calls"""
        with self.tracer.start_span("change_planning") as span:
            span.set_attributes({
                "planning.changes_count": len(planned_changes),
                "planning.strategy": "tools_based"
            })
    
    def trace_git_operations(self, operation: str, branch_name: str = None, success: bool = True):
        """Backward compatibility for old telemetry calls"""
        with self.tracer.start_span(f"git_{operation}") as span:
            attributes = {
                "git.operation": operation,
                "git.success": success
            }
            if branch_name:
                attributes["git.branch"] = branch_name
            span.set_attributes(attributes)
    
    def trace_error(self, error_type: str, error_message: str, context: dict = None):
        """Backward compatibility for old telemetry calls"""
        with self.tracer.start_span("error_occurred") as span:
            span.set_attributes({
                "error.type": error_type,
                "error.message": error_message
            })
            if context:
                span.add_event("Error context", context)
    
    def _analyze_prompt_complexity(self, prompt: str) -> str:
        """Analyze prompt complexity"""
        word_count = len(prompt.split())
        if word_count < 5:
            return "simple"
        elif word_count < 15:
            return "moderate"
        else:
            return "complex"
    
    def _estimate_file_count(self, prompt: str) -> int:
        """Estimate expected file count from prompt"""
        keywords = ['file', 'module', 'component', 'class', 'function']
        count = sum(1 for keyword in keywords if keyword in prompt.lower())
        return max(2, min(count + 2, 6))  # Between 2-6 files
    
    def _detect_project_type(self, prompt: str) -> str:
        """Detect project type from prompt"""
        prompt_lower = prompt.lower()
        if 'fastapi' in prompt_lower or 'api' in prompt_lower:
            return 'web_api'
        elif 'data science' in prompt_lower or 'analysis' in prompt_lower:
            return 'data_science'
        elif 'react' in prompt_lower or 'component' in prompt_lower:
            return 'frontend'
        elif 'game' in prompt_lower:
            return 'game'
        else:
            return 'general'
        """Detect project type from prompt"""
        prompt_lower = prompt.lower()
        if 'fastapi' in prompt_lower or 'api' in prompt_lower:
            return 'web_api'
        elif 'data science' in prompt_lower or 'analysis' in prompt_lower:
            return 'data_science'
        elif 'react' in prompt_lower or 'component' in prompt_lower:
            return 'frontend'
        elif 'game' in prompt_lower:
            return 'game'
        else:
            return 'general'
    
    def finish_coding_session(self, success: bool, pr_url: str = None):
        """Complete session with comprehensive metrics"""
        if self.current_span:
            end_time = time.time()
            start_time = self.current_span.attributes.get('session.start_time', end_time)
            total_duration = (end_time - start_time) * 1000  # Convert to ms
            
            self.current_span.set_attributes({
                "session.success": success,
                "session.total_duration_ms": total_duration,
                "session.pr_created": bool(pr_url),
                "session.end_time": end_time
            })
            
            if pr_url:
                self.current_span.set_attribute("session.pr_url", pr_url)
            
            # Add final session summary
            self.current_span.add_event("session_completed", {
                "outcome": "success" if success else "failure",
                "total_time_seconds": total_duration / 1000,
                "pr_generated": bool(pr_url)
            })
            
            self.current_span.end()

# Global enhanced telemetry instance
enhanced_telemetry = EnhancedCodingAgentTelemetry()

# Backward compatibility - create alias for old telemetry
telemetry = enhanced_telemetry
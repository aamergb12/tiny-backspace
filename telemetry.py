from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.sdk.resources import Resource
import json
from typing import Dict, Any, Sequence

# Custom Console Exporter (since the package doesn't exist)
class SimpleConsoleExporter(SpanExporter):
    """Simple console exporter for development debugging"""
    
    def export(self, spans) -> SpanExportResult:
        for span in spans:
            print(f"🔍 TRACE: {span.name} | Duration: {(span.end_time - span.start_time) / 1_000_000:.2f}ms")
            if span.attributes:
                for key, value in span.attributes.items():
                    print(f"   📊 {key}: {value}")
            if span.events:
                for event in span.events:
                    print(f"   📝 Event: {event.name}")
        return SpanExportResult.SUCCESS
    
    def shutdown(self):
        pass

# Set up tracing
resource = Resource.create({"service.name": "tiny-backspace-coding-agent"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Simple console exporter for development (shows traces in terminal)
console_exporter = SimpleConsoleExporter()
span_processor = BatchSpanProcessor(console_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

class CodingAgentTelemetry:
    """
    Telemetry wrapper that tracks the coding agent's thinking process
    and decision-making in real-time
    """
    
    def __init__(self):
        self.tracer = trace.get_tracer("coding-agent")
        self.current_span = None
    
    def start_coding_session(self, repo_url: str, prompt: str):
        """Start a new coding session trace"""
        self.current_span = self.tracer.start_span(
            "coding_session",
            attributes={
                "repo.url": repo_url,
                "user.prompt": prompt,
                "agent.version": "1.0.0"
            }
        )
        return self.current_span
    
    def trace_analysis_phase(self, files_found: list, analysis_result: dict):
        """Track the codebase analysis phase"""
        with self.tracer.start_span("codebase_analysis") as span:
            span.set_attributes({
                "analysis.files_count": len(files_found),
                "analysis.languages_detected": json.dumps(analysis_result.get("languages", [])),
                "analysis.complexity_score": analysis_result.get("complexity", 0)
            })
            span.add_event("Analysis completed", {
                "files_analyzed": len(files_found),
                "patterns_found": json.dumps(analysis_result.get("patterns", []))
            })
    
    def trace_planning_phase(self, planned_changes: list):
        """Track the AI planning and decision-making process"""
        with self.tracer.start_span("change_planning") as span:
            span.set_attributes({
                "planning.changes_count": len(planned_changes),
                "planning.strategy": "append_to_readme"  # Will be dynamic later
            })
            
            for i, change in enumerate(planned_changes):
                span.add_event(f"Planned change {i+1}", {
                    "change.type": change.get("type", "unknown"),
                    "change.file": change.get("file", "unknown"),
                    "change.description": change.get("description", "")
                })
    
    def trace_implementation_phase(self, file_path: str, change_type: str, success: bool):
        """Track individual file changes and their success/failure"""
        with self.tracer.start_span("file_implementation") as span:
            span.set_attributes({
                "implementation.file": file_path,
                "implementation.change_type": change_type,
                "implementation.success": success
            })
            
            if success:
                span.add_event("File modified successfully")
            else:
                span.add_event("File modification failed")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
    
    def trace_git_operations(self, operation: str, branch_name: str = None, success: bool = True):
        """Track git operations (branch creation, commits, pushes)"""
        with self.tracer.start_span(f"git_{operation}") as span:
            attributes = {
                "git.operation": operation,
                "git.success": success
            }
            if branch_name:
                attributes["git.branch"] = branch_name
                
            span.set_attributes(attributes)
            
            if not success:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
    
    def trace_ai_decision(self, decision_type: str, input_data: dict, output_data: dict):
        """Track AI decision-making process and reasoning"""
        with self.tracer.start_span("ai_decision") as span:
            span.set_attributes({
                "ai.decision_type": decision_type,
                "ai.input_tokens": len(str(input_data)),
                "ai.output_tokens": len(str(output_data))
            })
            
            span.add_event("AI decision made", {
                "reasoning": json.dumps(output_data.get("reasoning", "No reasoning provided")),
                "confidence": output_data.get("confidence", 0.5)
            })
    
    def trace_error(self, error_type: str, error_message: str, context: dict = None):
        """Track errors and failures for debugging"""
        with self.tracer.start_span("error_occurred") as span:
            span.set_attributes({
                "error.type": error_type,
                "error.message": error_message
            })
            
            if context:
                span.add_event("Error context", context)
            
            span.set_status(trace.Status(trace.StatusCode.ERROR))
    
    def finish_coding_session(self, success: bool, pr_url: str = None):
        """Complete the coding session trace"""
        if self.current_span:
            self.current_span.set_attributes({
                "session.success": success,
                "session.pr_created": bool(pr_url)
            })
            
            if pr_url:
                self.current_span.set_attribute("session.pr_url", pr_url)
            
            self.current_span.end()

# Global telemetry instance
telemetry = CodingAgentTelemetry()
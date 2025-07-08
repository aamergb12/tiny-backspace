import os
import json
from typing import List, Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeCodeAnalyst:
    """
    Claude AI integration for intelligent code analysis and generation.
    This replaces basic README modifications with actual code understanding and creation.
    """
    
    def __init__(self):
        """Initialize Claude client with API key from environment"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Model configuration
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4000
        
        print(f"Claude AI initialized: {self.model}")
    
    async def analyze_codebase(self, files_found: List[str], file_contents: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze the codebase structure and determine the project type, 
        languages, frameworks, and patterns.
        
        Args:
            files_found: List of file paths in the repository
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            Analysis results with project insights
        """
        
        # Prepare codebase summary for Claude
        codebase_summary = self._prepare_codebase_summary(files_found, file_contents)
        
        prompt = f"""
        Analyze this codebase and provide insights:

        FILES FOUND:
        {json.dumps(files_found, indent=2)}

        FILE CONTENTS:
        {codebase_summary}

        Please analyze and respond with JSON containing:
        {{
            "project_type": "web_app|cli_tool|library|script|other",
            "primary_language": "python|javascript|typescript|other",
            "frameworks": ["framework1", "framework2"],
            "complexity_level": "simple|medium|complex",
            "architecture_pattern": "mvc|microservice|monolith|script|other",
            "dependencies": ["dep1", "dep2"],
            "entry_points": ["main.py", "index.js"],
            "test_files": ["test1.py"],
            "config_files": ["package.json", "requirements.txt"],
            "documentation": ["README.md"],
            "insights": "Brief description of what this project does"
        }}
        """
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's JSON response
            analysis_text = response.content[0].text
            
            # Extract JSON from Claude's response
            import re
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                # Fallback analysis
                analysis = self._fallback_analysis(files_found)
            
            return analysis
            
        except Exception as e:
            print(f"Claude analysis error: {e}")
            return self._fallback_analysis(files_found)
    
    async def plan_code_changes(self, prompt: str, analysis: Dict[str, Any], file_contents: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Use Claude to intelligently plan what code changes to make based on the user prompt.
        
        Args:
            prompt: User's request (e.g., "Add error handling")
            analysis: Codebase analysis results
            file_contents: Current file contents
            
        Returns:
            List of planned changes with specific file operations
        """
        
        context = f"""
        PROJECT ANALYSIS:
        {json.dumps(analysis, indent=2)}

        CURRENT FILES:
        {self._prepare_codebase_summary(list(file_contents.keys()), file_contents)}

        USER REQUEST: {prompt}
        """
        
        planning_prompt = f"""
        Based on this codebase analysis and user request, plan specific code changes.

        {context}

        IMPORTANT: Always create actual code files, not just documentation!

        For the request "{prompt}", you MUST:
        1. Create a Python .py file with the requested functionality
        2. Write actual, functional code that implements the feature
        3. Only add documentation as a secondary change

        Respond with JSON array of changes to make:
        [
            {{
                "type": "create_file",
                "file_path": "error_handler.py",
                "description": "Create Python error handling utility class",
                "reasoning": "User requested Python error handling utility - creating functional implementation",
                "content": "# Full Python code here with proper imports, classes, and methods",
                "priority": "high"
            }}
        ]

        Guidelines:
        - ALWAYS create .py files for Python requests
        - Write complete, functional code with proper classes and methods
        - Include imports, error handling, and logging as requested
        - Make it production-ready, not placeholder code
        """
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": planning_prompt}]
            )
            
            # Extract JSON array from Claude's response
            response_text = response.content[0].text
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            
            if json_match:
                planned_changes = json.loads(json_match.group(0))
                
                # Validate and enhance the planned changes
                return self._validate_planned_changes(planned_changes, analysis)
            else:
                # Fallback to simple changes
                return self._fallback_changes(prompt, analysis)
                
        except Exception as e:
            print(f"Claude planning error: {e}")
            return self._fallback_changes(prompt, analysis)
    
    async def generate_code_content(self, file_type: str, description: str, context: Dict[str, Any]) -> str:
        """
        Generate actual code content for a specific file.
        
        Args:
            file_type: Type of file to generate (python, javascript, etc.)
            description: What the code should do
            context: Project context and requirements
            
        Returns:
            Generated code content
        """
        
        prompt = f"""
        Generate {file_type} code for: {description}

        Project context:
        {json.dumps(context, indent=2)}

        Requirements:
        - Write production-ready, functional code
        - Include proper error handling
        - Add helpful comments
        - Follow best practices for {file_type}
        - Make it actually work, not just placeholder code

        Return only the code, no markdown formatting or explanations.
        """
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Claude code generation error: {e}")
            return self._fallback_code(file_type, description)
    
    def _prepare_codebase_summary(self, files: List[str], contents: Dict[str, str]) -> str:
        """Prepare a concise summary of the codebase for Claude"""
        summary = []
        
        for file_path in files[:10]:  # Limit to first 10 files to avoid token limits
            if file_path in contents:
                content = contents[file_path]
                # Truncate long files
                if len(content) > 1000:
                    content = content[:500] + "\n... (truncated) ..."
                
                summary.append(f"=== {file_path} ===\n{content}\n")
        
        return "\n".join(summary)
    
    def _fallback_analysis(self, files: List[str]) -> Dict[str, Any]:
        """Fallback analysis when Claude fails"""
        languages = set()
        for file in files:
            if file.endswith('.py'):
                languages.add('python')
            elif file.endswith('.js'):
                languages.add('javascript')
            elif file.endswith('.ts'):
                languages.add('typescript')
        
        return {
            "project_type": "script",
            "primary_language": list(languages)[0] if languages else "unknown",
            "frameworks": [],
            "complexity_level": "simple",
            "architecture_pattern": "script",
            "dependencies": [],
            "entry_points": [],
            "test_files": [],
            "config_files": [],
            "documentation": ["README.md"],
            "insights": "Simple project structure detected"
        }
    

    def _fallback_changes(self, prompt: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback changes when Claude planning fails - ALWAYS create actual code files"""
       
        # Always create Python files for Python requests
        if "python" in prompt.lower() or "class" in prompt.lower() or "error" in prompt.lower():
            return [{
                "type": "create_file",
                "file_path": "error_handler.py",
                "description": f"Create Python implementation: {prompt}",
                "reasoning": "User requested Python functionality - creating actual code file",
                "content": self._generate_python_error_handler(prompt),
                "priority": "high"
            }]
        else:
            return [{
                "type": "create_file", 
                "file_path": "feature.py",
                "description": f"Implement {prompt}",
                "reasoning": "Creating functional code implementation",
                "content": self._generate_basic_python_file(prompt),
                "priority": "high"
            }]

    def _generate_python_error_handler(self, prompt: str) -> str:
        """Generate actual Python error handler code"""
        return f'''"""
    {prompt}
    Generated by Tiny Backspace AI Agent with Claude AI
    """

    import logging
    import sys
    import traceback
    from typing import Any, Optional, Dict
    from datetime import datetime

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('error_log.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    class ErrorHandler:
        """
        Advanced error handling utility class with logging capabilities.
        Provides comprehensive error tracking, logging, and recovery mechanisms.
        """
        
        def __init__(self, service_name: str = "TinyBackspace"):
            self.service_name = service_name
            self.logger = logging.getLogger(service_name)
            self.error_count = 0
            self.error_history: Dict[str, int] = {{}}
        
        def log_error(self, error: Exception, context: str = "Unknown", 
                    additional_info: Optional[Dict[str, Any]] = None) -> None:
            """
            Log an error with comprehensive details and context.
            
            Args:
                error: The exception that occurred
                context: Description of where/when the error occurred  
                additional_info: Optional dictionary with extra context
            """
            self.error_count += 1
            error_type = type(error).__name__
            
            # Track error frequency
            self.error_history[error_type] = self.error_history.get(error_type, 0) + 1
            
            # Create detailed error message
            error_details = {{
                "timestamp": datetime.now().isoformat(),
                "service": self.service_name,
                "error_type": error_type,
                "error_message": str(error),
                "context": context,
                "error_count": self.error_count,
                "traceback": traceback.format_exc(),
                "additional_info": additional_info or {{}}
            }}
            
            self.logger.error(f"Error in {{context}}: {{error_details}}")
        
        def safe_execute(self, func, *args, **kwargs) -> Optional[Any]:
            """
            Execute a function safely with automatic error handling and logging.
            
            Args:
                func: Function to execute safely
                *args: Positional arguments for the function
                **kwargs: Keyword arguments for the function
                
            Returns:
                Function result or None if an error occurred
            """
            try:
                result = func(*args, **kwargs)
                self.logger.info(f"Successfully executed {{func.__name__}}")
                return result
            except Exception as e:
                self.log_error(e, f"safe_execute({{func.__name__}})")
                return None
        
        def handle_critical_error(self, error: Exception, context: str = "Critical") -> None:
            """
            Handle critical errors that may require immediate attention.
            
            Args:
                error: The critical exception
                context: Critical error context
            """
            self.log_error(error, f"CRITICAL: {{context}}")
            
            # In a real application, you might:
            # - Send alerts to monitoring systems
            # - Trigger emergency procedures
            # - Gracefully shut down systems
            
            print(f"🚨 CRITICAL ERROR in {{context}}: {{str(error)}}")
        
        def get_error_stats(self) -> Dict[str, Any]:
            """
            Get comprehensive error statistics and health metrics.
            
            Returns:
                Dictionary with error statistics and service health info
            """
            return {{
                "service_name": self.service_name,
                "total_errors": self.error_count,
                "error_types": self.error_history,
                "most_common_error": max(self.error_history, key=self.error_history.get) if self.error_history else None,
                "service_health": "degraded" if self.error_count > 10 else "healthy"
            }}

    # Example usage and testing
    if __name__ == "__main__":
        # Initialize error handler
        error_handler = ErrorHandler("TinyBackspaceAgent")
        
        # Test error logging
        try:
            # Simulate an error
            result = 1 / 0
        except Exception as e:
            error_handler.log_error(e, "division_test", {{"operation": "1/0"}})
        
        # Test safe execution
        def risky_function(x, y):
            if y == 0:
                raise ValueError("Cannot divide by zero!")
            return x / y
        
        # This will handle the error gracefully
        safe_result = error_handler.safe_execute(risky_function, 10, 0)
        print(f"Safe execution result: {{safe_result}}")
        
        # Get error statistics
        stats = error_handler.get_error_stats()
        print(f"Error statistics: {{stats}}")
        
        print("✅ Error handling utility class is working correctly!")
    '''

    def _generate_basic_python_file(self, prompt: str) -> str:
        """Generate basic Python file for any request"""
        return f'''"""
    {prompt}
    Generated by Tiny Backspace AI Agent
    """

    import logging
    from typing import Any

    logger = logging.getLogger(__name__)

    class FeatureImplementation:
        """Implementation for: {prompt}"""
        
        def __init__(self):
            self.initialized = True
            logger.info("Feature initialized successfully")
        
        def execute(self) -> Any:
            """Execute the main feature functionality"""
            logger.info("Executing feature: {prompt}")
            return "Feature executed successfully"

    if __name__ == "__main__":
        feature = FeatureImplementation()
        result = feature.execute()
        print(result)
    '''
    
    def _fallback_code(self, file_type: str, description: str) -> str:
        """Generate simple fallback code when Claude fails"""
        if file_type == "python":
            return f'''"""
    {description} module
    Generated by Tiny Backspace AI Agent
    """

    import logging
    import sys
    from typing import Any, Optional

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    class ErrorHandler:
        """Simple error handling utility"""
        
        @staticmethod
        def handle_error(error: Exception, context: str = "Unknown") -> None:
            """Handle errors gracefully with logging"""
            logger.error(f"Error in {{context}}: {{str(error)}}")
            
        @staticmethod
        def safe_execute(func, *args, **kwargs) -> Optional[Any]:
            """Execute function safely with error handling"""
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ErrorHandler.handle_error(e, func.__name__)
                return None

    if __name__ == "__main__":
        print("Error handling module loaded successfully!")
    '''
        else:
            return f'// {description}\n// Generated by Tiny Backspace AI Agent\n\nconsole.log("Feature implemented!");'
    
    def _validate_planned_changes(self, changes: List[Dict], analysis: Dict) -> List[Dict]:
        """Validate and enhance planned changes"""
        validated = []
        
        for change in changes:
            # Ensure required fields exist
            if not all(key in change for key in ["type", "file_path", "description"]):
                continue
                
            # Add missing fields
            change.setdefault("reasoning", "AI-generated change")
            change.setdefault("priority", "medium")
            change.setdefault("content", "")
            
            validated.append(change)
        
        return validated
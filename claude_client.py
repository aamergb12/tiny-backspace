import os
import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeCodeAnalyst:
    """
    True tools implementation - Claude can directly execute actions
    instead of just planning them.
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
        
        # Store file changes for execution
        self.planned_files = []
        self.analysis_result = {}
        self.current_sandbox = None  # Store current sandbox reference
        
        # Define tools that Claude can actually execute
        self.tools = [
            {
                "name": "analyze_codebase",
                "description": "Analyze the structure and content of a codebase",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_type": {"type": "string"},
                        "primary_language": {"type": "string"}, 
                        "complexity_level": {"type": "string"},
                        "frameworks": {"type": "array", "items": {"type": "string"}},
                        "insights": {"type": "string"}
                    },
                    "required": ["project_type", "primary_language", "complexity_level", "insights"]
                }
            },
            {
                "name": "create_file",
                "description": "Create a new file with specified content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["file_path", "content", "description"]
                }
            },
            {
                "name": "modify_file", 
                "description": "Modify an existing file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["file_path", "content", "description"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "file_path": {"type": "string"}
                    },
                    "required": ["file_path"]
                }
            }
        ]
        
        print(f"Claude AI initialized with executable tools: {self.model}")
    
    async def execute_coding_request(self, prompt: str, files_found: List[str], file_contents: Dict[str, str], sandbox) -> List[Dict[str, Any]]:
        """
        True tools approach - Claude analyzes, plans, and executes all in one workflow
        """
        
        # Store sandbox reference for tool execution
        self.current_sandbox = sandbox
        
        codebase_summary = self._prepare_codebase_summary(files_found, file_contents)
        
        # Enhanced system prompt that encourages multiple file creation
        system_prompt = """You are an expert coding assistant with access to tools that can analyze codebases and create/modify files.

IMPORTANT: You MUST create multiple separate files for a complete implementation. Never put everything in one file.

Your workflow should be:
1. Use analyze_codebase tool to understand the project
2. Use create_file tool multiple times to create separate files for different concerns
3. Follow proper software architecture with separation of concerns
4. Create at least 3-5 files for any substantial request

For a Python calculator project, you should create:
- main.py (entry point)
- calculator.py (Calculator class)
- operations.py (math operations)
- utils.py (helper functions)
- README.md (documentation)

Always use multiple create_file tool calls - one for each file you need to create."""

        user_prompt = f"""
        I need you to implement: "{prompt}"

        Current codebase:
        FILES: {json.dumps(files_found, indent=2)}
        CONTENTS: {codebase_summary}

        REQUIREMENTS:
        1. First use analyze_codebase tool
        2. Then use create_file tool MULTIPLE TIMES to create separate files
        3. Create at least 3-4 different files with proper separation of concerns
        4. Each file should have a specific purpose
        5. Include proper documentation and comments

        Start by analyzing the codebase, then create multiple files one by one.
        """
        
        try:
            print(f"Sending request to Claude with {len(self.tools)} tools available")
            
            # First turn - let Claude analyze
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                tools=self.tools,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            print(f"Claude response received with {len(response.content)} content blocks")
            
            # Execute the tools Claude called in the first turn
            executed_changes = []
            messages = [{"role": "user", "content": user_prompt}]
            
            # Add assistant's response to conversation
            assistant_content = []
            for content_block in response.content:
                if content_block.type == "text":
                    assistant_content.append({"type": "text", "text": content_block.text})
                elif content_block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": content_block.id,
                        "name": content_block.name,
                        "input": content_block.input
                    })
                    
                    # Execute the tool
                    tool_result = await self._execute_tool(content_block, sandbox)
                    if tool_result:
                        executed_changes.append(tool_result)
            
            messages.append({"role": "assistant", "content": assistant_content})
            
            # Add tool results to conversation
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    if content_block.name == "analyze_codebase":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": "Analysis complete. Now create the calculator files."
                        })
            
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
                
                # Second turn - ask Claude to create the files
                follow_up_response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    tools=self.tools,
                    messages=messages + [{
                        "role": "user", 
                        "content": f"""Now create the actual implementation files for: "{prompt}"

IMPORTANT: Create files with names that are RELEVANT to the request "{prompt}".

For example:
- If it's about FastAPI → create main.py, auth.py, models.py, routes.py
- If it's about data science → create analysis.py, visualization.py, data_utils.py
- If it's about React → create App.jsx, components.jsx, utils.js

DO NOT create generic names like "calculator.py" unless specifically asked for a calculator.

Create 3-4 files with appropriate names using the create_file tool multiple times."""
                    }]
                )
                
                print(f"Follow-up response received with {len(follow_up_response.content)} content blocks")
                
                # Execute tools from second turn
                for content_block in follow_up_response.content:
                    if content_block.type == "tool_use":
                        print(f"Follow-up tool call: {content_block.name}")
                        tool_result = await self._execute_tool(content_block, sandbox)
                        if tool_result:
                            executed_changes.append(tool_result)
                
                # Third turn if we still don't have enough Python files
                python_files = [change for change in executed_changes if change.get('file_path', '').endswith('.py')]
                created_files = [change.get('file_path', '') for change in executed_changes]
                
                print(f"Created files so far: {created_files}")
                
                if len(python_files) < 3:
                    print(f"Only {len(python_files)} Python files created, requesting more relevant files...")
                    
                    # Ask Claude to create more files based on the original prompt
                    additional_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        tools=self.tools,
                        messages=[{
                            "role": "user", 
                            "content": f"""You created {len(python_files)} files so far: {created_files}

For the request: "{prompt}"

Please create 2-3 MORE files that are specifically relevant to this request:
1. Additional Python files with specific functionality
2. A comprehensive README.md that explains the project, setup instructions, and usage

Use create_file tool for each additional file with appropriate filenames and content.
Don't repeat the files you already created."""
                        }]
                    )
                    
                    for content_block in additional_response.content:
                        if content_block.type == "tool_use" and content_block.name == "create_file":
                            print(f"Additional file tool call: {content_block.name}")
                            tool_result = await self._execute_tool(content_block, sandbox)
                            if tool_result:
                                executed_changes.append(tool_result)
                                print(f"Successfully created additional file: {tool_result['file_path']}")
                
                # Always ensure README is created/updated
                readme_exists = any('README' in change.get('file_path', '').upper() for change in executed_changes)
                if not readme_exists:
                    print("No README found, creating comprehensive project documentation...")
                    
                    readme_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        tools=self.tools,
                        messages=[{
                            "role": "user", 
                            "content": f"""Update the existing README.md file for the project: "{prompt}"

The README should completely replace the existing content with:
- Project title and description  
- Features implemented
- Installation/setup instructions
- Usage examples
- File structure explanation
- Requirements/dependencies

Files created: {[change.get('file_path') for change in executed_changes]}

Use the modify_file tool with file_path="README.md" to replace the entire README content."""
                        }]
                    )
                    
                    for content_block in readme_response.content:
                        if content_block.type == "tool_use" and content_block.name in ["create_file", "modify_file"]:
                            print(f"README update tool call: {content_block.name}")
                            tool_result = await self._execute_tool(content_block, sandbox)
                            if tool_result:
                                executed_changes.append(tool_result)
                                print(f"Successfully updated README: {tool_result['file_path']}")
            
            print(f"Total executed changes: {len(executed_changes)}")
            
            # If no changes were made, use fallback
            if not executed_changes:
                print("No tool executions successful, using fallback")
                executed_changes = self._fallback_changes(prompt, {})
            
            return executed_changes
            
        except Exception as e:
            print(f"Claude tools execution error: {e}")
            return self._fallback_changes(prompt, {})
    
    async def _execute_tool(self, tool_call, sandbox) -> Optional[Dict[str, Any]]:
        """Execute a tool call that Claude made"""
        
        tool_name = tool_call.name
        tool_input = tool_call.input
        
        print(f"Executing tool: {tool_name} with input: {list(tool_input.keys())}")
        
        if tool_name == "analyze_codebase":
            # Store analysis for later use
            self.analysis_result = tool_input
            print(f"Claude analyzed project: {tool_input.get('project_type')} in {tool_input.get('primary_language')}")
            return None
            
        elif tool_name == "create_file":
            file_path = tool_input["file_path"]
            content = tool_input["content"]
            description = tool_input["description"]
            
            print(f"Claude creating file: {file_path} ({len(content)} chars)")
            
            # Actually create the file using sandbox
            workspace_id = getattr(sandbox, 'workspace_id', 'default')
            try:
                async for update in sandbox.write_file(file_path, content, workspace_id):
                    print(f"Sandbox write update: {update[:100]}...")
                print(f"Successfully created file: {file_path}")
            except Exception as e:
                print(f"Error creating file {file_path}: {e}")
                return None
            
            return {
                "type": "create_file",
                "file_path": file_path,
                "description": description,
                "reasoning": f"Claude created {file_path} using tools",
                "content": content,
                "priority": "high"
            }
            
        elif tool_name == "modify_file":
            file_path = tool_input["file_path"] 
            content = tool_input["content"]
            description = tool_input["description"]
            
            print(f"Claude modifying file: {file_path} ({len(content)} chars)")
            
            # Actually modify the file using sandbox
            workspace_id = getattr(sandbox, 'workspace_id', 'default')
            try:
                async for update in sandbox.write_file(file_path, content, workspace_id):
                    print(f"Sandbox modify update: {update[:100]}...")
                print(f"Successfully modified file: {file_path}")
            except Exception as e:
                print(f"Error modifying file {file_path}: {e}")
                return None
                
            return {
                "type": "modify_file",
                "file_path": file_path,
                "description": description,
                "reasoning": f"Claude modified {file_path} using tools",
                "content": content,
                "priority": "high"
            }
            
        elif tool_name == "read_file":
            file_path = tool_input["file_path"]
            
            # Read file using sandbox
            workspace_id = getattr(sandbox, 'workspace_id', 'default')
            try:
                content = await sandbox.read_file(file_path, workspace_id)
                print(f"Claude read file: {file_path} ({len(content)} chars)")
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
            
            return None  # Reading doesn't create a change
            
        return None
    
    # Backward compatibility methods for agent.py
    async def analyze_codebase_with_tools(self, files_found: List[str], file_contents: Dict[str, str]) -> Dict[str, Any]:
        """Backward compatibility - use the new tools approach"""
        # This will be called by the new execute_coding_request method
        return self.analysis_result or self._fallback_analysis(files_found)
    
    async def plan_code_changes_with_tools(self, prompt: str, analysis: Dict[str, Any], file_contents: Dict[str, str]) -> List[Dict[str, Any]]:
        """Backward compatibility - files are already created by tools"""
        return self.planned_files or self._fallback_changes(prompt, analysis)
    
    def _prepare_codebase_summary(self, files: List[str], contents: Dict[str, str]) -> str:
        """Prepare a concise summary of the codebase for Claude"""
        summary = []
        
        for file_path in files[:10]:
            if file_path in contents:
                content = contents[file_path]
                if len(content) > 1000:
                    content = content[:500] + "\n... (truncated) ..."
                summary.append(f"=== {file_path} ===\n{content}\n")
        
        return "\n".join(summary)
    
    def _fallback_analysis(self, files: List[str]) -> Dict[str, Any]:
        """Fallback analysis when Claude tools fail"""
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
            "insights": "Simple project structure detected"
        }
    
    def _fallback_changes(self, prompt: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Smart fallback changes that create files based on the actual prompt"""
        
        # Analyze the prompt to determine appropriate files
        prompt_lower = prompt.lower()
        
        if "fastapi" in prompt_lower or "web application" in prompt_lower:
            return [
                {
                    "type": "create_file",
                    "file_path": "main.py",
                    "description": f"FastAPI application entry point for {prompt}",
                    "reasoning": "Main FastAPI application file",
                    "content": f'"""FastAPI Application: {prompt}"""\n\nfrom fastapi import FastAPI\n\napp = FastAPI(title="{prompt}")\n\n@app.get("/")\ndef read_root():\n    return {{"message": "FastAPI application running"}}\n\nif __name__ == "__main__":\n    import uvicorn\n    uvicorn.run(app, host="0.0.0.0", port=8000)',
                    "priority": "high"
                },
                {
                    "type": "create_file",
                    "file_path": "auth.py",
                    "description": f"Authentication module for {prompt}",
                    "reasoning": "Authentication logic",
                    "content": f'"""Authentication module for {prompt}"""\n\nfrom fastapi import HTTPException, Depends\nfrom fastapi.security import HTTPBearer\n\nsecurity = HTTPBearer()\n\ndef authenticate_user(token: str = Depends(security)):\n    # Authentication logic here\n    if not token:\n        raise HTTPException(status_code=401, detail="Authentication required")\n    return {{"user": "authenticated"}}',
                    "priority": "high"
                }
            ]
        elif "data science" in prompt_lower or "analysis" in prompt_lower:
            return [
                {
                    "type": "create_file",
                    "file_path": "analysis.py",
                    "description": f"Data analysis module for {prompt}",
                    "reasoning": "Data analysis functionality",
                    "content": f'"""Data Analysis: {prompt}"""\n\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n\ndef load_data():\n    """Load and prepare data for analysis"""\n    pass\n\ndef analyze_data():\n    """Perform data analysis"""\n    pass\n\nif __name__ == "__main__":\n    print("Data analysis module ready")',
                    "priority": "high"
                },
                {
                    "type": "create_file",
                    "file_path": "visualization.py",
                    "description": f"Data visualization module for {prompt}",
                    "reasoning": "Visualization functionality",
                    "content": f'"""Data Visualization: {prompt}"""\n\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\ndef create_plots():\n    """Create data visualizations"""\n    pass\n\ndef save_charts():\n    """Save charts to files"""\n    pass',
                    "priority": "high"
                }
            ]
        elif "react" in prompt_lower or "component" in prompt_lower:
            return [
                {
                    "type": "create_file",
                    "file_path": "App.jsx",
                    "description": f"React application for {prompt}",
                    "reasoning": "Main React component",
                    "content": f'// React Application: {prompt}\nimport React from "react";\n\nfunction App() {{\n  return (\n    <div className="App">\n      <h1>{prompt}</h1>\n    </div>\n  );\n}}\n\nexport default App;',
                    "priority": "high"
                },
                {
                    "type": "create_file",
                    "file_path": "components.jsx",
                    "description": f"React components for {prompt}",
                    "reasoning": "Component library",
                    "content": f'// Components for {prompt}\nimport React from "react";\n\nexport const Button = ({{ children, onClick }}) => (\n  <button onClick={{onClick}}>{{children}}</button>\n);',
                    "priority": "high"
                }
            ]
        else:
            # Generic fallback based on prompt content
            return [
                {
                    "type": "create_file",
                    "file_path": "main.py",
                    "description": f"Main implementation for {prompt}",
                    "reasoning": "Primary implementation file",
                    "content": f'"""{prompt}"""\n\ndef main():\n    """Main function for {prompt}"""\n    print("Implementation ready")\n\nif __name__ == "__main__":\n    main()',
                    "priority": "high"
                },
                {
                    "type": "create_file",
                    "file_path": "utils.py",
                    "description": f"Utility functions for {prompt}",
                    "reasoning": "Helper utilities",
                    "content": f'"""Utilities for {prompt}"""\n\ndef helper_function():\n    """Helper function"""\n    pass',
                    "priority": "medium"
                }
            ]
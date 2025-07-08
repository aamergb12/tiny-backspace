import os
import json
import asyncio
from typing import AsyncGenerator, List, Dict
from sandbox import ModalSandbox, LocalSandbox
from claude_client import ClaudeCodeAnalyst
from dotenv import load_dotenv
from telemetry import telemetry

load_dotenv()

class CodingAgent:
    def __init__(self, use_local_sandbox: bool = False):
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        # Initialize Claude AI
        try:
            self.claude = ClaudeCodeAnalyst()
            print("Claude AI integration: ENABLED")
        except Exception as e:
            print(f"Claude AI integration: DISABLED ({e})")
            self.claude = None
        
        # Smart sandbox selection with Modal cloud
        if not use_local_sandbox:
            try:
                # Try to import modal and verify authentication
                import modal
                # Modal credentials are automatically loaded from ~/.modal.toml
                self.use_local_sandbox = False
                print("🔒 Modal cloud sandboxing: ENABLED (authenticated via ~/.modal.toml)")
            except ImportError:
                print("⚠️  Modal not installed, falling back to local sandbox")
                self.use_local_sandbox = True
            except Exception as e:
                print(f"⚠️  Modal setup failed: {str(e)[:100]}...")
                print("🔄 Falling back to Local sandbox for this session")
                self.use_local_sandbox = True
        else:
            self.use_local_sandbox = True
            print("💻 Local sandboxing: ENABLED")
        
        # Debug: Print token status
        print(f"GitHub token loaded: {'Yes' if self.github_token else 'No'}")
        if self.github_token:
            print(f"Token length: {len(self.github_token)}")
            
    async def process_coding_request(self, repo_url: str, prompt: str) -> AsyncGenerator[str, None]:
        """Main process that handles the entire coding workflow with Claude AI and telemetry"""
        
        # Start telemetry session
        session_span = telemetry.start_coding_session(repo_url, prompt)
        pr_url = None
        
        # Choose sandbox implementation
        sandbox_class = LocalSandbox if self.use_local_sandbox else ModalSandbox
        sandbox_type = "Local" if self.use_local_sandbox else "Modal Cloud"
        
        async with sandbox_class() as sandbox:
            try:
                # Step 1: Create workspace and clone repo
                yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing Claude-powered coding agent...', 'telemetry': {'phase': 'initialization', 'ai_enabled': bool(self.claude), 'sandbox': sandbox_type}})}\n\n"
                
                workspace_id = await sandbox.create_workspace(repo_url)
                
                # Stream repo cloning with telemetry
                async for update in sandbox.clone_repo(repo_url, workspace_id):
                    # Add telemetry context to each update
                    if '"type": "sandbox"' in update and 'cloned successfully' in update:
                        telemetry.trace_git_operations("clone", success=True)
                    yield update
                
                # Step 2: Enhanced codebase analysis with Claude
                yield f"data: {json.dumps({'type': 'analysis', 'message': f'Claude AI analyzing codebase in {sandbox_type} environment for: {prompt}', 'telemetry': {'phase': 'analysis', 'ai_powered': True, 'sandbox': sandbox_type}})}\n\n"
                
                # Get repository structure
                files_found = []
                async for update in sandbox.execute_command("find . -type f -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.json' -o -name '*.md' | head -20", workspace_id):
                    if '"type": "command_output"' in update:
                        import re
                        output_match = re.search(r'"output": "([^"]*)"', update)
                        if output_match:
                            files_found = [f.strip() for f in output_match.group(1).strip().split('\n') if f.strip()]
                    yield update
                
                # Read file contents for Claude analysis
                file_contents = {}
                important_files = [f for f in files_found if any(f.endswith(ext) for ext in ['.py', '.js', '.ts', '.json', '.md']) and len(f) < 100][:5]
                
                for file_path in important_files:
                    try:
                        content = await sandbox.read_file(file_path, workspace_id)
                        if not content.startswith("Error reading file"):
                            file_contents[file_path] = content
                    except:
                        pass
                
                # Claude-powered analysis
                if self.claude:
                    yield f"data: {json.dumps({'type': 'ai_analysis', 'message': 'Claude analyzing project structure and patterns...', 'telemetry': {'phase': 'ai_analysis', 'files_analyzed': len(file_contents)}})}\n\n"
                    
                    analysis_result = await self.claude.analyze_codebase(files_found, file_contents)
                    
                    project_type = analysis_result.get('project_type', 'unknown')
                    primary_lang = analysis_result.get('primary_language', 'unknown')
                    yield f"data: {json.dumps({'type': 'ai_insights', 'message': f'Project type: {project_type}, Language: {primary_lang}', 'analysis': analysis_result, 'telemetry': {'insights_generated': True}})}\n\n"
                else:
                    # Fallback analysis without Claude
                    analysis_result = {
                        "project_type": "script",
                        "primary_language": self._detect_primary_language(files_found),
                        "complexity_level": "simple"
                    }
                
                # Trace analysis phase
                telemetry.trace_analysis_phase(files_found, analysis_result)
                
                # Step 3: Claude-powered change planning
                yield f"data: {json.dumps({'type': 'planning', 'message': 'Claude AI planning intelligent code changes...', 'telemetry': {'phase': 'planning', 'ai_powered': bool(self.claude)}})}\n\n"
                
                if self.claude:
                    changes = await self.claude.plan_code_changes(prompt, analysis_result, file_contents)
                    
                    # Add reasoning to telemetry
                    for change in changes:
                        reasoning = change.get('reasoning', 'No reasoning provided')
                        yield f"data: {json.dumps({'type': 'ai_reasoning', 'message': f'Claude decided: {reasoning}', 'change': change, 'telemetry': {'ai_decision': True}})}\n\n"
                else:
                    changes = await self._fallback_plan_changes(prompt, workspace_id, sandbox)
                
                # Trace planning phase
                telemetry.trace_planning_phase(changes)
                
                for change in changes:
                    yield f"data: {json.dumps({'type': 'planned_change', 'change': change, 'telemetry': {'decision': 'change_planned', 'ai_generated': bool(self.claude)}})}\n\n"
                
                # Step 4: Implement Claude's planned changes
                yield f"data: {json.dumps({'type': 'implementation', 'message': 'Implementing Claude-generated changes...', 'telemetry': {'phase': 'implementation', 'changes_count': len(changes)}})}\n\n"
                
                for change in changes:
                    async for update in self._implement_claude_change(change, workspace_id, sandbox):
                        yield update
                
                # Step 5: Create branch and commit with enhanced commit message
                yield f"data: {json.dumps({'type': 'git', 'message': 'Creating feature branch...', 'telemetry': {'phase': 'git_operations'}})}\n\n"
                
                branch_name = f"feature/{prompt.lower().replace(' ', '-')[:50]}"
                async for update in sandbox.execute_command(f"git checkout -b {branch_name}", workspace_id):
                    yield update
                
                telemetry.trace_git_operations("create_branch", branch_name, True)
                
                # Add and commit changes with enhanced commit message
                async for update in sandbox.execute_command("git add .", workspace_id):
                    yield update
                
                # Create detailed commit message
                commit_message = f"feat: {prompt}\n\nGenerated by Claude AI:\n"
                for change in changes[:3]:  # Include up to 3 changes in commit message
                    commit_message += f"- {change.get('description', 'Code change')}\n"
                
                async for update in sandbox.execute_command(f'git commit -m "{commit_message}"', workspace_id):
                    yield update
                
                telemetry.trace_git_operations("commit", branch_name, True)
                
                # Step 6: Push and create PR with GitHub CLI
                print(f"DEBUG: GitHub token exists: {bool(self.github_token)}")
                if self.github_token:
                    print("DEBUG: Entering GitHub push section")
                    yield f"data: {json.dumps({'type': 'git', 'message': 'Setting up GitHub authentication...', 'telemetry': {'phase': 'github_integration'}})}\n\n"
                    
                    # Set git remote URL with token for authentication
                    repo_name = repo_url.split('/')[-2:]  # ['username', 'repo']
                    auth_url = f"https://{self.github_token}@github.com/{repo_name[0]}/{repo_name[1]}"
                    
                    async for update in sandbox.execute_command(f"git remote set-url origin {auth_url}", workspace_id):
                        yield update
                    
                    yield f"data: {json.dumps({'type': 'git', 'message': 'Pushing Claude-generated changes...', 'telemetry': {'phase': 'github_push'}})}\n\n"
                    
                    # Push branch
                    push_success = True
                    async for update in sandbox.execute_command(f"git push origin {branch_name}", workspace_id):
                        if '"type": "error"' in update:
                            push_success = False
                        yield update
                    
                    telemetry.trace_git_operations("push", branch_name, push_success)
                    
                    # Authenticate GitHub CLI and create PR
                    
                    # Create enhanced PR with Claude details
                    pr_title = f"🤖 Claude AI: {prompt}"
                    pr_body = f"""# 🤖 Claude AI Generated Changes

**User Request:** {prompt}

## 🔍 Analysis Results
- **Project Type:** {analysis_result.get('project_type', 'Unknown')}
- **Primary Language:** {analysis_result.get('primary_language', 'Unknown')}
- **Complexity:** {analysis_result.get('complexity_level', 'Unknown')}
- **Sandbox:** {sandbox_type}

## 🛠️ Changes Made
"""
                    
                    for i, change in enumerate(changes, 1):
                        pr_body += f"{i}. **{change.get('file_path', 'Unknown file')}**: {change.get('description', 'No description')}\\n"
                        if change.get('reasoning'):
                            pr_body += f"   - *Reasoning: {change.get('reasoning')}*\\n"
                    
                    pr_body += f"""
## 🚀 Generated by Tiny Backspace AI Agent
- **AI Model:** Claude 3 Sonnet
- **Sandbox:** {sandbox_type}
- **Telemetry:** Full observability enabled
- **Timestamp:** {asyncio.get_event_loop().time()}

*This PR was automatically generated with intelligent code analysis and planning.*
"""
                    
                    # Create PR using GitHub CLI
                    yield f"data: {json.dumps({'type': 'git', 'message': 'Creating pull request...', 'telemetry': {'phase': 'create_pr'}})}\n\n"
                    
                    async for update in sandbox.execute_command_with_env(
                        f'gh pr create --title "{pr_title}" --body "{pr_body}" --head {branch_name}',
                        workspace_id,
                        {"GITHUB_TOKEN": self.github_token}
                    ):
                        # Extract PR URL from output for telemetry
                        if '"type": "command_output"' in update and 'github.com' in update:
                            import re
                            url_match = re.search(r'https://github\.com/[^\s"]+', update)
                            if url_match:
                                pr_url = url_match.group(0)
                        yield update
                    
                    telemetry.trace_git_operations("create_pr", branch_name, bool(pr_url))
                else:
                    print("DEBUG: No GitHub token found, skipping push")
                    yield f"data: {json.dumps({'type': 'info', 'message': 'No GitHub token configured, skipping PR creation', 'telemetry': {'phase': 'skipped_github'}})}\n\n"
                
                # Final success message with Claude attribution
                final_message = f"Claude AI coding process completed successfully in {sandbox_type}!" if self.claude else f"Coding process completed successfully in {sandbox_type}!"
                yield f"data: {json.dumps({'type': 'completion', 'message': final_message, 'telemetry': {'phase': 'completion', 'pr_url': pr_url, 'ai_powered': bool(self.claude), 'changes_implemented': len(changes), 'sandbox': sandbox_type}})}\n\n"
                
                # Mark session as successful
                telemetry.finish_coding_session(True, pr_url)
                
            except Exception as e:
                # Trace the error
                telemetry.trace_error("coding_session_error", str(e), {"repo_url": repo_url, "prompt": prompt, "sandbox": sandbox_type})
                yield f"data: {json.dumps({'type': 'error', 'message': f'Process failed: {str(e)}', 'telemetry': {'phase': 'error', 'error_type': type(e).__name__, 'sandbox': sandbox_type}})}\n\n"
                telemetry.finish_coding_session(False)
            
            finally:
                # Clean up workspace - commented out for testing
                # await sandbox.cleanup_workspace(workspace_id)
                pass
    
    def _detect_primary_language(self, files: List[str]) -> str:
        """Detect primary programming language from file extensions"""
        language_counts = {}
        for file in files:
            if file.endswith('.py'):
                language_counts['python'] = language_counts.get('python', 0) + 1
            elif file.endswith('.js'):
                language_counts['javascript'] = language_counts.get('javascript', 0) + 1
            elif file.endswith('.ts'):
                language_counts['typescript'] = language_counts.get('typescript', 0) + 1
        
        if language_counts:
            return max(language_counts, key=language_counts.get)
        return "unknown"
    
    async def _fallback_plan_changes(self, prompt: str, workspace_id: str, sandbox) -> List[Dict]:
        """Fallback planning when Claude is not available"""
        return [
            {
                "type": "modify_file",
                "file_path": "README.md",
                "description": f"Add section about: {prompt}",
                "reasoning": "Basic documentation update as fallback",
                "content": f"\n\n## {prompt}\n\nThis feature was added by Tiny Backspace.\n",
                "priority": "medium"
            }
        ]
    
    async def _implement_claude_change(self, change: Dict, workspace_id: str, sandbox) -> AsyncGenerator[str, None]:
        """Implement a Claude-planned change with enhanced logic"""
        
        change_type = change.get("type", "unknown")
        file_path = change.get("file_path", "unknown")
        description = change.get("description", "No description")
        content = change.get("content", "")
        
        yield f"data: {json.dumps({'type': 'file_change', 'message': f'{change_type}: {file_path} - {description}', 'telemetry': {'file': file_path, 'operation': change_type, 'ai_generated': True}})}\n\n"
        
        success = True
        try:
            if change_type == "create_file":
                # Create new file with Claude-generated content
                async for update in sandbox.write_file(file_path, content, workspace_id):
                    yield update
                    
            elif change_type == "modify_file":
                if file_path == "README.md":
                    # Append to README
                    current_content = await sandbox.read_file(file_path, workspace_id)
                    if current_content.startswith("Error reading file"):
                        current_content = f"# {workspace_id.replace('local_', '').replace('modal_', '').replace('-', ' ').title()}\n\n"
                    
                    new_content = current_content + content
                    async for update in sandbox.write_file(file_path, new_content, workspace_id):
                        yield update
                else:
                    # For other files, use Claude's content directly
                    async for update in sandbox.write_file(file_path, content, workspace_id):
                        yield update
                        
            elif change_type == "delete_file":
                # Delete file (careful with this!)
                async for update in sandbox.execute_command(f"rm -f {file_path}", workspace_id):
                    yield update
            
        except Exception as e:
            success = False
            telemetry.trace_error("file_implementation_error", str(e), {"file": file_path, "change_type": change_type})
            yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to {change_type} {file_path}: {str(e)}', 'telemetry': {'error': True}})}\n\n"
        
        # Trace implementation success/failure
        telemetry.trace_implementation_phase(file_path, change_type, success)
        
        yield f"data: {json.dumps({'type': 'change_complete', 'file': file_path, 'success': success, 'telemetry': {'status': 'completed', 'ai_generated': True}})}\n\n"

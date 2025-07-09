import os
import json
import asyncio
import time
from typing import AsyncGenerator, List, Dict
from sandbox import ModalSandbox, LocalSandbox
from claude_client import ClaudeCodeAnalyst
from dotenv import load_dotenv
from telemetry import telemetry, enhanced_telemetry

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
        session_span = enhanced_telemetry.start_coding_session(repo_url, prompt)
        pr_url = None
        
        # Choose sandbox implementation
        sandbox_class = LocalSandbox if self.use_local_sandbox else ModalSandbox
        sandbox_type = "Local" if self.use_local_sandbox else "Modal Cloud"
        
        async with sandbox_class() as sandbox:
            try:
                # Step 1: Create workspace and clone repo
                yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing Claude-powered coding agent...', 'telemetry': {'phase': 'initialization', 'ai_enabled': bool(self.claude), 'sandbox': sandbox_type}})}\n\n"
                
                workspace_id = await sandbox.create_workspace(repo_url)
                # Store workspace_id in sandbox for tool access
                sandbox.workspace_id = workspace_id
                
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
                
                # Step 3: Use Claude's new tools-based approach
                if self.claude:
                    yield f"data: {json.dumps({'type': 'ai_analysis', 'message': 'Claude executing complete workflow with tools...', 'telemetry': {'phase': 'tools_execution', 'files_analyzed': len(file_contents), 'tools_enabled': True}})}\n\n"
                    
                    # Use the new tools-based method that does everything in one go
                    start_time = time.time()
                    executed_changes = await self.claude.execute_coding_request(prompt, files_found, file_contents, sandbox)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Enhanced telemetry for Claude tool execution
                    for change in executed_changes:
                        enhanced_telemetry.trace_claude_tool_execution(
                            tool_name=change.get('type', 'unknown'),
                            input_data={'file_path': change.get('file_path', ''), 'prompt': prompt},
                            output_data=change,
                            duration_ms=duration_ms / len(executed_changes) if executed_changes else duration_ms
                        )
                        
                        # Track AI decision making
                        enhanced_telemetry.trace_ai_decision_making(
                            decision_point="file_creation",
                            context={'prompt': prompt, 'files_found': files_found},
                            reasoning=change.get('reasoning', 'No reasoning provided'),
                            confidence=0.9  # High confidence for successful tool execution
                        )
                    
                    # Track file quality
                    for change in executed_changes:
                        if change.get('content'):
                            enhanced_telemetry.trace_file_generation_quality(
                                file_path=change.get('file_path', ''),
                                content=change.get('content', ''),
                                metrics={
                                    'complexity': len(change.get('content', '').split('\n')),
                                    'readability': 0.8  # Mock score
                                }
                            )
                    
                    # Stream the results of Claude's tool execution
                    for change in executed_changes:
                        description = change.get('description', 'Unknown action')
                        yield f"data: {json.dumps({'type': 'ai_tool_result', 'message': f'Claude executed: {description}', 'change': change, 'telemetry': {'tool_executed': True, 'ai_powered': True}})}\n\n"
                    
                    # Use executed_changes as our changes list
                    changes = executed_changes
                    
                    # Get analysis result from Claude
                    analysis_result = self.claude.analysis_result or self._fallback_analysis(files_found)
                    
                else:
                    # Fallback analysis and changes without Claude
                    analysis_result = self._fallback_analysis(files_found)
                    changes = await self._fallback_plan_changes(prompt, workspace_id, sandbox)
                
                # Trace analysis and planning phases
                telemetry.trace_analysis_phase(files_found, analysis_result)
                telemetry.trace_planning_phase(changes)
                
                # Step 4: Display what was accomplished
                yield f"data: {json.dumps({'type': 'implementation', 'message': f'Claude completed {len(changes)} changes using tools', 'telemetry': {'phase': 'implementation_complete', 'changes_count': len(changes)}})}\n\n"
                
                for change in changes:
                    yield f"data: {json.dumps({'type': 'completed_change', 'change': change, 'telemetry': {'decision': 'change_completed', 'ai_generated': bool(self.claude)}})}\n\n"
                
                # Step 5: Create branch and commit with enhanced commit message
                yield f"data: {json.dumps({'type': 'git', 'message': 'Creating feature branch...', 'telemetry': {'phase': 'git_operations'}})}\n\n"
                
                # Debug: List files before branching
                async for update in sandbox.execute_command("ls -la", workspace_id):
                    print(f"FILES BEFORE BRANCH: {update}")
                    yield update
                
                branch_name = f"feature/{prompt.lower().replace(' ', '-')[:50]}-{asyncio.get_event_loop().time():.0f}"
                async for update in sandbox.execute_command(f"git checkout -b {branch_name}", workspace_id):
                    yield update
                
                telemetry.trace_git_operations("create_branch", branch_name, True)
                
                # Debug: List files after branching
                async for update in sandbox.execute_command("ls -la", workspace_id):
                    print(f"FILES AFTER BRANCH: {update}")
                    yield update
                
                # Force add all files
                async for update in sandbox.execute_command("git add .", workspace_id):
                    yield update
                
                # Debug: Check what's being committed
                async for update in sandbox.execute_command("git status", workspace_id):
                    print(f"COMMIT STATUS: {update}")
                    yield update
                
                # Create detailed commit message
                commit_message = f"feat: {prompt}\\n\\nGenerated by Claude AI with Tools:\\n"
                for change in changes[:3]:  # Include up to 3 changes in commit message
                    commit_message += f"- {change.get('description', 'Code change')}\\n"
                
                async for update in sandbox.execute_command(f'git commit -m "{commit_message}"', workspace_id):
                    yield update
                
                telemetry.trace_git_operations("commit", branch_name, True)
                
                # Step 6: Push and create PR with GitHub CLI
                print(f"DEBUG: GitHub token exists: {bool(self.github_token)}")
                if self.github_token:
                    print("DEBUG: Entering GitHub push section")
                    yield f"data: {json.dumps({'type': 'git', 'message': 'Setting up GitHub authentication...', 'telemetry': {'phase': 'github_integration'}})}\n\n"
                    
                    # Debug: Check current git status
                    async for update in sandbox.execute_command("git status", workspace_id):
                        print(f"GIT STATUS: {update}")
                        yield update
                    
                    # Debug: Check current remote
                    async for update in sandbox.execute_command("git remote -v", workspace_id):
                        print(f"GIT REMOTE BEFORE: {update}")
                        yield update
                    
                    # Set git remote URL with token for authentication
                    repo_name = repo_url.split('/')[-2:]  # ['username', 'repo']
                    auth_url = f"https://{self.github_token}@github.com/{repo_name[0]}/{repo_name[1]}"
                    print(f"DEBUG: Setting remote to: https://[TOKEN]@github.com/{repo_name[0]}/{repo_name[1]}")
                    
                    async for update in sandbox.execute_command(f"git remote set-url origin {auth_url}", workspace_id):
                        print(f"SET REMOTE: {update}")
                        yield update
                    
                    # Debug: Verify remote was set
                    async for update in sandbox.execute_command("git remote -v", workspace_id):
                        print(f"GIT REMOTE AFTER: {update}")
                        yield update
                    
                    yield f"data: {json.dumps({'type': 'git', 'message': 'Pushing Claude-generated changes...', 'telemetry': {'phase': 'github_push'}})}\n\n"
                    
                    # Push branch with detailed output
                    push_success = True
                    push_command = f"git push -u origin {branch_name}"
                    print(f"DEBUG: Executing push command: {push_command}")
                    
                    async for update in sandbox.execute_command(push_command, workspace_id):
                        print(f"PUSH OUTPUT: {update}")
                        # More accurate success detection
                        if '"type": "command_error"' in update:
                            # Check if it's actually an error or just git's verbose output
                            if '"exit_code": 0' in update:
                                # Exit code 0 means success, even if in stderr
                                pass
                            elif any(error in update.lower() for error in ['rejected', 'failed', 'error:', 'fatal:']):
                                push_success = False
                        elif '"type": "error"' in update:
                            push_success = False
                        yield update
                    
                    print(f"DEBUG: Push success = {push_success}")
                    telemetry.trace_git_operations("push", branch_name, push_success)
                    
                    if push_success:
                        # Create enhanced PR with Claude details
                        pr_title = f"🤖 Claude AI Tools: {prompt}"
                        pr_body = f"""# 🤖 Claude AI Generated Changes (Tools-Based)

**User Request:** {prompt}

## 🔍 Analysis Results
- **Project Type:** {analysis_result.get('project_type', 'Unknown')}
- **Primary Language:** {analysis_result.get('primary_language', 'Unknown')}
- **Complexity:** {analysis_result.get('complexity_level', 'Unknown')}
- **Sandbox:** {sandbox_type}

## 🛠️ Changes Made by Claude Tools
"""
                        
                        for i, change in enumerate(changes, 1):
                            pr_body += f"{i}. **{change.get('file_path', 'Unknown file')}**: {change.get('description', 'No description')}\\n"
                            if change.get('reasoning'):
                                pr_body += f"   - *Reasoning: {change.get('reasoning')}*\\n"
                        
                        pr_body += f"""
## 🚀 Generated by Tiny Backspace AI Agent
- **AI Model:** Claude 3.5 Sonnet (with Native Tools)
- **Execution:** Direct tool execution by Claude
- **Sandbox:** {sandbox_type}
- **Telemetry:** Full observability enabled
- **Timestamp:** {asyncio.get_event_loop().time()}

*This PR was automatically generated using Claude's native tool execution capabilities.*
"""
                        
                        # Create PR using GitHub CLI
                        yield f"data: {json.dumps({'type': 'git', 'message': 'Creating pull request...', 'telemetry': {'phase': 'create_pr'}})}\n\n"
                        
                        pr_command = f'gh pr create --title "{pr_title}" --body "{pr_body}" --head {branch_name}'
                        print(f"DEBUG: Executing PR command: {pr_command[:100]}...")
                        
                        async for update in sandbox.execute_command_with_env(
                            pr_command,
                            workspace_id,
                            {"GITHUB_TOKEN": self.github_token}
                        ):
                            print(f"PR OUTPUT: {update}")
                            # Extract PR URL from output for telemetry
                            if '"type": "command_output"' in update and 'github.com' in update:
                                import re
                                url_match = re.search(r'https://github\.com/[^\s"]+', update)
                                if url_match:
                                    pr_url = url_match.group(0)
                            yield update
                        
                        telemetry.trace_git_operations("create_pr", branch_name, bool(pr_url))
                    else:
                        print("DEBUG: Push failed, skipping PR creation")
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Push failed, cannot create PR', 'telemetry': {'phase': 'push_failed'}})}\n\n"
                else:
                    print("DEBUG: No GitHub token found, skipping push")
                    yield f"data: {json.dumps({'type': 'info', 'message': 'No GitHub token configured, skipping PR creation', 'telemetry': {'phase': 'skipped_github'}})}\n\n"
                
                # Final success message with Claude attribution
                final_message = f"Claude AI tools-based coding process completed successfully in {sandbox_type}!" if self.claude else f"Coding process completed successfully in {sandbox_type}!"
                yield f"data: {json.dumps({'type': 'completion', 'message': final_message, 'telemetry': {'phase': 'completion', 'pr_url': pr_url, 'ai_powered': bool(self.claude), 'changes_implemented': len(changes), 'sandbox': sandbox_type, 'tools_used': bool(self.claude)}})}\n\n"
                
                # Mark session as successful
                enhanced_telemetry.finish_coding_session(True, pr_url)
                
            except Exception as e:
                # Trace the error
                telemetry.trace_error("coding_session_error", str(e), {"repo_url": repo_url, "prompt": prompt, "sandbox": sandbox_type})
                yield f"data: {json.dumps({'type': 'error', 'message': f'Process failed: {str(e)}', 'telemetry': {'phase': 'error', 'error_type': type(e).__name__, 'sandbox': sandbox_type}})}\n\n"
                telemetry.finish_coding_session(False)
            
            finally:
                # Clean up workspace - commented out for testing
                # await sandbox.cleanup_workspace(workspace_id)
                pass
    
    def _fallback_analysis(self, files: List[str]) -> Dict[str, str]:
        """Fallback analysis when Claude is not available"""
        language_counts = {}
        for file in files:
            if file.endswith('.py'):
                language_counts['python'] = language_counts.get('python', 0) + 1
            elif file.endswith('.js'):
                language_counts['javascript'] = language_counts.get('javascript', 0) + 1
            elif file.endswith('.ts'):
                language_counts['typescript'] = language_counts.get('typescript', 0) + 1
        
        primary_language = max(language_counts, key=language_counts.get) if language_counts else "unknown"
        
        return {
            "project_type": "script",
            "primary_language": primary_language,
            "frameworks": [],
            "complexity_level": "simple",
            "insights": "Basic project structure detected"
        }
    
    async def _fallback_plan_changes(self, prompt: str, workspace_id: str, sandbox) -> List[Dict]:
        """Fallback planning when Claude is not available"""
        return [
            {
                "type": "modify_file",
                "file_path": "README.md",
                "description": f"Add section about: {prompt}",
                "reasoning": "Basic documentation update as fallback",
                "content": f"\\n\\n## {prompt}\\n\\nThis feature was added by Tiny Backspace.\\n",
                "priority": "medium"
            }
        ]
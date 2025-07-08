import os
import asyncio
import json
import shutil
from typing import AsyncGenerator
import modal
from dotenv import load_dotenv

load_dotenv()


class ModalSandbox:
    """
    Modal sandbox implementation using Modal's secure container sandboxes.
    Provides true ephemeral, isolated execution environments in the cloud.
    """
    
    def __init__(self):
        """Initialize Modal app and sandbox configuration"""
        try:
            # Create or lookup Modal app
            self.app = modal.App.lookup("tiny-backspace-agent", create_if_missing=True)
            self.sandbox = None
            self.workspace_path = "/workspace/repo"
            
            # Define the image with git, GitHub CLI, and common tools
            self.image = (
                modal.Image.debian_slim()
                .apt_install("git", "curl", "wget", "nano", "gnupg", "software-properties-common")
                # Install GitHub CLI
                .run_commands(
                    "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
                    "chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg",
                    "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null",
                    "apt update",
                    "apt install gh -y"
                )
                .pip_install("requests", "python-dotenv")
                .run_commands("git config --global user.email 'agent@tinybackspace.com'")
                .run_commands("git config --global user.name 'Tiny Backspace Agent'")
            )
            
            print(f"✅ Modal sandbox initialized with secure cloud containers")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Modal: {str(e)}")
        
    async def __aenter__(self):
        """Async context manager entry - create sandbox"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup sandbox"""
        if self.sandbox:
            try:
                self.sandbox.terminate()
                print("✅ Modal sandbox terminated")
            except Exception as e:
                print(f"Error terminating Modal sandbox: {e}")
    
    async def create_workspace(self, repo_url: str) -> str:
        """
        Create a new Modal sandbox for secure code execution.
        
        Args:
            repo_url: GitHub repository URL to work with
            
        Returns:
            workspace_id: Unique identifier for the sandbox
        """
        try:
            # Create Modal sandbox with custom image
            with modal.enable_output():
                self.sandbox = modal.Sandbox.create(
                    image=self.image,
                    app=self.app,
                    workdir=self.workspace_path,
                    timeout=300,  # 5 minutes
                    verbose=True
                )
            
            # Generate workspace ID
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            workspace_id = f"modal_{repo_name}_{self.sandbox.object_id[:8]}"
            
            print(f"✅ Created Modal sandbox: {workspace_id}")
            return workspace_id
            
        except Exception as e:
            raise Exception(f"Failed to create Modal sandbox: {str(e)}")
    
    async def clone_repo(self, repo_url: str, workspace_id: str) -> AsyncGenerator[str, None]:
        """
        Clone repository into the Modal sandbox.
        
        Args:
            repo_url: GitHub repository URL to clone
            workspace_id: Sandbox identifier
            
        Yields:
            Server-Sent Event formatted strings with progress updates
        """
        yield f"data: {json.dumps({'type': 'sandbox', 'message': f'Creating Modal cloud sandbox: {workspace_id}'})}\n\n"
        
        try:
            yield f"data: {json.dumps({'type': 'sandbox', 'message': f'Cloning {repo_url} in Modal cloud...'})}\n\n"
            
            # Clone repository in Modal sandbox
            clone_process = self.sandbox.exec("git", "clone", repo_url, ".")
            
            # Wait for clone to complete
            exit_code = clone_process.wait()
            
            if exit_code == 0:
                yield f"data: {json.dumps({'type': 'sandbox', 'message': 'Repository cloned successfully in Modal cloud'})}\n\n"
            else:
                stderr_output = clone_process.stderr.read() if clone_process.stderr else "Unknown error"
                yield f"data: {json.dumps({'type': 'error', 'message': f'Clone failed in Modal: {stderr_output}'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Modal clone error: {str(e)}'})}\n\n"
    
    async def execute_command(self, command: str, workspace_id: str) -> AsyncGenerator[str, None]:
        """
        Execute a shell command inside the Modal sandbox.
        
        Args:
            command: Shell command to execute
            workspace_id: Sandbox identifier
            
        Yields:
            Server-Sent Event formatted strings with command output
        """
        yield f"data: {json.dumps({'type': 'command', 'command': command, 'workspace': workspace_id, 'platform': 'modal-cloud'})}\n\n"
        
        try:
            # Execute command in Modal sandbox
            process = self.sandbox.exec("bash", "-c", command)
            
            # Stream output in real-time
            stdout_lines = []
            stderr_lines = []
            
            # Read stdout
            if process.stdout:
                for line in process.stdout:
                    stdout_lines.append(line.rstrip())
            
            # Read stderr  
            if process.stderr:
                stderr_content = process.stderr.read()
                if stderr_content:
                    stderr_lines.append(stderr_content.rstrip())
            
            # Wait for completion
            exit_code = process.wait()
            
            # Stream outputs
            if stdout_lines:
                stdout_output = '\n'.join(stdout_lines)
                yield f"data: {json.dumps({'type': 'command_output', 'output': stdout_output, 'exit_code': exit_code})}\n\n"
            
            if stderr_lines:
                stderr_output = '\n'.join(stderr_lines)
                yield f"data: {json.dumps({'type': 'command_error', 'error': stderr_output, 'exit_code': exit_code})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Modal command error: {str(e)}'})}\n\n"
    
    async def execute_command_with_env(self, command: str, workspace_id: str, env_vars: dict = None) -> AsyncGenerator[str, None]:
        """
        Execute a shell command with environment variables inside the Modal sandbox.
        
        Args:
            command: Shell command to execute
            workspace_id: Sandbox identifier
            env_vars: Dictionary of environment variables
            
        Yields:
            Server-Sent Event formatted strings with command output
        """
        yield f"data: {json.dumps({'type': 'command', 'command': command, 'workspace': workspace_id, 'platform': 'modal-cloud'})}\n\n"
        
        try:
            # Prepare environment variables
            env_string = ""
            if env_vars:
                env_string = " ".join([f"{k}={v}" for k, v in env_vars.items()])
                command = f"{env_string} {command}"
            
            # Execute command in Modal sandbox
            process = self.sandbox.exec("bash", "-c", command)
            
            # Stream output in real-time
            stdout_lines = []
            stderr_lines = []
            
            # Read stdout
            if process.stdout:
                for line in process.stdout:
                    stdout_lines.append(line.rstrip())
            
            # Read stderr  
            if process.stderr:
                stderr_content = process.stderr.read()
                if stderr_content:
                    stderr_lines.append(stderr_content.rstrip())
            
            # Wait for completion
            exit_code = process.wait()
            
            # Stream outputs
            if stdout_lines:
                stdout_output = '\n'.join(stdout_lines)
                yield f"data: {json.dumps({'type': 'command_output', 'output': stdout_output, 'exit_code': exit_code})}\n\n"
            
            if stderr_lines:
                stderr_output = '\n'.join(stderr_lines)
                yield f"data: {json.dumps({'type': 'command_error', 'error': stderr_output, 'exit_code': exit_code})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Modal command error: {str(e)}'})}\n\n"
    
    async def execute_command_with_env(self, command: str, workspace_id: str, env_vars: dict = None) -> AsyncGenerator[str, None]:
        """
        Execute a shell command with environment variables inside the Modal sandbox.
        
        Args:
            command: Shell command to execute
            workspace_id: Sandbox identifier
            env_vars: Dictionary of environment variables
            
        Yields:
            Server-Sent Event formatted strings with command output
        """
        yield f"data: {json.dumps({'type': 'command', 'command': command, 'workspace': workspace_id, 'platform': 'modal-cloud'})}\n\n"
        
        try:
            # Prepare environment variables
            env_string = ""
            if env_vars:
                env_string = " ".join([f"{k}={v}" for k, v in env_vars.items()])
                command = f"{env_string} {command}"
            
            # Execute command in Modal sandbox
            process = self.sandbox.exec("bash", "-c", command)
            
            # Stream output in real-time
            stdout_lines = []
            stderr_lines = []
            
            # Read stdout
            if process.stdout:
                for line in process.stdout:
                    stdout_lines.append(line.rstrip())
            
            # Read stderr  
            if process.stderr:
                stderr_content = process.stderr.read()
                if stderr_content:
                    stderr_lines.append(stderr_content.rstrip())
            
            # Wait for completion
            exit_code = process.wait()
            
            # Stream outputs
            if stdout_lines:
                stdout_output = '\n'.join(stdout_lines)
                yield f"data: {json.dumps({'type': 'command_output', 'output': stdout_output, 'exit_code': exit_code})}\n\n"
            
            if stderr_lines:
                stderr_output = '\n'.join(stderr_lines)
                yield f"data: {json.dumps({'type': 'command_error', 'error': stderr_output, 'exit_code': exit_code})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Modal command error: {str(e)}'})}\n\n"
    
    async def read_file(self, file_path: str, workspace_id: str) -> str:
        """
        Read the contents of a file from the Modal sandbox.
        
        Args:
            file_path: Path to file within the sandbox
            workspace_id: Sandbox identifier
            
        Returns:
            File contents as string
        """
        try:
            # Read file using cat command in Modal
            process = self.sandbox.exec("cat", file_path)
            
            if process.wait() == 0:
                content = process.stdout.read()
                return content
            else:
                error_msg = process.stderr.read() if process.stderr else "File not found"
                return f"Error reading file {file_path}: {error_msg}"
                
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
    async def write_file(self, file_path: str, content: str, workspace_id: str) -> AsyncGenerator[str, None]:
        """
        Write content to a file in the Modal sandbox.
        
        Args:
            file_path: Path where to write the file
            content: Content to write to the file
            workspace_id: Sandbox identifier
            
        Yields:
            Server-Sent Event formatted strings with write progress
        """
        yield f"data: {json.dumps({'type': 'file_write', 'file': file_path, 'workspace': workspace_id, 'platform': 'modal-cloud'})}\n\n"
        
        try:
            # Create directory if needed
            dir_path = os.path.dirname(file_path)
            if dir_path:
                self.sandbox.exec("mkdir", "-p", dir_path).wait()
            
            # Write file using Modal's file operations
            with self.sandbox.open(file_path, "w") as f:
                f.write(content)
            
            yield f"data: {json.dumps({'type': 'file_write_complete', 'file': file_path, 'location': 'modal-cloud'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Modal file write error: {str(e)}'})}\n\n"
    
    async def cleanup_workspace(self, workspace_id: str):
        """
        Clean up and terminate the Modal sandbox.
        
        Args:
            workspace_id: Sandbox to cleanup
        """
        try:
            if self.sandbox:
                self.sandbox.terminate()
                self.sandbox = None
                print(f"✅ Cleaned up Modal sandbox: {workspace_id}")
        except Exception as e:
            print(f"Error cleaning up Modal sandbox: {e}")


# Keep LocalSandbox as fallback
class LocalSandbox:
    """Local sandbox fallback implementation"""
    
    def __init__(self):
        self.work_dir = "/tmp/tiny-backspace-sandbox"
        os.makedirs(self.work_dir, exist_ok=True)
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def create_workspace(self, repo_url: str) -> str:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        workspace_id = f"local_{repo_name}"
        return workspace_id
    
    async def clone_repo(self, repo_url: str, workspace_id: str) -> AsyncGenerator[str, None]:
        workspace_path = f"{self.work_dir}/{workspace_id}"
        
        yield f"data: {json.dumps({'type': 'sandbox', 'message': f'Preparing local workspace: {workspace_path}'})}\n\n"
        
        try:
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
            
            yield f"data: {json.dumps({'type': 'sandbox', 'message': f'Cloning {repo_url}...'})}\n\n"
            
            process = await asyncio.create_subprocess_exec(
                'git', 'clone', repo_url, workspace_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                yield f"data: {json.dumps({'type': 'sandbox', 'message': 'Repository cloned successfully'})}\n\n"
            else:
                error_msg = stderr.decode() if stderr else "Unknown clone error"
                yield f"data: {json.dumps({'type': 'error', 'message': f'Clone failed: {error_msg}'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Clone error: {str(e)}'})}\n\n"
    
    async def execute_command(self, command: str, workspace_id: str) -> AsyncGenerator[str, None]:
        workspace_path = f"{self.work_dir}/{workspace_id}"
        
        yield f"data: {json.dumps({'type': 'command', 'command': command, 'workspace': workspace_id})}\n\n"
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=workspace_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""
            
            if output:
                yield f"data: {json.dumps({'type': 'command_output', 'output': output})}\n\n"
            if error:
                yield f"data: {json.dumps({'type': 'command_error', 'error': error})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Command error: {str(e)}'})}\n\n"
    
    async def execute_command_with_env(self, command: str, workspace_id: str, env_vars: dict = None) -> AsyncGenerator[str, None]:
        """Execute command with environment variables - same as execute_command for local"""
        async for update in self.execute_command(command, workspace_id):
            yield update
    
    async def read_file(self, file_path: str, workspace_id: str) -> str:
        full_path = f"{self.work_dir}/{workspace_id}/{file_path}"
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
    async def write_file(self, file_path: str, content: str, workspace_id: str) -> AsyncGenerator[str, None]:
        full_path = f"{self.work_dir}/{workspace_id}/{file_path}"
        
        yield f"data: {json.dumps({'type': 'file_write', 'file': file_path, 'workspace': workspace_id})}\n\n"
        
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            yield f"data: {json.dumps({'type': 'file_write_complete', 'file': file_path})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'File write error: {str(e)}'})}\n\n"
    
    async def cleanup_workspace(self, workspace_id: str):
        workspace_path = f"{self.work_dir}/{workspace_id}"
        try:
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
        except Exception:
            pass
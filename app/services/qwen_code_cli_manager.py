"""
Qwen Code CLI Manager

Implementation of CLI manager for Qwen Code (Qwen3-Coder-32B).
Supports 3 parallel review tasks.
"""

from app.services.base_cli_manager import BaseCLIManager
from app.models import ReviewType, CLIAgent
from typing import List, Dict, Any, Optional
import asyncio
import tempfile
import json
import logging

logger = logging.getLogger(__name__)


class QwenCodeCLIManager(BaseCLIManager):
    """Manager for Qwen Code CLI operations"""
    
    @property
    def agent_type(self) -> CLIAgent:
        return CLIAgent.QWEN_CODE
    
    @property
    def cli_command(self) -> str:
        return "qwen-code"
    
    async def execute_review(
        self,
        review_type: ReviewType,
        repo_path: str,
        prompt_content: str,
        custom_rules: Optional[str] = None,
        jira_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute code review using Qwen Code CLI
        
        Args:
            review_type: Type of review
            repo_path: Path to cloned repository
            prompt_content: Prompt with instructions
            custom_rules: Custom rules (optional)
            jira_context: JIRA context (optional)
            
        Returns:
            Review results as dict
            
        Note:
            Changed files are automatically determined by CLI via git diff
        """
        # Substitute variables in prompt
        processed_prompt = self._substitute_prompt_variables(
            prompt_template=prompt_content,
            repo_path=repo_path,
            language="java",  # TODO: Make this configurable
            custom_rules=custom_rules,
            jira_context=jira_context
        )
        
        # Create temporary file for prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as prompt_file:
            prompt_file.write(processed_prompt)
            prompt_path = prompt_file.name
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # Build Qwen Code CLI command
            # Note: CLI will automatically detect changed files via git diff
            cmd = [
                self.cli_command,
                'review',
                '--repo', repo_path,
                '--prompt-file', prompt_path,
                '--output', output_path,
                '--json',
                '--api-base', self.model_api_url,
                '--model', self.model_name,
                '--api-key', self.api_key,
                '--timeout', str(self.timeout_seconds)
            ]
            
            logger.debug(f"Executing Qwen Code CLI: {' '.join(cmd[:6])}...")  # Don't log API key
            
            # Execute CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds + 30  # Add buffer
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Qwen Code CLI timed out after {self.timeout_seconds} seconds")
            
            # Check return code
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Qwen Code CLI failed: {error_msg}")
                raise RuntimeError(f"Qwen Code CLI failed with code {process.returncode}: {error_msg}")
            
            # Read output file
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            # Add review type if not present
            if 'review_type' not in result:
                result['review_type'] = review_type.value
            
            return result
            
        finally:
            # Cleanup temporary files
            import os
            try:
                os.unlink(prompt_path)
            except:
                pass
            try:
                os.unlink(output_path)
            except:
                pass
    
    def get_review_type_distribution(self, review_types: List[ReviewType]) -> List[List[ReviewType]]:
        """
        Distribute review types into parallel task groups for Qwen Code (3 parallel tasks)
        
        Strategy:
        Task 1: ERROR_DETECTION + SECURITY_AUDIT
        Task 2: BEST_PRACTICES + PERFORMANCE
        Task 3: REFACTORING + DATABASE_OPTIMIZATION
        
        Args:
            review_types: List of review types to distribute
            
        Returns:
            List of task groups (each group runs in parallel)
        """
        if ReviewType.ALL in review_types:
            # Full review - use predefined distribution
            # Note: Qwen Code handles fewer review types (faster but less comprehensive)
            return [
                [ReviewType.ERROR_DETECTION, ReviewType.SECURITY_AUDIT],
                [ReviewType.BEST_PRACTICES, ReviewType.PERFORMANCE],
                [ReviewType.REFACTORING, ReviewType.DATABASE_OPTIMIZATION]
            ]
        else:
            # Custom review types - distribute evenly
            groups = [[] for _ in range(min(3, len(review_types)))]
            for i, rt in enumerate(review_types):
                groups[i % len(groups)].append(rt)
            return [g for g in groups if g]  # Filter empty groups



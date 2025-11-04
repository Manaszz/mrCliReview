"""
Base CLI Manager - Abstract class for CLI agents

Defines the interface that all CLI managers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models import ReviewType, ReviewResult, CLIAgent
import asyncio
import logging

logger = logging.getLogger(__name__)


class BaseCLIManager(ABC):
    """Abstract base class for CLI agent managers"""
    
    # Class-level cache for system prompt
    _system_prompt_cache: Optional[str] = None
    
    def __init__(
        self,
        model_api_url: str,
        model_name: str,
        api_key: str,
        parallel_tasks: int,
        timeout_seconds: int = 300,
        system_prompt_path: str = "prompts/system_prompt.md"
    ):
        """
        Initialize CLI manager
        
        Args:
            model_api_url: Base URL for model API
            model_name: Model name to use
            api_key: API key for authentication
            parallel_tasks: Maximum number of parallel review tasks
            timeout_seconds: Timeout for each review task
            system_prompt_path: Path to system prompt file (loaded once, cached)
        """
        self.model_api_url = model_api_url
        self.model_name = model_name
        self.api_key = api_key
        self.parallel_tasks = parallel_tasks
        self.timeout_seconds = timeout_seconds
        self.system_prompt_path = system_prompt_path
        
        # Load system prompt once (singleton pattern)
        if BaseCLIManager._system_prompt_cache is None:
            BaseCLIManager._system_prompt_cache = self._load_system_prompt()
        
    @property
    @abstractmethod
    def agent_type(self) -> CLIAgent:
        """Return the CLI agent type"""
        pass
    
    @property
    @abstractmethod
    def cli_command(self) -> str:
        """Return the CLI command name (e.g., 'cline', 'qwen-code')"""
        pass
    
    @abstractmethod
    async def execute_review(
        self,
        review_type: ReviewType,
        repo_path: str,
        prompt_content: str,
        custom_rules: Optional[str] = None,
        jira_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a single review task
        
        Args:
            review_type: Type of review to perform
            repo_path: Local path to cloned repository
            prompt_content: Processed prompt content
            custom_rules: Custom rules content (optional)
            jira_context: JIRA task context (optional)
            
        Returns:
            Dict containing review results in JSON format
            
        Note:
            Changed files are automatically determined by CLI via git diff
        """
        pass
    
    async def execute_parallel_reviews(
        self,
        review_types: List[ReviewType],
        repo_path: str,
        prompts: Dict[ReviewType, str],
        custom_rules: Optional[str] = None,
        jira_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple reviews in parallel with task limit
        
        Args:
            review_types: List of review types to perform
            repo_path: Local path to cloned repository
            prompts: Mapping of review type to prompt content
            custom_rules: Custom rules content (optional)
            jira_context: JIRA task context (optional)
            
        Returns:
            List of review results
            
        Note:
            Changed files are automatically determined by CLI via git diff
        """
        semaphore = asyncio.Semaphore(self.parallel_tasks)
        
        async def bounded_review(review_type: ReviewType) -> Dict[str, Any]:
            async with semaphore:
                logger.info(f"Starting {review_type.value} review with {self.agent_type.value}")
                try:
                    result = await self.execute_review(
                        review_type=review_type,
                        repo_path=repo_path,
                        prompt_content=prompts[review_type],
                        custom_rules=custom_rules,
                        jira_context=jira_context
                    )
                    logger.info(f"Completed {review_type.value} review")
                    return result
                except Exception as e:
                    logger.error(f"Error in {review_type.value} review: {str(e)}", exc_info=True)
                    return {
                        "review_type": review_type.value,
                        "error": str(e),
                        "issues": [],
                        "summary": {"total_issues": 0}
                    }
        
        tasks = [bounded_review(rt) for rt in review_types]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to dicts
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Review task failed with exception: {str(result)}")
                continue
            valid_results.append(result)
            
        return valid_results
    
    async def check_availability(self) -> bool:
        """
        Check if CLI tool is available and properly configured
        
        Returns:
            True if CLI is available, False otherwise
        """
        try:
            import shutil
            cli_path = shutil.which(self.cli_command)
            if cli_path is None:
                logger.warning(f"{self.cli_command} not found in PATH")
                return False
            
            # Test CLI with version command
            process = await asyncio.create_subprocess_exec(
                self.cli_command,
                '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"{self.cli_command} is available: {version}")
                return True
            else:
                logger.warning(f"{self.cli_command} version check failed: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            logger.warning(f"{self.cli_command} version check timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking {self.cli_command} availability: {str(e)}")
            return False
    
    async def test_model_connection(self) -> bool:
        """
        Test connection to model API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.model_api_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    logger.info(f"Model API connection successful for {self.agent_type.value}")
                    return True
                else:
                    logger.warning(f"Model API returned status {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error testing model API connection: {str(e)}")
            return False
    
    def _load_system_prompt(self) -> str:
        """
        Load system prompt from file (once, cached at class level)
        
        Returns:
            System prompt content or empty string if file not found
        """
        import os
        from pathlib import Path
        
        try:
            system_prompt_file = Path(self.system_prompt_path)
            if system_prompt_file.exists():
                with open(system_prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"Loaded system prompt from {self.system_prompt_path}")
                return content
            else:
                logger.warning(f"System prompt file not found: {self.system_prompt_path}")
                return ""
        except Exception as e:
            logger.error(f"Failed to load system prompt: {str(e)}")
            return ""
    
    def _substitute_prompt_variables(
        self,
        prompt_template: str,
        repo_path: str,
        language: str,
        custom_rules: Optional[str] = None,
        jira_context: Optional[str] = None
    ) -> str:
        """
        Substitute variables in prompt template and prepend system prompt
        
        Args:
            prompt_template: Prompt template with {variables}
            repo_path: Repository path
            language: Programming language
            custom_rules: Custom rules content
            jira_context: JIRA context
            
        Returns:
            Prompt with substituted variables and system prompt prepended
            
        Note:
            Changed files are determined by CLI via git diff, not passed as parameter
            System prompt is loaded once and cached for performance
        """
        substitutions = {
            '{repo_path}': repo_path,
            '{language}': language,
            '{custom_rules}': custom_rules or "No custom rules provided",
            '{jira_context}': jira_context or "No JIRA context provided"
        }
        
        result = prompt_template
        for placeholder, value in substitutions.items():
            result = result.replace(placeholder, value)
        
        # Prepend system prompt (cached, loaded once)
        if BaseCLIManager._system_prompt_cache:
            result = BaseCLIManager._system_prompt_cache + "\n\n---\n\n" + result
            
        return result
    
    def _parse_cli_output(self, output: str) -> Dict[str, Any]:
        """
        Parse CLI output (expected to be JSON)
        
        Args:
            output: CLI output string
            
        Returns:
            Parsed JSON as dict
        """
        import json
        import re
        
        # Try to find JSON in output
        # Sometimes CLI outputs include non-JSON text
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, output)
        
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from CLI output: {str(e)}")
                logger.debug(f"CLI output: {output[:500]}")
                raise ValueError(f"Invalid JSON in CLI output: {str(e)}")
        else:
            logger.error("No JSON found in CLI output")
            logger.debug(f"CLI output: {output[:500]}")
            raise ValueError("No JSON found in CLI output")



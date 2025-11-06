"""
Git Repository Manager

Handles local git operations: cloning, branching, committing.
Minimal GitLab API usage - core logic for repository interaction.
"""

import os
import shutil
import asyncio
from pathlib import Path
from typing import List, Optional, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class GitRepositoryManager:
    """Manager for git repository operations"""
    
    def __init__(self, work_dir: str = "/tmp/review"):
        """
        Initialize repository manager
        
        Args:
            work_dir: Base directory for cloned repositories
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Track active reviews to prevent concurrent reviews of same MR
        self._active_reviews: Set[str] = set()
        self._review_lock = asyncio.Lock()
        
    async def clone_repository(
        self,
        clone_url: str,
        branch: str,
        project_id: int,
        mr_iid: int,
        target_branch: str = "develop"
    ) -> str:
        """
        Clone repository and checkout MR branch with target branch for comparison
        
        Args:
            clone_url: Git clone URL with authentication
            branch: Source branch to checkout (MR source branch)
            project_id: Project ID (for directory naming)
            mr_iid: MR IID (for directory naming)
            target_branch: Target branch for diff comparison (usually main/master)
            
        Returns:
            Path to cloned repository
            
        Raises:
            RuntimeError: If review for this MR is already in progress
        """
        # Check if review is already in progress
        review_key = f"{project_id}-{mr_iid}"
        
        async with self._review_lock:
            if review_key in self._active_reviews:
                logger.warning(f"Review already in progress for project {project_id}, MR !{mr_iid}")
                raise RuntimeError(
                    f"Review for project {project_id}, MR !{mr_iid} is already in progress. "
                    f"Please wait for the current review to complete."
                )
            
            # Register this review as active
            self._active_reviews.add(review_key)
            logger.info(f"Registered active review: {review_key}")
        
        # Create unique directory for this MR
        repo_dir = self.work_dir / f"project-{project_id}-mr-{mr_iid}"
        
        # Clean up if exists (from previous failed review)
        if repo_dir.exists():
            logger.info(f"Removing existing repository at {repo_dir}")
            shutil.rmtree(repo_dir)
        
        # Clone source branch
        logger.info(f"Cloning {branch} to {repo_dir}")
        cmd = ['git', 'clone', '--branch', branch, '--single-branch', clone_url, str(repo_dir)]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"Git clone failed: {error_msg}")
            raise RuntimeError(f"Failed to clone repository: {error_msg}")
        
        logger.info(f"Successfully cloned {branch}")
        
        # Fetch target branch for diff comparison
        logger.info(f"Fetching {target_branch} for comparison")
        cmd = [
            'git', 'fetch', 'origin',
            f'{target_branch}:refs/remotes/origin/{target_branch}'
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(repo_dir)
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            # Not critical - can work without target branch in some cases
            logger.warning(f"Failed to fetch {target_branch}: {stderr.decode()}")
        else:
            logger.info(f"Successfully fetched {target_branch} for comparison")
        
        return str(repo_dir)
    
    async def get_changed_files(
        self,
        repo_path: str,
        base_branch: str = "origin/main"
    ) -> List[str]:
        """
        Get list of changed files compared to base branch
        
        Args:
            repo_path: Path to repository
            base_branch: Base branch to compare against
            
        Returns:
            List of changed file paths
        """
        # Get diff files
        cmd = ['git', 'diff', '--name-only', base_branch]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=repo_path
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.warning(f"Git diff failed: {stderr.decode()}")
            # Fallback: get all Java files in src/
            return await self._get_all_source_files(repo_path)
        
        files = [f.strip() for f in stdout.decode().split('\n') if f.strip()]
        logger.info(f"Found {len(files)} changed files")
        return files
    
    async def _get_all_source_files(self, repo_path: str) -> List[str]:
        """
        Get all source files in repository (fallback)
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of source file paths
        """
        source_files = []
        repo_pathlib = Path(repo_path)
        
        # Look for Java files in src/
        src_dir = repo_pathlib / "src"
        if src_dir.exists():
            for java_file in src_dir.rglob("*.java"):
                relative_path = java_file.relative_to(repo_pathlib)
                source_files.append(str(relative_path))
        
        logger.info(f"Found {len(source_files)} source files (fallback)")
        return source_files
    
    async def create_branch(
        self,
        repo_path: str,
        branch_name: str,
        base_branch: Optional[str] = None
    ) -> None:
        """
        Create new branch
        
        Args:
            repo_path: Path to repository
            branch_name: New branch name
            base_branch: Base branch to branch from (current if None)
        """
        # Checkout base branch if specified
        if base_branch:
            cmd = ['git', 'checkout', base_branch]
            await self._run_git_command(cmd, repo_path)
        
        # Create and checkout new branch
        cmd = ['git', 'checkout', '-b', branch_name]
        await self._run_git_command(cmd, repo_path)
        
        logger.info(f"Created branch: {branch_name}")
    
    async def commit_changes(
        self,
        repo_path: str,
        commit_message: str,
        files: Optional[List[str]] = None
    ) -> str:
        """
        Commit changes to current branch
        
        Args:
            repo_path: Path to repository
            commit_message: Commit message
            files: List of files to commit (all if None)
            
        Returns:
            Commit SHA
        """
        # Add files
        if files:
            for file in files:
                cmd = ['git', 'add', file]
                await self._run_git_command(cmd, repo_path)
        else:
            cmd = ['git', 'add', '-A']
            await self._run_git_command(cmd, repo_path)
        
        # Commit
        cmd = ['git', 'commit', '-m', commit_message]
        await self._run_git_command(cmd, repo_path)
        
        # Get commit SHA
        cmd = ['git', 'rev-parse', 'HEAD']
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=repo_path
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to get commit SHA: {stderr.decode()}")
        
        commit_sha = stdout.decode().strip()
        logger.info(f"Created commit: {commit_sha}")
        return commit_sha
    
    async def push_branch(
        self,
        repo_path: str,
        branch_name: str,
        remote: str = "origin"
    ) -> None:
        """
        Push branch to remote
        
        Args:
            repo_path: Path to repository
            branch_name: Branch name to push
            remote: Remote name
        """
        cmd = ['git', 'push', remote, branch_name]
        await self._run_git_command(cmd, repo_path)
        logger.info(f"Pushed branch {branch_name} to {remote}")
    
    async def _run_git_command(
        self,
        cmd: List[str],
        cwd: str,
        timeout: int = 60
    ) -> Tuple[str, str]:
        """
        Run git command
        
        Args:
            cmd: Command and arguments
            cwd: Working directory
            timeout: Command timeout
            
        Returns:
            Tuple of (stdout, stderr)
        """
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Git command timed out: {' '.join(cmd)}")
        
        if process.returncode != 0:
            raise RuntimeError(f"Git command failed: {stderr.decode()}")
        
        return stdout.decode(), stderr.decode()
    
    async def cleanup_repository(self, repo_path: str) -> None:
        """
        Clean up cloned repository and release review lock
        
        Args:
            repo_path: Path to repository
        """
        # Extract project_id and mr_iid from repo_path
        # Format: /tmp/review/project-{project_id}-mr-{mr_iid}
        try:
            path_parts = Path(repo_path).name.split('-')
            if len(path_parts) >= 4 and path_parts[0] == 'project' and path_parts[2] == 'mr':
                project_id = path_parts[1]
                mr_iid = path_parts[3]
                review_key = f"{project_id}-{mr_iid}"
                
                # Remove from active reviews
                async with self._review_lock:
                    if review_key in self._active_reviews:
                        self._active_reviews.remove(review_key)
                        logger.info(f"Released active review: {review_key}")
        except Exception as e:
            logger.warning(f"Failed to extract review key from path {repo_path}: {str(e)}")
        
        # Clean up directory
        if os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository: {repo_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup repository {repo_path}: {str(e)}")



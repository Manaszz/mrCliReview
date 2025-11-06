"""
GitLab Service

Minimal GitLab API integration for MR operations.
Focus: Get MR metadata, clone URL, post comments, create MRs.
"""

from typing import List, Dict, Any, Optional
import logging
import httpx

logger = logging.getLogger(__name__)


class GitLabService:
    """Minimal GitLab API service"""
    
    def __init__(self, gitlab_url: str, gitlab_token: str):
        """
        Initialize GitLab service
        
        Args:
            gitlab_url: GitLab instance URL (e.g., https://gitlab.example.com)
            gitlab_token: GitLab personal access token
        """
        self.gitlab_url = gitlab_url.rstrip('/')
        self.api_url = f"{self.gitlab_url}/api/v4"
        self.headers = {
            "Private-Token": gitlab_token,
            "Content-Type": "application/json"
        }
        
    async def get_merge_request(
        self,
        project_id: int,
        mr_iid: int
    ) -> Dict[str, Any]:
        """
        Get merge request details
        
        Args:
            project_id: Project ID
            mr_iid: MR internal ID
            
        Returns:
            MR data dict
        """
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
    
    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """
        Get project details
        
        Args:
            project_id: Project ID
            
        Returns:
            Project data dict
        """
        url = f"{self.api_url}/projects/{project_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
    
    async def get_mr_changes(
        self,
        project_id: int,
        mr_iid: int
    ) -> List[Dict[str, Any]]:
        """
        Get MR changed files
        
        Args:
            project_id: Project ID
            mr_iid: MR IID
            
        Returns:
            List of changed files with diffs
        """
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}/changes"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('changes', [])
    
    async def post_mr_comment(
        self,
        project_id: int,
        mr_iid: int,
        comment: str
    ) -> Dict[str, Any]:
        """
        Post comment to merge request
        
        Args:
            project_id: Project ID
            mr_iid: MR IID
            comment: Comment text (markdown)
            
        Returns:
            Created note data
        """
        url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}/notes"
        payload = {"body": comment}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    
    async def create_merge_request(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create new merge request
        
        Args:
            project_id: Project ID
            source_branch: Source branch name
            target_branch: Target branch name
            title: MR title
            description: MR description
            labels: List of labels
            assignee_id: Assignee user ID
            
        Returns:
            Created MR data
        """
        url = f"{self.api_url}/projects/{project_id}/merge_requests"
        payload = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description
        }
        
        if labels:
            payload["labels"] = ",".join(labels)
        if assignee_id:
            payload["assignee_id"] = assignee_id
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    
    async def commit_file_changes(
        self,
        project_id: int,
        branch: str,
        commit_message: str,
        files: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Commit file changes to branch
        
        Args:
            project_id: Project ID
            branch: Branch name
            commit_message: Commit message
            files: List of file actions, each with:
                  - action: "create", "update", "delete"
                  - file_path: Path to file
                  - content: File content (for create/update)
            
        Returns:
            Commit data
        """
        url = f"{self.api_url}/projects/{project_id}/repository/commits"
        payload = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": files
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
    
    async def test_connection(self) -> bool:
        """
        Test GitLab API connection
        
        Returns:
            True if connection successful
        """
        try:
            url = f"{self.api_url}/version"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    version_data = response.json()
                    logger.info(f"GitLab connection successful: {version_data.get('version')}")
                    return True
                return False
        except Exception as e:
            logger.error(f"GitLab connection test failed: {str(e)}")
            return False
    
    def get_clone_url(self, project_data: Dict[str, Any]) -> str:
        """
        Get HTTP clone URL with authentication
        
        Args:
            project_data: Project data from get_project()
            
        Returns:
            Clone URL with token authentication
        """
        # Use http_url_to_repo and inject token
        http_url = project_data.get('http_url_to_repo', '')
        if not http_url:
            raise ValueError("No HTTP clone URL in project data")
        
        # Format: https://gitlab.example.com/group/project.git
        # Convert to: https://oauth2:TOKEN@gitlab.example.com/group/project.git
        if http_url.startswith('https://'):
            parts = http_url.replace('https://', '').split('/', 1)
            if len(parts) == 2:
                domain, path = parts
                return f"https://oauth2:{self.headers['Private-Token']}@{domain}/{path}"
        
        return http_url



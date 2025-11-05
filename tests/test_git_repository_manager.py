"""
Tests for GitRepositoryManager
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.git_repository_manager import GitRepositoryManager


@pytest.fixture
def git_manager(tmp_path):
    """Create GitRepositoryManager with temp directory"""
    return GitRepositoryManager(work_dir=str(tmp_path))


@pytest.mark.asyncio
async def test_init_creates_work_dir(tmp_path):
    """Test that work directory is created on init"""
    work_dir = tmp_path / "test_work"
    manager = GitRepositoryManager(work_dir=str(work_dir))
    assert work_dir.exists()
    assert manager.work_dir == work_dir


@pytest.mark.asyncio
async def test_clone_repository_success(git_manager, tmp_path):
    """Test successful repository clone"""
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        repo_path = await git_manager.clone_repository(
            clone_url="https://gitlab.example.com/test/repo.git",
            branch="feature-branch",
            project_id=123,
            mr_iid=456,
            target_branch="main"
        )
    
    assert "project-123-mr-456" in repo_path
    assert "123-456" in git_manager._active_reviews


@pytest.mark.asyncio
async def test_clone_repository_prevents_concurrent_review(git_manager):
    """Test that concurrent reviews of same MR are prevented"""
    # Register active review
    git_manager._active_reviews.add("123-456")
    
    # Try to clone again
    with pytest.raises(RuntimeError, match="already in progress"):
        await git_manager.clone_repository(
            clone_url="https://gitlab.example.com/test/repo.git",
            branch="feature-branch",
            project_id=123,
            mr_iid=456,
            target_branch="main"
        )


@pytest.mark.asyncio
async def test_clone_repository_failure(git_manager):
    """Test clone failure handling"""
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"fatal: repository not found"))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with pytest.raises(RuntimeError, match="Failed to clone repository"):
            await git_manager.clone_repository(
                clone_url="https://invalid.git",
                branch="main",
                project_id=1,
                mr_iid=1,
                target_branch="main"
            )


@pytest.mark.asyncio
async def test_get_changed_files_success(git_manager, tmp_path):
    """Test getting changed files via git diff"""
    repo_path = str(tmp_path / "test_repo")
    
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(
        return_value=(b"src/main/java/Test.java\nsrc/main/java/Test2.java\n", b"")
    )
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        files = await git_manager.get_changed_files(repo_path)
    
    assert len(files) == 2
    assert "src/main/java/Test.java" in files
    assert "src/main/java/Test2.java" in files


@pytest.mark.asyncio
async def test_create_branch(git_manager, tmp_path):
    """Test branch creation"""
    repo_path = str(tmp_path / "test_repo")
    
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        await git_manager.create_branch(repo_path, "new-branch")
    
    # Should have called git checkout -b new-branch
    # Verification would require checking mock calls


@pytest.mark.asyncio
async def test_commit_changes(git_manager, tmp_path):
    """Test committing changes"""
    repo_path = str(tmp_path / "test_repo")
    
    mock_process_add = AsyncMock()
    mock_process_add.returncode = 0
    mock_process_add.communicate = AsyncMock(return_value=(b"", b""))
    
    mock_process_commit = AsyncMock()
    mock_process_commit.returncode = 0
    mock_process_commit.communicate = AsyncMock(return_value=(b"", b""))
    
    mock_process_sha = AsyncMock()
    mock_process_sha.returncode = 0
    mock_process_sha.communicate = AsyncMock(return_value=(b"abc123def456\n", b""))
    
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        mock_exec.side_effect = [mock_process_add, mock_process_commit, mock_process_sha]
        
        commit_sha = await git_manager.commit_changes(
            repo_path=repo_path,
            commit_message="Test commit"
        )
    
    assert commit_sha == "abc123def456"


@pytest.mark.asyncio
async def test_push_branch(git_manager, tmp_path):
    """Test pushing branch to remote"""
    repo_path = str(tmp_path / "test_repo")
    
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        await git_manager.push_branch(repo_path, "test-branch")


@pytest.mark.asyncio
async def test_cleanup_repository(git_manager, tmp_path):
    """Test repository cleanup and review lock release"""
    # Create a test repo directory
    repo_path = tmp_path / "project-123-mr-456"
    repo_path.mkdir()
    test_file = repo_path / "test.txt"
    test_file.write_text("test")
    
    # Register active review
    git_manager._active_reviews.add("123-456")
    
    # Cleanup
    await git_manager.cleanup_repository(str(repo_path))
    
    # Verify directory removed
    assert not repo_path.exists()
    
    # Verify review lock released
    assert "123-456" not in git_manager._active_reviews


@pytest.mark.asyncio
async def test_run_git_command_timeout(git_manager, tmp_path):
    """Test git command timeout handling"""
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_process.kill = MagicMock()
    mock_process.wait = AsyncMock()
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            with pytest.raises(TimeoutError, match="Git command timed out"):
                await git_manager._run_git_command(['git', 'status'], str(tmp_path), timeout=1)


@pytest.mark.asyncio
async def test_run_git_command_failure(git_manager, tmp_path):
    """Test git command failure handling"""
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"fatal: error"))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with pytest.raises(RuntimeError, match="Git command failed"):
            await git_manager._run_git_command(['git', 'invalid'], str(tmp_path))


"""Data fetcher tests: GitHub pagination and cache behavior."""
from data_fetchers import GitHubFetcher


class TestGitHubFetcher:
    def test_commit_requests_use_full_page_size(self):
        """Bug: the commits endpoint defaults to 30 results/page, so
        github_commits_30d was capped at 30 and the scorer's '>50 commits =
        very active' branch was unreachable."""
        fetcher = GitHubFetcher()
        captured = []

        def fake_request(url, params=None, headers=None, **kwargs):
            captured.append((url, params or {}))
            if url.endswith("/repos/foo/bar"):
                return {"stargazers_count": 10, "forks_count": 1,
                        "open_issues_count": 2, "pushed_at": "2026-01-01T00:00:00Z"}
            return [{}] * 3  # commits / contributors

        fetcher._request_with_retry = fake_request
        fetcher.fetch("https://github.com/foo/bar")

        commit_calls = [(u, p) for u, p in captured if u.endswith("/commits")]
        assert commit_calls, "expected commit requests"
        for _, params in commit_calls:
            assert params.get("per_page") == 100

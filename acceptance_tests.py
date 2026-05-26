import unittest
import responses
import sys
import os

sys.path.insert(0, '/workspace/projects/RepoHealth-CLI')

class TestRepoHealthCLI(unittest.TestCase):
    @responses.activate
    def test_criterion_1_auth_and_repo_fetch(self):
        from main import fetch_repos
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/test-org/repos',
            json=[{'full_name': 'test-org/repo1', 'id': 1}],
            status=200
        )
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/test-org/repos',
            json=[],
            status=200
        )
        repos = fetch_repos('test-org', 'test-token')
        assert len(repos) == 1
        assert repos[0]['full_name'] == 'test-org/repo1'

    @responses.activate
    def test_criterion_2_fetch_issues_and_prs(self):
        from main import fetch_issues_and_prs
        responses.add(
            responses.GET,
            'https://api.github.com/repos/test-org/repo1/issues',
            json=[{'id': 1, 'title': 'Stale Issue', 'updated_at': '2020-01-01T00:00:00Z', 'number': 1}],
            status=200
        )
        responses.add(
            responses.GET,
            'https://api.github.com/repos/test-org/repo1/issues',
            json=[],
            status=200
        )
        responses.add(
            responses.GET,
            'https://api.github.com/repos/test-org/repo1/pulls',
            json=[{'id': 2, 'title': 'Stale PR', 'updated_at': '2020-01-01T00:00:00Z', 'number': 2, 'type': 'PR'}],
            status=200
        )
        responses.add(
            responses.GET,
            'https://api.github.com/repos/test-org/repo1/pulls',
            json=[],
            status=200
        )
        repos = [{'full_name': 'test-org/repo1'}]
        items = fetch_issues_and_prs(repos, 'test-token')
        assert len(items) == 2
        assert any(i.get('type') == 'PR' for i in items)

    @responses.activate
    def test_criterion_3_filter_stale(self):
        from main import filter_stale
        items = [
            {'updated_at': '2020-01-01T00:00:00Z'},
            {'updated_at': '2025-01-01T00:00:00Z'}
        ]
        stale = filter_stale(items, 30)
        assert len(stale) == 1

    @responses.activate
    def test_criterion_4_generate_markdown_report(self):
        from main import generate_report
        items = [{'repo': 'test', 'title': 'Test', 'updated_at': '2020-01-01T00:00:00Z', 'type': 'Issue'}]
        md = generate_report(items, 'markdown')
        assert 'test' in md
        assert 'Test' in md
        assert '|---|---|---|---|' in md

    @responses.activate
    def test_criterion_5_generate_shell_script(self):
        from main import generate_script
        items = [{'repo': 'test-org/repo1', 'number': 1}]
        script = generate_script(items)
        assert '#!/bin/bash' in script
        assert 'test-org/repo1#1' in script

if __name__ == '__main__':
    unittest.main()

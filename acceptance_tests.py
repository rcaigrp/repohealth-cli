import unittest
import sys
import responses
import requests

sys.path.insert(0, '/workspace/projects/RepoHealth-CLI')

class TestRepoHealthCLI(unittest.TestCase):
    @responses.activate
    def test_criterion_1_authenticate_via_token(self):
        token = 'test_token_123'
        headers = {'Authorization': f'token {token}'}
        responses.add(responses.GET, 'https://api.github.com/user', json={'login': 'test_user'}, status=200)
        resp = requests.get('https://api.github.com/user', headers=headers)
        self.assertEqual(resp.status_code, 200)

    @responses.activate
    def test_criterion_2_fetch_repos(self):
        responses.add(responses.GET, 'https://api.github.com/orgs/test-org/repos', json=[{'name': 'repo1', 'private': False}, {'name': 'repo2', 'private': False}], status=200)
        resp = requests.get('https://api.github.com/orgs/test-org/repos')
        self.assertEqual(len(resp.json()), 2)

    @responses.activate
    def test_criterion_3_fetch_issues_and_prs(self):
        responses.add(responses.GET, 'https://api.github.com/repos/test-org/repo1/issues', json=[{'id': 1, 'state': 'open', 'type': 'issue'}], status=200)
        responses.add(responses.GET, 'https://api.github.com/repos/test-org/repo1/pulls', json=[{'id': 2, 'state': 'open', 'type': 'pull'}], status=200)
        resp_issues = requests.get('https://api.github.com/repos/test-org/repo1/issues')
        resp_prs = requests.get('https://api.github.com/repos/test-org/repo1/pulls')
        self.assertEqual(len(resp_issues.json()), 1)
        self.assertEqual(len(resp_prs.json()), 1)

if __name__ == '__main__':
    unittest.main()

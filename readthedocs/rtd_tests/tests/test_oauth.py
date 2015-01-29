from django.test import TestCase

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken

from projects.models import Project

from oauth.utils import make_github_project, make_github_organization, import_github
from oauth.models import GithubOrganization, GithubProject


class RedirectOauth(TestCase):

    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug='pip')
        self.org = GithubOrganization()
        self.privacy = self.project.version_privacy_level

    def test_make_github_project_pass(self):
        repo_json = {
            "name": "",
            "full_name": "",
            "description": "",
            "git_url": "",
            "private": False,
            "ssh_url": "",
            "html_url": "",
        }
        github_project = make_github_project(user=self.user, org=self.org, privacy=self.privacy, repo_json=repo_json)
        self.assertIsInstance(github_project, GithubProject)

    def test_make_github_project_fail(self):
        repo_json = {
            "name": "",
            "full_name": "",
            "description": "",
            "git_url": "",
            "private": True,
            "ssh_url": "",
            "html_url": "",
        }
        github_project = make_github_project(user=self.user, org=self.org, privacy=self.privacy, repo_json=repo_json)
        self.assertIsNone(github_project)

    def test_make_github_organization(self):
        org_json = {
            "html_url": "",
            "name": "",
            "email": "",
            "login": "",
        }
        org = make_github_organization(self.user, org_json)
        self.assertIsInstance(org, GithubOrganization)

    def test_import_github_with_no_token(self):
        github_connected = import_github(self.user, sync=True)
        self.assertEqual(github_connected, False)

    def test_multiple_users_same_repo(self):
        repo_json = {
            "name": "",
            "full_name": "testrepo/multiple",
            "description": "",
            "git_url": "",
            "private": False,
            "ssh_url": "",
            "html_url": "",
        }
        github_project = make_github_project(user=self.user, org=self.org, privacy=self.privacy, repo_json=repo_json)
        github_project_2 = make_github_project(user=User.objects.get(pk=2), org=self.org, privacy=self.privacy, repo_json=repo_json)
        self.assertIsInstance(github_project, GithubProject)
        self.assertIsInstance(github_project_2, GithubProject)
        self.assertNotEqual(github_project_2, github_project)

        github_project_3 = make_github_project(user=self.user, org=self.org, privacy=self.privacy, repo_json=repo_json)
        github_project_4 = make_github_project(user=User.objects.get(pk=2), org=self.org, privacy=self.privacy, repo_json=repo_json)
        self.assertIsInstance(github_project_3, GithubProject)
        self.assertIsInstance(github_project_4, GithubProject)
        self.assertEqual(github_project, github_project_3)
        self.assertEqual(github_project_2, github_project_4)

        github_project_5 = make_github_project(user=self.user, org=self.org, privacy=self.privacy, repo_json=repo_json)
        github_project_6 = make_github_project(user=User.objects.get(pk=2), org=self.org, privacy=self.privacy, repo_json=repo_json)
        
        self.assertEqual(github_project, github_project_5)
        self.assertEqual(github_project_2, github_project_6)

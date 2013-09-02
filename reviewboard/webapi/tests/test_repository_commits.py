import os

from djblets.testing.decorators import add_fixtures
from djblets.webapi.errors import INVALID_FORM_DATA

from reviewboard import scmtools
from reviewboard.scmtools.models import Repository, Tool
from reviewboard.site.models import LocalSite
from reviewboard.webapi.errors import REPO_NOT_IMPLEMENTED
from reviewboard.webapi.tests.base import BaseWebAPITestCase
from reviewboard.webapi.tests.mimetypes import repository_commits_item_mimetype
from reviewboard.webapi.tests.urls import get_repository_commits_url


class RepositoryCommitsResourceTests(BaseWebAPITestCase):
    """Testing the RepositoryCommitsResource APIs."""
    fixtures = ['test_users', 'test_scmtools']

    def test_get_repository_commits(self):
        """Testing the GET repositories/<id>/commits/ API"""
        rsp = self.apiGet(get_repository_commits_url(self.repository),
                          query={'start': 5},
                          expected_mimetype=repository_commits_item_mimetype)
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['commits']), 5)
        self.assertEqual(rsp['commits'][0]['date'],
                         '2010-05-21T09:33:40.893946')
        self.assertEqual(rsp['commits'][3]['author_name'], 'emurphy')

    def test_get_repository_commits_without_start(self):
        """Testing the GET repositories/<id>/commits/ API without providing a start parameter"""
        rsp = self.apiGet(get_repository_commits_url(self.repository),
                          expected_status=400)
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], INVALID_FORM_DATA.code)
        self.assertTrue('start' in rsp['fields'])

    @add_fixtures(['test_site'])
    def test_get_repository_commits_with_site(self):
        """Testing the GET repositories/<id>/commits/ API with a local site"""
        self._login_user(local_site=True)
        self.repository.local_site = \
            LocalSite.objects.get(name=self.local_site_name)
        self.repository.save()

        rsp = self.apiGet(
            get_repository_commits_url(self.repository, self.local_site_name),
            query={'start': 7},
            expected_mimetype=repository_commits_item_mimetype)
        self.assertEqual(len(rsp['commits']), 7)
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['commits'][0]['id'], '7')
        self.assertEqual(rsp['commits'][1]['message'],
                         'Add a branches directory')

    @add_fixtures(['test_site'])
    def test_get_repository_commits_with_site_no_access(self):
        """Testing the GET repositories/<id>/commits/ API with a local site and Permission Denied error"""
        self.repository.local_site = \
            LocalSite.objects.get(name=self.local_site_name)
        self.repository.save()

        self.apiGet(
            get_repository_commits_url(self.repository, self.local_site_name),
            expected_status=403)

    def test_get_repository_commits_with_no_support(self):
        """Testing the GET repositories/<id>/commits/ API with a repository that does not implement it"""
        hg_repo_path = os.path.join(os.path.dirname(scmtools.__file__),
                                    'testdata', 'hg_repo.bundle')
        repository = Repository(name='Test HG',
                                path=hg_repo_path,
                                tool=Tool.objects.get(name='Mercurial'))
        repository.save()

        rsp = self.apiGet(
            get_repository_commits_url(repository),
            query={'start': ''},
            expected_status=501)
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], REPO_NOT_IMPLEMENTED.code)
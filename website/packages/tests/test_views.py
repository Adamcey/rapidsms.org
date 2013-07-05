import mock

from website.tests import factories
from website.tests.base import ViewTestMixin, WebsiteTestBase

from ..models import Package
from .base import MockPyPIRequest


__all__ = ['TestPackageCreateView', 'TestPackageDetailView',
        'TestPackageEditView', 'TestPackageFlagView', 'TestPackageRefreshView']


class PackageViewTestBase(ViewTestMixin, WebsiteTestBase):

    def _post(self, *args, **kwargs):
        status_code = kwargs.pop('mock_status_code', None)
        with mock.patch.object(Package, '_get_pypi_request') as mock_get:
            mock_get.return_value = MockPyPIRequest(status_code=status_code)
            return super(PackageViewTestBase, self)._post(*args, **kwargs)


class TestPackageCreateView(PackageViewTestBase):
    url_name = 'package_create'
    template_name = 'packages/package_form.html'

    def test_get_authenticated(self):
        self.login_user(factories.UserFactory.create())
        response = self._get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertFalse('object' in response.context)

    def test_get_unauthenticated(self):
        self.client.logout()
        response = self._get()
        self.assertRedirectsToLogin(response)

    def test_post_unauthenticated(self):
        self.client.logout()
        response = self._post()
        self.assertRedirectsToLogin(response)

    def test_create(self):
        self.login_user(factories.UserFactory.create())
        response = self._post(data={
            'pkg_type': Package.APPLICATION,
            'name': 'test-application',
        })
        self.assertEquals(Package.objects.count(), 1)
        pkg = Package.objects.get()
        self.assertRedirectsNoFollow(response, pkg.get_absolute_url())

    def test_create_invalid(self):
        self.login_user(factories.UserFactory.create())
        response = self._post(data={
            'pkg_type': 'invalid',
            'name': 'test-application',
        })
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertFalse(response.context['form'].is_valid())


class TestPackageDetailView(PackageViewTestBase):
    url_name = 'package_detail'
    template_name = 'packages/package_detail.html'

    def setUp(self):
        super(TestPackageDetailView, self).setUp()
        self.package = factories.PackageFactory.create()
        self.url_kwargs = {'slug': self.package.slug}

    def test_get_authenticated(self):
        self.login_user(factories.UserFactory.create())
        response = self._get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertEquals(response.context['object'], self.package)

    def test_get_unauthenticated(self):
        self.client.logout()
        response = self._get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertEquals(response.context['object'], self.package)

    def test_get_bad_slug(self):
        response = self._get(url_kwargs={'slug': 'invalid'})
        self.assertEquals(response.status_code, 404)

    def test_get_is_inactive(self):
        self.package.is_active = False
        self.package.save()
        response = self._get()
        self.assertEquals(response.status_code, 404)


class TestPackageEditView(PackageViewTestBase):
    url_name = 'package_edit'
    template_name = 'packages/package_form.html'

    def setUp(self):
        super(TestPackageEditView, self).setUp()
        self.user = factories.UserFactory.create()
        self.login_user(self.user)
        self.package = factories.PackageFactory.create()
        self.url_kwargs = {'slug': self.package.slug}

    def test_get_authenticated(self):
        response = self._get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertEquals(response.context['object'], self.package)

    def test_get_unauthenticated(self):
        self.client.logout()
        response = self._get()
        self.assertRedirectsToLogin(response)

    def test_get_bad_slug(self):
        response = self._get(url_kwargs={'slug': 'invalid'})
        self.assertEquals(response.status_code, 404)

    def test_get_inactive(self):
        self.package.is_active = False
        self.package.save()
        response = self._get()
        self.assertEquals(response.status_code, 404)

    def test_post_unauthenticated(self):
        self.client.logout()
        response = self._post()
        self.assertRedirectsToLogin(response)

    def test_edit(self):
        new_url = 'http://example.com/tests'
        response = self._post(data={
            'tests_url': new_url,
        })
        self.assertRedirectsNoFollow(response, self.package.get_absolute_url())
        package = Package.objects.get(pk=self.package.pk)
        self.assertEquals(package.tests_url, new_url)

    def test_edit_invalid(self):
        new_url = 'invalid'
        response = self._post(data={
            'tests_url': new_url,
        })
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertEquals(response.context['object'], self.package)
        self.assertNotEquals(response.context['object'].tests_url, new_url)
        self.assertFalse(response.context['form'].is_valid())



class TestPackageFlagView(PackageViewTestBase):
    url_name = 'package_flag'
    template_name = 'packages/package_flag.html'

    def setUp(self):
        super(TestPackageFlagView, self).setUp()
        self.user = factories.UserFactory.create()
        self.login_user(self.user)
        self.package = factories.PackageFactory.create()
        self.url_kwargs = {'slug': self.package.slug}

    def test_get_authenticated(self):
        response = self._get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertEquals(response.context['object'], self.package)

    def test_get_unauthenticated(self):
        self.client.logout()
        response = self._get()
        self.assertRedirectsToLogin(response)

    def test_post_unauthenticated(self):
        self.client.logout()
        response = self._post()
        self.assertRedirectsToLogin(response)

    def test_flag(self):
        response = self._post(data={
            'reason': 'reason',
        })
        self.assertRedirectsNoFollow(response, self.package.get_absolute_url())
        pkg = Package.objects.get(pk=self.package.pk)
        self.assertTrue(pkg.is_flagged)
        # TODO: check that email was sent.

    def test_flag_invalid(self):
        response = self._post(data={
            'reason': '',
        })
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertEquals(response.context['object'], self.package)
        self.assertFalse(response.context['form'].is_valid())
        # TODO: check that email was NOT sent.


class TestPackageRefreshView(PackageViewTestBase):
    url_name = 'package_refresh'

    def setUp(self):
        super(TestPackageRefreshView, self).setUp()
        self.user = factories.UserFactory.create()
        self.login_user(self.user)
        self.package = factories.PackageFactory.create()
        self.url_kwargs = {'slug': self.package.slug}

    def test_get(self):
        response = self._get()
        self.assertEquals(response.status_code, 405)

    def test_post_unauthenticated(self):
        self.client.logout()
        response = self._post()
        self.assertRedirectsToLogin(response)

    def test_refresh(self):
        response = self._post()
        self.assertRedirectsNoFollow(response, self.package.get_edit_url())
        # TODO: check that PyPI was called and data was updated.

    def test_refresh_failure(self):
        response = self._post(mock_status_code=500)
        self.assertRedirectsNoFollow(response, self.package.get_edit_url())
        # TODO: check that data was NOT updated.
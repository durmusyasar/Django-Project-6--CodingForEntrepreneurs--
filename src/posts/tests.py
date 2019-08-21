from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.utils.text import slugify
from django.utils import timezone
from .forms import PostForm
from .models import Post # from http://kirr.co/9u0caa/ the posts app.
from .views import post_update, post_create
from rest_framework.test import APIRequestFactory, force_authenticate
from posts.api.views import (
    PostCreateAPIView,
    PostDeleteAPIView,
    PostDetailAPIView,
    PostListAPIView,
    PostUpdateAPIView,
    )

class PostModelTestCase(TestCase):
    def setUp(self):
        Post.objects.create(title='A new title', slug='some-prob-unique-slug-by-this-test-abc-123')

    def create_post(self, title='This title'):
        return Post.objects.create(title=title)

    def test_post_title(self):
        obj = Post.objects.get(slug='some-prob-unique-slug-by-this-test-abc-123')
        self.assertEqual(obj.title, 'A new title')
        self.assertTrue(obj.content == "") # maybe i want to change 

    def test_post_slug(self):
        # generate slug
        title1 = 'another title abc'
        title2 = 'another title abc'
        title3 = 'another title abc'
        slug1 = slugify(title1)
        slug2 = slugify(title2)
        slug3 = slugify(title3)
        obj1 = self.create_post(title=title1)
        obj2 = self.create_post(title=title2)
        obj3 = self.create_post(title=title2)
        self.assertEqual(obj1.slug, slug1)
        self.assertNotEqual(obj2.slug, slug2)
        self.assertNotEqual(obj3.slug, slug3)

    def test_post_qs(self):
        title1 = 'another title abc'
        obj1 = self.create_post(title=title1)
        obj2 = self.create_post(title=title1)
        obj3 = self.create_post(title=title1)
        qs = Post.objects.filter(title=title1)
        self.assertEqual(qs.count(), 3)
        qs2 = Post.objects.filter(slug=obj1.slug)
        self.assertEqual(qs2.count(), 1)

class PostFormTestCase(TestCase):
    def test_valid_form(self):
        title = 'A new title'
        slug = 'some-prob-unique-slug-by-this-test-abc-123'
        content  = 'some content'
        obj = Post.objects.create(title=title, slug=slug, publish=timezone.now(), content=content)
        data = {'title': obj.title, "slug": obj.slug, "publish": obj.publish, "content": content}
        form = PostForm(data=data) # PostForm(request.POST)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('title'), obj.title)
        self.assertNotEqual(form.cleaned_data.get("content"), "Another item")

    def test_invalid_form(self):
        title = 'A new title'
        slug = 'some-prob-unique-slug-by-this-test-abc-123'
        content  = 'some content'
        obj = Post.objects.create(title=title, slug=slug, publish=timezone.now(), content=content)
        data = {'title': obj.title, "slug": obj.slug, "publish": obj.publish, "content": ""}
        form = PostForm(data=data) # PostForm(request.POST)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)


class PostViewTestCase(TestCase):
    def create_post(self, title='This title'):
        return Post.objects.create(title=title)

    def test_list_view(self):
        list_url = reverse("posts:list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)


    def test_detail_view(self):
        obj = self.create_post(title='Another New Title Test')
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    
    def test_update_view(self):
        obj = self.create_post(title='Another New Title Test')
        edit_url = reverse("posts:update", kwargs={"slug": obj.slug})
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 404)

    def test_delete_view(self):
        obj = self.create_post(title='Another New Title Test')
        delete_url = obj.get_absolute_url() + "delete/"
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 404)


User = get_user_model()

class PostViewAdvanceTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(
                    username='abc123test123',
                    email = 'abc123test123@gmail.com',
                    password = 'pwtest123#$$$',
                    is_staff=True,
                    is_superuser=True,
                )

    def create_post(self, title='This title'):
        return Post.objects.create(title=title)

    def test_user_auth(self):
        obj = self.create_post(title='Another New Title Test')
        edit_url = reverse("posts:update", kwargs={"slug": obj.slug})
        request = self.factory.get(edit_url)
        request.user = self.user
        response = post_update(request, slug=obj.slug)
        self.assertEqual(response.status_code, 200)
        #print(request.user.is_authenticated())

    def test_user_post(self):
        obj = self.create_post(title='Another New Title Test')
        request = self.factory.post("/posts/create/")
        request.user = self.user
        response = post_create(request)
        self.assertEqual(response.status_code, 200)
        #print(request.user.is_authenticated())

    def test_empty_page(self):
        page = '/asdfads/asdfasd/fasdfasdfasd/'
        request = self.factory.get(page)
        request.user = self.user
        response = post_create(request)
        self.assertEqual(response.status_code, 200)

    def test_unauth_user(self):
        obj = self.create_post(title='Another New Title Test')
        edit_url = reverse("posts:update", kwargs={"slug": obj.slug})
        request = self.factory.get(edit_url)
        request.user = AnonymousUser()
        response = post_update(request, slug=obj.slug)
        '''
        Using Class Based views instead of FBVs
        response = PostUpdateView.as_view()(request)
        '''
        self.assertEqual(response.status_code, 404)


class PostAPITest(TestCase):
    def setUp(self):
        self.data = {"title": "Some title", "content": "New content", "publish": timezone.now().date()}
        self.factory = APIRequestFactory()
        self.user = User.objects.create(
                    username='abc123test123',
                    email = 'abc123test123@gmail.com',
                    password = 'pwtest123#$$$',
                    is_staff=True,
                    is_superuser=True,
                )

    def create_post(self, title='This title'):
        return Post.objects.create(title=title)

    def test_get_data(self):
        # GET METHOD
        list_url = reverse("posts-api:list")
        obj = self.create_post()
        detail_url = reverse("posts-api:detail", kwargs={"slug": obj.slug})

        request = self.factory.get(list_url)
        response = PostListAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.get(detail_url)
        response = PostDetailAPIView.as_view()(request, slug=obj.slug)
        self.assertEqual(response.status_code, 200)

    def test_post_data(self):
        create_url = reverse("posts-api:create")
        request = self.factory.post(create_url, data=self.data)
        response1 = PostCreateAPIView.as_view()(request)
        self.assertEqual(response1.status_code, 401)

        force_authenticate(request, user=self.user)
        response2 = PostCreateAPIView.as_view()(request)
        self.assertEqual(response2.status_code, 201)

    def test_update_data(self):
        obj = self.create_post()
        update_url = reverse("posts-api:update", kwargs={"slug": obj.slug})
        request = self.factory.put(update_url, data=self.data)
        response1 = PostUpdateAPIView.as_view()(request, slug=obj.slug)
        self.assertEqual(response1.status_code, 401)

        force_authenticate(request, user=self.user)
        response2 = PostUpdateAPIView.as_view()(request, slug=obj.slug)
        self.assertEqual(response2.status_code, 200)


    def test_delete_data(self):
        obj = self.create_post(title='another new title')
        delete_url = reverse("posts-api:delete", kwargs={"slug": obj.slug})
        request = self.factory.delete(delete_url)
        response1 = PostDeleteAPIView.as_view()(request, slug=obj.slug)
        self.assertEqual(response1.status_code, 401)

        force_authenticate(request, user=self.user)
        response2 = PostDeleteAPIView.as_view()(request, slug=obj.slug)
        self.assertEqual(response2.status_code, 204)
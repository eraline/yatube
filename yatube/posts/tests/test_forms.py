import shutil
import tempfile

from django.test.utils import override_settings

from posts.models import Group, Post, User
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test-group',
            description='Test group'
        )
        cls.post = Post.objects.create(
            text='Первый тестовый пост',
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)
        self.guest_client = Client()

    def test_create_post(self):
        '''Тестируем создание поста'''
        post_count = Post.objects.count()
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=test_image,
            content_type='image/jpg'
        )

        form_data = {
            'text': 'Новый созданный пост',
            'group': PostFormTests.group.pk,
            'image': uploaded_image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Новый созданный пост',
                group=PostFormTests.group,
                author=PostFormTests.user
            ).exists()
        )

    def test_post_edit(self):
        '''Тестируем редактирование поста'''
        initial_text = PostFormTests.post.text
        post_id = PostFormTests.post.pk
        form_data = {
            'text': 'Измененный пост'
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=(post_id,)),
            data=form_data,
            follow=True
        )
        # Проверяем, что текст поста изменился
        new_text = Post.objects.get(pk=post_id).text
        self.assertNotEqual(initial_text, new_text)

    def test_comments_authorized_only(self):
        post = PostFormTests.post
        post_id = post.pk
        user = PostFormTests.user
        comment_count = post.comments.count()
        form_data = {
            'text': 'Test Comment',
            'post': post,
            'author': user
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=(post_id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(comment_count, post.comments.count())
        self.authorized_client.post(
            reverse('posts:add_comment', args=(post_id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(comment_count + 1, post.comments.count())

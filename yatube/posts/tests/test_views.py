import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, Comment, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
# User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Создаём двух разных юзеров, две группы, два поста для юзера auth
        # и 12 постов для юзера shlomo
        super().setUpClass()

        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded_image = SimpleUploadedFile(
            name='test.jpg',
            content=test_image,
            content_type='image/jpg'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.second_user = User.objects.create_user(username='shlomo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы')

        cls.second_group = Group.objects.create(
            title='Вторая тестовая группа',
            slug='second_group',
            description='Тестовое описание группы')

        Post.objects.create(
            text='Тестовый текст поста 2, второй группы',
            author=cls.user,
            group=cls.second_group)

        posts_obj = []
        for i in range(12):
            posts_obj.append(
                Post(text=('Тестовый текст поста второго юзера', i),
                     author=cls.second_user,
                     group=cls.second_group)
            )
        Post.objects.bulk_create(posts_obj)

        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded_image)

        cls.post_id = cls.post.pk

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        post_id = PostsPagesTests.post.pk
        template_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': post_id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': post_id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in template_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        '''Проверяем, что передается пост в объекте страницы'''
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверяем, что картинка передается в посте
        self.assertTrue(response.context['page_obj'][0].image)
        self.assertIsInstance(response.context['page_obj'][0], Post)

    def test_group_list_shows_correct_context(self):
        '''Проверяем, что передается верный контекст на страницу группы'''
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
        )
        self.assertIsInstance(response.context['page_obj'][0], Post)
        self.assertIsInstance(response.context['group'], Group)
        # Проверяем, что картинка передается в посте
        self.assertTrue(response.context['page_obj'][0].image)
        # Проверяем, что отдаёт только один пост группы test_slug
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_shows_correct_context(self):
        '''Проверяем, что передается верый контекст на страницу профиля'''
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        # Проверяем, что это пост
        self.assertIsInstance(response.context['page_obj'][0], Post)
        # Проверяем переданный user_profile
        self.assertIsInstance(response.context['author'], User)
        # Проверяем, что картинка передается в посте
        self.assertTrue(response.context['page_obj'][0].image)
        # Проверяем, что отдаёт только два поста юзера auth
        self.assertEqual(len(response.context['page_obj']), 2)
        
        self.assertIsInstance(response.context['following'], bool)

    def test_post_detail_shows_correct_context(self):
        '''Проверяем, что передается верный контекст на страницу поста'''
        post_count = PostsPagesTests.user.posts.all().count()
        test_comment = Comment.objects.create(
            text='Test comment',
            post=PostsPagesTests.post,
            author=PostsPagesTests.second_user
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsPagesTests.post_id})
        )
        # Проверяем, что это пост
        self.assertIsInstance(response.context['post'], Post)
        # Проверяем, что картинка передается в посте
        self.assertTrue(response.context['post'].image)
        # Проверяем, что количество постов соответствует
        self.assertEqual(response.context['post_count'], post_count)
        self.assertEqual(response.context['comments'][0], test_comment)

    def test_edit_post_shows_correct_context(self):
        '''Верная ли форма в контексте на странице edit post'''
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsPagesTests.post_id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        self.assertTrue(response.context['is_edit'])
        self.assertEqual(response.context['post_id'],
                         PostsPagesTests.post_id)

    def test_create_post_shows_correct_context(self):
        '''Проверяем типы полей у формы при создани поста'''
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    # Тестируем Паджинатор
    def test_first_page_paginator(self):
        '''Паджинатор передает 10 постов на страницу'''
        posts_per_page = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': 'second_group'}),
            reverse('posts:profile',
                    kwargs={'username': 'shlomo'})
        )
        for reverse_name in posts_per_page:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_paginator(self):
        '''Тестирум вторую страницу паджинатора'''
        posts_per_page = {
            reverse('posts:index'): 4,
            reverse('posts:group_list',
                    kwargs={'slug': 'second_group'}): 3,
            reverse('posts:profile',
                    kwargs={'username': 'shlomo'}): 2,
        }
        for reverse_name, pages in posts_per_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), pages)

    def test_adding_post(self):
        '''Проверяем, что пост добавляется на нужные страницы'''
        test_post = Post.objects.create(
            text='Recently Added Post',
            author=PostsPagesTests.user,
            group=PostsPagesTests.group
        )

        pages = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}),
            reverse('posts:profile',
                    kwargs={'username': 'auth'}),
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(
                    response.context['page_obj'][0], test_post)

        # Проверка, что пост не добавляется в чужую группу
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'second_group'})
        )
        self.assertNotEqual(
            response.context['page_obj'][0], test_post)

    def test_following(self):
        #PostsPagesTests.authorized_client.get(
        #    'posts:profile_follow', args=(PostsPagesTests.user.username,),
        #)
        pass 

class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest = Client()
        cls.user = User.objects.create_user(username='cache')
        cls.post = Post.objects.create(
            text='Test cache page',
            author=cls.user)

    def test_index_page_is_cached(self):
        '''Проверяем кэшируется ли главная страница'''
        initial_response = CacheTests.guest.get(reverse('posts:index'))
        CacheTests.post.delete()
        second_response = CacheTests.guest.get(reverse('posts:index'))
        cache.clear()
        third_response = CacheTests.guest.get(reverse('posts:index'))
        self.assertEqual(initial_response.content,
                         second_response.content,
                         'Страница не была закэширована')
        self.assertNotEqual(initial_response.content,
                            third_response.content,
                            'Кэш не отчистился')

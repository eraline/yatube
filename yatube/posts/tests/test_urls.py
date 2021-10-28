from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another_user = User.objects.create_user(username='another_user')
        cls.another_client = Client()
        cls.another_client.force_login(cls.another_user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы')
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group)

    # Проверяем общудоступные страницы

    def test_homepage(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.status_code, 200)

    def test_group_page_url_exists_at_desired_location(self):
        response = self.guest_client.get(
            reverse('posts:group_list', args=['test_slug'])
        )
        self.assertEqual(response.status_code, 200)

    def test_profile_url_exists_at_desired_location(self):
        response = self.guest_client.get(
            reverse('posts:profile', args=['auth'])
        )
        self.assertEqual(response.status_code, 200)

    def test_post_detail_url_exists_at_desired_location(self):
        post_id = PostsURLTests.post.pk
        response = self.guest_client.get(
            reverse('posts:post_detail', args=[post_id])
        )
        self.assertEqual(response.status_code, 200)

    # Проверяем редиректы для неавторизованного пользователя
    def test_create_post_redirect_guest(self):
        '''Проверка создания поста для неавторизованного юзера'''
        response = self.guest_client.get(
            reverse('posts:post_create'),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/create/'
        )

    # Проверяем редирект для не-автора
    def test_post_edit_redirect_not_author(self):
        '''Проверка, что для не автора при попытке
         редактировании поста будет редирект на пост'''
        post_id = PostsURLTests.post.pk
        response = self.another_client.get(
            reverse('posts:post_edit', args=[post_id]),
            follow=True
        )
        self.assertRedirects(
            response, (reverse('posts:post_detail', args=[post_id]))
        )

    def test_unexisting_page_404(self):
        '''Проверяем, что несуществующая страница вернет 404'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_templates(self):
        '''Проверяем корректные ли шаблоны используются'''
        post_id = PostsURLTests.post.pk
        template_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=['test_slug']):
                'posts/group_list.html',
            reverse('posts:profile', args=['auth']): 'posts/profile.html',
            reverse('posts:post_detail', args=[post_id]):
                'posts/post_detail.html',
            reverse('posts:post_edit', args=[post_id]):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in template_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

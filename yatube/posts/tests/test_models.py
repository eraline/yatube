from django.contrib.auth import get_user_model

from django.test import TestCase
from posts.models import Post, Group

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы')
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostsModelTest.post
        group = PostsModelTest.group
        field_str = {
            post: 'Тестовый текст ',
            group: 'Тестовая группа'
        }
        for object, expected_value in field_str.items():
            with self.subTest(object=object):
                self.assertEqual(
                    str(object), expected_value
                )

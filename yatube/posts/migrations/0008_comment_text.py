# Generated by Django 2.2.16 on 2021-10-21 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='text',
            field=models.TextField(default='Text', verbose_name='Текст комментария'),
            preserve_default=False,
        ),
    ]
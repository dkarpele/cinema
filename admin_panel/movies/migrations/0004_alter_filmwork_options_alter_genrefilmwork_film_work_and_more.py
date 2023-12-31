# Generated by Django 4.1.7 on 2023-03-24 20:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0003_rename_person_filmwork_persons'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filmwork',
            options={'ordering': ['-id'], 'verbose_name': 'verbose_name_filmwork', 'verbose_name_plural': 'verbose_name_filmwork_plural'},
        ),
        migrations.AlterField(
            model_name='genrefilmwork',
            name='film_work',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='genrefilmwork', to='movies.filmwork', verbose_name='film_work'),
        ),
        migrations.AlterField(
            model_name='genrefilmwork',
            name='genre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='genrefilmwork', to='movies.genre', verbose_name='genre'),
        ),
        migrations.AlterField(
            model_name='personfilmwork',
            name='film_work',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='personfilmwork', to='movies.filmwork', verbose_name='film_work'),
        ),
        migrations.AlterField(
            model_name='personfilmwork',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='personfilmwork', to='movies.person', verbose_name='person'),
        ),
    ]

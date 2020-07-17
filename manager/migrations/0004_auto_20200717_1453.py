# Generated by Django 3.0.6 on 2020-07-17 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0003_task_command'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='sensors',
            field=models.ManyToManyField(blank=True, to='manager.Sensor'),
        ),
        migrations.AlterField(
            model_name='plant',
            name='tasks',
            field=models.ManyToManyField(blank=True, to='manager.Task'),
        ),
    ]
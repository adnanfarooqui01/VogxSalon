"""
Migration to add firebase_uid field to CustomUser model.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Adjust based on your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='firebase_uid',
            field=models.CharField(
                blank=True,
                help_text='Firebase user UID for phone authentication',
                max_length=128,
                null=True,
                unique=True
            ),
        ),
    ]

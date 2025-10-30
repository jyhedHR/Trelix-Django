import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0005_alter_badge_description_alter_badge_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badge',
            name='icon',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='image', blank=True, null=True),
        ),
    ]


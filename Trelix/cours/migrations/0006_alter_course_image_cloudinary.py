import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cours', '0005_chapterquizscore'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='image',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='image', blank=True, null=True),
        ),
    ]


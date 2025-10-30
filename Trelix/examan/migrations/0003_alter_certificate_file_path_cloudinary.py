import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('examan', '0002_answer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificate',
            name='file_path',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='image', blank=True, null=True),
        ),
    ]


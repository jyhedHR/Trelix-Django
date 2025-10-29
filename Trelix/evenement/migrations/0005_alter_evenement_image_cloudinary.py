import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('evenement', '0004_alter_evenement_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evenement',
            name='image',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='image', blank=True, null=True),
        ),
    ]
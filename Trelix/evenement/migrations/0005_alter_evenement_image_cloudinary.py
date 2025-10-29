import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('evenement', '0003_alter_evenement_image_alter_evenement_titre'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evenement',
            name='image',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='image', blank=True, null=True),
        ),
    ]
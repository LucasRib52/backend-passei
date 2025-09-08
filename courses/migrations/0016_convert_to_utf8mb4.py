# Generated manually for emoji support

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0015_category_icon'),
    ]

    operations = [
        migrations.RunSQL(
            # SQL para converter charset para utf8mb4
            sql=[
                "ALTER TABLE courses_course CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE courses_course MODIFY COLUMN description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE courses_course MODIFY COLUMN detailed_description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE courses_course MODIFY COLUMN content TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE courses_course MODIFY COLUMN benefits TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE courses_course MODIFY COLUMN requirements TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            ],
            # SQL reverso (não é crítico para emojis, mas mantém consistência)
            reverse_sql=[
                "ALTER TABLE courses_course CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;",
            ],
        ),
    ]

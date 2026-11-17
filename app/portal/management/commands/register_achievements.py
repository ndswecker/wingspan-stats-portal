from django.core.management.base import BaseCommand

from ...services.achievements.registry import ALL_ACHIEVEMENTS


class Command(BaseCommand):
    help = "Register achievement definitions in the database."

    def handle(self, *args, **options):
        for achievement_class in ALL_ACHIEVEMENTS:
            achievement = achievement_class.register()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Registered achievement: {achievement.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Achievement registration completed."
            )
        )
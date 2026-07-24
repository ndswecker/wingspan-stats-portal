import csv
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.models import Game, GameResult, Player


class Command(BaseCommand):
    help = "Replace game data from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path to the CSV file containing game data",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])

        if not csv_path.is_file():
            raise CommandError(f"CSV file not found: {csv_path}")

        games_created = 0
        results_created = 0
        players_created = 0

        with csv_path.open(
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            date_column = "date_played"
            player_columns = [
                column
                for column in reader.fieldnames
                if column != date_column
            ]

            with transaction.atomic():
                Game.objects.all().delete()
                Player.objects.all().delete()

                players = {}

                for player_name in player_columns:
                    player, created = Player.objects.get_or_create(
                        name=player_name.strip(),
                    )
                    players[player_name] = player

                    if created:
                        players_created += 1

                for row in reader:
                    game = Game.objects.create(
                        date_played=date.fromisoformat(
                            row[date_column].strip()
                        ),
                        human_player_mode=(
                            Game.HumanPlayerMode.MULTIPLE
                        ),
                    )
                    games_created += 1

                    for player_name in player_columns:
                        score_value = row[player_name].strip()

                        if not score_value:
                            continue

                        GameResult.objects.create(
                            game=game,
                            player=players[player_name],
                            score=int(score_value),
                        )
                        results_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {games_created} games, "
                f"{results_created} results, and "
                f"{players_created} players."
            )
        )
import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.models import Player, Game, GameResult

class Command(BaseCommand):
    help = "Import games from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path to the CSV file containing game data",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")
        
        games_created = 0
        results_created = 0
        players_created = 0

        with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)

            if not reader.fieldnames or len(reader.fieldnames) < 2:
                raise CommandError("CSV file must have at least two columns: date and player scores")
            
            date_column = reader.fieldnames[0]
            player_columns = reader.fieldnames[1:]

            with transaction.atomic():
                players = {}

                for column_name in player_columns:
                    player, created = Player.objects.get_or_create(
                        name=column_name.strip()
                    )
                    players[column_name] = player
                    if created:
                        players_created += 1

                for row_number, row in enumerate(reader, start=2):
                    date_value = row[date_column].strip()

                    if not date_value:
                        raise CommandError(f"Missing date value in row {row_number}")

                    date_played = datetime.strptime(date_value, "%m/%d/%Y").date()
                    game  = Game.objects.create(date_played=date_played)
                    games_created += 1

                    for column_name in player_columns:
                        score_value = row[column_name].strip()

                        if not score_value:
                            continue

                        score = int(score_value)

                        GameResult.objects.create(
                            game=game,
                            player=players[column_name],
                            score=score,
                        )
                        results_created += 1

        self.stdout.write(
            self.style.SUCCESS(
            f"Successfully imported {games_created} games, {results_created} results, and {players_created} players."
            )
        )
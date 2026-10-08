"""Tests for the turn-order research dataset preparation pipeline.

Run manually with:
    python manage.py test portal.tests.test_turn_order_research

These tests use Django's isolated test database, not the development database.
"""

from datetime import date

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from portal.models import Game, GameResult, Player
from portal.services.research.turn_order_research import (
    GamePrincipalOutcome,
    build_turn_order_dataset,
    build_turn_order_game_record,
    select_turn_order_games,
)


class TurnOrderResearchTestBase(TestCase):
    """Shared, explicit test-data setup for turn-order research tests."""

    @classmethod
    def setUpTestData(cls):
        cls.principal = Player.objects.create(name="Nate", handle="nate")
        cls.opponent = Player.objects.create(name="Nick", handle="nick")
        cls.other_player = Player.objects.create(name="Alex", handle="alex")

    def create_game(
        self,
        *,
        date_played=date(2026, 9, 15),
        mode=Game.HumanPlayerMode.MULTIPLE,
        principal_turn=1,
        opponent_turn=2,
        principal_score=100,
        opponent_score=90,
        principal_player=None,
        opponent_player=None,
        include_principal=True,
        include_opponent=True,
        additional_player=False,
        principal_confirmed=False,
        opponent_confirmed=False,
    ):
        """Create a game and its recorded human results."""
        principal_player = principal_player or self.principal
        opponent_player = opponent_player or self.opponent

        game = Game.objects.create(
            date_played=date_played,
            human_player_mode=mode,
        )

        if include_principal:
            GameResult.objects.create(
                game=game,
                player=principal_player,
                score=principal_score,
                turn_order=principal_turn,
                is_confirmed=principal_confirmed,
            )

        if include_opponent:
            GameResult.objects.create(
                game=game,
                player=opponent_player,
                score=opponent_score,
                turn_order=opponent_turn,
                is_confirmed=opponent_confirmed,
            )

        if additional_player:
            GameResult.objects.create(
                game=game,
                player=self.other_player,
                score=80,
                turn_order=3,
            )

        return game


class SelectTurnOrderGamesTests(TurnOrderResearchTestBase):
    def select(self, **kwargs):
        return select_turn_order_games(
            principal_player=self.principal,
            opponent_player=self.opponent,
            **kwargs,
        )

    def test_selects_only_qualifying_competitive_games(self):
        included = self.create_game()
        self.create_game(mode=Game.HumanPlayerMode.SINGLE)
        self.create_game(include_principal=False)
        self.create_game(include_opponent=False)
        self.create_game(additional_player=True)
        self.create_game(opponent_player=self.other_player)
        self.create_game(principal_turn=None)
        self.create_game(opponent_turn=None)

        games = self.select()

        self.assertEqual([game.pk for game in games], [included.pk])

    def test_unconfirmed_games_are_not_excluded(self):
        game = self.create_game(
            principal_confirmed=False,
            opponent_confirmed=False,
        )
        self.assertEqual([g.pk for g in self.select()], [game.pk])

    def test_turn_order_requires_presence_not_range(self):
        # Research selection intentionally checks only non-null values.
        # Upstream entry validation owns the 1-5 range requirement.
        game = self.create_game(principal_turn=6, opponent_turn=7)
        self.assertEqual([g.pk for g in self.select()], [game.pk])

    def test_optional_date_boundaries_are_inclusive(self):
        earlier = self.create_game(date_played=date(2026, 9, 1))
        first = self.create_game(date_played=date(2026, 9, 10))
        last = self.create_game(date_played=date(2026, 9, 20))
        later = self.create_game(date_played=date(2026, 10, 1))

        self.assertEqual(
            [g.pk for g in self.select(start_date=date(2026, 9, 10), end_date=date(2026, 9, 20))],
            [first.pk, last.pk],
        )
        self.assertEqual(
            [g.pk for g in self.select(start_date=date(2026, 9, 20))],
            [last.pk, later.pk],
        )
        self.assertEqual(
            [g.pk for g in self.select(end_date=date(2026, 9, 10))],
            [earlier.pk, first.pk],
        )
        self.assertEqual(
            [g.pk for g in self.select()],
            [earlier.pk, first.pk, last.pk, later.pk],
        )

    def test_order_is_date_then_id_ascending(self):
        newer = self.create_game(date_played=date(2026, 9, 20))
        older = self.create_game(date_played=date(2026, 9, 10))
        same_day = self.create_game(date_played=date(2026, 9, 10))
        self.assertEqual(
            [g.pk for g in self.select()],
            [older.pk, same_day.pk, newer.pk],
        )

    def test_rejects_identical_players(self):
        with self.assertRaises(ValueError):
            select_turn_order_games(
                principal_player=self.principal,
                opponent_player=self.principal,
            )

    def test_prefetches_results_and_related_players(self):
        self.create_game()
        self.create_game(date_played=date(2026, 9, 16))

        # Game selection plus a single results-prefetch query.
        with CaptureQueriesContext(connection) as queries:
            games = self.select()
        self.assertEqual(len(queries), 2)

        with CaptureQueriesContext(connection) as queries:
            for game in games:
                self.assertEqual(len(game.prefetched_results), 2)
                for result in game.prefetched_results:
                    self.assertEqual(result.player.pk, result.player_id)
        self.assertEqual(len(queries), 0)

    def test_empty_selection(self):
        self.assertEqual(self.select(), [])


class BuildTurnOrderGameRecordTests(TurnOrderResearchTestBase):
    def build(self, **kwargs):
        game = self.create_game(**kwargs)
        selected_game = select_turn_order_games(
            principal_player=self.principal,
            opponent_player=self.opponent,
        )[0]
        self.assertEqual(selected_game.pk, game.pk)
        return build_turn_order_game_record(
            game=selected_game,
            principal_player=self.principal,
            opponent_player=self.opponent,
        )

    def test_score_differential_and_win(self):
        record = self.build(principal_score=112, opponent_score=95)
        self.assertEqual(record.principal_score, 112)
        self.assertEqual(record.opponent_score, 95)
        self.assertEqual(record.score_differential, 17)
        self.assertEqual(record.outcome, GamePrincipalOutcome.WIN)
        self.assertEqual(record.winner, self.principal)
        self.assertEqual(record.principal_player, self.principal)
        self.assertEqual(record.opponent_player, self.opponent)
        self.assertEqual(record.date_played, date(2026, 9, 15))

    def test_loss(self):
        record = self.build(principal_score=70, opponent_score=100)
        self.assertEqual(record.score_differential, -30)
        self.assertEqual(record.outcome, GamePrincipalOutcome.LOSS)
        self.assertEqual(record.winner, self.opponent)

    def test_tie(self):
        record = self.build(principal_score=100, opponent_score=100)
        self.assertEqual(record.score_differential, 0)
        self.assertEqual(record.outcome, GamePrincipalOutcome.TIE)
        self.assertIsNone(record.winner)

    def test_all_twenty_distinct_turn_order_combinations(self):
        """Verify spacing and direct-preceding independently for all positions."""
        for principal_turn in range(1, 6):
            for opponent_turn in range(1, 6):
                if principal_turn == opponent_turn:
                    continue

                with self.subTest(principal=principal_turn, opponent=opponent_turn):
                    # Each case gets its own Game to honor the unique turn constraint.
                    game = self.create_game(
                        principal_turn=principal_turn,
                        opponent_turn=opponent_turn,
                    )
                    game.prefetched_results = list(
                        GameResult.objects.filter(game=game).select_related("player")
                    )

                    record = build_turn_order_game_record(
                        game=game,
                        principal_player=self.principal,
                        opponent_player=self.opponent,
                    )

                    expected_after = 0
                    current_position = principal_turn
                    while True:
                        current_position = current_position % 5 + 1
                        if current_position == opponent_turn:
                            break
                        expected_after += 1

                    expected_before = 3 - expected_after
                    expected_precedes = (principal_turn % 5 + 1 == opponent_turn)

                    self.assertEqual(record.principal_turn_order, principal_turn)
                    self.assertEqual(record.opponent_turn_order, opponent_turn)
                    self.assertEqual(record.npcs_after_principal, expected_after)
                    self.assertEqual(record.npcs_before_principal, expected_before)
                    self.assertEqual(
                        record.principal_directly_precedes_opponent,
                        expected_precedes,
                    )

    def test_building_record_does_not_query_database(self):
        game = self.create_game()
        selected_game = select_turn_order_games(
            principal_player=self.principal,
            opponent_player=self.opponent,
        )[0]
        with CaptureQueriesContext(connection) as queries:
            record = build_turn_order_game_record(
                game=selected_game,
                principal_player=self.principal,
                opponent_player=self.opponent,
            )
        self.assertEqual(len(queries), 0)
        self.assertEqual(record.game_id, game.pk)


class BuildTurnOrderDatasetTests(TurnOrderResearchTestBase):
    def build(self, **kwargs):
        return build_turn_order_dataset(
            principal_player=self.principal,
            opponent_player=self.opponent,
            **kwargs,
        )

    def test_dataset_contains_one_record_per_qualifying_game(self):
        first = self.create_game(date_played=date(2026, 9, 10))
        second = self.create_game(date_played=date(2026, 9, 20))
        self.create_game(mode=Game.HumanPlayerMode.SINGLE)
        self.create_game(opponent_turn=None)

        dataset = self.build()

        self.assertEqual(dataset.principal_player, self.principal)
        self.assertEqual(dataset.opponent_player, self.opponent)
        self.assertIsNone(dataset.start_date)
        self.assertIsNone(dataset.end_date)
        self.assertEqual([r.game_id for r in dataset.games], [first.pk, second.pk])
        self.assertEqual([r.score_differential for r in dataset.games], [10, 10])

    def test_dataset_preserves_date_filters(self):
        self.create_game(date_played=date(2026, 9, 1))
        included = self.create_game(date_played=date(2026, 9, 15))
        self.create_game(date_played=date(2026, 10, 1))

        start = date(2026, 9, 10)
        end = date(2026, 9, 20)
        dataset = self.build(start_date=start, end_date=end)

        self.assertEqual(dataset.start_date, start)
        self.assertEqual(dataset.end_date, end)
        self.assertEqual([r.game_id for r in dataset.games], [included.pk])

    def test_empty_dataset_is_valid(self):
        dataset = self.build()
        self.assertEqual(dataset.games, [])
        self.assertEqual(dataset.principal_player, self.principal)
        self.assertEqual(dataset.opponent_player, self.opponent)

    def test_reversed_perspective_changes_outcome_and_spacing(self):
        self.create_game(
            principal_turn=5,
            opponent_turn=1,
            principal_score=120,
            opponent_score=100,
        )
        forward = self.build().games[0]
        reverse = build_turn_order_dataset(
            principal_player=self.opponent,
            opponent_player=self.principal,
        ).games[0]

        self.assertEqual(forward.outcome, GamePrincipalOutcome.WIN)
        self.assertEqual(reverse.outcome, GamePrincipalOutcome.LOSS)
        self.assertEqual(forward.score_differential, 20)
        self.assertEqual(reverse.score_differential, -20)
        self.assertTrue(forward.principal_directly_precedes_opponent)
        self.assertFalse(reverse.principal_directly_precedes_opponent)
        self.assertEqual(forward.npcs_after_principal, reverse.npcs_before_principal)
        self.assertEqual(forward.npcs_before_principal, reverse.npcs_after_principal)

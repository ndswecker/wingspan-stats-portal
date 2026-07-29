from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet, formset_factory
from django.utils import timezone

from .models import Game, Player

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            "date_played",
            "human_player_mode"
        ]
        widgets = {
            "date_played": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "human_player_mode": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound:
            self.fields["date_played"].initial = timezone.localdate()

    def clean_date_played(self):
        date_played = self.cleaned_data["date_played"]

        if date_played > timezone.localdate():
            raise ValidationError("The date played cannot be in the future")
        
        return date_played
    

class GameResultForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        required=False,
        empty_label="Select a Player",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    score = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 0,
            }
        ),
    )

    turn_order = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "inputmode": "numeric",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["player"].queryset = (
            Player.objects.filter(is_active=True).order_by("name")
        )

    def clean(self):
        cleaned_data = super().clean()

        player = cleaned_data.get("player")
        score = cleaned_data.get("score")
        turn_order = cleaned_data.get("turn_order")

        row_is_blank = (
            player is None
            and score is None
            and turn_order is None
        )

         # if the row is blank then the row will not be used, and will be returned as empty. 
         # Otherwise it will be considered 'populated'
        if row_is_blank:
            cleaned_data["is_populated"] = False
            return cleaned_data
        
        cleaned_data["is_populated"] = True

        if player is None:
            self.add_error(
                "player",
                "Select a player for this result.",
            )

        if score is None:
            self.add_error(
                "score",
                "Enter a score for this player.",
            )

        return cleaned_data
    
class BaseGameResultFormSet(BaseFormSet):
    def __init__(
        self, *args, human_player_mode=None, **kwargs
    ):
        self.human_player_mode = human_player_mode
        super().__init__(*args, **kwargs)
        
    def clean(self):
        super().clean()

        if any(self.errors):
            return
        
        populated_forms = []

        for form in self.forms:
            if form.cleaned_data.get("is_populated"):
                populated_forms.append(form)

        player_count = len(populated_forms)
        if (
            self.human_player_mode == Game.HumanPlayerMode.SINGLE
            and player_count !=1
        ):
            raise ValidationError("A solo game must have exactly one player")

        if (
            self.human_player_mode == Game.HumanPlayerMode.MULTIPLE
            and player_count < 2
        ):
            raise ValidationError("A competitive game must have two or more players.")

        players = []

        for form in populated_forms:
            players.append(form.cleaned_data["player"])

        turn_orders = []

        for form in populated_forms:
            turn_order = form.cleaned_data["turn_order"]

            if turn_order is not None:
                turn_orders.append(turn_order)

        if len(players) != len(set(players)):
            raise ValidationError("Each player may appear only once.")
        
        if len(turn_orders) != len(set(turn_orders)):
            raise ValidationError("Each provided turn order must be unique.")

GameResultFormSet = formset_factory(
    GameResultForm,
    formset=BaseGameResultFormSet,
    extra=5,
    max_num=5,
    validate_max=True,
)

class PlayerStatisticsFilterForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        empty_label="Select a player",
        widget=forms.Select(
            attrs={"class": "form-select",}
        ),
    )

    game_type = forms.ChoiceField(
        choices=Game.HumanPlayerMode.choices,
        widget=forms.Select(
            attrs={"class": "form-select",}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["player"].queryset = (
            Player.objects.filter(is_active=True)
        )
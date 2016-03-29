from django import forms
from club.models import Game, Ladder, Ranking


class PGNForm(forms.Form):
    pgn_string = forms.CharField(widget=forms.Textarea)


class GameForm(forms.ModelForm):
    datetime = forms.DateTimeField()
    ladder = forms.ModelChoiceField(queryset=Ladder.objects.filter(ladder_type=0))

    def clean(self):
        cleaned_data = super(GameForm, self).clean()
        white = cleaned_data['white']
        black = cleaned_data['black']
        ladder = cleaned_data['ladder']
        players = [ranking.player for ranking in Ranking.objects.filter(ladder=ladder)]
        if white == black:
            raise forms.ValidationError('You cannot report a game against yourself!')
        if white not in players or black not in players:
            raise forms.ValidationError('One or more of the players has not joined the ladder.')
        return cleaned_data

    class Meta:
        model = Game
        fields = ('white', 'black', 'time_control', 'result', 'datetime')
        hidden_fields = ('ladder', 'status')
    

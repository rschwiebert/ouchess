from django import forms

class PGNForm(forms.Form):
    pgn_string = forms.CharField(widget=forms.Textarea)


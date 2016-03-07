from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.generic import DetailView, ListView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
import requests
import datetime
from club.models import Player, Ranking, Ladder, Rating, Game


# Create your views here.
def index(request):
    template = loader.get_template('club/index.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))


class PlayerDetailView(DetailView):
    model = Player

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        rankings = Ranking.objects.filter(player=self.object)
        ladders = [ranking.ladder for ranking in rankings]
        ratings_rankings_list = []
        for ranking in rankings:
            ratings_rankings_list.append((ranking.ladder, ranking.rank, ranking.player.int_rating(ranking.ladder)))

        context['ratings_rankings_list'] = ratings_rankings_list
        return context


class LadderDetailView(DetailView):
    model = Ladder

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        rankings = self.object.ranking_set.order_by('rank')
        context['ranking_list'] = rankings

        ratings = list((ranking.player, ranking.int_rating) for ranking in rankings)
        ratings = sorted(ratings, key=lambda x: x[1],  reverse=True)
        context['rating_list'] = ratings
        context['timestamp'] = datetime.datetime.now()

        games = self.object.game_set.order_by('-datetime')
        recent_games = games[:20]
        context['recent_games'] = recent_games
        return context


class PlayerListView(ListView):
    model = Player


class LadderListView(ListView):
    model = Ladder


class LadderGameListView(ListView):
    model = Game

    def get_queryset(self):
        queryset = super(ListView, self).get_queryset()
        ladder_id = self.kwargs['pk']
        return queryset.filter(ladder=ladder_id)

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        ladder = Ladder.objects.get(id=self.kwargs['pk'])
        context['ladder'] = ladder
        return context

    def get_template_names(self):
        return ['club/ladder_games.html']

class GameListView(ListView):
    model = Game


class GameDetailView(LoginRequiredMixin, DetailView):
    model = Game
    redirect_field_name = '/games/'

        

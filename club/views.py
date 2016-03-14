import datetime
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.generic import DetailView, ListView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from club.models import Player, Ranking, Ladder, Game
from club.forms import PGNForm


# Create your views here.
def index(request):
    template = loader.get_template('club/index.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))


class PlayerDetailView(DetailView):
    model = Player

    def get_context_data(self, **kwargs):
        context = super(PlayerDetailView, self).get_context_data(**kwargs)
        rankings = Ranking.objects.filter(player=self.object)
        ratings_rankings_list = []
        for ranking in rankings:
            ratings_rankings_list.append(
                (ranking.ladder, ranking.rank,
                 ranking.player.int_rating(ranking.ladder)))

        context['ratings_rankings_list'] = ratings_rankings_list
        return context


class LadderDetailView(DetailView):
    model = Ladder

    def get_context_data(self, **kwargs):
        context = super(LadderDetailView, self).get_context_data(**kwargs)
        rankings = self.object.ranking_set.order_by('rank')
        context['ranking_list'] = rankings

        ratings = list((ranking.player, ranking.int_rating)
                       for ranking in rankings)
        ratings = sorted(ratings, key=lambda x: x[1],  reverse=True)
        context['rating_list'] = ratings
        context['timestamp'] = datetime.datetime.now()

        games = self.object.game_set.order_by('-datetime')
        recent_games = games[:20]
        context['recent_games'] = recent_games
        return context


class TourneyDetailView(DetailView):
    model = Ladder

    def get_context_data(self, **kwargs):
        context = super(TourneyDetailView, self).get_context_data(**kwargs)
        rankings = self.object.ranking_set.order_by('rank')
        context['ranking_list'] = rankings

        ratings = list((ranking.player, ranking.int_rating)
                       for ranking in rankings)
        ratings = sorted(ratings, key=lambda x: x[1],  reverse=True)
        context['rating_list'] = ratings
        context['timestamp'] = datetime.datetime.now()

        games = self.object.game_set.order_by('-datetime')
        recent_games = games[:20]
        context['recent_games'] = recent_games
        return context

    def get_template_names(self):
        return ['club/tourney_detail.html']


class PlayerListView(ListView):
    model = Player


class LadderListView(ListView):
    model = Ladder

    def get_context_data(self, **kwargs):
        context = super(LadderListView, self).get_context_data(**kwargs)
        queryset = self.get_queryset()
        ladders = queryset.filter(ladder_type=0)
        tourneys = queryset.filter(ladder_type=1)
        context['current_ladder_list'] = \
            ladders.filter(end_date=None).order_by('-start_date')
        context['closed_ladder_list'] = \
            ladders.exclude(end_date=None).order_by('-start_date')
        context['tourney_list'] = tourneys.order_by('-start_date')
        return context


class TourneyListView(ListView):
    model = Ladder
    
    def get_queryset(self):
        queryset = super(TourneyListView, self).get_queryset()
        return queryset.filter(ladder_type=1)

    def get_template_names(self):
        return ['club/tourney_list.html']


class LadderGameListView(ListView):
    model = Game

    def get_queryset(self):
        queryset = super(LadderGameListView, self).get_queryset()
        ladder_id = self.kwargs['pk']
        return queryset.filter(ladder=ladder_id)

    def get_context_data(self, **kwargs):
        context = super(LadderGameListView, self).get_context_data(**kwargs)
        ladder = Ladder.objects.get(id=self.kwargs['pk'])
        context['ladder'] = ladder
        return context

    def get_template_names(self):
        return ['club/ladder_games.html']


class TourneyGameListView(ListView):
    model = Game

    def get_queryset(self):
        queryset = super(TourneyGameListView, self).get_queryset()
        ladder_id = self.kwargs['pk']
        return queryset.filter(ladder=ladder_id).order_by('round')

    def get_context_data(self, **kwargs):
        context = super(TourneyGameListView, self).get_context_data(**kwargs)
        ladder = Ladder.objects.get(id=self.kwargs['pk'])
        context['ladder'] = ladder
        return context

    def get_template_names(self):
        return ['club/tourney_games.html']


class GameListView(ListView):
    model = Game


class GameDetailView(LoginRequiredMixin, DetailView):
    model = Game
    redirect_field_name = '/games/'
    
    def get_context_data(self, **kwargs):
        context = super(GameDetailView, self).get_context_data(**kwargs)
        game = self.object
        if self.request.user.is_staff or \
            game.white.user == self.request.user or \
            game.black.user == self.request.user:
            context['user_can_edit_pgn'] = True
        else:
            context['user_can_edit_pgn'] = False
        return context
        

class FAQView(TemplateView):
    def get_template_names(self):
        return ['club/faq.html']


class ToolView(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        return ['club/tools.html']


class PGNView(LoginRequiredMixin, FormView):
    form_class = PGNForm
    template_name = 'club/pgn_editor.html'
    
    @property
    def initial(self):
        game_id = self.kwargs.get('pk', None)
        if game_id:
            return {'pgn_string': Game.objects.get(id=game_id).pgn}
        else:
            return {}

    @property
    def success_url(self):
        context = self.get_context_data(**self.kwargs)
        return reverse('game-detail', kwargs={'pk': context['pk']})

    def get_context_data(self, **kwargs):
        context = super(PGNView, self).get_context_data(**kwargs)
        game_id = self.kwargs.get('pk', None)
        if game_id:
            context['game_id'] = game_id
            game = Game.objects.get(id=game_id)
            context['game'] = game
            if self.request.user.is_staff or \
                game.white.user == self.request.user or \
                    game.black.user == self.request.user:
                context['user_can_edit_pgn'] = True
            else:
                context['user_can_edit_pgn'] = False
        return context
    
    def form_valid(self, form):
        game = Game.objects.get(id=self.kwargs.get('pk'))
        game.pgn = form.data['pgn_string']
        game.save()
        return super(PGNView, self).form_valid(form)

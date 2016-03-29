import datetime
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.generic import DetailView, ListView, TemplateView, FormView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from club.models import Player, Ranking, Ladder, Game
from club.forms import PGNForm, GameForm
from django.db.models import Q


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

        ladder_games = Game.objects.filter(Q(white=self.object) | Q(black=self.object))
        reported = ladder_games.filter(
            Q(white=self.request.user.player, status=1)|Q(black=self.request.user.player, status=2))
        awaiting = ladder_games.filter(
            Q(white=self.request.user.player, status=2)|Q(black=self.request.user.player, status=1))
        disputed = ladder_games.filter(status__in=[-1, -2])
        context['awaiting'] = awaiting
        context['reported'] = reported
        context['disputed'] = disputed

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
        return context


class TourneyDetailView(DetailView):
    model = Ladder
    template_name = 'club/tourney_detail.html'

    def get_context_data(self, **kwargs):
        context = super(TourneyDetailView, self).get_context_data(**kwargs)
        rankings = self.object.ranking_set.order_by('rank')
        context['ranking_list'] = rankings

        ratings = list((ranking.player, ranking.int_rating)
                       for ranking in rankings)
        ratings = sorted(ratings, key=lambda x: x[1],  reverse=True)
        context['rating_list'] = ratings
        context['timestamp'] = datetime.datetime.now()
        return context


class PlayerListView(ListView):
    model = Player

    def get_queryset(self):
        return Player.objects.filter(visible=True).exclude(membership=0)


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
    template_name = 'club/tourney_list.html'
    
    def get_queryset(self):
        queryset = super(TourneyListView, self).get_queryset()
        return queryset.filter(ladder_type=1)


class LadderGameListView(ListView):
    model = Game
    template_name = 'club/ladder_games.html'

    def get_queryset(self):
        queryset = super(LadderGameListView, self).get_queryset()
        ladder_id = self.kwargs['pk']
        return queryset.filter(ladder=ladder_id, status=3)

    def get_context_data(self, **kwargs):
        context = super(LadderGameListView, self).get_context_data(**kwargs)
        ladder = Ladder.objects.get(id=self.kwargs['pk'])
        context['ladder'] = ladder
        
        return context


class TourneyGameListView(ListView):
    model = Game
    template_name = 'club/tourney_games.html'

    def get_queryset(self):
        queryset = super(TourneyGameListView, self).get_queryset()
        ladder_id = self.kwargs['pk']
        return queryset.filter(ladder=ladder_id).order_by('round')

    def get_context_data(self, **kwargs):
        context = super(TourneyGameListView, self).get_context_data(**kwargs)
        ladder = Ladder.objects.get(id=self.kwargs['pk'])
        context['ladder'] = ladder
        return context


class GameListView(LoginRequiredMixin, ListView):
    model = Game
    redirect_field_name = '/games/'

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


class ToolView(LoginRequiredMixin, TemplateView):
    template_name = 'club/tools.html'


class ReportGameView(LoginRequiredMixin, CreateView):
    template_name = 'club/report_game.html'
    form_class = GameForm
    success_url = '/ladders/{ladder_id}/games'
    
    @property
    def initial(self):
        ladder_id = self.kwargs.get('pk', None)
        if ladder_id:
            return {'ladder': Ladder.objects.get(id=ladder_id)}
        else:
            return {}

    def form_valid(self, form):
        white = Player.objects.get(id=form.data['white'])
        black = Player.objects.get(id=form.data['black'])
        ladder_id = self.kwargs.get('pk', None)
        ladder = Ladder.objects.get(id=ladder_id)
        form.instance.ladder = ladder
        
        if self.request.user.is_staff:
            form.instance.status = 3
        elif self.request.user.player == white:
            form.instance.status = 1
        elif self.request.user.player == black:
            form.instance.status = 2
        else:
            forms.ValidationError('Request user is not allowed to complete this form.')
        
        return super(ReportGameView, self).form_valid(form)


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




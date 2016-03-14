from __future__ import unicode_literals
from django.db import models
from model_utils import Choices
from django_pgjson.fields import JsonBField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

#####
# Models
#####


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_student_member = models.NullBooleanField(blank=True, null=True)

    def rating(self, ladder):
        ratings = ladder.rating_set.filter(player=self).order_by('-timestamp')
        if ratings:
            return ratings[0].rating
        else:
            return ladder.ranking_set.get(player=self).initial_rating

    def int_rating(self, ladder):
        return int(self.rating(ladder))

    def __unicode__(self):
        return self.user.username


class Algorithm(models.Model):
    name = models.CharField(max_length=30, blank=True, null=True)
    method = models.CharField(
        max_length=30,
        help_text="The name of the method used in rating_algs.py", null=True)
    params = JsonBField(default={}, blank=True)

    def __unicode__(self):
        return self.name


class Ladder(models.Model):
    name = models.CharField(max_length=30)
    algorithm = models.ForeignKey(Algorithm)
    ladder_type = models.SmallIntegerField(choices=Choices((0, 'ladder'),
                                                           (1, 'tournament'),),
                                           null=True, blank=True)
    location = models.CharField(max_length=30, null=True, blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    inactivity_period = models.IntegerField(
        null=True, blank=True, 
        help_text="After this many days without a game, the player's ranking "
                  "will drop by demotion_inc places.")
    demotion_inc = models.IntegerField(
        null=True, blank=True,
        help_text="When the inactivity penalty is enforced, the player's "
                  "ranking falls this many places")

    def __unicode__(self):
        return '%s' % (self.name,)


class Game(models.Model):
    white = models.ForeignKey(Player, related_name='white')
    black = models.ForeignKey(Player, related_name='black')
    white_rating = models.IntegerField(null=True, blank=True)
    black_rating = models.IntegerField(null=True, blank=True)
    time_control = models.CharField(max_length=25, null=True, blank=True)
    result = models.SmallIntegerField(choices=Choices((0, '1-0'), (1, '0-1'),
                                                      (2, '1/2-1/2')))
    ladder = models.ForeignKey(Ladder)
    datetime = models.DateTimeField(
        null=True, blank=True, auto_now_add=True,
        help_text='NOTE: game time MUST be sufficient to place it in '
                  'sufficiently correct chronological order with other games.')
    round = models.SmallIntegerField(null=True, blank=True)
    status = models.SmallIntegerField(choices=Choices((0, 'public'),
                                                      (1, 'private')),
                                      default=0)
    eco = models.CharField(max_length=50, null=True, blank=True)
    pgn = models.CharField(max_length=2500, null=True, blank=True)

    def __unicode__(self):
        return '%s (%r) - %s (%r): %s' % (
            self.white.user.username, self.white_rating,
            self.black.user.username, self.black_rating,
            self.get_result_display())


class Rating(models.Model):
    player = models.ForeignKey(Player)
    ladder = models.ForeignKey(Ladder)
    rating = models.DecimalField(decimal_places=3, max_digits=7)
    timestamp = models.DateTimeField(blank=True)
    game = models.ForeignKey(
        Game, null=True, blank=True,
        help_text='The game associated with this rating change.')

    def __unicode__(self):
        return '%s (%d) %s' % (self.player.user.username, self.rating,
                               self.ladder)

    @property
    def int_rating(self):
        return int(self.rating)
        

class Ranking(models.Model):
    player = models.ForeignKey(Player)
    ladder = models.ForeignKey(Ladder)
    rank = models.IntegerField(null=True, blank=True)
    initial_rating = models.IntegerField(default=1200)
    is_active = models.BooleanField(default=True)
    
    @property
    def rating(self):
        query = Rating.objects.filter(
            player=self.player, ladder=self.ladder).order_by('-timestamp')
        if query.exists():
            # latest rating for this player on this ladder
            return query[0].rating
        else:
            return self.initial_rating

    @property
    def int_rating(self):
        return int(self.rating)

    def __unicode__(self):
        return '#%d %s (%d) [%s]' \
               % (self.rank, self.player.user.username, self.rating,
                  self.ladder.name)

    class Meta:
        unique_together = ('player', 'ladder')

#####
# Rating computation methods
#####


def calculate_ratings(ladder, white, black, result):
    exec('from rating_algs import %s as func' % ladder.algorithm.method)
    kwargs = ladder.algorithm.params
    return func(white, black, result, ladder, **kwargs)


def set_ratings(game):
    """
    Historical record of rating changes.
    It is important for players to provide good datetimes for their game reports
    """
    new_white_rating, new_black_rating = calculate_ratings(
        game.ladder, game.white, game.black, game.result)
    Rating.objects.create(
        ladder=game.ladder, player=game.white, rating=new_white_rating,
        timestamp=game.datetime, game=game)
    Rating.objects.create(
        ladder=game.ladder, player=game.black, rating=new_black_rating,
        timestamp=game.datetime, game=game)
    return new_white_rating, new_black_rating


def crunch_ratings(ladder):
    """
    Nuclear option to recompute all ratings on a ladder from scratch based on
    game history
    """
    # blow away old ratings
    old_ratings = Rating.objects.filter(ladder=ladder.id)
    old_ratings.delete()

    games = ladder.game_set.order_by('datetime')
    for game in games:
        game.white_rating = game.white.rating(ladder)
        game.black_rating = game.black.rating(ladder)
        game.save()
        set_ratings(game)

#####
# Rank manipulation helper methods
#####


def insert(player1, player2, ladder, above=False):
    """If above is True, insert player1 immediately above player2 in the ranking
    and adjust all other ranks. If above is False, insert player1 immediately
    below player2."""
    p1_ranking = Ranking.objects.get(player=player1, ladder=ladder)
    p2_ranking = Ranking.objects.get(player=player2, ladder=ladder)
    if above:
        new_rank = p1_ranking.rank
    else:
        new_rank = p1_ranking.rank + 1
    move = Ranking.objects.filter(ladder=ladder, rank__gte=new_rank)
    for ranking in move:
        ranking.rank += 1
        ranking.save()
    p2_ranking.rank = new_rank
    p2_ranking.save()


def demote(target, ladder):
    """Penalize player by dropping 1 rank on given ladder"""
    target_ranking = Ranking.objects.get(player=target, ladder=ladder)
    other = ladder.ranking_set.filter(rank=target_ranking.rank + 1)
    if other.exists():
        other = other[0]
        target.rank, other.rank = (other.rank, target.rank)
        target.save()
        other.save()


def remove(target, ladder):
    """
    Strip player of rank, mark as inactive, adjust all other ranks accordingly.
    """
    target_ranking = Ranking.objects.get(player=target, ladder=ladder)
    lower = ladder.ranking_set.filter(rank__lt=target_ranking.rank)
    for ranking in lower:
        ranking.rank += 1
        ranking.save()
    target_ranking.rank = None
    target_ranking.is_active = False
    target_ranking.save()


def rejoin(target, ladder):
    """
    Mark the player as active again and put them at the bottom of the ladder.
    """
    target_ranking = Ranking.objects.get(player=target, ladder=ladder)
    target_ranking.is_active = True
    max_rank = ladder.ranking_set.aggregate(models.Max('ranking'))
    max_rank = max_rank['ranking__max']
    target_ranking.rank = max_rank + 1
    target_ranking.save()
        
#####
# Signals
#####


# Signal to associate a Player profile to each Django's User instance.
@receiver(post_save, sender=User)
def add_player(sender, instance, created, **kwargs):
    if created:
        Player.objects.create(user=instance)


# Hook ratings from players at the time the game record is created
@receiver(post_save, sender=Game)
def set_rankings(sender, instance, created, **kwargs):
    if created:
        white = instance.white
        black = instance.black
        ladder = instance.ladder
        white_ranking = instance.ladder.ranking_set.get(player=white)
        black_ranking = instance.ladder.ranking_set.get(player=black)

        # compute new ratings
        instance.white_rating = white.rating(ladder)
        instance.black_rating = black.rating(ladder)
        instance.save()
        set_ratings(instance)

        # compute new ranks  
        # Creation of a game will "reawaken" an inactive ranking 
        # (no good way to automatically reverse this if the Game is retracted.)
        white_ranking.is_active = black_ranking.is_active = True
        if instance.result == 0:
            if white_ranking.rank < black_ranking.rank:
                pass
            else:
                insert(black, white, ladder, above=True)
        elif instance.result == 1:
            if white_ranking.rank < black_ranking.rank:
                insert(black, white, ladder, above=True)
            else:
                pass
        elif instance.result == 2:
            if white_ranking.rank < black_ranking.rank:
                pass
            else:
                insert(black, white, ladder, above=False)
        else:
            raise Exception('What game result code is this? %d'
                            % instance.result)


# People join ladders at the bottom
@receiver(post_save, sender=Ranking)
def set_rank(sender, instance, created, **kwargs):
    if created:
        max_rank = instance.ladder.ranking_set.aggregate(models.Max('rank'))
        max_rank = max_rank['rank__max']
        if max_rank is None:
            max_rank = 0
        instance.rank = max_rank + 1
        instance.save()

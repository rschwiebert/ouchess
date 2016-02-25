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
    	
    def __unicode__(self):
        return self.user.username

class Algorithm(models.Model):
    name = models.CharField(max_length=30, blank=True, null=True)
    formula = models.CharField(max_length=100)
    params = JsonBField(default={}, blank=True)

    def __unicode__(self):
        return self.name


class Ladder(models.Model):
    name = models.CharField(max_length=30)
    rating_algorithm = models.ForeignKey(Algorithm)
    location = models.CharField(max_length=30, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    inactivity_period = models.IntegerField(
        null=True, blank=True, 
        help_text="After this many days without a game, the player's ranking "
                  "will drop by demotion_inc places.")
    demotion_inc = models.IntegerField(
        null=True, blank=True,
        help_text="When the inactivity penalty is enforced, the player's ranking "
                  "falls this many places")

    def __unicode__(self):
        return '%s: %s-%s' % (self.name, self.start_date, self.end_date)


class Game(models.Model):
    white = models.ForeignKey(Player, related_name='white')
    black = models.ForeignKey(Player, related_name='black')
    white_rating = models.IntegerField(null=True, blank=True)
    black_rating = models.IntegerField(null=True, blank=True)
    time_control = models.CharField(max_length=25)
    result = models.SmallIntegerField(choices=Choices((0, '1-0'),(1, '0-1'), (2, '1/2-1/2')))
    ladder = models.ForeignKey(Ladder)
    datetime = models.DateTimeField(null=True, blank=True)
    round = models.SmallIntegerField(null=True, blank=True)
    status = models.SmallIntegerField(choices=Choices((0, 'public'), (1, 'private')))
    eco = models.CharField(max_length=50, null=True, blank=True)
    pgn = models.CharField(max_length=2500, null=True, blank=True)

    def __unicode__(self):
        return '%s (%d) - %s (%d): %s [%s]' % (self.white.user.username, self.white_rating,
                                               self.black.user.username, self.black_rating,
                                               self.get_result_display(), self.datetime)


class Rating(models.Model):
    player = models.ForeignKey(Player)
    ladder = models.ForeignKey(Ladder)
    rating = models.IntegerField()
    timestamp = models.DateTimeField(blank=True)
        

class Ranking(models.Model):
    player = models.ForeignKey(Player)
    ladder = models.ForeignKey(Ladder)
    rank = models.IntegerField(null=True, blank=True)
    initial_rating = models.IntegerField(default=1200)
    is_active = models.BooleanField(default=True)
    
    @property
    def rating(self):
        query = Rating.objects.filter(player=self.player, ladder=self.ladder).order_by('-timestamp')
        if query.exists():
            # latest rating for this player on this ladder
            return query[0].rating
        else:
            return self.initial_rating

    def __unicode__(self):
        return '#%d %s (%d) [%s]' % (self.ranking, self.player.user.username, self.rating, self.ladder.name)

    class Meta:
        unique_together = ('player', 'ladder')

#####
# Rating computation methods
#####
def calculate_ratings(ladder, white, black):
    # Successful execution of the following line depends on validity of 
    # the formula with 'white' and 'black' plugged in
    # must return a tuple (white_rating, black_rating)
    return eval(ladder.algorithm.formula)

def set_ratings(white_ranking, black_ranking, datetime):
    """
    Historical record of rating changes.
    It is important for players to provide good datetimes for their game reports
    """
    ladder = white_ranking.ladder
    new_white_rating, new_black_rating = calculate_ratings(
        ladder, white_ranking.rating, black_ranking.rating)
    Rating.objects.create(
        ladder=ladder, player=white, rating=new_white_rating, timestamp=datetime)        
    Rating.objects.create(
        ladder=ladder, player=black, rating=new_black_rating, timestamp=datetime)        
   
def crunch_ratings(ladder):
    """
    Nuclear option to recompute all ratings on a ladder from scratch based on game history
    """
    # blow away old ratings
    old_ratings = Ratings.objects.filter(ladder=ladder)
    old_ratings.delete()

    games = ladder.game_set.order_by('datetime')
    for game in games:
        set_rating(white_ranking, black_ranking, game.datetime)

#####
# Rank manipulation helper methods
#####
def insert(player1, player2, ladder, above=False):
    """If above is True, insert player1 immediately above player2 in the ranking and 
    adjust all other ranks. If above is False, insert player1 immediately below player2."""
    p1_rank = Ranking.objects.get(player=player1, ladder=ladder)
    p2_rank = Ranking.objects.get(player=player2, ladder=ladder)
    if above:
        new_rank = p1_ranking.rank
    else:
        new_rank = p1_ranking.rank + 1
    move = Ranking.objects.filter(ladder=ladder, rank__lte=new_rank)
    for raking in move:
        raking.rank += 1
        ranking.save()
    p2_ranking.rank = new_rank
    p2_ranking.save()

def demote(target, ladder):
    """Penalize player by dropping 1 rank on given ladder"""
    target_ranking = Ranking.objects.get(player=target, ladder=ladder)
    other = ladder.ranking_set.filter(rank=target_ranking.rank + 1)
    if other.exists():
        other = other[0]
        target.rank, other.rank = (other.rank, target.rank )
        target.save()
        other.save()

def remove(target, ladder):
    """Strip player of rank, mark as inactive, adjust all other ranks accordingly."""
    target_ranking = Ranking.objects.get(player=target, ladder=ladder)
    lower = ladder.ranking_set.filter(rank__lt=target_ranking.rank)
    for ranking in lower:
        ranking.rank += 1
        ranking.save()
    target_ranking.rank = None
    target_ranking.is_active = False
    target_ranking.save()

def rejoin(target, ladder):
    """Mark the player as active again and put them at the bottom of the ladder."""
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
        set_ratings(white_ranking, black_ranking, instance.datetime)
        
        # compute new ranks      
        if instance.result == 0:
            if white_ranking.rank > black_ranking.rank:
                pass
            else:
                insert(black, white, ladder, above=True)
        elif instance.result == 1:
            if white_ranking.rank > black_ranking.rank:
                insert(black, white, ladder, above=True)
            else:
                pass
        elif instance.result == 2:
            if white_ranking.rank > black_ranking.rank:
                pass
            else:
                insert(black, white, ladder, above=False)
        else:
            raise Exception('What game result code is this? %d' % instance.result)
            
        
# People join ladders at the bottom
@receiver(post_save, sender=Ranking)
def set_rank(sender, instance, created, **kwargs):
    if created:
        max_rank = instance.ladder.ranking_set.aggregate(models.Max('ranking'))
        max_rank = max_rank['ranking__max']
        instance.rank = max_rank + 1
        instance.save()

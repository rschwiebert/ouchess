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
    rating = models.IntegerField(default=1200)
    ranking = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s (%d) [%s]' % (self.player.user.username, self.rating, self.ladder.name)

    class Meta:
        unique_together = ('player', 'ladder')

#####
# Rank manipulation helper methods
#####
def insert(player1, player2, ladder, above=False):
    """If above is True, insert player1 immediately above player2 in the ranking and 
    adjust all other ranks. If above is False, insert player1 immediately below player2."""
    p1_rating = Rating.objects.get(player=player1, ladder=ladder)
    p2_rating = Rating.objects.get(player=player2, ladder=ladder)
    if above:
        new_rank = p1_rating.rank
    else:
        new_rank = p1_rating.rank + 1
    move = Rating.objects.filter(ladder=ladder, rank__lte=new_rank)
    for rating in move:
        rating.rank += 1
        rating.save()
    p2_rating.rank = new_rank
    p2_rating.save()

def demote(target, ladder):
    """Penalize player by dropping 1 rank on given ladder"""
    target_rating = Rating.objects.get(player=target, ladder=ladder)
    other = ladder.rating_set.filter(rank=target_rating.rank + 1)
    if other.exists():
        other = other[0]
        target.rank, other.rank = (other.rank, target.rank )
        target.save()
        other.save()

def remove(target, ladder):
    """Strip player of rank, mark as inactive, adjust all other ranks accordingly."""
    target_rating = Rating.objects.get(player=target, ladder=ladder)
    lower = ladder.rating_set.filter(rank__lt=target_rating.rank)
    for rating in lower:
        rating.rank += 1
        rating.save()
    target_rating.rank = None
    target_rating.is_active = False
    target_rating.save()

def rejoin(target, ladder):
    """Mark the player as active again and put them at the bottom of the ladder."""
    target_rating = Rating.objects.get(player=target, ladder=ladder)
    target_rating.is_active = True
    max_rank = ladder.rating_set.aggregate(models.Max('ranking'))
    max_rank = max_rank['ranking__max']
    target_rating.rank = max_rank + 1
    target_rating.save()
        



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
def set_ratings(sender, instance, created, **kwargs):
    if created:
        instance.white_rating = instance.ladder.rating_set.get(player=instance.white).rating
        instance.black_rating = instance.ladder.rating_set.get(player=instance.black).rating
        # now use helper methods above to adjust ranks and set ratings.
        instance.save()
        

# People join ladders at the bottom
@receiver(post_save, sender=Rating)
def set_rank(sender, instance, created, **kwargs):
    if created:
        max_rank = instance.ladder.rating_set.aggregate(models.Max('ranking'))
        max_rank = max_rank['ranking__max']
        instance.ranking = max_rank + 1
        instance.save()

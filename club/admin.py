from django.contrib import admin
from club.models import Player, Game, Algorithm, Ladder, Rating

class PlayerAdmin(admin.ModelAdmin):
    pass


class GameAdmin(admin.ModelAdmin):
    pass


class AlgorithmAdmin(admin.ModelAdmin):
    pass


class LadderAdmin(admin.ModelAdmin):
    pass


class RatingAdmin(admin.ModelAdmin):
    pass


admin.site.register(Player, PlayerAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Algorithm, AlgorithmAdmin)
admin.site.register(Ladder, LadderAdmin)
admin.site.register(Rating, RatingAdmin)

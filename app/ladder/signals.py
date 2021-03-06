from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

from app.ladder.models import ScoreChange, Match, Player, LadderSettings, QueuePlayer, LadderQueue


@receiver([post_save, post_delete], sender=ScoreChange)
def score_change(instance, **kwargs):
    player = instance.player

    season = LadderSettings.get_solo().current_season
    vals = player.scorechange_set.filter(season=season).aggregate(
        Sum('mmr_change'), Sum('score_change'))

    player.ladder_mmr = vals['mmr_change__sum']
    player.score = vals['score_change__sum']

    player.save()


@receiver(post_delete, sender=Match)
def match_change(**kwargs):
    Player.objects.update_ranks()


@receiver(post_delete, sender=QueuePlayer)
def qplayer_change(instance, **kwargs):
    try:
        queue = instance.queue
    except LadderQueue.DoesNotExist:
        # this happens on bulk removal of afk players;
        # queue already been deleted, it's fine
        return

    if queue.players.count() < 10:
        queue.balance = None
        queue.save()

    if queue.players.count() < 1:
        queue.delete()

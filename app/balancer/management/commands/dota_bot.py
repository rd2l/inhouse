from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from app.balancer.managers import BalanceResultManager
from app.ladder.managers import MatchManager
from enum import IntEnum
import gevent
from app.ladder.models import Player
import dota2
import os

from steam import SteamClient, SteamID
from dota2 import Dota2Client

from dota2.enums import DOTA_GC_TEAM, EMatchOutcome, DOTAChatChannelType_t


class LobbyState(IntEnum):
    UI = 0
    READYUP = 4
    SERVERSETUP = 1
    RUN = 2
    POSTGAME = 3
    NOTREADY = 5
    SERVERASSIGN = 6

GameModes = {
    'AP': dota2.enums.DOTA_GameMode.DOTA_GAMEMODE_AP,
    'AR': dota2.enums.DOTA_GameMode.DOTA_GAMEMODE_AR,
    'RD': dota2.enums.DOTA_GameMode.DOTA_GAMEMODE_RD,
    'SD': dota2.enums.DOTA_GameMode.DOTA_GAMEMODE_SD,
    'CD': dota2.enums.DOTA_GameMode.DOTA_GAMEMODE_CD,
    'CM': dota2.enums.DOTA_GameMode.DOTA_GAMEMODE_CM,
}

GameServers = {
    'EU': dota2.enums.EServerRegion.Europe,
    'EUW': dota2.enums.EServerRegion.Europe,
    'EUE': dota2.enums.EServerRegion.Austria,
    'US': dota2.enums.EServerRegion.USWest,
    'USW': dota2.enums.EServerRegion.USWest,
    'USE': dota2.enums.EServerRegion.USEast,
    'AU': dota2.enums.EServerRegion.Australia,
    'SEA': dota2.enums.EServerRegion.Singapore,
    'SI': dota2.enums.EServerRegion.Singapore,
    'KO': dota2.enums.EServerRegion.Korea,
}


# TODO: make DotaBot class

class Command(BaseCommand):
    def __init__(self):
        self.bots = []

    def add_arguments(self, parser):
        parser.add_argument('-n', '--number',
                            nargs='?', type=int, default=2, const=2)

    def handle(self, *args, **options):
        bots_num = options['number']

        bot_login = os.environ.get('BOT_LOGIN', '')
        bot_password = os.environ.get('BOT_PASSWORD', '')
        credentials = [
            {
                'login': '%s%d' % (bot_login, i),
                'password': '%s%d' % (bot_password, i),
            } for i in xrange(1, bots_num+1)
        ]

        try:
            gevent.joinall([
                gevent.spawn(self.start_bot, c) for c in credentials
            ])
        finally:
            for bot in self.bots:
                bot.exit()
                bot.steam.logout()

    def start_bot(self, credentials):
        client = SteamClient()
        dota = Dota2Client(client)

        dota.balance_answer = None
        dota.min_mmr = 0
        dota.lobby_options = {}
        dota.voice_required = False

        self.bots.append(dota)

        client.verbose_debug = True
        dota.verbose_debug = True

        @client.on('logged_on')
        def start_dota():
            dota.launch()

        @dota.on('ready')
        def dota_started():
            print 'Logged in: %s %s' % (dota.steam.username, dota.account_id)

            self.create_new_lobby(dota)

        @dota.on(dota2.features.Lobby.EVENT_LOBBY_NEW)
        def lobby_new(lobby):
            print '%s joined lobby %s' % (dota.steam.username, lobby.lobby_id)

            dota.join_practice_lobby_team()  # jump to unassigned players
            dota.join_lobby_chat()

        @dota.on(dota2.features.Lobby.EVENT_LOBBY_CHANGED)
        def lobby_changed(lobby):
            if int(lobby.state) == LobbyState.UI:
                # game isn't launched yet;
                # check if all players have right to play
                if dota.voice_required:
                    Command.kick_voice_issues(dota)
                if dota.min_mmr > 0:
                    Command.kick_low_mmr(dota)

            if int(lobby.state) == LobbyState.POSTGAME:
                # game ended, process result and create new lobby
                self.process_game_result(dota)
                self.create_new_lobby(dota)

        @dota.on(dota2.features.Chat.EVENT_CHAT_JOINED)
        def chat_joined(channel):
            print '%s joined chat channel %s' % (dota.steam.username, channel.channel_name)

        @dota.on(dota2.features.Chat.EVENT_CHAT_MESSAGE)
        def chat_message(channel, sender, text, msg_obj):
            if channel.channel_type != DOTAChatChannelType_t.DOTAChannelType_Lobby:
                return  # ignore postgame and other chats

            # process known commands
            # TODO: refactor to something like this:
            # TODO:    command = text.split[' '][0]
            # TODO:    commands[command].run()
            if text.startswith('!balance'):
                self.balance_command(dota, text)
            elif text.startswith('!start'):
                self.start_command(dota)
            elif text.startswith('!mmr'):
                self.mmr_command(dota, text)
            elif text.startswith('!flip'):
                dota.flip_lobby_teams()
            elif text.startswith('!voice'):
                self.voice_command(dota, text)
            elif text.startswith('!teamkick'):
                self.teamkick_command(dota, text)
            elif text.startswith('!check'):
                self.check_command(dota)
            elif text.startswith('!forcestart'):
                self.balance_answer = None
                dota.launch_practice_lobby()
            elif text.startswith('!mode'):
                self.mode_command(dota, text)
            elif text.startswith('!server'):
                self.server_command(dota, text)

        client.login(credentials['login'], credentials['password'])
        client.run_forever()

    @staticmethod
    def create_new_lobby(bot):
        print 'Making new lobby\n'

        bot.balance_answer = None
        bot.lobby_options = {
            'game_name': Command.generate_lobby_name(bot),
            'game_mode': dota2.enums.DOTA_GameMode.DOTA_GAMEMODE_CD,
            'server_region': int(dota2.enums.EServerRegion.Europe),
            'fill_with_bots': False,
            'allow_spectating': True,
            'allow_cheats': False,
            'allchat': False,
            'dota_tv_delay': 2,
            'pause_setting': 1,
        }

        bot.create_practice_lobby(
            password=os.environ.get('LOBBY_PASSWORD', ''),
            options=bot.lobby_options)

    @staticmethod
    def balance_command(bot, command):
        print
        print 'Balancing players'

        # convert steam64 into 32bit dota id and build a dic of {id: player}
        players_steam = {
            SteamID(player.id).as_32: player for player in bot.lobby.members
            if player.team in (DOTA_GC_TEAM.GOOD_GUYS, DOTA_GC_TEAM.BAD_GUYS)
        }

        if len(players_steam) < 10:
            bot.send_lobby_message('We don\'t have 10 players')
            return

        # get players from DB using dota id
        players = Player.objects.filter(dota_id__in=players_steam.keys())
        players = {player.dota_id: player for player in players}

        unregistered = [players_steam[p].name for p in players_steam.keys()
                        if str(p) not in players]

        if unregistered:
            bot.send_lobby_message('I don\'t know these guys: %s' %
                                   ', '.join(unregistered))
            return

        print players

        players = [(p.name, p.ladder_mmr) for p in players.values()]
        result = BalanceResultManager.balance_teams(players)

        try:
            answer_num = int(command.split(' ')[1])
            answer_num = max(1, min(40, answer_num))
        except (IndexError, ValueError):
            answer_num = 1

        url = reverse('balancer:balancer-result', args=(result.id,))
        host = os.environ.get('BASE_URL', 'localhost:8000')

        url = '%s%s?page=%s' % (host, url, answer_num)

        bot.balance_answer = answer = result.answers.all()[answer_num-1]
        for i, team in enumerate(answer.teams):
            player_names = [p[0] for p in team['players']]
            bot.send_lobby_message('Team %d: %s' % (i+1, ' | '.join(player_names)))
        bot.send_lobby_message(url)

    @staticmethod
    def start_command(bot):
        if not bot.balance_answer:
            bot.send_lobby_message('Please balance teams first.')
            return

        if not Command.check_teams_setup(bot):
            bot.send_lobby_message('Please join slots according to balance.')
            return

        bot.send_lobby_message('Ready to start')
        bot.launch_practice_lobby()

    @staticmethod
    def mmr_command(bot, command):
        print
        print 'Setting lobby MMR: '
        print command

        try:
            min_mmr = int(command.split(' ')[1])
            min_mmr = max(0, min(9000, min_mmr))
        except (IndexError, ValueError):
            return

        bot.min_mmr = min_mmr
        bot.lobby_options['game_name'] = Command.generate_lobby_name(bot)
        bot.config_practice_lobby(bot.lobby_options)

        bot.send_lobby_message('Min MMR set to %d' % min_mmr)

    @staticmethod
    def voice_command(bot, command):
        print
        print 'Voice command: '
        print command

        bot.voice_required = True
        try:
            if command.split(' ')[1] == 'off':
                bot.voice_required = False
        except (IndexError, ValueError):
            pass

        if bot.voice_required:
            Command.kick_voice_issues(bot)

        bot.lobby_options['game_name'] = Command.generate_lobby_name(bot)
        bot.config_practice_lobby(bot.lobby_options)

        bot.send_lobby_message('Voice required set to %s' % bot.voice_required)

    @staticmethod
    def teamkick_command(bot, command):
        print
        print 'Teamkick command'
        print command

        try:
            name = command.split(' ')[1].lower()
        except (IndexError, ValueError):
            return

        for player in bot.lobby.members:
            if player.team not in (DOTA_GC_TEAM.GOOD_GUYS, DOTA_GC_TEAM.BAD_GUYS):
                continue
            if player.name.lower().startswith(name):
                print 'kicking %s' % player.name
                bot.practice_lobby_kick_from_team(SteamID(player.id).as_32)

    # this command checks if all lobby members are known to bot
    @staticmethod
    def check_command(bot):
        players_steam = {
            SteamID(player.id).as_32: player for player in bot.lobby.members
        }

        # get players from DB using dota id
        players = Player.objects.filter(
            dota_id__in=players_steam.keys()
        ).values_list('dota_id', flat=True)

        unregistered = [players_steam[p].name for p in players_steam.keys()
                        if str(p) not in players]

        if unregistered:
            bot.send_lobby_message('I don\'t know these guys: %s' %
                                   ', '.join(unregistered))
        else:
            bot.send_lobby_message('I know everybody here.')

    @staticmethod
    def mode_command(bot, command):
        print
        print 'Mode command'
        print command

        try:
            mode = command.split(' ')[1].upper()
        except (IndexError, ValueError):
            return

        bot.lobby_options['game_mode'] = GameModes[mode]
        bot.config_practice_lobby(bot.lobby_options)

        bot.send_lobby_message('Game mode set to %s' % mode)

    @staticmethod
    def server_command(bot, command):
        print
        print 'Server command'
        print command

        try:
            mode = command.split(' ')[1].upper()
        except (IndexError, ValueError):
            return

        bot.lobby_options['server_region'] = GameServers[mode]
        bot.config_practice_lobby(bot.lobby_options)

        bot.send_lobby_message('Game server set to %s' % mode)

    @staticmethod
    def process_game_result(bot):
        print 'Game is finished!\n'
        print bot.lobby

        if not bot.balance_answer:
            print 'No balance exists (probably !forcestart)'
            return

        if bot.lobby.match_outcome == EMatchOutcome.RadVictory:
            print 'Radiant won!'
            MatchManager.record_balance(bot.balance_answer, 0)
        elif bot.lobby.match_outcome == EMatchOutcome.DireVictory:
            print 'Dire won!'
            MatchManager.record_balance(bot.balance_answer, 1)

    # checks if teams are setup according to balance
    @staticmethod
    def check_teams_setup(bot):
        print 'Checking teams setup\n'

        # get teams from game (player ids)
        # TODO: make function game_members_to_ids(lobby)
        game_teams = [set(), set()]
        for player in bot.lobby.members:
            if player.team in (DOTA_GC_TEAM.GOOD_GUYS, DOTA_GC_TEAM.BAD_GUYS):
                player_id = str(SteamID(player.id).as_32)  # TODO: models.Player.dota_id should be int, not str
                game_teams[player.team].add(player_id)

        print 'Game teams:'
        print game_teams

        # get teams from balance result (player ids)
        # TODO: make function balance_teams_to_ids(balance_answer)
        balancer_teams = [
            set(Player.objects.filter(name__in=[player[0] for player in team['players']])
                              .values_list('dota_id', flat=True))
            for team in bot.balance_answer.teams
        ]

        print 'Balancer teams:'
        print balancer_teams

        # compare teams from game to teams from balancer
        if game_teams == balancer_teams:
            print 'Teams are correct'
            return True
        elif game_teams == list(reversed(balancer_teams)):
            print 'Teams are correct (reversed)'

            # reverse teams in balance answer
            bot.balance_answer.teams = list(reversed(bot.balance_answer.teams))
            bot.balace_answer.save()

            print 'Corrected balance result:'
            print bot.balance_answer.teams

            return True

        print 'Teams don\'t match'

        return False

    @staticmethod
    def generate_lobby_name(bot):
        lobby_name = 'Inhouse Ladder'

        if bot.min_mmr > 0:
            lobby_name += ' %d+' % bot.min_mmr
        if bot.voice_required:
            lobby_name += ' Voice'

        return lobby_name

    @staticmethod
    def kick_voice_issues(bot):
        players_steam = {
            SteamID(player.id).as_32: player for player in bot.lobby.members
            if player.team in (DOTA_GC_TEAM.GOOD_GUYS, DOTA_GC_TEAM.BAD_GUYS)
        }

        problematic = Player.objects.filter(
            dota_id__in=players_steam.keys(),
            voice_issues=True
        ).values_list('dota_id', flat=True)

        print 'Problematic: %s' % problematic

        for player in problematic:
            bot.practice_lobby_kick_from_team(int(player))

    @staticmethod
    def kick_low_mmr(bot):
        players_steam = {
            SteamID(player.id).as_32: player for player in bot.lobby.members
            if player.team in (DOTA_GC_TEAM.GOOD_GUYS, DOTA_GC_TEAM.BAD_GUYS)
        }
        players = Player.objects.filter(
            dota_id__in=players_steam.keys()
        ).values_list('dota_id', flat=True)

        if bot.min_mmr > 1000:
            # this is dota mmr
            problematic = players.filter(dota_mmr__lt=bot.min_mmr)
        else:
            # this is ladder mmr
            problematic = players.filter(ladder_mmr__lt=bot.min_mmr)

        print 'Problematic: %s' % problematic

        for player in problematic:
            bot.practice_lobby_kick_from_team(int(player))

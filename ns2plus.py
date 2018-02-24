import asyncio
import logging
import sqlite3

import aiohttp
from requests.structures import CaseInsensitiveDict

import config
import queries
import templates
import utils

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)

DB = 'ns2plus.sqlite3'


class Database():
    def __init__(self):
        self.db = DB

    def __enter__(self):
        self.conn = sqlite3.connect(self.db)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()


class Stats():
    def __init__(self, loop):
        loop.run_until_complete(self.update())

    async def update(self):
        logger.info(templates.LOG_GET.format(config.NS2STATS_DB_URL))

        if config.NS2STATS_ENABLE_UPDATES:
            with aiohttp.ClientSession() as session:
                async with session.get(config.NS2STATS_DB_URL) as resp:
                    data = await resp.read()
                    with open(DB, 'wb') as f:
                        f.write(data)

        with Database() as db:
            self.steam_ids = CaseInsensitiveDict()
            for ix in db.execute('SELECT steamId, playerName from PlayerRoundStats').fetchall():
                entry = dict(ix)
                self.steam_ids[entry['playerName']] = entry['steamId']

    @staticmethod
    def _percent_formatter(x1, x2, x3=False):
        if not x3:
            r = [x1, x1 + x2]
        else:
            r = [x1, x2 + x3]
        try:
            r.append('({}%)'.format(round(r[0] / r[1] * 100, 1)))
        except ZeroDivisionError:
            r.append('')

        return '{}/{} {}'.format(*r)

    @staticmethod
    def _weighted_avg(l):
        a = sum([x * y for x, y in l])
        b = sum([y for _, y in l])
        return a / b

    def get_comm_stats(self, player):
        if player in self.steam_ids:
            steam_id = self.steam_ids[player]
        else:
            raise ValueError

        comm_stats = {'supplies': {}}

        with Database() as db:
            try:
                query = queries.PLAYER_STATS.format(steam_id)
                results = [dict(ix) for ix in db.execute(query).fetchall()]
                stats = results[0]
            except:
                pass
            else:
                comm_stats['Name'] = stats['playerName']
                comm_stats['Steam ID'] = stats['steamId']
                comm_stats['Hive Skill'] = stats['hiveSkill']

            try:
                query = queries.COMM_WL.format(steam_id)
                results = [dict(ix) for ix in db.execute(query).fetchall()]
                winloss = results[0]
            except:
                pass
            else:
                comm_stats['Wins'] = self._percent_formatter(winloss['commanderWins'], winloss['commanderLosses'])

            try:
                query = queries.COMM_SUPPLIES.format(steam_id)
                results = [dict(ix) for ix in db.execute(query).fetchall()]
                supply = results[0]
            except:
                pass
            else:
                comm_stats['supplies']['Medpack Efficiency'] = self._percent_formatter(supply['medpackPicks'],
                                                                                       supply['medpackMisses'])
                comm_stats['supplies']['Medpack Accuracy'] = self._percent_formatter(supply['medpackHitsAcc'],
                                                                                     supply['medpackPicks'],
                                                                                     supply['medpackMisses'])
                comm_stats['supplies']['Ammo Efficiency'] = self._percent_formatter(supply['ammopackPicks'],
                                                                                    supply['ammopackMisses'])
                comm_stats['supplies']['Catpack Efficiency'] = self._percent_formatter(supply['catpackPicks'],
                                                                                       supply['catpackMisses'])

        return comm_stats

    def get_player_stats(self, player):
        if player in self.steam_ids:
            steam_id = self.steam_ids[player]
        else:
            raise ValueError

        player_stats = {'marine': {}, 'alien': {}}
        weapons = {}

        with Database() as db:
            try:
                query = queries.PLAYER_STATS.format(steam_id)
                results = [dict(ix) for ix in db.execute(query).fetchall()]
                stats = results[0]
            except:
                pass
            else:
                player_stats['Name'] = stats['playerName']
                player_stats['Steam ID'] = stats['steamId']
                player_stats['Hive Skill'] = stats['hiveSkill']
                player_stats['Wins'] = self._percent_formatter(stats['wins'], stats['losses'])
                player_stats['KDR'] = round(stats['kdr'], 1)

            try:
                query = queries.PLAYER_ACC.format(steam_id)
                for ix in db.execute(query).fetchall():
                    row = dict(ix)
                    weapons[row['weapon']] = row
            except:
                pass
            else:
                marine_weapons = ['Rifle', 'Pistol', 'Shotgun']
                alien_weapons = ['Bite', 'Swipe', 'Gore', 'Spikes']

                for weapon in marine_weapons:
                    try:
                        player_stats['marine'][weapon + ' Accuracy'] = '{}%'.format(
                            round(weapons[weapon]['accuracy'], 1))
                    except:
                        pass
                for weapon in alien_weapons:
                    try:
                        player_stats['alien'][weapon + ' Accuracy'] = '{}%'.format(
                            round(weapons[weapon]['accuracy'], 1))
                    except:
                        pass

                # Only run weighted average with weapons that the player has used.
                available_marine_weapons = []
                available_alien_weapons = []

                for weapon in marine_weapons:
                    if weapon in weapons:
                        available_marine_weapons.append((weapons[weapon]['accuracy'], weapons[weapon]['playerDamage']))
                for weapon in alien_weapons:
                    if weapon in weapons:
                        available_alien_weapons.append((weapons[weapon]['accuracy'], weapons[weapon]['playerDamage']))

                marine_acc_wavg = self._weighted_avg(available_marine_weapons)
                alien_acc_melee_wavg = self._weighted_avg(available_alien_weapons)

                player_stats['Marine Accuracy'] = '{}%'.format(round(marine_acc_wavg, 1))
                player_stats['Alien Melee Accuracy'] = '{}%'.format(round(alien_acc_melee_wavg, 1))

        return player_stats


loop = asyncio.get_event_loop()
stats = Stats(loop)

import asyncio
import logging
import statistics

import aiohttp
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from requests.structures import CaseInsensitiveDict
from scipy.stats import norm
import io

import config
from config import Database
import queries
import templates
import utils

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)



class Stats():
    def __init__(self, loop):
        loop.run_until_complete(self.update())

    async def update(self):
        if config.DATABASE == 'SQLITE' and config.SQLITE_ENABLE_UPDATES:
            logger.info(templates.LOG_GET.format(config.SQLITE_DB_URL))
            with aiohttp.ClientSession() as session:
                async with session.get(config.SQLITE_DB_URL) as resp:
                    data = await resp.read()
                    with open(config.DB, 'wb') as f:
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

    def _player_weapon_stats(self, steam_id):
        weapons = {}
        with Database() as db:
            weapon_list = [dict(ix)['weapon'] for ix in db.execute(queries.WEAPON_LIST).fetchall()]
            round_weapon = [dict(ix) for ix in db.execute(queries.PLAYER_ACC.format(steam_id)).fetchall()]

            for weapon in weapon_list:
                accuracies = [(x['hits'] - x['onosHits']) / (x['hits'] + x['misses'] - x['onosHits'])
                              for x in round_weapon if x['weapon'] == weapon
                              and (x['hits'] + x['misses'] - x['onosHits']) != 0
                              and (x['hits'] - x['onosHits']) != 0]
                player_dmg = sum([x['playerDamage'] for x in round_weapon
                                  if x['weapon'] == weapon and x['playerDamage']])
                if len(accuracies) > 2:
                    weapons[weapon] = {
                        'acc_avg': statistics.mean(accuracies),
                        'acc_std': statistics.pstdev(accuracies),
                        'player_dmg': player_dmg,
                        'data': accuracies
                    }
        return weapons

    def get_player_stats(self, player):
        if player in self.steam_ids:
            steam_id = self.steam_ids[player]
        else:
            raise ValueError

        player_stats = {'marine': {}, 'alien': {}}

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

            try:
                query = queries.PLAYER_LIFEFORM.format(steam_id)
                results = [dict(ix) for ix in db.execute(query).fetchall()]
                stats = results[0]
            except:
                pass
            else:
                player_stats['Lifeform'] = stats['class']

            try:
                query = queries.PLAYER_KDR.format(steam_id)
                kdr_per_match = [dict(ix)['kdr'] for ix in db.execute(query).fetchall()]
            except:
                pass
            else:
                player_stats['KDR'] = round(statistics.mean(kdr_per_match), 2)

            weapons = self._player_weapon_stats(steam_id)

            marine_weapons = ['Rifle', 'Pistol', 'Shotgun']
            alien_weapons = ['Bite', 'Swipe', 'Gore', 'Spikes', 'LerkBite']

            for weapon in marine_weapons:
                try:
                    player_stats['marine'][weapon + ' Accuracy'] = '{}% (σ={}%)'.format(
                        round(weapons[weapon]['acc_avg']*100, 1),
                        round(weapons[weapon]['acc_std'] * 100, 1))
                except:
                    pass
            for weapon in alien_weapons:
                try:
                    player_stats['alien'][weapon + ' Accuracy'] = '{}% (σ={}%)'.format(
                        round(weapons[weapon]['acc_avg']*100, 1),
                        round(weapons[weapon]['acc_std'] * 100, 1))
                except:
                    pass

            # Only run weighted average with weapons that the player has used.
            available_marine_weapons = []
            available_alien_weapons = []

            wavg_marine_weapons = ['Rifle', 'Pistol', 'Shotgun']
            wavg_alien_weapons = ['Bite', 'Swipe', 'Gore', 'LerkBite']

            for weapon in wavg_marine_weapons:
                if weapon in weapons:
                    available_marine_weapons.append((weapons[weapon]['acc_avg']*100, weapons[weapon]['player_dmg']))
            for weapon in wavg_alien_weapons:
                if weapon in weapons:
                    available_alien_weapons.append((weapons[weapon]['acc_avg']*100, weapons[weapon]['player_dmg']))

            marine_acc_wavg = self._weighted_avg(available_marine_weapons)
            alien_acc_melee_wavg = self._weighted_avg(available_alien_weapons)

            player_stats['Marine Accuracy'] = '{}%'.format(round(marine_acc_wavg, 1))
            player_stats['Alien Melee Accuracy'] = '{}%'.format(round(alien_acc_melee_wavg, 1))

        return player_stats


    def get_player_chart(self, player, type):
        if player in self.steam_ids:
            steam_id = self.steam_ids[player]
        else:
            raise ValueError

        if type == 'kdr':
            fig, ax = plt.subplots()

            with Database() as db:
                results = [dict(ix) for ix in db.execute(queries.PLAYER_KDR.format(steam_id)).fetchall()]
            data = np.array([float(x['kdr']) for x in results])
            mu, std = norm.fit(data)

            xmin, xmax = 0, max(data)
            values, bins, _ = ax.hist(data, bins=np.arange(xmin, xmax, 0.2), density=1, alpha=0.6, color='g')
            index_1 = next(x[0] for x in enumerate(bins) if x[1] > 1.0)
            area = sum(np.diff([x for x in bins[index_1:] if x > 1]) * values[index_1:])

            ax.set_title("P(KDR≥1) = %.2f" % (area))
            ax.axvline(1, color='black', linestyle='dashed', linewidth=1)
            ax.axvline(mu, color='r', linestyle='dashed', linewidth=1)
            ax.set_xlabel('KDR')

            img = io.BytesIO()
            fig.savefig(img, format='png')
            plt.close(fig)
            img.seek(0)

            return img

        else:
            weapon_stats = self._player_weapon_stats(steam_id)
            if type.title() in weapon_stats:
                fig, ax = plt.subplots()
                weapon = type.title()
                data = np.array([x*100 for x in weapon_stats[weapon]['data']])

                mu, std = norm.fit(data)
                n = len(data)

                xmin, xmax = 0, max(data)
                ax.hist(data, bins=np.arange(xmin, xmax, 2), density=1, alpha=0.6, color='g')
                x = np.linspace(xmin, xmax, 100)
                p = norm.pdf(x, mu, std)
                ax.plot(x, p, 'k', linewidth=2)

                title = "%s: μ = %.2f,  σ = %.2f, N = %i" % (weapon, mu, std, n)
                ax.set_title(title)
                ax.axvline(mu + std, color='black', linestyle='dashed', linewidth=1)
                ax.axvline(mu - std, color='black', linestyle='dashed', linewidth=1)
                ax.axvline(mu, color='r', linestyle='dashed', linewidth=1)
                ax.set_xlabel('Accuracy')

                img = io.BytesIO()
                fig.savefig(img, format='png')
                plt.close(fig)
                img.seek(0)

                return img
            else:
                raise ValueError

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

    def get_awards(self):
        def _queryFetch(query):
            r = [dict(ix) for ix in db.execute(query).fetchall()][0]
            for key, value in r.items():
                if key == 'time':
                    m, s = divmod(value, 60)
                    h, m = divmod(m, 60)
                    h_plural = 's' if int(h) > 1 else ''
                    m_plural = 's' if int(m) > 1 else ''
                    s_plural = 's' if int(s) > 1 else ''
                    human_time = ''
                    if h > 0:
                        human_time += '{} hora{}, '.format(int(h), h_plural)
                    if m > 0:
                        human_time += '{} min{}, '.format(int(m), m_plural)
                    if s > 1 or h or m:
                        human_time += '{} seg{}'.format(int(s), s_plural)
                    else:
                        human_time += '{} milisegs'.format(int(s*1000))
                    r['time'] = human_time
                if key == 'winmarine':
                    r['winmarine'] = 'ganó' if value == 1 else 'perdió'
                if key == 'winalien':
                    r['winalien'] = 'ganó' if value == 2 else 'perdió'
            return tuple(r.values())

        awards = {}
        with Database() as db:
            awards['parasite'] = _queryFetch(queries.AWARD_PARASITE)
            awards['dead'] = _queryFetch(queries.AWARD_DEAD)
            awards['embryo'] = _queryFetch(queries.AWARD_EMBRYO)
            awards['exo_egg'] = _queryFetch(queries.AWARD_EXO_EGG)
            awards['welder_kills'] = _queryFetch(queries.AWARD_WELDER_KILLS)
            awards['parasite_kills'] = _queryFetch(queries.AWARD_PARASITE_KILLS)
            awards['spray_kills'] = _queryFetch(queries.AWARD_SPRAY_KILLS)
            awards['whip_kills'] = _queryFetch(queries.AWARD_WHIP_KILLS)
            awards['sentry_kills'] = _queryFetch(queries.AWARD_SENTRY_KILLS)
            awards['onos_killer'] = _queryFetch(queries.AWARD_ONOS_KILLER)
            awards['fade_killer'] = _queryFetch(queries.AWARD_FADE_KILLER)
            awards['lerk_killer'] = _queryFetch(queries.AWARD_LERK_KILLER)
            awards['1_kill_lerk'] = _queryFetch(queries.AWARD_1KILL_LERK)

            awards['killing_place'] = _queryFetch(queries.AWARD_KILLING_PLACE)

            awards['2nd_hive'] = _queryFetch(queries.AWARD_2ND_HIVE)
            awards['exo_tech'] = _queryFetch(queries.AWARD_EXO_TECH)
            awards['catpack_tech'] = _queryFetch(queries.AWARD_CATPACK_TECH)
            awards['shotgun_tech'] = _queryFetch(queries.AWARD_SHOTGUN_TECH)
            awards['jp_tech'] = _queryFetch(queries.AWARD_JP_TECH)
            awards['gl_tech'] = _queryFetch(queries.AWARD_GL_TECH)

            awards['phase_gate'] = _queryFetch(queries.AWARD_PHASE_GATE)
            awards['arc'] = _queryFetch(queries.AWARD_ARC)

            awards['commander_eject'] = _queryFetch(queries.AWARD_COMMANDER_EJECT)
        return awards

    def get_top(self, type):
        if type == 'melee':
            query = queries.TOP10_MELEE
        elif type == 'kdr':
            query = queries.TOP10_KDR
        elif type == 'rifle':
            query = queries.TOP10_RIFLE
        elif type == 'shotgun':
            query = queries.TOP10_SHOTGUN
        elif type == 'comm':
            query = queries.TOP10_COMM
        else:
            raise ValueError('Query does not exists')
        with Database() as db:
            results = [dict(ix) for ix in db.execute(query).fetchall()]
            top10 = []
            for i, r in enumerate(results, 1):
                top10.append('{}. **{}** (*{}*)'.format(i, r['playerName'], round(r['value'], 1)))
            return top10

loop = asyncio.get_event_loop()
stats = Stats(loop)

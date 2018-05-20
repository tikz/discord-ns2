COMM_SUPPLIES = 'SELECT sum(medpackPicks) as medpackPicks, sum(medpackMisses) as medpackMisses, sum(ammopackPicks) as ammopackPicks, sum(ammopackMisses) as ammopackMisses, sum(catpackPicks) as catpackPicks, sum(catpackMisses) as catpackMisses, sum(medpackHitsAcc) as medpackHitsAcc from MarineCommStats where steamId = {}'

COMM_WL = 'SELECT commanderWins, commanderLosses from PlayerStats where steamId = {}'

COMM_MAPS = 'select ri.mapName, count(*) as wins from PlayerRoundStats as prs inner join RoundInfo as ri on ri.roundId = prs.roundId where prs.steamId = {} and prs.commanderTime > 600 and ri.winningTeam = prs.teamNumber group by ri.mapName order by wins desc limit 3'

PLAYER_ACC = 'select *, 100.0*(hits-onosHits)/(hits+misses-onosHits) as accuracy from (select pws.steamId, pws.weapon, sum(pws.hits) as hits, sum(pws.misses) as misses, sum(pws.onosHits) as onosHits, sum(pws.playerDamage) as playerDamage from PlayerWeaponStats pws where pws.steamId = {} and pws.roundId > {} group by pws.weapon) order by hits desc'

WEAPON_LIST = 'select weapon from PlayerWeaponStats group by weapon'
PLAYER_ACC = 'select * from PlayerWeaponStats where steamId = {}'

PLAYER_STATS = 'SELECT steamId, playerName, hiveSkill, wins, losses, 1.0*kills/deaths as kdr from PlayerStats where steamId = {}'

PLAYER_MAPS = 'select wins.mapName, 100.0*wins/(wins+losses) as wl, wins+losses as playcount from (select ri.mapName, count(*) as wins from PlayerRoundStats as prs inner join RoundInfo as ri on ri.roundId = prs.roundId where prs.steamId = {0} and ri.winningTeam = prs.teamNumber group by ri.mapName) wins inner join (select ri.mapName, count(*) as losses from PlayerRoundStats as prs inner join RoundInfo as ri on ri.roundId = prs.roundId  where prs.steamId = {0} and ri.winningTeam != prs.teamNumber group by ri.mapName) losses on wins.mapName = losses.mapName where playcount > 10 order by wl desc limit 3'


AWARD_DEAD = 'select ps.playerName, sum(pc.classTime) as time from PlayerClassStats as pc inner join PlayerStats ps on ps.steamId = pc.steamId where pc.class = "Dead" group by pc.steamId  order by time desc limit 1'
AWARD_EMBRYO = 'select ps.playerName, sum(pc.classTime) as time from PlayerClassStats as pc inner join PlayerStats ps on ps.steamId = pc.steamId where pc.class = "Embryo" group by pc.steamId  order by time desc limit 1'
AWARD_GORGE = 'select ps.playerName, sum(pc.classTime) as time from PlayerClassStats as pc inner join PlayerStats ps on ps.steamId = pc.steamId where pc.class = "Gorge" group by pc.steamId  order by time desc limit 1'
AWARD_KILLING_PLACE = 'select victimLocation, count(*) c from KillFeed group by victimLocation order by c desc limit 1'
AWARD_PARASITE = 'select ps.playerName, sum(pws.hits) as hits from PlayerWeaponStats pws inner join PlayerStats ps on ps.steamId = pws.steamId where pws.weapon = "Parasite" group by pws.steamId order by hits desc'
AWARD_EXO_EGG = 'select ps.playerName, sum(pws.kills) as kills from PlayerWeaponStats pws inner join PlayerStats ps on ps.steamId = pws.steamId where pws.weapon = "Exo" group by pws.steamId order by kills desc limit 1'
AWARD_COMMANDER_EJECT = 'select playerName, commanderTime as time from PlayerRoundStats prs inner join RoundInfo ri on ri.roundId = prs.roundId where commanderTime > 0 order by commanderTime asc limit 1'

AWARD_1KILL_LERK = 'select prs.playerName, pcs.classTime as time from PlayerClassStats pcs inner join PlayerRoundStats prs on prs.steamId = pcs.steamId and prs.roundId = pcs.roundId inner join PlayerWeaponStats pws on pws.steamId = pcs.steamId and pws.roundId = pcs.roundId and pws.weapon = "LerkBite" and pws.kills = 1  where pcs.class = "Lerk" order by pcs.classTime asc limit 1'

_AWARD_WEAPON_KILLS = 'select ps.playerName, sum(pws.kills) as kills from PlayerWeaponStats pws inner join PlayerStats ps on ps.steamId = pws.steamId where pws.weapon like "%{}%" group by pws.steamId order by kills desc'
_AWARD_RUSH_TECH = 'select playerName, r.gameTime time, ri.winningTeam as win{} from Research r inner join (select *, max(commanderTime) from PlayerRoundStats where teamNumber = {} group by roundId) prs on prs.roundId = r.roundId inner join RoundInfo ri on ri.roundId = r.roundId where r.researchId = "{}" order by r.gameTime asc'
_AWARD_RUSH_BUILDING = 'select prs.playerName, b.gameTime as time, ri.winningTeam as win{} from Buildings b inner join (select *, max(commanderTime) from PlayerRoundStats where teamNumber = {} group by roundId) prs on prs.roundId = b.roundId inner join RoundInfo ri on ri.roundId = b.roundId where b.techId = "{}" and b.gameTime != 0 order by gameTime asc limit 1'
_AWARD_CLASS_KILLER = 'select ps.playerName, count(*) c from KillFeed kf inner join PlayerStats ps on ps.steamId = kf.killerSteamId where kf.victimClass = "{}" group by ps.playerName order by c desc limit 1'
AWARD_WELDER_KILLS = _AWARD_WEAPON_KILLS.format('Welder')
AWARD_PARASITE_KILLS = _AWARD_WEAPON_KILLS.format('Parasite')
AWARD_SPRAY_KILLS = _AWARD_WEAPON_KILLS.format('Spray')
AWARD_SENTRY_KILLS = _AWARD_WEAPON_KILLS.format('Sentry')
AWARD_WHIP_KILLS = _AWARD_WEAPON_KILLS.format('Whip')
AWARD_ONOS_KILLER = _AWARD_CLASS_KILLER.format('Onos')
AWARD_FADE_KILLER = _AWARD_CLASS_KILLER.format('Fade')
AWARD_LERK_KILLER = _AWARD_CLASS_KILLER.format('Lerk')
AWARD_SHOTGUN_TECH = _AWARD_RUSH_TECH.format('marine', 1, 'ShotgunTech')
AWARD_CATPACK_TECH = _AWARD_RUSH_TECH.format('marine', 1, 'CatPackTech')
AWARD_EXO_TECH = _AWARD_RUSH_TECH.format('marine', 1, 'ExosuitTech')
AWARD_JP_TECH = _AWARD_RUSH_TECH.format('marine', 1, 'JetpackTech')
AWARD_GL_TECH = _AWARD_RUSH_TECH.format('marine', 1, 'GrenadeLauncherTech')

AWARD_ARC = _AWARD_RUSH_BUILDING.format('marine', 1, 'ARC')
AWARD_PHASE_GATE = _AWARD_RUSH_BUILDING.format('marine', 1, 'PhaseGate')
AWARD_2ND_HIVE = _AWARD_RUSH_BUILDING.format('alien', 2, 'Hive')

TOP10_KDR = 'select playerName, 1.0*kills/deaths value from PlayerStats where roundsPlayed > 20 order by value desc limit 10'
TOP10_RIFLE = 'select ps.playerName, 100.0*sum(pws.hits)/(sum(pws.hits)+sum(pws.misses)) value from PlayerWeaponStats pws inner join PlayerStats ps on ps.steamId = pws.steamId where pws.weapon = "Rifle" and ps.roundsPlayed > 20 group by pws.steamId order by value desc limit 10'
TOP10_SHOTGUN = 'select ps.playerName, 100.0*sum(pws.hits)/(sum(pws.hits)+sum(pws.misses)) value from PlayerWeaponStats pws inner join PlayerStats ps on ps.steamId = pws.steamId where pws.weapon = "Shotgun" and ps.roundsPlayed > 20 group by pws.steamId order by value desc limit 10'
TOP10_COMM = 'select playerName, 1.0*commanderWins/commanderLosses value from PlayerStats where commanderWins+commanderLosses > 10 order by value desc limit 10'
TOP10_MELEE = 'select playerName, sum(acc*dmg)/sumdmg value from (select ps.playerName, pws.*, 100.0*sum(pws.hits)/(sum(pws.hits)+sum(pws.misses)) acc, sum(pws.playerDamage) dmg, sumdmg from PlayerWeaponStats pws inner join PlayerStats ps on ps.steamId = pws.steamId left join (select steamId, sum(playerDamage) sumdmg from PlayerWeaponStats where (weapon = "Bite" or weapon = "LerkBite" or weapon = "Swipe" or weapon = "Gore") group by steamId) pws2 on pws2.steamId = pws.steamId where (pws.weapon = "Bite" or pws.weapon = "LerkBite" or pws.weapon = "Swipe" or pws.weapon = "Gore") and ps.roundsPlayed > 20 group by pws.steamId, pws.weapon) group by steamId order by value desc limit 10'
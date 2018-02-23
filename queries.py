COMM_SUPPLIES = 'SELECT sum(medpackPicks) as medpackPicks, sum(medpackMisses) as medpackMisses, sum(ammopackPicks) as ammopackPicks, sum(ammopackMisses) as ammopackMisses, sum(catpackPicks) as catpackPicks, sum(catpackMisses) as catpackMisses, sum(medpackHitsAcc) as medpackHitsAcc from MarineCommStats where steamId = {}'

COMM_WL = 'SELECT commanderWins, commanderLosses from PlayerStats where steamId = {}'

COMM_MAPS = 'select ri.mapName, count(*) as wins from PlayerRoundStats as prs inner join RoundInfo as ri on ri.roundId = prs.roundId where prs.steamId = {} and prs.commanderTime > 600 and ri.winningTeam = prs.teamNumber group by ri.mapName order by wins desc limit 3'

PLAYER_ACC = 'select *, 100.0*hits/(hits+misses) as accuracy from (select pws.steamId, pws.weapon, sum(pws.hits) as hits, sum(pws.misses) as misses, sum(pws.playerDamage) as playerDamage from PlayerWeaponStats pws where pws.steamId = {} group by pws.weapon) order by hits desc'

PLAYER_STATS = 'SELECT steamId, playerName, hiveSkill, wins, losses, 1.0*kills/deaths as kdr from PlayerStats where steamId = {}'

PLAYER_MAPS = 'select wins.mapName, 100.0*wins/(wins+losses) as wl, wins+losses as playcount from (select ri.mapName, count(*) as wins from PlayerRoundStats as prs inner join RoundInfo as ri on ri.roundId = prs.roundId where prs.steamId = {0} and ri.winningTeam = prs.teamNumber group by ri.mapName) wins inner join (select ri.mapName, count(*) as losses from PlayerRoundStats as prs inner join RoundInfo as ri on ri.roundId = prs.roundId  where prs.steamId = {0} and ri.winningTeam != prs.teamNumber group by ri.mapName) losses on wins.mapName = losses.mapName where playcount > 10 order by wl desc limit 3'

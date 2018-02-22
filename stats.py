# ns2plus.sqlite3 does not have proper CREATE TABLEs with relationships. Rearranging all the tables on update
# to make a proper SQLAlchemy model is a PITA

import json
import sqlite3

import config
import queries


class Database():
    def __init__(self):
        self.db = 'ns2plus.sqlite'

    def __enter__(self):
        self.conn = sqlite3.connect(self.db)
        self.conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
        return self.conn.cursor()

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()


class Stats():
    def __init__(self):
        self.update()
        pass

    def update(self):
        db_url = config.NS2STATS_DB_URL

        # response = requests.get(db_url, stream=True)
        #
        # with open(db, "wb") as handle:
        #     for data in tqdm(response.iter_content()):
        #         handle.write(data)

        with Database() as db:
            self.steam_ids = {}
            for ix in db.execute('SELECT steamId, playerName from PlayerStats').fetchall():
                entry = dict(ix)
                self.steam_ids[entry['playerName']] = entry['steamId']

        # self.round_info = json.dumps([dict(ix) for ix in db.execute('SELECT * from RoundInfo').fetchall()])
        # self.comm = json.dumps([dict(ix) for ix in db.execute('SELECT * from MarineCommStats').fetchall()])
        # self.player = json.dumps([dict(ix) for ix in db.execute('SELECT * from PlayerStats').fetchall()])

    def get_comm_stats(self, player):
        if player in self.steam_ids:
            steam_id = self.steam_ids[player]
        else:
            raise ValueError('No se encuentra el jugador')

        comm_stats = {}

        with Database() as db:
            try:
                query = json.dumps([dict(ix) for ix in db.execute(queries.COMM_SUPPLIES.format(steam_id)).fetchall()])
                supply = query[0]
            except:
                raise ValueError('El jugador no tiene partidas de comm marine')
            else:
                try:
                    accuracy =
                except ZeroDivisionError:

                else:
                    comm_stats['Medpack Accuracy'] = '{}/{} ({}%)'.format(supplies['medpackPicks'],
                                                                          supplies['medpackPicks'] + supplies[
                                                                              'medpackMiss'],
                                                                          round(supplies['medpackPicks'] / (
                                                                                  supplies['medpackPicks'] +
                                                                                  supplies['medpackMiss']), 2))


            print(supplies)
            print(round(supplies['medpackPicks'], 2))
            comm_stats['Medpack Accuracy'] = '{}/{} ({}%)'.format(supplies['medpackPicks'],
                                                                  supplies['medpackPicks'] + supplies['medpackMiss'],
                                                                  round(supplies['medpackPicks'] / (
                                                                              supplies['medpackPicks'] +
                                                                              supplies['medpackMiss']), 2))
        print(comm_stats)

a = Stats()
a.get_comm_stats('Tik')

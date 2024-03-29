class Game:
    def __init__(self, row):
        self.season_id = row[0]
        self.team_id = row[1]
        self.team_abbreviation = row[2]
        self.team_name = row[3]
        self.game_id = row[4]
        self.game_date = row[5]
        self.matchup = row[6]
        self.wl = row[7]
        self.minutes = row[8]
        self.points = row[9]
        self.fgm = row[10]
        self.fga = row[11]
        self.fg_pct = row[12]
        self.fg3m = row[13]
        self.fg3a = row[14]
        self.fg3_pct = row[15]
        self.ftm = row[16]
        self.fta = row[17]
        self.ft_pct = row[18]
        self.oreb = row[19]
        self.dreb = row[20]
        self.reb = row[21]
        self.ast = row[22]
        self.stl = row[23]
        self.blk = row[24]
        self.tov = row[25]
        self.pf = row[26]
        self.plus_minus = row[27]

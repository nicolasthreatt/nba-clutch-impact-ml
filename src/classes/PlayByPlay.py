# PlayByPlay.py

class PlayByPlay:
    def __init__(self, row):
        self.game_id = row[0]
        self.season = self.game_id[3:5]
        self.event_num = row[1]
        self.event_msg_type = row[2]
        self.event_msg_action_type = row[3]
        self.period = row[4]
        self.wc_time_string = row[5]
        self.pc_time = self.convert_pc_time(row[6])
        self.home_description = row[7]
        self.neutral_description = row[8]
        self.visitor_description = row[9]
        self.description = self.home_description or self.visitor_description
        self.score = row[10]
        self.score_margin = int(row[11]) if row[11] not in (None, "TIE") else 0
        self.person1_type = row[12]
        self.player1_id = row[13]
        self.player1_name = row[14]
        self.player1_team_id = row[15]
        self.player1_team_city = row[16]
        self.player1_team_nickname = row[17]
        self.player1_team_abbreviation = row[18]
        self.person2_type = row[19]
        self.player2_id = row[20]
        self.player2_name = row[21]
        self.player2_team_id = row[22]
        self.player2_team_city = row[23]
        self.player2_team_nickname = row[24]
        self.player2_team_abbreviation = row[25]
        self.person3_type = row[26]
        self.player3_id = row[27]
        self.player3_name = row[28]
        self.player3_team_id = row[29]
        self.player3_team_city = row[30]
        self.player3_team_nickname = row[31]
        self.player3_team_abbreviation = row[32]
        self.video_available_flag = row[33]
        self.home_possession = None
        self.home_win = None
    
    def convert_pc_time(self, pc_time_string: str) -> int:
        pc_time_minutes = int(pc_time_string.split(":")[0]) if pc_time_string else None
        pc_time_seconds = int(pc_time_string.split(":")[1]) if pc_time_string else None
        return pc_time_minutes * 60 + pc_time_seconds if pc_time_string else None

    def set_home_possession(self, home_possession):
            self.home_possession = home_possession

    def set_home_win(self, home_win):
        self.home_win = home_win

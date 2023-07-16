# PlayByPlay.py
from src.classes.EventMsgType import EventMsgType

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


class PlayByPlayLive:
    def __init__(self, row):
        self.action_number = row['actionNumber'] if 'actionNumber' in row else None
        self.clock = row['clock'] if 'clock' in row else None
        self.pc_time = self.convert_pc_time() if self.clock else None
        self.time_actual = row['timeActual'] if 'timeActual' in row else None
        self.period = row['period'] if 'period' in row else None
        self.period_type = row['periodType'] if 'periodType' in row else None
        self.team_id = row['teamId'] if 'teamId' in row else None
        self.team_tricode = row['teamTricode'] if 'teamTricode' in row else None
        self.action_type = row['actionType'] if 'actionType' in row else None
        self.sub_type = row['subType'] if 'subType' in row else None
        self.descriptor = row['descriptor'] if 'descriptor' in row else None
        self.qualifiers = row['qualifiers'] if 'qualifiers' in row else None
        self.person_id = row['personId'] if 'personId' in row else None
        self.x = row['x'] if 'x' in row else None
        self.y = row['y'] if 'y' in row else None
        self.area = row['area'] if 'area' in row else None
        self.area_detail = row['areaDetail'] if 'areaDetail' in row else None
        self.side = row['side'] if 'side' in row else None
        self.shot_distance = row['shotDistance'] if 'shotDistance' in row else None
        self.possession = row['possession'] if 'possession' in row else None
        self.score_home = int(row['scoreHome']) if 'scoreHome' in row else None
        self.score_away = int(row['scoreAway']) if 'scoreAway' in row else None
        self.score_margin = self.score_home - self.score_away if all([self.score_home, self.score_away]) else None
        self.edited = row['edited'] if 'edited' in row else None
        self.order_number = row['orderNumber'] if 'orderNumber' in row else None
        self.x_legacy = row['xLegacy'] if 'xLegacy' in row else None
        self.y_legacy = row['yLegacy'] if 'yLegacy' in row else None
        self.is_field_goal = row['isFieldGoal'] if 'isFieldGoal' in row else None
        self.shot_result = row['shotResult'] if 'shotResult' in row else None
        self.points_total = row['pointsTotal'] if 'pointsTotal' in row else None
        self.description = row['description'] if 'description' in row else None
        self.player_name = row['playerName'] if 'playerName' in row else None
        self.player_name_i = row['playerNameI'] if 'playerNameI' in row else None
        self.person_ids_filter = row['personIdsFilter'] if 'personIdsFilter' in row else None
        self.home_possession = int(bool(self.team_id == self.possession))

    def convert_pc_time(self, pc_time_string: str) -> int:
        """Converts a string representing the time remaining in a period to an integer
           representing the number of seconds remaining in the period.

        Returns:
            int: The number of seconds remaining in the period.
        """
        # Check if the string is empty
        if not self.pc_time_string:
            return None
    
        # Remove the 'PT' prefix and 'S' suffix
        self.pc_time_string = self.pc_time_string[2:-1]
        
        # Check if 'M' exists in the string
        if 'M' in self.pc_time_string:
            # Split the string into minutes and seconds
            minutes, seconds = self.pc_time_string.split('M')
            
            # Remove any leading zeros from the minutes
            minutes = minutes.lstrip('0')
            
            # Remove any leading zeros and the decimal point from the seconds
            seconds = seconds.rstrip('0').rstrip('.')
            
            # Convert minutes and seconds to integers
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            
            # Convert minutes to seconds and add to the total
            total_seconds = minutes * 60 + seconds
        else:
            # Remove any leading zeros and the decimal point from the seconds
            seconds = self.pc_time_string.rstrip('0').rstrip('.')
            
            # Convert seconds to an integer
            seconds = int(seconds) if seconds else 0
            
            total_seconds = seconds
        
        return total_seconds

    def determine_event_num():
        pass

    def determine_event_msg():
        pass

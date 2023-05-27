import requests

headers = {
            'Host': 'stats.nba.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Connection': 'keep-alive',
            'Referer': 'https://stats.nba.com/',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
    }

def get_game_ids() -> set:
    # Set the base URL for the NBA API
    base_url = 'https://stats.nba.com/stats/'

    # Set the required parameters
    params = {
        'PlayerOrTeam': 'T',
        'LeagueID': '00',
        'Season': '2022-23',
        'SeasonType': 'Regular Season',
    }

    # Send the GET request
    response = requests.get("https://stats.nba.com/stats/leaguegamefinder", headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        # Extract all distinct game IDs
        # TODO: SHOW OFF DATA STRUCTURES AND ALGO AND USE CUSTOM SORT
        game_ids =  sorted(set(game[4] for game in data['resultSets'][0]['rowSet']))

        for game_id in game_ids:
            # Set the parameters for play-by-play request
            pbp_params = {
                'GameID': game_id,
                'StartPeriod': 4,
                'EndPeriod': 10,
                'RangeType': 2,
                'StartRange': 0,
                'EndRange': 28800,
            }

            # Send the GET request to retrieve play-by-play data
            pbp_response = requests.get(base_url + 'playbyplayv2', headers=headers, params=pbp_params)

            # Check if the request was successful
            if pbp_response.status_code == 200:
                pbp_data = pbp_response.json()
                print(pbp_data)
        
            break

    else:
        print('Request failed with status code:', response.status_code)
        return None

get_game_ids()
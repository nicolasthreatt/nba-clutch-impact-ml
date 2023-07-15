import signal
# from kafka import KafkaProducer
import requests
import time

headers  = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-token': 'true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://stats.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}



# Create a Kafka producer instance
# producer = KafkaProducer(bootstrap_servers='localhost:9092')

def signal_handler(sig, frame):
    # Gracefully exit the program
    producer.close()
    print("Program terminated.")
    exit(0)

def main():
    # signal.signal(signal.SIGINT, signal_handler)  # Register signal handler for Ctrl+C
    game_id = "0042200401"
    # play_by_play_url = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json"
    play_by_play_url = "https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{}.json".format(game_id)

    while True:
        
        response = requests.get(url=play_by_play_url, headers=headers)
        print(response.status_code)
        if response.status_code != 200:
            print("Error: Could not get play-by-play data.")
            break
        else:
            print("Success: Got play-by-play data.")
            print(response.json())
            break

        # Make an API call and retrieve the data
        # response = requests.get('https://streaming-api.example.com/data')
        # data = response.json()

        # # Send each record to Kafka
        # for record in data:
        #     # Convert the record to bytes
        #     record_bytes = str(record).encode('utf-8')

        #     # Replace 'topic_name' with the name of your Kafka topic
        #     producer.send('topic_name', value=record_bytes)

        # # Check for an exit condition
        # if some_condition:  # Replace with your own exit condition
        #     break

        # Sleep for a desired interval before making the next API call
        time.sleep(5)  # Adjust the interval as needed

    # Perform any necessary cleanup
    # producer.close()
    print("Program exited.")

if __name__ == '__main__':
    main()

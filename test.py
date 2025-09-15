# Install snscrape if you haven't
# pip install snscrape

import snscrape.modules.twitter as sntwitter

# Replace with the Tweet ID you want to fetch replies for
tweet_id = "1962874710263263248"  

query = f"conversation_id:{tweet_id}"

print(f"Fetching replies to tweet {tweet_id}...\n")

for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
    if str(tweet.id) != tweet_id:  # skip the original tweet itself
        print(f"{i+1}. @{tweet.user.username}: {tweet.content}\n")

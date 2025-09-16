import tweepy

# BEARER = os.environ.get("TWITTER_BEARER_TOKEN")

# Tweet ID you want to get replies for
TWEET_ID = "1962874710263263248"

def get_replies(tweet_id, bearer_token):
    # Initialize Twitter client
    client = tweepy.Client(bearer_token=bearer_token)
    
    replies = []
    next_token = None
    
    while True:
        # Search for replies using conversation_id
        response = client.search_recent_tweets(
            query=f"conversation_id:{tweet_id}",
            max_results=100,
            tweet_fields=['author_id', 'created_at', 'text'],
            next_token=next_token
        )
        
        if not response.data:
            break
            
        # Add tweets to replies list (skip original tweet)
        for tweet in response.data:
            if tweet.id != tweet_id:  # Skip the original tweet
                replies.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id,
                    'created_at': str(tweet.created_at)
                })
        
        # Check for more pages
        if 'next_token' in response.meta:
            next_token = response.meta['next_token']
        else:
            break
    
    return replies

# Get all replies
all_replies = get_replies(TWEET_ID, BEARER_TOKEN)

# Print results
print(f"Found {len(all_replies)} replies:")
for reply in all_replies:
    print(f"\n{reply['text'][:100]}...")
    print(f"By: {reply['author_id']} at {reply['created_at']}")

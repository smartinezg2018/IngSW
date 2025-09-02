import requests
import json

# Your credentials
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAKa33wEAAAAA0QJdb5SwerbduhjH%2F8k%2FVgpfxuM%3DzKZYSLWhNA2BQWkLzFcQMywbMCEyfdlsXerwpuNy2tmMjCCPJR"
USER_ID = "your_user_id_here"  # You can get this from /2/users/by/username/{username}

def get_user_tweets(user_id, max_results=1):
    """
    Get the last tweets from a user
    
    Args:
        user_id (str): The user ID
        max_results (int): Number of tweets to retrieve (5-100)
    """
    
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,context_annotations",
        "expansions": "author_id",
        "user.fields": "name,username,verified"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

def get_my_user_id(username):
    """
    Get user ID from username
    """
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data['data']['id']
    else:
        print(f"Error getting user ID: {response.status_code}")
        return None

def display_tweets(tweets_data):
    """
    Display tweets in a readable format
    """
    if not tweets_data or 'data' not in tweets_data:
        print("No tweets found")
        return
    
    tweets = tweets_data['data']
    
    print(f"\n--- Your Last {len(tweets)} Tweets ---\n")
    
    for i, tweet in enumerate(tweets, 1):
        print(f"{i}. Tweet ID: {tweet['id']}")
        print(f"   Created: {tweet['created_at']}")
        print(f"   Text: {tweet['text']}")
        
        if 'public_metrics' in tweet:
            metrics = tweet['public_metrics']
            print(f"   Likes: {metrics['like_count']} | "
                  f"Retweets: {metrics['retweet_count']} | "
                  f"Replies: {metrics['reply_count']}")
        
        print("-" * 50)

# Example usage
if __name__ == "__main__":
    # Option 1: If you know your user ID
    # tweets = get_user_tweets("your_user_id_here", max_results=10)
    
    # Option 2: Get user ID from username first
    username = "simon375825"  # Your Twitter username without @
    user_id = get_my_user_id(username)
    # print(user_id)
    
    if user_id:
        print(f"Your User ID: {user_id}")
        tweets = get_user_tweets(user_id, max_results=10)
        display_tweets(tweets)
    else:
        print("Could not retrieve user ID")
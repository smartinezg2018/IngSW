import requests
import time

# Replace with your token
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAKa33wEAAAAA0QJdb5SwerbduhjH%2F8k%2FVgpfxuM%3DzKZYSLWhNA2BQWkLzFcQMywbMCEyfdlsXerwpuNy2tmMjCCPJR"

def create_headers(bearer_token):
    return {"Authorization": f"Bearer {bearer_token}"}

def get_user_id(username, headers):
    """
    Looks up the user ID given a username.
    """
    url = f"https://api.x.com/2/users/by/username/{username}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["id"]

def get_all_posts(user_id, headers, max_results_per_page=100):
    """
    Fetches all posts (tweets) by a user, paginating until no more results.
    """
    posts = []
    params = {
        "max_results": max_results_per_page,  # max is 100 for user timeline. :contentReference[oaicite:3]{index=3}
        "tweet.fields": "created_at,public_metrics,text",  # add fields you need
        # "exclude": "retweets,replies"  # optional: to filter
    }
    
    url = f"https://api.x.com/2/users/{user_id}/tweets"
    next_token = None
    
    while True:
        if next_token:
            params["pagination_token"] = next_token
        
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        j = resp.json()
        
        if "data" in j:
            posts.extend(j["data"])
        else:
            # no more posts
            break
        
        meta = j.get("meta", {})
        next_token = meta.get("next_token")
        if not next_token:
            break
        
        # optional: delay to respect rate limits
        time.sleep(1)  
    
    return posts

def main():
    username = "simon375825"  # replace
    headers = create_headers(BEARER_TOKEN)
    user_id = get_user_id(username, headers)
    print(f"User ID of {username} is {user_id}")
    
    posts = get_all_posts(user_id, headers)
    print(f"Fetched {len(posts)} posts.")
    # e.g., write to a file
    import json
    with open(f"{username}_posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

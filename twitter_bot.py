import tweepy
import schedule
import time
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Environment variable setup code
# Load .env file in local development, use system environment variables in production
if os.path.exists('tweepy_keys.env'):
    load_dotenv('tweepy_keys.env')
    print("Local environment variables loaded.")
else:
    print("Loading environment variables from system.")

class TwitterBot:
    def __init__(self):
        # Get API keys from environment variables
        self.api_key = os.environ.get("TWITTER_API_KEY")
        self.api_secret = os.environ.get("TWITTER_API_SECRET")
        self.access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
        
        # Check environment variables
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            print("Warning: Some Twitter API keys are not set.")
            print(f"API_KEY: {'Set' if self.api_key else 'Not set'}")
            print(f"API_SECRET: {'Set' if self.api_secret else 'Not set'}")
            print(f"ACCESS_TOKEN: {'Set' if self.access_token else 'Not set'}")
            print(f"ACCESS_TOKEN_SECRET: {'Set' if self.access_token_secret else 'Not set'}")
        
        # Twitter API authentication and client setup
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        # Tweet interval setting (get from environment variable or use default)
        self.tweet_interval = int(os.environ.get("TWEET_INTERVAL_HOURS", 4))
        print(f"Tweet interval: {self.tweet_interval} hours")
        
        # Load tweet list
        self.tweets = self.load_tweets()
        
        # Load current index (to prevent duplicate tweets)
        self.current_index = self.load_current_index()
        print(f"Current tweet index: {self.current_index}")
    
    def load_tweets(self):
        try:
            # Get file path from environment variable (default: tweets.json)
            tweets_file = os.environ.get("TWEETS_FILE", "tweets.json")
            with open(tweets_file, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                print(f"Loaded tweet list ({len(tweets)} tweets):")
                for i, tweet in enumerate(tweets[:3]):  # Show only first 3
                    print(f"  {i+1}. {tweet[:50]}..." if len(tweet) > 50 else f"  {i+1}. {tweet}")
                if len(tweets) > 3:
                    print(f"  ... and {len(tweets)-3} more")
                return tweets
        except FileNotFoundError:
            print(f"tweets.json file not found.")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON file format is invalid: {e}")
            return []
    
    def load_current_index(self):
        """Load current tweet index (to prevent duplicate tweets)"""
        try:
            if os.path.exists('current_index.txt'):
                with open('current_index.txt', 'r') as f:
                    index = int(f.read().strip())
                    # Check if index is valid
                    if self.tweets and index < len(self.tweets):
                        return index
                    else:
                        return 0
            return 0
        except Exception as e:
            print(f"Failed to load index: {e}")
            return 0
    
    def save_current_index(self):
        """Save current tweet index"""
        try:
            with open('current_index.txt', 'w') as f:
                f.write(str(self.current_index))
            print(f"Index saved: {self.current_index}")
        except Exception as e:
            print(f"Failed to save index: {e}")
    
    def reload_tweets(self):
        """Refresh tweet list and start from beginning if changed"""
        old_tweets = self.tweets.copy()
        self.tweets = self.load_tweets()
        
        # Check if content has changed
        if old_tweets != self.tweets:
            self.current_index = 0  # Start from beginning
            self.save_current_index()  # Save index
            print("New tweet list detected, starting from the beginning!")
            print(f"Total {len(self.tweets)} tweets available.")
    
    def post_next_tweet(self):
        # Check tweet list before each posting
        self.reload_tweets()
        
        if not self.tweets:
            print("No tweets to post.")
            return
        
        try:
            tweet = self.tweets[self.current_index]
            
            # Add invisible character (zero-width space)
            invisible_char = "\u200B"  # Zero-width space
            modified_tweet = tweet + invisible_char * (self.current_index % 5 + 1)
            
            response = self.client.create_tweet(text=modified_tweet)
            print(f"Tweet sent successfully! ({datetime.now()})")
            print(f"Content: {tweet}")
            
            # Move to next tweet
            self.current_index = (self.current_index + 1) % len(self.tweets)
            self.save_current_index()  # Save index
            
        except Exception as e:
            print(f"Failed to send tweet: {e}")
            
            # If duplicate content error, move to next tweet
            if "duplicate content" in str(e).lower():
                print("Duplicate content error, moving to next tweet.")
                self.current_index = (self.current_index + 1) % len(self.tweets)
                self.save_current_index()  # Save index

def main():
    bot = TwitterBot()
    
    # Run at interval set in environment variable
    interval = bot.tweet_interval
    schedule.every(interval).hours.do(bot.post_next_tweet)
    
    # Send first tweet immediately (can be controlled by environment variable)
    if os.environ.get("TWEET_ON_START", "true").lower() == "true":
        print("Sending first tweet on startup.")
        bot.post_next_tweet()
    else:
        print(f"First tweet will be sent after {interval} hours.")
    
    print("\nTwitter bot is running...")
    print(f"Tweets will be automatically sent every {interval} hours.")
    print("Press Ctrl+C to exit the program.\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nExiting program.")

if __name__ == "__main__":
    main()

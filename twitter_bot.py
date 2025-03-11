import tweepy
import schedule
import time
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import random

# 환경 변수 설정을 위한 코드
# 로컬 개발 환경에서는 .env 파일 로드, 배포 환경에서는 환경 변수 사용
if os.path.exists('tweepy_keys.env'):
    load_dotenv('tweepy_keys.env')
    print("Local environment variables loaded.")
else:
    print("Loading environment variables from system.")

class TwitterBot:
    def __init__(self):
        # 환경 변수에서 API 키 가져오기
        self.api_key = os.environ.get("TWITTER_API_KEY")
        self.api_secret = os.environ.get("TWITTER_API_SECRET")
        self.access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
        
        # 환경 변수 확인
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            print("Warning: Some Twitter API keys are not set.")
            print(f"API_KEY: {'Set' if self.api_key else 'Not set'}")
            print(f"API_SECRET: {'Set' if self.api_secret else 'Not set'}")
            print(f"ACCESS_TOKEN: {'Set' if self.access_token else 'Not set'}")
            print(f"ACCESS_TOKEN_SECRET: {'Set' if self.access_token_secret else 'Not set'}")
        
        # 트위터 API 인증 및 클라이언트 설정 - wait_on_rate_limit 추가
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True  # 속도 제한 자동 준수
        )
        
        # 트윗 간격 설정 (환경 변수에서 가져오거나 기본값 사용)
        self.tweet_interval = int(os.environ.get("TWEET_INTERVAL_HOURS", 6))  # 기본값 6시간으로 증가
        print(f"Tweet interval: {self.tweet_interval} hours")
        
        # 트윗 목록 로드
        self.tweets = self.load_tweets()
        
        # 현재 인덱스 로드 (중복 트윗 방지)
        self.current_index = self.load_current_index()
        print(f"Current tweet index: {self.current_index}")
        
        # 마지막 트윗 시간 및 속도 제한 상태 추적
        self.last_tweet_time = None
        self.rate_limit_reset = None
    
    def load_tweets(self):
        try:
            # 환경 변수에서 파일 경로 가져오기 (기본값: tweets.json)
            tweets_file = os.environ.get("TWEETS_FILE", "tweets.json")
            with open(tweets_file, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                print(f"Loaded tweet list ({len(tweets)} tweets):")
                for i, tweet in enumerate(tweets[:3]):  # 처음 3개만 출력
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
        """현재 트윗 인덱스 로드 (중복 트윗 방지)"""
        try:
            if os.path.exists('current_index.txt'):
                with open('current_index.txt', 'r') as f:
                    index = int(f.read().strip())
                    # 인덱스가 유효한지 확인
                    if self.tweets and index < len(self.tweets):
                        return index
                    else:
                        return 0
            return 0
        except Exception as e:
            print(f"Failed to load index: {e}")
            return 0
    
    def save_current_index(self):
        """현재 트윗 인덱스 저장"""
        try:
            with open('current_index.txt', 'w') as f:
                f.write(str(self.current_index))
            print(f"Index saved: {self.current_index}")
        except Exception as e:
            print(f"Failed to save index: {e}")
    
    def reload_tweets(self):
        """트윗 목록 새로고침 및 처음부터 시작"""
        old_tweets = self.tweets.copy()
        self.tweets = self.load_tweets()
        
        # 내용이 변경되었는지 확인
        if old_tweets != self.tweets:
            self.current_index = 0  # 처음부터 시작
            self.save_current_index()  # 인덱스 저장
            print("New tweet list detected, starting from the beginning!")
            print(f"Total {len(self.tweets)} tweets available.")
    
    def should_respect_rate_limit(self):
        """속도 제한을 준수해야 하는지 확인"""
        # 속도 제한 재설정 시간이 있으면 확인
        if self.rate_limit_reset:
            now = datetime.now()
            if now < self.rate_limit_reset:
                wait_seconds = (self.rate_limit_reset - now).total_seconds()
                print(f"Rate limit in effect. Need to wait {wait_seconds:.0f} seconds until {self.rate_limit_reset}")
                return True
            else:
                # 재설정 시간이 지남
                self.rate_limit_reset = None
                
        # 트윗 간격을 준수하는지 확인
        if self.last_tweet_time:
            now = datetime.now()
            elapsed = (now - self.last_tweet_time).total_seconds() / 3600  # 시간 단위
            if elapsed < self.tweet_interval * 0.9:  # 간격의 90%
                print(f"Only {elapsed:.2f} hours since last tweet. Waiting for full interval ({self.tweet_interval} hours).")
                return True
                
        return False
    
    def post_next_tweet(self):
        # 속도 제한을 준수해야 하는지 확인
        if self.should_respect_rate_limit():
            return
            
        # 매번 포스팅 전에 트윗 목록 확인
        self.reload_tweets()
        
        if not self.tweets:
            print("No tweets to post.")
            return
        
        try:
            tweet = self.tweets[self.current_index]
            
            # 눈에 보이지 않는 문자 추가 (제로 너비 공백)
            invisible_char = "\u200B"  # 제로 너비 공백
            modified_tweet = tweet + invisible_char * (self.current_index % 5 + 1)
            
            # 트윗 발송 전 약간의 지연 추가 (1-5초)
            time.sleep(random.uniform(1, 5))
            
            response = self.client.create_tweet(text=modified_tweet)
            print(f"Tweet sent successfully! ({datetime.now()})")
            print(f"Content: {tweet}")
            
            # 마지막 트윗 시간 업데이트
            self.last_tweet_time = datetime.now()
            
            # 다음 트윗으로 이동
            self.current_index = (self.current_index + 1) % len(self.tweets)
            self.save_current_index()  # 인덱스 저장
            
        except Exception as e:
            error_str = str(e)
            print(f"Failed to send tweet: {error_str}")
            
            # 속도 제한 오류 처리
            if "429" in error_str:
                print("Rate limit exceeded. Setting cooldown period.")
                # 속도 제한 재설정 시간을 현재 시간으로부터 60분 후로 설정
                self.rate_limit_reset = datetime.now() + timedelta(minutes=60)
                print(f"Will retry after: {self.rate_limit_reset}")
            
            # 중복 콘텐츠 오류인 경우 다음 트윗으로 이동
            elif "duplicate content" in error_str.lower():
                print("Duplicate content error, moving to next tweet.")
                self.current_index = (self.current_index + 1) % len(self.tweets)
                self.save_current_index()  # 인덱스 저장

def main():
    bot = TwitterBot()
    
    # 환경 변수에서 설정한 시간 간격으로 실행
    interval = bot.tweet_interval
    
    # 시작 시간에 약간의 무작위성 추가 (0-30분)
    random_minutes = random.randint(0, 30)
    schedule.every(interval).hours.at(f":{random_minutes:02d}").do(bot.post_next_tweet)
    print(f"Scheduled tweets to run every {interval} hours at :{random_minutes:02d} minutes past the hour")
    
    # 첫 번째 트윗 즉시 발송 (환경 변수로 제어 가능)
    if os.environ.get("TWEET_ON_START", "false").lower() == "true":  # 기본값을 false로 변경
        print("Sending first tweet on startup.")
        bot.post_next_tweet()
    else:
        next_run = schedule.next_run()
        print(f"First tweet will be sent at: {next_run}")
    
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

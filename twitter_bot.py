import tweepy
import schedule
import time
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import random

# Tweepy 버전 출력
print(f"Tweepy 버전: {tweepy.__version__}")

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
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        
        # Check environment variables
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            print("경고: 일부 트위터 API 키가 설정되지 않았습니다.")
            print(f"API_KEY: {'설정됨' if self.api_key else '설정되지 않음'}")
            print(f"API_SECRET: {'설정됨' if self.api_secret else '설정되지 않음'}")
            print(f"ACCESS_TOKEN: {'설정됨' if self.access_token else '설정되지 않음'}")
            print(f"ACCESS_TOKEN_SECRET: {'설정됨' if self.access_token_secret else '설정되지 않음'}")
            print(f"BEARER_TOKEN: {'설정됨' if self.bearer_token else '설정되지 않음'}")
        
        # Twitter API v2 setup
        try:
            print("API v2 설정 시도 중...")
            print(f"API 키: {self.api_key[:5]}... (일부만 표시)")
            print(f"API 시크릿: {self.api_secret[:5]}... (일부만 표시)")
            print(f"액세스 토큰: {self.access_token[:5]}... (일부만 표시)")
            print(f"액세스 토큰 시크릿: {self.access_token_secret[:5]}... (일부만 표시)")
            print(f"Bearer Token: {self.bearer_token[:5] if self.bearer_token else 'None'}... (일부만 표시)")
            
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            
            # 계정 정보 확인 (연결 테스트)
            me = self.client.get_me()
            if me.data:
                print(f"인증된 계정: @{me.data.username}")
                print("API v2 설정 완료")
            else:
                print("계정 정보를 가져올 수 없습니다.")
                
        except Exception as e:
            print(f"API v2 설정 실패: {str(e)}")
            print(f"오류 타입: {type(e)}")
            self.client = None
        
        # Tweet interval setting (8 hours)
        self.tweet_interval = 8
        print(f"트윗 간격: {self.tweet_interval} 시간")
        
        # Load tweet list
        self.tweets = self.load_tweets()
        
        # Load current index (to prevent duplicate tweets)
        self.current_index = self.load_current_index()
        print(f"현재 트윗 인덱스: {self.current_index}")
    
    def load_tweets(self):
        try:
            # Get file path from environment variable (default: tweets.json)
            tweets_file = os.environ.get("TWEETS_FILE", "tweets.json")
            with open(tweets_file, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                print(f"트윗 목록 로드됨 ({len(tweets)} 트윗):")
                for i, tweet in enumerate(tweets[:3]):  # Show only first 3
                    print(f"  {i+1}. {tweet[:50]}..." if len(tweet) > 50 else f"  {i+1}. {tweet}")
                if len(tweets) > 3:
                    print(f"  ... 그리고 {len(tweets)-3} 개 더")
                return tweets
        except FileNotFoundError:
            print(f"tweets.json 파일을 찾을 수 없습니다.")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON 파일 형식이 잘못되었습니다: {e}")
            print(f"파일 내용: {open(tweets_file, 'r', encoding='utf-8').read()}")
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
            print(f"인덱스 로드 실패: {e}")
            return 0
    
    def save_current_index(self):
        """Save current tweet index"""
        try:
            with open('current_index.txt', 'w') as f:
                f.write(str(self.current_index))
            print(f"인덱스 저장됨: {self.current_index}")
        except Exception as e:
            print(f"인덱스 저장 실패: {e}")
    
    def reload_tweets(self):
        """Refresh tweet list and start from beginning if changed"""
        old_tweets = self.tweets.copy() if self.tweets else []
        self.tweets = self.load_tweets()
        
        # Check if content has changed
        if old_tweets != self.tweets:
            self.current_index = 0  # Start from beginning
            self.save_current_index()  # Save index
            print("새 트윗 목록이 감지되어 처음부터 시작합니다!")
            print(f"총 {len(self.tweets)} 트윗이 사용 가능합니다.")
    
    def post_next_tweet(self):
        # Check tweet list before each posting
        self.reload_tweets()
        
        if not self.tweets:
            print("게시할 트윗이 없습니다.")
            return
        
        if self.client is None:
            print("API가 설정되지 않았습니다. 트윗을 게시할 수 없습니다.")
            return
        
        try:
            tweet = self.tweets[self.current_index]
            
            # Add random invisible characters to avoid duplicate content errors
            invisible_chars = ["\u200B", "\u200C", "\u200D", "\u2060", "\uFEFF"]
            random_invisible = ''.join(random.choice(invisible_chars) for _ in range(random.randint(1, 5)))
            modified_tweet = tweet + random_invisible
            
            # Print tweet info before sending
            print(f"트윗 전송 시도 중... (인덱스: {self.current_index})")
            print(f"내용: {tweet[:50]}..." if len(tweet) > 50 else f"내용: {tweet}")
            
            # API v2로 트윗 전송
            response = self.client.create_tweet(text=modified_tweet)
            
            if response.data:
                tweet_id = response.data['id']
                print(f"트윗 전송 성공! (API v2)")
                print(f"트윗 ID: {tweet_id}")
                print(f"트윗 URL: https://twitter.com/user/status/{tweet_id}")
                
                # 다음 트윗으로 이동
                self.current_index = (self.current_index + 1) % len(self.tweets)
                self.save_current_index()
                print(f"다음 트윗 인덱스: {self.current_index}")
            else:
                print("트윗 전송 실패: 응답에 데이터가 없습니다.")
                
        except Exception as e:
            print(f"트윗 전송 실패: {str(e)}")
            print(f"오류 타입: {type(e)}")
            
            # If duplicate content error, move to next tweet
            if "duplicate" in str(e).lower():
                print("중복 콘텐츠 오류, 다음 트윗으로 이동합니다.")
                self.current_index = (self.current_index + 1) % len(self.tweets)
                self.save_current_index()
            
            # If rate limit error, wait and try again later
            if "rate limit" in str(e).lower():
                print("속도 제한 오류, 나중에 다시 시도합니다.")
            
            # If monthly limit reached
            if "monthly" in str(e).lower() or "limit" in str(e).lower():
                print("월간 API 사용량 제한에 도달했습니다. 다음 달까지 기다려야 합니다.")
                print("무료 플랜은 월 500회 트윗 게시로 제한됩니다.")

def main():
    bot = TwitterBot()
    
    # 8시간마다 실행
    schedule.every(bot.tweet_interval).hours.do(bot.post_next_tweet)
    
    # 시작 시 첫 번째 트윗 즉시 전송
    print("시작 시 첫 번째 트윗을 전송합니다.")
    bot.post_next_tweet()
    
    # 다음 예정된 트윗 시간 계산
    next_run = schedule.next_run()
    if next_run:
        print(f"다음 트윗 예정 시간: {next_run}")
    
    print("\n트위터 봇이 실행 중입니다...")
    print(f"트윗은 {bot.tweet_interval}시간마다 자동으로 전송됩니다.")
    print("프로그램을 종료하려면 Ctrl+C를 누르세요.\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()

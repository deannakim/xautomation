import tweepy
import schedule
import time
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# 환경 변수 설정을 위한 코드
# 로컬 개발 환경에서는 .env 파일 로드, 배포 환경에서는 환경 변수 사용
if os.path.exists('tweepy_keys.env'):
    load_dotenv('tweepy_keys.env')
    print("로컬 환경 변수 파일을 로드했습니다.")
else:
    print("환경 변수를 시스템에서 직접 로드합니다.")

class TwitterBot:
    def __init__(self):
        # 환경 변수에서 API 키 가져오기
        self.api_key = os.environ.get("TWITTER_API_KEY")
        self.api_secret = os.environ.get("TWITTER_API_SECRET")
        self.access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
        
        # 환경 변수 확인
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            print("경고: 일부 트위터 API 키가 설정되지 않았습니다.")
            print(f"API_KEY: {'설정됨' if self.api_key else '설정되지 않음'}")
            print(f"API_SECRET: {'설정됨' if self.api_secret else '설정되지 않음'}")
            print(f"ACCESS_TOKEN: {'설정됨' if self.access_token else '설정되지 않음'}")
            print(f"ACCESS_TOKEN_SECRET: {'설정됨' if self.access_token_secret else '설정되지 않음'}")
        
        # 트위터 API 인증 및 클라이언트 설정
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        # 트윗 간격 설정 (환경 변수에서 가져오거나 기본값 사용)
        self.tweet_interval = int(os.environ.get("TWEET_INTERVAL_HOURS", 4))
        print(f"트윗 간격: {self.tweet_interval}시간")
        
        # 트윗 목록 로드
        self.tweets = self.load_tweets()
        
        # 현재 인덱스 로드 (중복 트윗 방지)
        self.current_index = self.load_current_index()
        print(f"현재 트윗 인덱스: {self.current_index}")
    
    def load_tweets(self):
        try:
            # 환경 변수에서 파일 경로 가져오기 (기본값: tweets.json)
            tweets_file = os.environ.get("TWEETS_FILE", "tweets.json")
            with open(tweets_file, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                print(f"로드된 트윗 목록 ({len(tweets)}개):")
                for i, tweet in enumerate(tweets[:3]):  # 처음 3개만 출력
                    print(f"  {i+1}. {tweet[:50]}..." if len(tweet) > 50 else f"  {i+1}. {tweet}")
                if len(tweets) > 3:
                    print(f"  ... 외 {len(tweets)-3}개")
                return tweets
        except FileNotFoundError:
            print(f"tweets.json 파일을 찾을 수 없습니다.")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON 파일 형식이 잘못되었습니다: {e}")
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
            print(f"인덱스 로드 실패: {e}")
            return 0
    
    def save_current_index(self):
        """현재 트윗 인덱스 저장"""
        try:
            with open('current_index.txt', 'w') as f:
                f.write(str(self.current_index))
            print(f"인덱스 저장 완료: {self.current_index}")
        except Exception as e:
            print(f"인덱스 저장 실패: {e}")
    
    def reload_tweets(self):
        """트윗 목록 새로고침 및 처음부터 시작"""
        old_tweets = self.tweets.copy()
        self.tweets = self.load_tweets()
        
        # 내용이 변경되었는지 확인
        if old_tweets != self.tweets:
            self.current_index = 0  # 처음부터 시작
            self.save_current_index()  # 인덱스 저장
            print("새로운 트윗 목록이 감지되어 처음부터 시작합니다!")
            print(f"총 {len(self.tweets)}개의 트윗이 있습니다.")
    
    def post_next_tweet(self):
        # 매번 포스팅 전에 트윗 목록 확인
        self.reload_tweets()
        
        if not self.tweets:
            print("포스팅할 트윗이 없습니다.")
            return
        
        try:
            tweet = self.tweets[self.current_index]
            
            # 타임스탬프 없이 원본 트윗 그대로 사용
            modified_tweet = tweet
            
            response = self.client.create_tweet(text=modified_tweet)
            print(f"트윗 발송 성공! ({datetime.now()})")
            print(f"내용: {modified_tweet}")
            
            # 다음 트윗으로 이동
            self.current_index = (self.current_index + 1) % len(self.tweets)
            self.save_current_index()  # 인덱스 저장
            
        except Exception as e:
            print(f"트윗 발송 실패: {e}")
            
            # 중복 콘텐츠 오류인 경우 다음 트윗으로 이동
            if "duplicate content" in str(e).lower():
                print("중복 콘텐츠 오류로 다음 트윗으로 넘어갑니다.")
                self.current_index = (self.current_index + 1) % len(self.tweets)
                self.save_current_index()  # 인덱스 저장

def main():
    bot = TwitterBot()
    
    # 환경 변수에서 설정한 시간 간격으로 실행
    interval = bot.tweet_interval
    schedule.every(interval).hours.do(bot.post_next_tweet)
    
    # 첫 번째 트윗 즉시 발송 (환경 변수로 제어 가능)
    # 기본값을 false로 변경하여 중복 트윗 방지
    if os.environ.get("TWEET_ON_START", "true").lower() == "true":
        print("시작 시 첫 번째 트윗을 발송합니다.")
        bot.post_next_tweet()
    else:
        print(f"첫 번째 트윗은 {interval}시간 후에 발송됩니다.")
    
    print("\n트위터 봇이 실행 중입니다...")
    print(f"{interval}시간마다 트윗이 자동으로 발송됩니다.")
    print("프로그램을 종료하려면 Ctrl+C를 누르세요.\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()

import os
import feedparser
import requests
from datetime import datetime
import pytz

# 새 Gemini SDK (google-genai) import
import google.genai as genai

# Gemini 설정
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
KST = pytz.timezone('Asia/Seoul')

def main():
    now = datetime.now(KST)
    hour = now.hour

    # KST 오전 7시 ~ 새벽 1시까지만 실행
    if not (hour >= 7 or hour <= 1):
        print(f"시간 외 스킵 ({now.strftime('%H:%M KST')})")
        return

    print(f"AI 뉴스 브리핑 시작 ({now.strftime('%m/%d %H:%M KST')})")

    rss_urls = [
        "https://news.google.com/rss/search?q=인공지능+OR+AI+OR+LLM+OR+Gemini+OR+Claude+OR+Grok&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=artificial+intelligence+OR+AI+OR+LLM+OR+Gemini+OR+Claude+OR+Grok&hl=en-US&gl=US&ceid=US:en"
    ]
    
    all_news = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title
            link = entry.link
            summary = (entry.get('summary') or entry.get('description') or '')[:150]
            all_news.append(f"{title}\n{link}\n{summary}...")

    news_text = "\n\n".join(all_news[:8])

    prompt = f"""지금은 한국시간 {now.strftime('%m월 %d일 %H:%M')}입니다.

아래 최신 AI 관련 뉴스를 신문 기사 스타일로 간결하게 요약해주세요.
- 가장 중요한 4~6개 뉴스만 선별
- 각 뉴스를 자세히 설명
- 링크는 포함하지 말 것
- 불필요한 이모지나 장식은 사용하지 말 것
- 각 뉴스의 일자,시간 표시

뉴스 원문:
{news_text}"""

    try:
        response = model.generate_content(prompt)
        summary = response.text

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': f"AI 뉴스 브리핑 ({now.strftime('%m/%d %H:%M KST')})\n\n{summary}",
            'parse_mode': 'Markdown'
        }
        requests.post(telegram_url, data=payload)
        print("Telegram 전송 완료")
    except Exception as e:
        print(f"오류: {str(e)}")

if __name__ == "__main__":
    main()

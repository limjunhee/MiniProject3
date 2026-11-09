# [2단계: 골라낸 폐업 기사의 본문 크롤링]
# 입력: ./limjunhee/Crawling_CSV/폐업기사_목록.csv (joongang_filter.py 결과)
# 출력: ./limjunhee/Crawling_CSV/폐업기사_본문.csv
# 기사 주소(/article/)는 중앙일보 robots.txt에서 허용, 본문은 id="article_body" 안의 <p> 태그에 있음
import requests, time
import pandas as pd
from bs4 import BeautifulSoup

closing = pd.read_csv('./limjunhee/Crawling_CSV/폐업기사_목록.csv', encoding='utf-8-sig')

bodies = []
for i, link in enumerate(closing['주소']):
    try:
        response = requests.get(link, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.select('#article_body p')                       # 본문 문단들
        body = ' '.join(p.get_text(strip=True) for p in paragraphs)
    except Exception as e:
        print(link, '실패:', e)
        body = ''
    bodies.append(body)
    time.sleep(1)                                                        # 서버 부담 줄이기 (1초 간격)
    if (i + 1) % 20 == 0:
        print(i + 1, '/', len(closing), '완료')

closing['본문'] = bodies
print('본문 길이(글자 수):')
print(closing['본문'].str.len().describe())
print('본문이 비어 있는 기사:', (closing['본문'].str.len() == 0).sum(), '건')

# 본문은 분석용으로만 사용 (깃허브 등에 올리지 않기)
closing.to_csv('./limjunhee/Crawling_CSV/폐업기사_본문.csv', index=False, encoding='utf-8-sig')
print('저장 완료: ./limjunhee/Crawling_CSV/폐업기사_본문.csv')

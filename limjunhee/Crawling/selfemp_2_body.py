# [B-2단계: 자영업 기사 본문 크롤링 (약 1시간)]
# 입력: ./limjunhee/Crawling_CSV/자영업기사_목록.csv (selfemp_1_list.py 결과)
# 출력: ./limjunhee/Crawling_CSV/자영업기사_본문_2021~2025.csv (연도별로 저장)
# 기사 주소(/article/)는 중앙일보 robots.txt에서 허용, 본문은 id="article_body" 안의 <p> 태그에 있음
# 중간에 끊겨도 다시 실행하면 이미 저장된 연도는 건너뛰고 이어서 받는다
import requests, time, os
import pandas as pd
from bs4 import BeautifulSoup

articles = pd.read_csv('./limjunhee/Crawling_CSV/자영업기사_목록.csv', encoding='utf-8-sig')

failed = []                                            # 실패한 기사 주소 기록


def get_body(link):
    """기사 주소로 들어가 본문 글자만 가져오기 (실패하면 빈 문자열)"""
    try:
        response = requests.get(link, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.select('#article_body p')                       # 본문 문단들
        return ' '.join(p.get_text(strip=True) for p in paragraphs)
    except Exception as e:
        print(link, '실패:', e)
        failed.append(link)
        return ''
    finally:
        time.sleep(1)                                                    # 서버 부담 줄이기 (1초 간격)


for year in range(2021, 2026):
    path = f'./limjunhee/Crawling_CSV/자영업기사_본문_{year}.csv'

    if os.path.exists(path):                           # 이미 저장된 연도 -> 본문이 빈 기사만 다시 시도
        group = pd.read_csv(path, encoding='utf-8-sig')
        group['본문'] = group['본문'].fillna('')
        empty = group['본문'] == ''
        print(year, '이미 있음 -> 본문이 빈 기사', empty.sum(), '건만 다시 시도')
        for idx in group[empty].index:
            group.loc[idx, '본문'] = get_body(group.loc[idx, '주소'])
    else:
        group = articles[articles['연도'] == year].copy()
        bodies = []
        for i, link in enumerate(group['주소'], start=1):
            bodies.append(get_body(link))
            if i % 50 == 0:
                print(year, i, '/', len(group), '진행 중...')
        group['본문'] = bodies
    # 본문은 분석용으로만 사용 (깃허브 등에 올리지 않기)
    group.to_csv(path, index=False, encoding='utf-8-sig')
    print(year, '저장 완료:', len(group), '건 / 본문이 비어 있는 기사:', (group['본문'].str.len() == 0).sum(), '건')

print('실패한 기사:', len(failed), '건', failed)

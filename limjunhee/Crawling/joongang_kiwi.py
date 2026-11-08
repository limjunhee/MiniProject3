# [3단계: kiwi로 연도별 키워드 빈도 세기 + 시각화]
# 입력: ./limjunhee/Crawling_CSV/폐업기사_본문.csv (joongang_body.py 결과)
# 설치: pip install kiwipiepy
import pandas as pd
import matplotlib.pyplot as plt
from kiwipiepy import Kiwi
from collections import Counter

plt.rc('font', family='Malgun Gothic')        # 윈도우 맑은고딕으로 변경
plt.rcParams['axes.unicode_minus'] = False    # 음수 기호 깨짐 방지

df = pd.read_csv('./limjunhee/Crawling_CSV/폐업기사_본문.csv', encoding='utf-8-sig')
df['본문'] = df['본문'].fillna('')
df['글'] = df['제목'] + ' ' + df['본문']          # 제목 + 본문을 합쳐서 분석

# 1) kiwi 준비: 한 단어로 묶어야 하는 말은 사전에 추가 (안 하면 '소상공인' -> '소' + '상공인'으로 쪼개짐)
kiwi = Kiwi()
for word in ['소상공인', '자영업자', '최저임금', '노란우산', '소진공', '손실보상', '배달앱', '고금리', '고물가',
             '거리두기', '인건비', '중소벤처기업부', '코로나19']:
    kiwi.add_user_word(word, 'NNP', 5)            # 5: 쪼개진 것보다 한 단어로 묶는 쪽을 우선하는 점수

# 같은 뜻인데 다르게 쓰인 단어는 하나로 합치기
same = {'코로나19': '코로나', '신종 코로나바이러스 감염증': '코로나'}

# 2) 불용어: 세어도 의미 없는 단어
stop = {
    # 기사를 고를 때 쓴 단어 -> 모든 기사에 들어 있어 순위만 차지함
    '폐업', '폐점', '자영업', '자영업자', '소상공인', '음식점', '식당', '가게', '점포', '매장', '업종', '업체', '사업자', '사업', '사장', '대표', '손님', '장사', '영업',
    # 기사 형식 단어
    '기자', '사진', '이미지', '크게', '보기', '뉴스', '중앙일보', '무단', '전재', '재배포', '연합뉴스', '뉴시스', '뉴스1',
    # 어느 기사에나 나오는 일반 단어 (시간·장소·설명)
    '지난해', '올해', '이번', '최근', '지난달', '처음', '기간', '당시', '이후', '이날', '오전', '오후', '시간',
    '서울', '한국', '지역', '경우', '정도', '관계자', '가운데', '상황', '때문', '운영', '기준', '이상', '문제', '결과',
    '설명', '대상', '이유', '규모', '사람', '생각', '관련', '진행', '예정', '전년', '동기', '대비', '전체', '수준',
    '기록', '발표', '조사', '이용', '사용', '제공', '확인', '필요', '가능', '계획', '다양',
}

def get_nouns(text):
    """글에서 두 글자 이상 명사(NNG: 일반명사, NNP: 고유명사)만 뽑기"""
    nouns = []
    for t in kiwi.tokenize(text):
        if t.tag in ('NNG', 'NNP') and len(t.form) >= 2:
            word = same.get(t.form, t.form)
            if word not in stop:
                nouns.append(word)
    return nouns

# 3) 연도별로 세기
#    - 한 기사 안에서 같은 단어가 여러 번 나와도 1번으로 센다 (set 사용)
#      -> 한 기사가 특정 단어를 수십 번 반복해서 순위를 독차지하는 것을 막기 위함
#    - 연도마다 기사 수가 달라서, '그 단어가 나온 기사 수 ÷ 그해 기사 수 × 100' (%)로 비교
counts = {}
for year, group in df.groupby('연도'):
    counter = Counter()
    for text in group['글']:
        counter.update(set(get_nouns(text)))
    counts[year] = {word: n / len(group) * 100 for word, n in counter.most_common(20)}
    print(year, '기사', len(group), '건 / 상위 10개:',
          [(w, f'{p:.0f}%') for w, p in list(counts[year].items())[:10]])

# 4) 표로 저장 (연도별 상위 20개)
rows = []
for year, top in counts.items():
    for rank, (word, pct) in enumerate(top.items(), start=1):
        rows.append({'연도': year, '순위': rank, '키워드': word, '등장 기사 비율(%)': round(pct, 1)})
pd.DataFrame(rows).to_csv('./limjunhee/Crawling_CSV/연도별_키워드빈도.csv', index=False, encoding='utf-8-sig')

# 5) 시각화: 연도별 상위 10개 키워드 가로 막대그래프
years = list(counts.keys())
plt.figure(figsize=(20, 6))
for i, year in enumerate(years, start=1):
    top = list(counts[year].items())[:10][::-1]             # 많은 단어가 위로 오도록 뒤집기
    plt.subplot(1, len(years), i)
    plt.barh([w for w, p in top], [p for w, p in top], color='steelblue')
    n_articles = (df['연도'] == year).sum()
    plt.title(f'{year}년 (기사 {n_articles}건)')
    plt.xlabel('등장 기사 비율 (%)')
    plt.xlim(0, 100)
plt.suptitle('중앙일보 음식점·자영업 폐업 기사 연도별 상위 키워드 (2021~2025, 기사 1건당 1번만 셈)')
plt.tight_layout()
plt.show()

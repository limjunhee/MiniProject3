# [1단계: 중앙일보 기사 제목에서 음식점·자영업 폐업 기사 골라내기]
# 입력: ./limjunhee/Crawling_CSV/중앙일보_기사제목_2021~2025.csv (joongang_crawling.py 결과)
# 출력: ./limjunhee/Crawling_CSV/폐업기사_목록.csv
import pandas as pd
import html

# 1) 5개 연도 파일 합치기
df = pd.concat([pd.read_csv(f'./limjunhee/Crawling_CSV/중앙일보_기사제목_{y}.csv', encoding='utf-8-sig')
                for y in range(2021, 2026)])
print('전체 기사 수:', len(df))

# 2) 제목 정리: 중앙일보가 기호를 두 번 변환해 둔 경우가 있어 한 번 더 풀어준다 ('&#91;사설&#93;' -> '[사설]')
df['제목'] = df['제목'].map(html.unescape)
df['연도'] = df['날짜'].str[:4]

# 3) 골라내기 조건: 제목에 (폐업 표현) + (음식점·자영업 단어)가 함께 있고, (제외 단어)는 없는 기사
close = '폐업|문 닫|문닫|줄폐점|폐점'
biz = '음식점|식당|외식|자영업|소상공인|가게|요식|카페|치킨|빵집|맛집|상권|상인|술집|호프'
excl = ('北|中|日|美|북한|일본|중국|미국|뉴욕|미쉐린'                    # 해외·북한 기사 (中·日·美 한자 표기 포함)
        '|병원|헬스장|코인|거래소|은행|약국|극장|영화관|공장|농장|목욕탕|예식장|터미널|학원|어린이집'  # 다른 업종
        '|홈플러스|이마트|롯데마트|백화점'                                    # 대형마트·백화점
        '|방역지침|음주|마약|시신|대변|리얼돌')                               # 폐업과 상관없는 사건

cond = df['제목'].str.contains(close) & df['제목'].str.contains(biz) & ~df['제목'].str.contains(excl)
closing = df[cond].sort_values('날짜')

print('폐업 기사 수:', len(closing))
print(closing['연도'].value_counts().sort_index())

closing[['날짜', '연도', '제목', '키워드', '주소']].to_csv(
    './limjunhee/Crawling_CSV/폐업기사_목록.csv', index=False, encoding='utf-8-sig')
print('저장 완료: ./limjunhee/Crawling_CSV/폐업기사_목록.csv')

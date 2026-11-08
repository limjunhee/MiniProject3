# [B-1단계: 자영업·소상공인·외식업 기사 목록 만들기]
# 입력: ./limjunhee/Crawling_CSV/중앙일보_기사제목_2021~2025.csv (joongang_crawling.py 결과)
# 출력: ./limjunhee/Crawling_CSV/자영업기사_목록.csv
import pandas as pd
import html

# 1) 5개 연도 파일 합치기
df = pd.concat([pd.read_csv(f'./limjunhee/Crawling_CSV/중앙일보_기사제목_{y}.csv', encoding='utf-8-sig')
                for y in range(2021, 2026)])
print('전체 기사 수:', len(df))

# 2) 제목 정리: 중앙일보가 기호를 두 번 변환해 둔 경우가 있어 한 번 더 풀어준다 ('&#91;사설&#93;' -> '[사설]')
df['제목'] = df['제목'].map(html.unescape)
df['연도'] = df['날짜'].str[:4]

# 3) 골라내기 조건: 제목에 자영업·소상공인·외식업·음식점·식당이 들어간 기사 (폐업 여부는 따지지 않음)
biz = '자영업|소상공인|외식업|음식점|식당'
excl = ('北|中|日|美|북한|일본|중국|미국|뉴욕|미쉐린'          # 해외·북한 기사 (中·日·美 한자 표기 포함)
        '|구내식당|학생식당|학식|급식')                         # 회사·학교 식당 (자영업 아님)

cond = df['제목'].str.contains(biz) & ~df['제목'].str.contains(excl)
selfemp = df[cond].sort_values('날짜')

print('자영업 관련 기사 수:', len(selfemp))
print(selfemp['연도'].value_counts().sort_index())

selfemp[['날짜', '연도', '제목', '키워드', '주소']].to_csv(
    './limjunhee/Crawling_CSV/자영업기사_목록.csv', index=False, encoding='utf-8-sig')
print('저장 완료: ./limjunhee/Crawling_CSV/자영업기사_목록.csv')

# [1. 인구·외식 소비량·음식점 매출 분석]
# 출처: KOSIS 국가통계포털 (서비스업생산지수), 행정안전부 (주민등록인구)

# [2. 가설]
# 가설 2: 인구가 줄어든 비율만큼 외식 소비량이 줄고, 그만큼 음식점 매출도 줄어들 것이다.

# [3. 자료수집]
# 3-1 : 월별 산업별 서비스업생산지수 -> 음식점업 경상지수(매출액), 불변지수(실질 매출액), 계절조정지수(외식 소비량)
# 3-2 : 행정구역(시군구)별 성별 인구수 -> 전국 총인구수
import pandas as pd
import matplotlib.pyplot as plt

plt.rc('font', family='Malgun Gothic')        # 윈도우 맑은고딕으로 변경
plt.rcParams['axes.unicode_minus'] = False    # 음수 기호 깨짐 방지

prod = pd.read_csv('./limjunhee/CSV/월별_산업별_서비스업생산지수.csv', encoding='cp949')
pop = pd.read_csv('./limjunhee/CSV/(월별)행정구역_시군구_별__성별_인구수_(2020-2026.08).csv', encoding='utf-8-sig', header=[0, 1])


# [4. 데이터 전처리]
# 4-1 (매출·소비량): 음식점업 행만 남기고, 월 열('2020.01 월' 등)만 골라서 행/열을 뒤집는다(.T).
prod = prod[prod['업종별'] == '음식점업'].set_index('항목').filter(like='월').T

# 4-2 (인구): 첫 번째 행이 '전국' -> 그중 '총인구수 (명)' 값만 꺼낸다.
pop = pop.iloc[0].xs('총인구수 (명)', level=1)

# 4-3 (합치기): 날짜 표기('2020.01 월', '2020.01')를 '2020-01-01' 날짜로 바꾸고 하나의 표로 합친다.
prod.index = pd.to_datetime(prod.index.str.replace(' ', '').str[:7], format='%Y.%m')
pop.index = pd.to_datetime(pop.index.str.replace(' ', '').str[:7], format='%Y.%m')

df = pd.DataFrame({
    '매출': prod['경상지수'],
    '실질매출': prod['불변지수'],        # 2020년 가격으로 고정한 매출 = 물가 상승분을 뺀 매출
    '소비량': prod['계절조정지수'],      # 명절·연말 같은 계절 변동을 뺀 값
    '인구': pop,
}).astype(float)

# 4-4 (파생변수): 매출(경상지수)·실질 매출(불변지수)은 계절 변동이 커서 '최근 12개월 평균'을 따로 만든다.
#                 2021년 1월 값도 계산되도록 기간을 자르기 전에 만든다(2020년 값 사용).
df['매출_12개월평균'] = df['매출'].rolling(12).mean()
df['실질매출_12개월평균'] = df['실질매출'].rolling(12).mean()
df = df.loc['2021-01':'2025-12']          # 분석 기간 2021~2025

# 4-5 (지수화): 단위가 다른 값(명, 지수)을 한 그래프에서 비교하려고 '2022년 평균 = 100'으로 맞춘다.
base = df.loc['2022'].mean()
df_100 = pd.DataFrame({
    '매출': df['매출_12개월평균'] / base['매출'] * 100,   # 기준은 실제 2022년 평균 매출
    '실질매출': df['실질매출_12개월평균'] / base['실질매출'] * 100,
    '소비량': df['소비량'] / base['소비량'] * 100,
    '인구': df['인구'] / base['인구'] * 100,
})
df_100['1인당소비량'] = df_100['소비량'] / df_100['인구'] * 100
print(df_100.round(1))


# [5. 데이터 시각화 및 분석]
# 5-1 (변화율): 2022년 평균 -> 2025년 평균 몇 % 변했는지 계산한다.
change = (df.loc['2025'].mean() / df.loc['2022'].mean() - 1) * 100
change['1인당소비량'] = ((1 + change['소비량'] / 100) / (1 + change['인구'] / 100) - 1) * 100
print('2022년 -> 2025년 평균 변화율(%)')
print(change[['매출', '실질매출', '소비량', '1인당소비량', '인구']].round(1))

# 5-2 (선 그래프): 매출·소비량·1인당 소비량·인구를 월별로 한 그래프에 그린다.
plt.figure(figsize=(12, 6))
plt.plot(df_100.index, df_100['매출'], label='음식점 매출액(경상지수, 최근 12개월 평균)', color='orange', marker='o', markersize=3)
plt.plot(df_100.index, df_100['실질매출'], label='음식점 실질 매출액(불변지수, 최근 12개월 평균)', color='purple', marker='o', markersize=3)
plt.plot(df_100.index, df_100['소비량'], label='외식 소비량(계절조정지수)', color='blue', marker='o', markersize=3)
plt.plot(df_100.index, df_100['1인당소비량'], label='1인당 외식 소비량', color='green', marker='o', markersize=3)
plt.plot(df_100.index, df_100['인구'], label='주민등록 인구', color='red', linestyle='--', marker='o', markersize=3)
plt.axhline(100, color='black', linewidth=0.8)                       # 2022년 평균 기준선
plt.axvspan(pd.Timestamp('2021-10-01'), pd.Timestamp('2023-03-31'),
            color='lightgray', alpha=0.5, label='코로나 회복기')    # 코로나 회복기 음영

plt.title('가설 2. 인구 감소 → 외식 소비량 감소 → 음식점 매출 감소 확인하기')
plt.xlabel('연월')
plt.ylabel('지수 (2022년 평균 = 100)')
plt.legend(loc='lower right')
plt.grid(axis='y', alpha=0.3)
plt.xlim(pd.Timestamp('2021-01-01'), pd.Timestamp('2025-12-01'))   # x축을 분석 기간(2021.01~2025.12)에 딱 맞춤
ticks = list(pd.date_range('2021-01-01', '2025-07-01', freq='6MS')) + [pd.Timestamp('2025-12-01')]   # 6개월 간격 + 마지막 달
plt.xticks(ticks, [t.strftime('%Y-%m') for t in ticks])
plt.show()

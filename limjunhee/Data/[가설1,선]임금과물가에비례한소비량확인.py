# [1. 음식점 임금·외식물가·외식 소비량 분석]
# 출처: KOSIS 국가통계포털 (소비자물가지수, 서비스업생산지수), 고용노동부 (산업/규모별 임금 및 근로시간)

# [2. 가설]
# 가설 1: 음식점 임금이 오르면 외식물가도 같은 비율로 오르고,
#         외식물가가 오른 만큼 외식 소비량은 거의 같은 시기에 같은 비율로 줄어들 것이다.

# [3. 자료수집]
# 3-1 : 지출목적별 소비자물가지수(품목포함, 2020=100) (전국, 2020.01~2025.12) -> 외식물가(11.1 음식 서비스), 전체 물가(0 총지수)
# 3-2 : 산업/규모별 임금 및 근로시간 (2020.01~2025.12) -> 음식점 및 주점업, 전규모, 상용정액급여
# 3-3 : 월별 산업별 서비스업생산지수 -> 음식점업 계절조정지수 (외식 소비량)
import pandas as pd
import matplotlib.pyplot as plt

plt.rc('font', family='Malgun Gothic')        # 윈도우 맑은고딕으로 변경
plt.rcParams['axes.unicode_minus'] = False    # 음수 기호 깨짐 방지

cpi = pd.read_csv('./limjunhee/CSV/지출목적별소비자물가지수.csv', encoding='cp949')
wage = pd.read_csv('./limjunhee/CSV/산업_규모별_임금_및_근로시간_(2020.01-2025.12).csv', encoding='utf-8-sig', header=[0, 1])
prod = pd.read_csv('./limjunhee/CSV/월별_산업별_서비스업생산지수.csv', encoding='cp949')


# [4. 데이터 전처리]
# 4-1 (물가): 지출목적별 이름을 행 이름으로 두고, 월 열('2020.01 월' 등)만 골라서 행/열을 뒤집는다(.T).
cpi = cpi.set_index('지출목적별').filter(like='월').T

# 4-2 (임금): 첫 번째 행이 '음식점 및 주점업 / 전규모(1인이상)' -> 그중 '상용정액급여 (원)' 값만 꺼낸다.
wage = wage.iloc[0].xs('상용정액급여 (원)', level=1)

# 4-3 (소비량): 음식점업 행에서 '계절조정지수'(명절·연말 같은 계절 변동을 뺀 값)만 꺼낸다.
prod = prod[prod['업종별'] == '음식점업'].set_index('항목').filter(like='월').T
prod = prod['계절조정지수']

# 4-4 (합치기): 날짜 표기('2020.01 월', '2020. 01')를 '2020-01-01' 날짜로 바꾸고 하나의 표로 합친다.
cpi.index = pd.to_datetime(cpi.index.str.replace(' ', '').str[:7], format='%Y.%m')
wage.index = pd.to_datetime(wage.index.str.replace(' ', '').str[:7], format='%Y.%m')
prod.index = pd.to_datetime(prod.index.str.replace(' ', '').str[:7], format='%Y.%m')

df = pd.DataFrame({
    '임금': wage,
    '외식물가': cpi['11.1 음식 서비스'],
    '전체물가': cpi['0 총지수'],
    '소비량': prod,
}).astype(float)
df = df.loc['2021-01':'2025-12']          # 분석 기간 2021~2025
print(df)

# 4-5 (지수화): 단위가 다른 값(원, 지수)을 한 그래프에서 비교하려고 '2022년 평균 = 100'으로 맞춘다.
df_100 = df / df.loc['2022'].mean() * 100
print(df_100.round(1))


# [5. 데이터 시각화 및 분석]
# 5-1 (변화율): 2022년 평균 -> 2025년 평균 몇 % 변했는지 계산한다.
change = (df.loc['2025'].mean() / df.loc['2022'].mean() - 1) * 100
print('2022년 -> 2025년 평균 변화율(%)')
print(change.round(1))

# 5-2 (선 그래프): 임금·외식물가·전체 물가·소비량을 월별로 한 그래프에 그린다.
plt.figure(figsize=(12, 6))
plt.plot(df_100.index, df_100['임금'], label='음식점 임금·급여(정액급여)', color='blue', marker='o', markersize=3)
plt.plot(df_100.index, df_100['외식물가'], label='외식물가(음식 서비스)', color='orange', marker='o', markersize=3)
plt.plot(df_100.index, df_100['전체물가'], label='전체 물가(소비자물가 총지수)', color='green', marker='o', markersize=3)
plt.plot(df_100.index, df_100['소비량'], label='외식 소비량(계절조정지수)', color='gray', linestyle='--', marker='o', markersize=3)
plt.axhline(100, color='black', linewidth=0.8)                       # 2022년 평균 기준선
plt.axvspan(pd.Timestamp('2021-10-01'), pd.Timestamp('2023-03-31'),
            color='lightgray', alpha=0.5, label='코로나 회복기')    # 코로나 회복기 음영

plt.title('가설 1. 음식점 임금 상승 → 외식물가 상승 → 외식 소비량 감소 확인하기')
plt.xlabel('연월')
plt.ylabel('지수 (2022년 평균 = 100)')
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.xlim(pd.Timestamp('2021-01-01'), pd.Timestamp('2025-12-01'))   # x축을 분석 기간(2021.01~2025.12)에 딱 맞춤
ticks = list(pd.date_range('2021-01-01', '2025-07-01', freq='6MS')) + [pd.Timestamp('2025-12-01')]   # 6개월 간격 + 마지막 달
plt.xticks(ticks, [t.strftime('%Y-%m') for t in ticks])
plt.show()
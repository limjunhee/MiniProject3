# [1. 인구·외식 소비량·음식점 매출 분석 - 산점도]
# 출처: KOSIS 국가통계포털 (서비스업생산지수), 행정안전부 (주민등록인구)

# [2. 가설]
# 가설 2: 인구가 줄어든 비율만큼 외식 소비량이 줄고, 그만큼 음식점 매출도 줄어들 것이다.

# [3. 자료수집]
# 3-1 : 월별 산업별 서비스업생산지수 -> 음식점업 경상지수(매출액), 계절조정지수(외식 소비량)
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
    '인구': pop,
    '소비량': prod['계절조정지수'],      # 명절·연말 같은 계절 변동을 뺀 값
    '매출': prod['경상지수'],
}).astype(float)

# 4-4 (증가율): 산점도는 '얼마나 늘었나/줄었나'끼리 비교해야 하므로 전년 같은 달 대비 증가율(%)로 바꾼다.
#              (전년 같은 달과 비교하므로 매출의 계절 변동도 같이 빠진다)
#              2021년 1월 증가율에 2020년 1월 값이 필요하므로, 기간을 자르기 전에 계산한다.
rate = df.pct_change(12, fill_method=None) * 100   # fill_method=None: 빈 값을 임의로 채우지 않음
rate = rate.loc['2021-01':'2025-12']      # 분석 기간 2021~2025

# 4-5 (구분): 코로나 회복기(2021.10~2023.03)는 소비량이 크게 출렁여서 따로 표시하고 상관계수에서 뺀다.
covid = (rate.index >= '2021-10-01') & (rate.index <= '2023-03-01')
normal = rate[~covid]
print(rate.round(2))


# [5. 데이터 시각화 및 분석]
# 5-1 (상관계수·평균): 코로나 회복기를 뺀 기간으로 계산한다.
r1 = normal['인구'].corr(normal['소비량'])
r2 = normal['소비량'].corr(normal['매출'])
print('인구 vs 외식 소비량 상관계수:', round(r1, 2))
print('외식 소비량 vs 매출액 상관계수:', round(r2, 2))
print('인구 증가율 범위(%):', round(normal['인구'].min(), 2), '~', round(normal['인구'].max(), 2))
print('외식 소비량 증가율 범위(%):', round(normal['소비량'].min(), 2), '~', round(normal['소비량'].max(), 2))
print('매출액 증가율 - 소비량 증가율 평균(%p, 가격 상승분):', round((normal['매출'] - normal['소비량']).mean(), 2))

# 5-2 (산점도 1): 인구 증가율 vs 외식 소비량 증가율
#      점선(같은 비율 선) 위에 점이 모이면 '인구가 준 만큼 소비량이 준다'는 가설이 맞는 것
plt.figure(figsize=(7, 6))
plt.scatter(normal['인구'], normal['소비량'], color='blue', alpha=0.7, label='그 외 기간')
plt.scatter(rate[covid]['인구'], rate[covid]['소비량'], color='gray', alpha=0.5, label='코로나 회복기')
plt.plot([-0.4, 0], [-0.4, 0], color='red', linestyle='--', label='같은 비율 선 (y = x)')
plt.axhline(0, color='black', linewidth=0.8)
plt.title(f'가설 2-1. 인구 증가율 vs 외식 소비량 증가율 (r = {r1:.2f}, 회복기 제외)')
plt.xlabel('주민등록 인구 증가율 (전년 동월 대비, %)')
plt.ylabel('외식 소비량 증가율 (전년 동월 대비, %)')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 5-3 (산점도 2): 외식 소비량 증가율 vs 매출액 증가율
#      점선(같은 비율 선)보다 점이 위에 있으면 '소비량보다 매출이 더 늘었다' = 가격(외식물가)이 오른 몫
plt.figure(figsize=(7, 6))
plt.scatter(normal['소비량'], normal['매출'], color='blue', alpha=0.7, label='그 외 기간')
plt.scatter(rate[covid]['소비량'], rate[covid]['매출'], color='gray', alpha=0.5, label='코로나 회복기')
plt.plot([-35, 35], [-35, 35], color='red', linestyle='--', label='같은 비율 선 (y = x)')
plt.axhline(0, color='black', linewidth=0.8)
plt.axvline(0, color='black', linewidth=0.8)
plt.title(f'가설 2-2. 외식 소비량 증가율 vs 매출액 증가율 (r = {r2:.2f}, 회복기 제외)')
plt.xlabel('외식 소비량 증가율 (전년 동월 대비, %)')
plt.ylabel('음식점 매출액 증가율 (전년 동월 대비, %)')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

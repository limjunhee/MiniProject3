# [1. 음식점 임금·외식물가·외식 소비량 분석 - 산점도]
# 출처: KOSIS 국가통계포털 (소비자물가지수, 서비스업생산지수), 고용노동부 (산업/규모별 임금 및 근로시간)

# [2. 가설]
# 가설 1: 음식점 임금이 오르면 외식물가도 같은 비율로 오르고,
#         외식물가가 오른 만큼 외식 소비량은 거의 같은 시기에 같은 비율로 줄어들 것이다.

# [3. 자료수집]
# 3-1 : 월별 소비자물가지수 2개 (2020.01~2022.12, 2023.01~2026.09) -> 외식물가(음식점·숙박)
# 3-2 : 산업/규모별 임금 및 근로시간 (2020.01~2025.12) -> 음식점 및 주점업, 전규모, 상용정액급여
# 3-3 : 월별 산업별 서비스업생산지수 -> 음식점업 계절조정지수 (외식 소비량)
import pandas as pd
import matplotlib.pyplot as plt

plt.rc('font', family='Malgun Gothic')        # 윈도우 맑은고딕으로 변경
plt.rcParams['axes.unicode_minus'] = False    # 음수 기호 깨짐 방지

cpi1 = pd.read_csv('./limjunhee/CSV/월별소비자물가지수_2020년01월-2022년12월.csv', encoding='cp949')
cpi2 = pd.read_csv('./limjunhee/CSV/월별소비자물가지수_2023년01월-2026년09월.csv', encoding='cp949')
wage = pd.read_csv('./limjunhee/CSV/산업_규모별_임금_및_근로시간_(2020.01-2025.12).csv', encoding='utf-8-sig', header=[0, 1])
prod = pd.read_csv('./limjunhee/CSV/월별_산업별_서비스업생산지수.csv', encoding='cp949')


# [4. 데이터 전처리]
# 4-1 (물가): 대한민국 행만 남기고, 월 열('2020.01 월' 등)만 골라서 행/열을 뒤집는다(.T).
cpi1 = cpi1[cpi1['국가'] == '대한민국'].set_index('항목').filter(like='월').T
cpi2 = cpi2[cpi2['국가'] == '대한민국'].set_index('항목').filter(like='월').T
cpi = pd.concat([cpi1, cpi2], axis=0)     # 두 기간을 위아래로 합치기

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
    '외식물가': cpi['음식점·숙박'],
    '소비량': prod,
}).astype(float)

# 4-5 (증가율): 산점도는 '얼마나 올랐나/줄었나'끼리 비교해야 하므로 전년 같은 달 대비 증가율(%)로 바꾼다.
#              2021년 1월 증가율에 2020년 1월 값이 필요하므로, 기간을 자르기 전에 계산한다.
rate = df.pct_change(12, fill_method=None) * 100   # fill_method=None: 빈 값을 임의로 채우지 않음
rate = rate.loc['2021-01':'2025-12']      # 분석 기간 2021~2025

# 4-6 (시차): 외식물가가 오른 뒤 '2개월 뒤' 소비량을 같은 줄에 놓는다. (shift(-2): 2칸 위로 당기기)
rate['소비량_2개월뒤'] = rate['소비량'].shift(-2)

# 4-7 (구분): 코로나 회복기(2021.10~2023.03)는 소비량이 크게 출렁여서 따로 표시하고 상관계수에서 뺀다.
covid = (rate.index >= '2021-10-01') & (rate.index <= '2023-03-01')
normal = rate[~covid]
print(rate.round(2))


# [5. 데이터 시각화 및 분석]
# 5-1 (상관계수): 코로나 회복기를 뺀 기간으로 계산한다.
r1 = normal['임금'].corr(normal['외식물가'])
r2 = normal['외식물가'].corr(normal['소비량'])
r3 = normal['외식물가'].corr(normal['소비량_2개월뒤'])
print('임금 vs 외식물가 상관계수:', round(r1, 2))
print('외식물가 vs 같은 달 소비량 상관계수:', round(r2, 2))
print('외식물가 vs 2개월 뒤 소비량 상관계수:', round(r3, 2))

# 5-2 (산점도 1): 임금 증가율 vs 외식물가 증가율
#      점선(같은 비율 선) 위에 점이 모이면 '같은 비율로 오른다'는 가설이 맞는 것
plt.figure(figsize=(7, 6))
plt.scatter(normal['임금'], normal['외식물가'], color='blue', alpha=0.7, label='그 외 기간')
plt.scatter(rate[covid]['임금'], rate[covid]['외식물가'], color='gray', alpha=0.5, label='코로나 회복기')
plt.plot([-4, 10], [-4, 10], color='red', linestyle='--', label='같은 비율 선 (y = x)')
plt.title(f'가설 1-1. 임금 증가율 vs 외식물가 증가율 (r = {r1:.2f}, 회복기 제외)')
plt.xlabel('음식점 임금·급여 증가율 (전년 동월 대비, %)')
plt.ylabel('외식물가 증가율 (전년 동월 대비, %)')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 5-3 (산점도 2): 외식물가 증가율 vs 같은 달 외식 소비량 증가율
#      점선(반대 방향 같은 비율 선) 위에 점이 모이면 '거의 같은 시기에 같은 비율로 줄어든다'는 가설이 맞는 것
plt.figure(figsize=(7, 6))
plt.scatter(normal['외식물가'], normal['소비량'], color='blue', alpha=0.7, label='그 외 기간')
plt.scatter(rate[covid]['외식물가'], rate[covid]['소비량'], color='gray', alpha=0.5, label='코로나 회복기')
plt.plot([0, 10], [0, -10], color='red', linestyle='--', label='반대 방향 같은 비율 선 (y = -x)')
plt.axhline(0, color='black', linewidth=0.8)
plt.title(f'가설 1-2. 외식물가 증가율 vs 같은 달 외식 소비량 증가율 (r = {r2:.2f}, 회복기 제외)')
plt.xlabel('외식물가 증가율 (전년 동월 대비, %)')
plt.ylabel('외식 소비량 증가율 (전년 동월 대비, %)')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 5-4 (산점도 3): 외식물가 증가율 vs 2개월 뒤 외식 소비량 증가율
plt.figure(figsize=(7, 6))
plt.scatter(normal['외식물가'], normal['소비량_2개월뒤'], color='blue', alpha=0.7, label='그 외 기간')
plt.scatter(rate[covid]['외식물가'], rate[covid]['소비량_2개월뒤'], color='gray', alpha=0.5, label='코로나 회복기')
plt.plot([0, 10], [0, -10], color='red', linestyle='--', label='반대 방향 같은 비율 선 (y = -x)')
plt.axhline(0, color='black', linewidth=0.8)
plt.title(f'가설 1-3. 외식물가 증가율 vs 2개월 뒤 외식 소비량 증가율 (r = {r3:.2f}, 회복기 제외)')
plt.xlabel('외식물가 증가율 (전년 동월 대비, %)')
plt.ylabel('2개월 뒤 외식 소비량 증가율 (전년 동월 대비, %)')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

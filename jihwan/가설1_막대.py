import pandas as pd                      # 표(데이터프레임)를 다루는 라이브러리
import matplotlib.pyplot as plt          # 그래프를 그리는 라이브러리

# ── 1. 데이터 불러오기 : 연도별 점포 파일 5개를 읽는다
s21 = pd.read_csv( "data/store_2021.csv" )
s22 = pd.read_csv( "data/store_2022.csv" )
s23 = pd.read_csv( "data/store_2023.csv" )
s24 = pd.read_csv( "data/store_2024.csv" )
s25 = pd.read_csv( "data/store_2025.csv" )
# 5개 파일을 위아래로 이어붙여 하나의 표로 만든다
store = pd.concat( [ s21 , s22 , s23 , s24 , s25 ] , axis = 0 , ignore_index = True )
# 기준_년분기_코드(예 20241)를 10으로 나눠 정수로 바꾸면 연도(2024)가 된다
store["연도"] = ( store["기준_년분기_코드"] / 10 ).astype(int)

# ── 2. 상권 유형을 두 묶음으로 나눈다
store["묶음"] = "중심"                                                              # 일단 전부 중심으로 두고
store.loc[ store["상권_구분_코드_명"] == "골목상권" , "묶음" ] = "동네"             # 골목상권은 동네로
store.loc[ store["상권_구분_코드_명"] == "전통시장" , "묶음" ] = "동네"             # 전통시장도 동네로

# ── 3. 상권×연도 단위로 합산해서 개업률·폐업률 계산
g = store.groupby( [ "연도" , "상권_코드" , "묶음" ] ).agg(
    폐업합계 = ( "폐업_점포_수" , "sum" ),             # 폐업한 점포 수 합
    개업합계 = ( "개업_점포_수" , "sum" ),             # 개업한 점포 수 합
    유사업종합계 = ( "유사_업종_점포_수" , "sum" )     # 비교 기준이 되는 점포 수 합
).reset_index()
g["폐업률"] = g["폐업합계"] / g["유사업종합계"] * 100   # 폐업률(%)
g["개업률"] = g["개업합계"] / g["유사업종합계"] * 100   # 개업률(%)
g["순증"] = g["개업률"] - g["폐업률"]                   # 순증 = 개업률 - 폐업률 (+면 늘어남, -면 줄어듦)
g = g[ g["유사업종합계"] >= 30 ]                         # 점포가 30개 미만인 상권(64행)은 비율이 불안정해서 제외

# ── 4. 연도×묶음별 평균을 구한다
r = g.groupby( [ "연도" , "묶음" ] ).agg(
    폐업률 = ( "폐업률" , "mean" ),                      # 상권들의 평균 폐업률
    순증 = ( "순증" , "mean" )                           # 상권들의 평균 순증
).reset_index()
dongne = r[ r["묶음"] == "동네" ]                        # 동네 상권만 (5행: 2021~2025)
center = r[ r["묶음"] == "중심" ]                        # 중심 상권만 (5행)
print( dongne )
print( center )

# ── 5. 막대를 연도마다 나란히 놓기 위한 x위치 (동네는 왼쪽, 중심은 오른쪽)
x1 = []
x2 = []
for i in range( 5 ):
    x1.append( i - 0.2 )
    x2.append( i + 0.2 )

plt.rc( 'font' , family = 'Malgun Gothic' )              # 한글 폰트
plt.rcParams['axes.unicode_minus'] = False               # 마이너스 기호가 깨지지 않게

# ── 6. 막대그래프 1 : 연도별 평균 폐업률
d_val = dongne["폐업률"].round( 2 )                      # 막대 위 숫자를 소수 둘째 자리까지만 보이게
c_val = center["폐업률"].round( 2 )
plt.figure( figsize = ( 9 , 5 ) )
b1 = plt.bar( x1 , d_val , width = 0.4 , color = "red" , label = "동네 상권(골목+전통시장)" )
b2 = plt.bar( x2 , c_val , width = 0.4 , color = "blue" , label = "중심 상권(발달+관광특구)" )
plt.bar_label( b1 , padding = 3 , fontsize = 9 )         # 막대 위에 값 표시
plt.bar_label( b2 , padding = 3 , fontsize = 9 )
plt.xticks( [ 0 , 1 , 2 , 3 , 4 ] , [ 2021 , 2022 , 2023 , 2024 , 2025 ] )   # 숫자 0~4 대신 연도를 눈금 이름으로
plt.title( "가설 1. 연도별 평균 폐업률 : 동네 상권이 중심 상권보다 높음" )
plt.xlabel( "연도" )
plt.ylabel( "평균 폐업률(%)" )
plt.legend()
plt.grid(alpha = 0.2)
plt.show()

# ── 7. 막대그래프 2 : 연도별 평균 순증(개업률-폐업률)
d_val = dongne["순증"].round( 2 )
c_val = center["순증"].round( 2 )
plt.figure( figsize = ( 9 , 5 ) )
b1 = plt.bar( x1 , d_val , width = 0.4 , color = "red" , label = "동네 상권(골목+전통시장)" )
b2 = plt.bar( x2 , c_val , width = 0.4 , color = "blue" , label = "중심 상권(발달+관광특구)" )
plt.bar_label( b1 , padding = 3 , fontsize = 9 )
plt.bar_label( b2 , padding = 3 , fontsize = 9 )
plt.xticks( [ 0 , 1 , 2 , 3 , 4 ] , [ 2021 , 2022 , 2023 , 2024 , 2025 ] )
plt.title( "가설 1. 연도별 평균 순증(개업률-폐업률) : 동네 상권이 더 낮음" )
plt.xlabel( "연도" )
plt.ylabel( "평균 순증(%p)" )
plt.legend()
plt.grid(alpha = 0.2)
plt.show()
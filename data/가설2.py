import pandas as pd
import matplotlib.pyplot as plt

plt.rc( 'font' , family = 'Malgun Gothic' )
plt.rcParams['axes.unicode_minus'] = False

s21 = pd.read_csv( "data/store_2021.csv" )
s22 = pd.read_csv( "data/store_2022.csv" )
s23 = pd.read_csv( "data/store_2023.csv" )
s24 = pd.read_csv( "data/store_2024.csv" )
s25 = pd.read_csv( "data/store_2025.csv" )
flow = pd.read_csv( "data/Foot_Traffic.csv" )
sa21 = pd.read_csv( "data/sales_2021.csv" )
sa22 = pd.read_csv( "data/sales_2022.csv" )
sa23 = pd.read_csv( "data/sales_2023.csv" )
sa24 = pd.read_csv( "data/sales_2024.csv" )
sa25 = pd.read_csv( "data/sales_2025.csv" )
pop = pd.read_csv( "data/population.csv" )
work = pd.read_csv( "data/workplace_population.csv" )

store = pd.concat( [ s21 , s22 , s23 , s24 , s25 ] , axis = 0 , ignore_index = True )
sales = pd.concat( [ sa21 , sa22 , sa23 , sa24 , sa25 ] , axis = 0 , ignore_index = True )

print( flow.shape , sales.shape , pop.shape , work.shape )
print( flow.isnull().sum() )
print( sales.isnull().sum() )
print( pop.isnull().sum() )
print( work.isnull().sum() )
print( flow.shape , flow.drop_duplicates().shape )
print( sales.shape , sales.drop_duplicates().shape )
print( pop.shape , pop.drop_duplicates().shape )
print( work.shape , work.drop_duplicates().shape )

store["연도"] = ( store["기준_년분기_코드"] / 10 ).astype(int)
flow["연도"] = ( flow["기준_년분기_코드"] / 10 ).astype(int)
sales["연도"] = ( sales["기준_년분기_코드"] / 10 ).astype(int)
pop["연도"] = ( pop["기준_년분기_코드"] / 10 ).astype(int)
work["연도"] = ( work["기준_년분기_코드"] / 10 ).astype(int)

flow = flow[ flow["연도"] <= 2025 ]
pop = pop[ pop["연도"] <= 2025 ]
work = work[ work["연도"] <= 2025 ]

g = store.groupby( [ "연도" , "상권_코드" , "상권_구분_코드_명" ] ).agg(
    폐업합계 = ( "폐업_점포_수" , "sum" ),
    유사업종합계 = ( "유사_업종_점포_수" , "sum" )
).reset_index()
g["폐업률"] = g["폐업합계"] / g["유사업종합계"] * 100
g = g[ g["유사업종합계"] >= 30 ]
print( "점포 집계" , g.shape )

flow["낮비중"] = ( flow["시간대_06_11_유동인구_수"] + flow["시간대_11_14_유동인구_수"] + flow["시간대_14_17_유동인구_수"] ) / flow["총_유동인구_수"] * 100
f = flow.groupby( [ "연도" , "상권_코드" ] ).agg(
    총유동인구 = ( "총_유동인구_수" , "mean" ),
    낮비중 = ( "낮비중" , "mean" )
).reset_index()

sales["낮매출"] = sales["시간대_06~11_매출_금액"] + sales["시간대_11~14_매출_금액"] + sales["시간대_14~17_매출_금액"]
sa = sales.groupby( [ "연도" , "상권_코드" ] ).agg(
    낮매출 = ( "낮매출" , "sum" ),
    총매출 = ( "당월_매출_금액" , "sum" )
).reset_index()
sa["낮매출비중"] = sa["낮매출"] / sa["총매출"] * 100

p = pop.groupby( [ "연도" , "상권_코드" ] ).agg(
    상주인구 = ( "총_상주인구_수" , "mean" )
).reset_index()
w = work.groupby( [ "연도" , "상권_코드" ] ).agg(
    직장인구 = ( "총_직장_인구_수" , "mean" )
).reset_index()
pw = pd.merge( p , w , on = [ "연도" , "상권_코드" ] , how = "inner" )
pw["직장비중"] = pw["직장인구"] / ( pw["상주인구"] + pw["직장인구"] ) * 100

m = pd.merge( g , f , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( "유동 합친 후" , m.shape )
m = pd.merge( m , sa[ [ "연도" , "상권_코드" , "낮매출비중" ] ] , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( "매출 합친 후" , m.shape )
m = pd.merge( m , pw[ [ "연도" , "상권_코드" , "직장비중" ] ] , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( "인구 합친 후" , m.shape )

# 가설2 : 낮 시간대 비중 vs 폐업률
years = [ 2021 , 2022 , 2023 , 2024 , 2025 ]
year_str = [ "2021" , "2022" , "2023" , "2024" , "2025" ]
r_day = []
r_work = []
r_sales = []
r_total = []

# 연도별로 상관계수를 구한다.
for y in years:
    dy = m[ m["연도"] == y ]
    r_day.append( dy[ [ "낮비중" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r_work.append( dy[ [ "직장비중" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r_sales.append( dy[ [ "낮매출비중" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r_total.append( dy[ [ "총유동인구" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )

print( "낮 유동인구 비중 r :" , r_day )
print( "직장인구 비중 r :" , r_work )
print( "낮 매출 비중 r :" , r_sales )
print( "총유동인구 r :" , r_total )

# 가설2 통계 : 변수별·연도별 회귀계수, R2, t값
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

for c in [ "낮비중" , "직장비중" , "낮매출비중" , "총유동인구" ]:
    for y in years:
        d = m[ m["연도"] == y ]
        X = d[ [ c ] ]
        Y = d[ "폐업률" ]
        model = LinearRegression()
        model.fit( X , Y )
        r2 = r2_score( Y , model.predict( X ) )
        r = d[ [ c , "폐업률" ] ].corr().iloc[ 0 , 1 ]
        t = r * np.sqrt( ( len(d) - 2 ) / ( 1 - r * r ) )
        print( c , y , "회귀계수" , round( model.coef_[0] , 4 ) , "R2" , round( r2 , 3 ) , "t" , round( t , 1 ) )

# 가설2 그래프 1 : 연도별 낮 유동인구 비중 vs 폐업률 산점도
plt.figure( figsize = ( 15 , 12 ) )
for i in range( 0 , 5 ):
    dy = m[ m["연도"] == years[i] ]
    plt.subplot( 2 , 3 , i + 1 )
    plt.scatter( dy["낮비중"] , dy["폐업률"] , color = "purple" , s = 10 , alpha = 0.4 )
    plt.title( f"{year_str[i]}년 (r = {round( r_day[i] , 2 )})" )
    plt.xlabel( "낮(06~17시) 유동인구 비중(%)" )
    plt.ylabel( "폐업률(%)" )
    plt.grid()
plt.show()

# 가설2 그래프 2 : 연도별 직장인구 비중 vs 폐업률 산점도
plt.figure( figsize = ( 15 , 12 ) )
for i in range( 0 , 5 ):
    dy = m[ m["연도"] == years[i] ]
    plt.subplot( 2 , 3 , i + 1 )
    plt.scatter( dy["직장비중"] , dy["폐업률"] , color = "green" , s = 10 , alpha = 0.4 )
    plt.title( f"{year_str[i]}년 (r = {round( r_work[i] , 2 )})" )
    plt.xlabel( "직장인구 비중(%)" )
    plt.ylabel( "폐업률(%)" )
    plt.grid()
plt.show()

# 가설2 그래프 3 : 연도별 낮 매출 비중 vs 폐업률 산점도
plt.figure( figsize = ( 15 , 12 ) )
for i in range( 0 , 5 ):
    dy = m[ m["연도"] == years[i] ]
    plt.subplot( 2 , 3 , i + 1 )
    plt.scatter( dy["낮매출비중"] , dy["폐업률"] , color = "orange" , s = 10 , alpha = 0.4 )
    plt.title( f"{year_str[i]}년 (r = {round( r_sales[i] , 2 )})" )
    plt.xlabel( "낮(06~17시) 매출 비중(%)" )
    plt.ylabel( "폐업률(%)" )
    plt.grid()
plt.show()

# 가설2 그래프 4 : 연도별 상관계수
plt.figure( figsize = ( 8 , 6 ) )
plt.plot( year_str , r_day , label = "낮 유동인구 비중" , color = "purple" , marker = "o" )
plt.plot( year_str , r_work , label = "직장인구 비중" , color = "green" , marker = "o" )
plt.plot( year_str , r_sales , label = "낮 매출 비중" , color = "orange" , marker = "o" )
plt.plot( year_str , r_total , label = "총유동인구(대조)" , color = "gray" , linestyle = "--" , marker = "o" )
plt.plot( year_str , [ 0 , 0 , 0 , 0 , 0 ] , color = "black" )
plt.title( "가설 2. 연도별 상관계수 r (각 변수 - 폐업률)" )
plt.xlabel( "연도" )
plt.ylabel( "상관계수 r" )
plt.legend()
plt.grid()
plt.show()
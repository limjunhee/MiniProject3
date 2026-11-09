import pandas as pd
import matplotlib.pyplot as plt

plt.rc( 'font' , family = 'Malgun Gothic' )
plt.rcParams['axes.unicode_minus'] = False

# 연도별 점포 파일을 읽어서 하나로 합친다.
s21 = pd.read_csv( "data/store_2021.csv" )
s22 = pd.read_csv( "data/store_2022.csv" )
s23 = pd.read_csv( "data/store_2023.csv" )
s24 = pd.read_csv( "data/store_2024.csv" )
s25 = pd.read_csv( "data/store_2025.csv" )

store = pd.concat( [ s21 , s22 , s23 , s24 , s25 ] , axis = 0 , ignore_index = True )

# 결측치와 중복 행, 점포 수가 0인 행을 확인한다.
print( store.shape )
print( store.isnull().sum() )
print( store.shape , store.drop_duplicates().shape )
print( ( store["점포_수"] == 0 ).sum() )

store["연도"] = ( store["기준_년분기_코드"] / 10 ).astype(int)

# 골목상권·전통시장은 동네, 발달상권·관광특구는 중심으로 구분한다.
store["묶음"] = "중심"
store.loc[ store["상권_구분_코드_명"] == "골목상권" , "묶음" ] = "동네"
store.loc[ store["상권_구분_코드_명"] == "전통시장" , "묶음" ] = "동네"

# 상권·연도별로 합산하여 폐업률과 개업률을 산출한다.
g = store.groupby( [ "연도" , "상권_코드" , "상권_구분_코드_명" , "묶음" ] ).agg(
    폐업합계 = ( "폐업_점포_수" , "sum" ),
    개업합계 = ( "개업_점포_수" , "sum" ),
    유사업종합계 = ( "유사_업종_점포_수" , "sum" )
).reset_index()
g["폐업률"] = g["폐업합계"] / g["유사업종합계"] * 100
g["개업률"] = g["개업합계"] / g["유사업종합계"] * 100
print( "제외 전" , g.shape )

# 유사업종 점포 수 합계가 30 미만인 상권은 제외한다.
g = g[ g["유사업종합계"] >= 30 ]
print( "제외 후" , g.shape )

# 가설1 : 개업률 vs 폐업률
years = [ 2021 , 2022 , 2023 , 2024 , 2025 ]
year_str = [ "2021" , "2022" , "2023" , "2024" , "2025" ]
r_all = []
r_dongne = []
r_center = []

# 연도별로 상관계수를 구한다.
for y in years:
    dy = g[ g["연도"] == y ]
    dd = dy[ dy["묶음"] == "동네" ]
    dc = dy[ dy["묶음"] == "중심" ]
    r_all.append( dy[ [ "개업률" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r_dongne.append( dd[ [ "개업률" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r_center.append( dc[ [ "개업률" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )

print( "전체 r :" , r_all )
print( "동네 r :" , r_dongne )
print( "중심 r :" , r_center )

# 가설1 통계 : 연도별·유형별 회귀계수, R2, t값
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

b_all = []
b_dongne = []
b_center = []

for y in years:
    for nm in [ "전체" , "동네" , "중심" ]:
        d = g[ g["연도"] == y ]
        if nm != "전체":
            d = d[ d["묶음"] == nm ]
        X = d[ [ "개업률" ] ]
        Y = d[ "폐업률" ]
        model = LinearRegression()
        model.fit( X , Y )
        r2 = r2_score( Y , model.predict( X ) )
        r = d[ [ "개업률" , "폐업률" ] ].corr().iloc[ 0 , 1 ]
        t = r * np.sqrt( ( len(d) - 2 ) / ( 1 - r * r ) )
        print( y , nm , "회귀계수" , round( model.coef_[0] , 3 ) , "R2" , round( r2 , 3 ) , "t" , round( t , 1 ) )
        if nm == "전체":
            b_all.append( model.coef_[0] )
        if nm == "동네":
            b_dongne.append( model.coef_[0] )
        if nm == "중심":
            b_center.append( model.coef_[0] )

# 가설1 선 그래프 1 : 연도별 회귀계수 (개업률 1%p당 폐업률 증가폭)
plt.figure( figsize = ( 8 , 6 ) )
plt.plot( year_str , b_all , label = "전체" , color = "gray" , marker = "o" )
plt.plot( year_str , b_dongne , label = "동네 상권" , color = "red" , marker = "o" )
plt.plot( year_str , b_center , label = "중심 상권" , color = "blue" , marker = "o" )
plt.title( "가설 1. 연도별 회귀계수 (개업률 1%p당 폐업률 증가폭)" )
plt.xlabel( "연도" )
plt.ylabel( "회귀계수" )
plt.legend()
plt.grid()
plt.show()

# 가설1 선 그래프 2 : 연도별 상관계수
plt.figure( figsize = ( 8 , 6 ) )
plt.plot( year_str , r_all , label = "전체" , color = "gray" , marker = "o" )
plt.plot( year_str , r_dongne , label = "동네 상권" , color = "red" , marker = "o" )
plt.plot( year_str , r_center , label = "중심 상권" , color = "blue" , marker = "o" )
plt.title( "가설 1. 연도별 상관계수 r (개업률 - 폐업률)" )
plt.xlabel( "연도" )
plt.ylabel( "상관계수 r" )
plt.legend()
plt.grid()
plt.show()
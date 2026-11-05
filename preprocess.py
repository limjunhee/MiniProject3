import pandas as pd

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

print( store.shape , flow.shape , sales.shape , pop.shape , work.shape )
print( store.isnull().sum().sum() , flow.isnull().sum().sum() , sales.isnull().sum().sum() , pop.isnull().sum().sum() , work.isnull().sum().sum() )
print( store.shape , store.drop_duplicates().shape )
print( flow.shape , flow.drop_duplicates().shape )
print( sales.shape , sales.drop_duplicates().shape )
print( pop.shape , pop.drop_duplicates().shape )
print( work.shape , work.drop_duplicates().shape )
print( ( store["점포_수"] == 0 ).sum() )

store["연도"] = ( store["기준_년분기_코드"] / 10 ).astype(int)
flow["연도"] = ( flow["기준_년분기_코드"] / 10 ).astype(int)
sales["연도"] = ( sales["기준_년분기_코드"] / 10 ).astype(int)
pop["연도"] = ( pop["기준_년분기_코드"] / 10 ).astype(int)
work["연도"] = ( work["기준_년분기_코드"] / 10 ).astype(int)

flow = flow[ flow["연도"] <= 2025 ]
pop = pop[ pop["연도"] <= 2025 ]
work = work[ work["연도"] <= 2025 ]

store["묶음"] = "중심"
store.loc[ store["상권_구분_코드_명"] == "골목상권" , "묶음" ] = "동네"
store.loc[ store["상권_구분_코드_명"] == "전통시장" , "묶음" ] = "동네"

g = store.groupby( [ "연도" , "상권_코드" , "상권_구분_코드_명" , "묶음" ] ).agg(
    폐업합계 = ( "폐업_점포_수" , "sum" ),
    개업합계 = ( "개업_점포_수" , "sum" ),
    유사업종합계 = ( "유사_업종_점포_수" , "sum" )
).reset_index()
g["폐업률"] = g["폐업합계"] / g["유사업종합계"] * 100
g["개업률"] = g["개업합계"] / g["유사업종합계"] * 100
print( "제외 전" , g.shape )

g = g[ g["유사업종합계"] >= 30 ]
print( "제외 후" , g.shape )

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
print( ( sa["총매출"] == 0 ).sum() )
sa["낮매출비중"] = sa["낮매출"] / sa["총매출"] * 100

p = pop.groupby( [ "연도" , "상권_코드" ] ).agg(
    상주인구 = ( "총_상주인구_수" , "mean" )
).reset_index()
w = work.groupby( [ "연도" , "상권_코드" ] ).agg(
    직장인구 = ( "총_직장_인구_수" , "mean" )
).reset_index()
pw = pd.merge( p , w , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( ( ( pw["상주인구"] + pw["직장인구"] ) == 0 ).sum() )
pw["직장비중"] = pw["직장인구"] / ( pw["상주인구"] + pw["직장인구"] ) * 100

m = pd.merge( g , f , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( "유동 합친 후" , m.shape )
m = pd.merge( m , sa[ [ "연도" , "상권_코드" , "낮매출비중" ] ] , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( "매출 합친 후" , m.shape )
m = pd.merge( m , pw[ [ "연도" , "상권_코드" , "직장비중" ] ] , on = [ "연도" , "상권_코드" ] , how = "inner" )
print( "인구 합친 후" , m.shape )
print( m.isnull().sum() )
print( m.head() )


import matplotlib.pyplot as plt

plt.rc( 'font' , family = 'Malgun Gothic' )
plt.rcParams['axes.unicode_minus'] = False

# 현황1 : 동네 vs 중심 
r = m.groupby( [ "연도" , "묶음" ] ).agg(
    폐업률 = ( "폐업률" , "mean" )
).reset_index()
r["연도"] = r["연도"].astype(str)

dongne = r[ r["묶음"] == "동네" ]
center = r[ r["묶음"] == "중심" ]

print( dongne )
print( center )

plt.figure( figsize = ( 8 , 5 ) )
plt.plot( dongne["연도"] , dongne["폐업률"] , label = "동네 상권(골목+전통시장)" , color = "red" , marker = "o" )
plt.plot( center["연도"] , center["폐업률"] , label = "중심 상권(발달+관광특구)" , color = "blue" , marker = "o" )
plt.title( "연도별 폐업률 : 동네 상권 vs 중심 상권" )
plt.xlabel( "연도" )
plt.ylabel( "폐업률(%)" )
plt.legend()
plt.grid()
plt.show()

# 현황2 : 상권 4유형    
r4 = m.groupby( [ "연도" , "상권_구분_코드_명" ] ).agg(
    폐업률 = ( "폐업률" , "mean" ),
    상권수 = ( "상권_코드" , "count" )
).reset_index()
r4["연도"] = r4["연도"].astype(str)

a = r4[ r4["상권_구분_코드_명"] == "골목상권" ]
b = r4[ r4["상권_구분_코드_명"] == "전통시장" ]
c = r4[ r4["상권_구분_코드_명"] == "발달상권" ]
d = r4[ r4["상권_구분_코드_명"] == "관광특구" ]

print( r4 )

plt.figure( figsize = ( 8 , 5 ) )
plt.plot( a["연도"] , a["폐업률"] , label = "골목상권" , color = "red" , marker = "o" )
plt.plot( b["연도"] , b["폐업률"] , label = "전통시장" , color = "orange" , marker = "o" )
plt.plot( c["연도"] , c["폐업률"] , label = "발달상권" , color = "blue" , marker = "o" )
plt.plot( d["연도"] , d["폐업률"] , label = "관광특구" , color = "green" , linestyle = "--" , marker = "o" )
plt.title( "연도별 폐업률 : 상권 4유형" )
plt.xlabel( "연도" )
plt.ylabel( "폐업률(%)" )
plt.legend()
plt.grid()
plt.show()

# 가설1 : 개업률 vs 폐업률 (2025 산점도 + 연도별 상관계수)
years = [ 2021 , 2022 , 2023 , 2024 , 2025 ]
year_str = [ "2021" , "2022" , "2023" , "2024" , "2025" ]
r_all = []
r_dongne = []
r_center = []

for y in years:
    dy = m[ m["연도"] == y ]
    dd = dy[ dy["묶음"] == "동네" ]
    dc = dy[ dy["묶음"] == "중심" ]
    r_all.append( dy[ [ "개업률" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r_dongne.append( dd[ [ "개업률" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )
    r_center.append( dc[ [ "개업률" , "폐업률" ] ].corr().iloc[ 0 , 1 ] )

print( "전체 r :" , r_all )
print( "동네 r :" , r_dongne )
print( "중심 r :" , r_center )

d25 = m[ m["연도"] == 2025 ]
d25_dongne = d25[ d25["묶음"] == "동네" ]
d25_center = d25[ d25["묶음"] == "중심" ]

plt.figure( figsize = ( 14 , 5 ) )

plt.subplot( 1 , 2 , 1 )
plt.scatter( d25_dongne["개업률"] , d25_dongne["폐업률"] , color = "red" , s = 20 , alpha = 0.4 , label = "동네 상권" )
plt.scatter( d25_center["개업률"] , d25_center["폐업률"] , color = "blue" , s = 20 , alpha = 0.4 , label = "중심 상권" )
plt.title( f"가설 1 : 개업률 vs 폐업률 (2025, 전체 r = {r_all[4]:.2f})" )
plt.xlabel( "개업률(%)" )
plt.ylabel( "폐업률(%)" )
plt.legend()
plt.grid()

plt.subplot( 1 , 2 , 2 )
plt.plot( year_str , r_all , label = "전체" , color = "gray" , marker = "o" )
plt.plot( year_str , r_dongne , label = "동네 상권" , color = "red" , marker = "o" )
plt.plot( year_str , r_center , label = "중심 상권" , color = "blue" , marker = "o" )
plt.title( "가설 1 : 연도별 상관계수 r (개업률 - 폐업률)" )
plt.xlabel( "연도" )
plt.ylabel( "상관계수 r" )
plt.legend()
plt.grid()
plt.show()


# 가설2 : 낮 시간대 비중 vs 폐업률 (2025 산점도 + 연도별 상관계수)
years = [ 2021 , 2022 , 2023 , 2024 , 2025 ]
year_str = [ "2021" , "2022" , "2023" , "2024" , "2025" ]
r_day = []
r_work = []
r_sales = []
r_total = []

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

d25 = m[ m["연도"] == 2025 ]

plt.figure( figsize = ( 18 , 5 ) )

plt.subplot( 1 , 3 , 1 )
plt.scatter( d25["낮비중"] , d25["폐업률"] , color = "purple" , s = 20 , alpha = 0.4 )
plt.title( f"낮 유동인구 비중 vs 폐업률 (2025, r = {r_day[4]:.2f})" )
plt.xlabel( "낮(06~17시) 유동인구 비중(%)" )
plt.ylabel( "폐업률(%)" )
plt.grid()

plt.subplot( 1 , 3 , 2 )
plt.scatter( d25["직장비중"] , d25["폐업률"] , color = "green" , s = 20 , alpha = 0.4 )
plt.title( f"직장인구 비중 vs 폐업률 (2025, r = {r_work[4]:.2f})" )
plt.xlabel( "직장인구 비중(%)" )
plt.ylabel( "폐업률(%)" )
plt.grid()

plt.subplot( 1 , 3 , 3 )
plt.scatter( d25["낮매출비중"] , d25["폐업률"] , color = "orange" , s = 20 , alpha = 0.4 )
plt.title( f"낮 매출 비중 vs 폐업률 (2025, r = {r_sales[4]:.2f})" )
plt.xlabel( "낮(06~17시) 매출 비중(%)" )
plt.ylabel( "폐업률(%)" )
plt.grid()
plt.show()

plt.figure( figsize = ( 8 , 5 ) )
plt.plot( year_str , r_day , label = "낮 유동인구 비중" , color = "purple" , marker = "o" )
plt.plot( year_str , r_work , label = "직장인구 비중" , color = "green" , marker = "o" )
plt.plot( year_str , r_sales , label = "낮 매출 비중" , color = "orange" , marker = "o" )
plt.plot( year_str , r_total , label = "총유동인구(대조)" , color = "gray" , linestyle = "--" , marker = "o" )
plt.plot( year_str , [ 0 , 0 , 0 , 0 , 0 ] , color = "black" , linewidth = 1 )
plt.title( "가설 2 : 연도별 상관계수 r (각 변수 - 폐업률)" )
plt.xlabel( "연도" )
plt.ylabel( "상관계수 r" )
plt.legend()
plt.grid()
plt.show()
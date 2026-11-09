import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

store["연도"] = ( store["기준_년분기_코드"] / 10 ).astype(int)
flow["연도"] = ( flow["기준_년분기_코드"] / 10 ).astype(int)
sales["연도"] = ( sales["기준_년분기_코드"] / 10 ).astype(int)
pop["연도"] = ( pop["기준_년분기_코드"] / 10 ).astype(int)
work["연도"] = ( work["기준_년분기_코드"] / 10 ).astype(int)
flow = flow[ flow["연도"] <= 2025 ]
pop = pop[ pop["연도"] <= 2025 ]
work = work[ work["연도"] <= 2025 ]

g = store.groupby( [ "연도" , "상권_코드" ] ).agg(
    폐업합계 = ( "폐업_점포_수" , "sum" ),
    개업합계 = ( "개업_점포_수" , "sum" ),
    유사업종합계 = ( "유사_업종_점포_수" , "sum" )
).reset_index()
g["폐업률"] = g["폐업합계"] / g["유사업종합계"] * 100
g["개업률"] = g["개업합계"] / g["유사업종합계"] * 100
g = g[ g["유사업종합계"] >= 30 ]

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

p = pop.groupby( [ "연도" , "상권_코드" ] ).agg( 상주인구 = ( "총_상주인구_수" , "mean" ) ).reset_index()
w = work.groupby( [ "연도" , "상권_코드" ] ).agg( 직장인구 = ( "총_직장_인구_수" , "mean" ) ).reset_index()
pw = pd.merge( p , w , on = [ "연도" , "상권_코드" ] , how = "inner" )
pw["직장비중"] = pw["직장인구"] / ( pw["상주인구"] + pw["직장인구"] ) * 100

m = pd.merge( g , f , on = [ "연도" , "상권_코드" ] , how = "inner" )
m = pd.merge( m , sa[ [ "연도" , "상권_코드" , "낮매출비중" ] ] , on = [ "연도" , "상권_코드" ] , how = "inner" )
m = pd.merge( m , pw[ [ "연도" , "상권_코드" , "직장비중" ] ] , on = [ "연도" , "상권_코드" ] , how = "inner" )

# 연도별로 폐업률과 각 변수의 상관계수를 구해서 표로 만들기
vars = [ "개업률" , "낮비중" , "직장비중" , "낮매출비중" , "총유동인구" ]
years = [ 2021 , 2022 , 2023 , 2024 , 2025 ]
rows = []
for v in vars:
    row = []
    for y in years:
        d = m[ m["연도"] == y ]
        r = d[ [ v , "폐업률" ] ].corr().iloc[ 0 , 1 ]
        row.append( r )
    rows.append( row )
c = pd.DataFrame( rows , index = vars , columns = [ "2021" , "2022" , "2023" , "2024" , "2025" ] )
print( c.round(2) )

plt.rc( 'font' , family = 'Malgun Gothic' )
plt.rcParams['axes.unicode_minus'] = False
plt.figure( figsize = ( 8 , 5 ) )
sns.heatmap( c , annot = True , fmt = ".2f" , cmap = "coolwarm" , vmin = -1 , vmax = 1 )
plt.title( "연도별 폐업률과 각 변수의 상관계수 (2021~2025)" )
plt.xlabel( "연도" )
plt.show()
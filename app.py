import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="산불 분석 통합 대시보드", layout="wide")

# --- 데이터베이스 연결 및 초기화 ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    # 테이블 생성 및 샘플 데이터는 이전과 동일 (생략 가능하지만 구조 유지를 위해 포함)
    cursor.execute("CREATE TABLE IF NOT EXISTS fire_stations (name TEXT, address TEXT, region TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS weather (region TEXT, humidity REAL, wind_speed REAL, area REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS wildfires (region TEXT, location TEXT, cause TEXT, area REAL)")
    
    # 샘플 데이터 (전국 단위 분석을 위해 다양하게 입력)
    cursor.execute("INSERT INTO fire_stations VALUES ('속초소방서', '강원도 속초시', '강원')")
    cursor.execute("INSERT INTO fire_stations VALUES ('강릉소방서', '강원도 강릉시', '강원')")
    cursor.execute("INSERT INTO fire_stations VALUES ('안동소방서', '경상북도 안동시', '경북')")
    
    cursor.executemany("INSERT INTO weather VALUES (?,?,?,?)", [
        ('강원', 35.0, 12.0, 500.0), ('경북', 40.0, 8.0, 300.0), ('경기', 55.0, 5.0, 50.0)
    ])
    
    cursor.executemany("INSERT INTO wildfires VALUES (?,?,?,?)", [
        ('강원', '속초시', '입산자 실화', 450.0), ('강원', '강릉시', '논밭 소각', 150.0),
        ('경북', '안동시', '쓰레기 소각', 320.0), ('경기', '양평군', '입산자 실화', 20.0)
    ])
    conn.commit()
    return conn

conn = init_db()

# --- 사이드바 설정 ---
st.sidebar.header("📍 1번 차트 지역 설정")
sido_list = ["선택하세요", "강원", "경기", "경북", "경남", "전북", "전남", "충북", "충남"]
selected_sido = st.sidebar.selectbox("광역 지역 선택", sido_list, key="sido_select")
selected_sigungu = st.sidebar.text_input("상세 지역 입력 (필수)", placeholder="예: 속초시", key="sigungu_input")

st.title("🔥 전국 산불 분석 및 지역별 대응 사각지대 대시보드")

# --- [차트 1] 지역별 대응 취약 지역 (선택 지역 전용) ---
st.header(f"1. 지역별 대응 취약 지역 파악 (대상: {selected_sigungu if selected_sigungu else '미선택'})")

if not selected_sigungu or selected_sido == "선택하세요":
    st.warning("⚠️ 1번 차트를 보려면 좌측 사이드바에서 지역을 입력해주세요.")
else:
    # 선택된 시군구에 대한 특정 데이터 쿼리
    sql1 = f"""
    SELECT 
        w.location as sigungu, 
        SUM(w.area) as total_area,
        (SELECT COUNT(*) FROM fire_stations f WHERE f.address LIKE '%' || '{selected_sigungu}' || '%') as station_count
    FROM wildfires w
    WHERE w.location LIKE '%' || '{selected_sigungu}' || '%'
    GROUP BY w.location
    """
    df1 = pd.read_sql(sql1, conn)
    
    if not df1.empty:
        col1_1, col1_2 = st.columns([2, 1])
        with col1_1:
            fig1 = px.scatter(df1, x="station_count", y="total_area", size="total_area", 
                             color_discrete_sequence=['#FF4B4B'], hover_name="sigungu",
                             labels={"station_count": "관내 소방시설 수", "total_area": "누적 피해 면적(ha)"},
                             title=f"{selected_sigungu} 산불 사각지대 분석", size_max=50)
            st.plotly_chart(fig1, use_container_width=True, key="c1")
        with col1_2:
            st.subheader("📝 SQL (Local Only)")
            st.code(sql1, language='sql')
            st.write(f"💡 **{selected_sigungu}**의 소방 인프라 대비 피해 규모를 집중 분석합니다.")
    else:
        st.error("해당 지역의 데이터를 찾을 수 없습니다.")

st.divider()

# --- [차트 2] 기상 조건 상관관계 (전국 데이터 기준) ---
st.header("2. [전국] 기상 조건과 피해 규모 상관관계")
# 지역 필터 없이 전국 데이터를 가져옴
sql2 = "SELECT humidity, wind_speed, area FROM weather"
df2 = pd.read_sql(sql2, conn)

col2_1, col2_2 = st.columns([2, 1])
with col2_1:
    fig2 = px.scatter(df2, x="humidity", y="area", trendline="ols",
                     labels={"humidity": "전국 평균 습도(%)", "area": "피해 면적(ha)"},
                     title="전국 데이터 기반 습도-피해면적 상관성 분석",
                     trendline_color_override="red")
    st.plotly_chart(fig2, use_container_width=True, key="c2")
with col2_2:
    st.subheader("📝 SQL (National)")
    st.code(sql2, language='sql')
    st.write("💡 1번 차트 지역과 상관없이 **전국적인 기상 패턴**이 산불에 미치는 영향을 보여줍니다.")

st.divider()

# --- [차트 3] 발생 원인별 피해 분석 (전국 데이터 기준) ---
st.header("3. [전국] 산불 발생 원인별 피해 규모")
# 전국 모든 산불 원인을 집계
sql3 = "SELECT cause, SUM(area) as total_area FROM wildfires GROUP BY cause ORDER BY total_area DESC"
df3 = pd.read_sql(sql3, conn)

col3_1, col3_2 = st.columns([2, 1])
with col3_1:
    fig3 = px.bar(df3, x="cause", y="total_area", color="total_area",
                 labels={"cause": "원인", "total_area": "전국 누적 피해(ha)"},
                 title="전국 산불 발생 주원인 분석")
    st.plotly_chart(fig3, use_container_width=True, key="c3")
with col3_2:
    st.subheader("📝 SQL (National)")
    st.code(sql3, language='sql')
    st.error("⚠️ **경고: 대다수의 산불은 우리의 부주의로 발생합니다.**")

st.info("💡 전국 통계를 보면 특정 지역뿐만 아니라 모든 지역에서 인적 실화 방지가 가장 중요함을 알 수 있습니다.")

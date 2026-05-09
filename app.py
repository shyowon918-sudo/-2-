import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="전국 산불 분석 통합 대시보드", layout="wide")

# --- 데이터베이스 연결 및 초기화 ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    
    # 테이블 생성
    cursor.execute("CREATE TABLE IF NOT EXISTS fire_stations (name TEXT, address TEXT, region TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS weather (region TEXT, humidity REAL, wind_speed REAL, area REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS wildfires (region TEXT, location TEXT, cause TEXT, area REAL)")
    
    # [테스트용 샘플] 수원, 철원, 서울 등 데이터 삽입
    samples_stations = [
        ('수원소방서', '경기도 수원시 팔달구', '경기'),
        ('철원소방서', '강원도 철원군 갈말읍', '강원'),
        ('종로소방서', '서울특별시 종로구', '서울')
    ]
    cursor.executemany("INSERT INTO fire_stations VALUES (?,?,?)", samples_stations)
    
    samples_fires = [
        ('경기', '수원시', '담배꽁초', 15.5),
        ('강원', '철원군', '입산자 실화', 88.0),
        ('서울', '종로구', '전기적 요인', 5.2)
    ]
    cursor.executemany("INSERT INTO wildfires VALUES (?,?,?,?)", samples_fires)
    
    # 전국 기상 통계용 (2번 차트)
    cursor.executemany("INSERT INTO weather VALUES (?,?,?,?)", [
        ('경기', 45.0, 3.5, 100.0), ('강원', 30.0, 15.0, 1200.0), ('서울', 50.0, 2.1, 20.0)
    ])
    
    conn.commit()
    return conn

conn = init_db()

# --- 사이드바 설정 ---
st.sidebar.header("📍 1번 차트 지역 설정")
selected_sigungu = st.sidebar.text_input("상세 지역 입력 (예: 수원, 철원, 서울)", placeholder="시/군/구 명칭 입력", key="sigungu_input")

st.title("🔥 전국 산불 분석 및 실시간 대응 체계 대시보드")

# --- [차트 1] 지역별 대응 취약 지역 (선택 지역 검색) ---
st.header(f"1. 지역별 대응 취약 지역 분석")

if not selected_sigungu:
    st.info("💡 **좌측 사이드바에 분석하고 싶은 시/군/구 명칭을 입력하세요.** (전국 모든 지역 검색 가능)")
else:
    # SQL 검색: 입력값이 포함된 모든 시군구 검색
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
                             title=f"'{selected_sigungu}' 포함 지역 분석 결과", size_max=50)
            st.plotly_chart(fig1, use_container_width=True, key="c1")
        with col1_2:
            st.subheader("📝 실행 쿼리")
            st.code(sql1, language='sql')
            st.success(f"✅ **{selected_sigungu}** 지역의 데이터를 성공적으로 불러왔습니다.")
    else:
        # 데이터가 없을 경우 공지 문구 출력
        st.error(f"⚠️ **현재 '{selected_sigungu}' 지역에 대한 직접적인 산불 피해 기록이 없습니다.**")
        st.warning("💡 **공지:** 해당 지역은 최근 기록이 없거나 데이터 집계 중일 수 있습니다. **근처 지역(예: 인접 시/군)**을 검색하여 광역적인 위험도를 확인해 주세요.")

st.divider()

# --- [차트 2] 기상 조건 상관관계 (전국 기준) ---
st.header("2. [전국] 기상 조건과 피해 규모 상관관계")
sql2 = "SELECT humidity, wind_speed, area FROM weather"
df2 = pd.read_sql(sql2, conn)

col2_1, col2_2 = st.columns([2, 1])
with col2_1:
    fig2 = px.scatter(df2, x="humidity", y="area", trendline="ols",
                     labels={"humidity": "습도(%)", "area": "피해 면적(ha)"},
                     title="전국 기상-피해면적 상관 분석", trendline_color_override="red")
    st.plotly_chart(fig2, use_container_width=True, key="c2")
with col2_2:
    st.subheader("💡 인사이트")
    st.write("- 전국적으로 습도가 낮을수록 피해 면적이 급격히 증가하는 경향을 보입니다.")

st.divider()

# --- [차트 3] 발생 원인별 피해 분석 (전국 기준) ---
st.header("3. [전국] 산불 발생 원인별 피해 순위")
sql3 = "SELECT cause, SUM(area) as total_area FROM wildfires GROUP BY cause ORDER BY total_area DESC"
df3 = pd.read_sql(sql3, conn)

col3_1, col3_2 = st.columns([2, 1])
with col3_1:
    fig3 = px.bar(df3, x="cause", y="total_area", color="total_area",
                 labels={"cause": "원인", "total_area": "전국 누적 피해(ha)"},
                 title="전국 원인별 피해 규모")
    st.plotly_chart(fig3, use_container_width=True, key="c3")
with col3_2:
    st.error("🚨 **우리의 부주의가 산불의 시작입니다.**")
    st.write("- 인위적인 요인(입산자 실화, 소각)이 자연 발화보다 훨씬 큰 피해를 줍니다.")

st.markdown("---")
st.caption("본 대시보드는 산림청 및 소방청의 가상 데이터를 기반으로 구성되었습니다.")

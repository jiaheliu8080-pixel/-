import streamlit as st
import random
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# ==========================================
# 页面配置与侧边栏菜单
# ==========================================
st.set_page_config(page_title="综合彩票分析与模拟系统", page_icon="🎰", layout="wide")

st.sidebar.title("🎰 彩种切换面板")
lottery_choice = st.sidebar.radio("请选择您要分析与模拟的彩票：", ["🔴 双色球 (SSQ)", "🔵 大乐透 (DLT)"])

st.sidebar.divider()
st.sidebar.caption("提示：彩票开奖是独立随机事件，没有任何算法能预测未来开奖。本工具仅用于概率演示与娱乐，请理性看待。")

# ==========================================
# 核心功能函数：自动获取最新真实数据
# ==========================================
@st.cache_data(ttl=3600)
def fetch_lottery_data(lotto_type):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    if lotto_type == "ssq":
        url = "https://datachart.500.com/ssq/history/newinc/history.php?start=00000"
    else:
        url = "https://datachart.500.com/dlt/history/newinc/history.php?start=00000"
        
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        tbody = soup.find('tbody', id='tdata')
        
        if not tbody:
            return None, "未能解析到数据表格。"

        rows = tbody.find_all('tr')
        recent_data = []
        count = 0
        
        for row in rows:
            if 'class' in row.attrs and 'tdbck' in row['class']: continue
            cols = row.find_all('td')
            
            if lotto_type == "ssq" and len(cols) >= 8:
                qihao = cols[0].text.strip()
                reds = " ".join([cols[i].text.strip() for i in range(1, 7)])
                blue = cols[7].text.strip()
                recent_data.append({"期号": qihao, "红球 (前区)": reds, "蓝球 (后区)": blue})
                count += 1
                
            elif lotto_type == "dlt" and len(cols) >= 8:
                qihao = cols[0].text.strip()
                fronts = " ".join([cols[i].text.strip() for i in range(1, 6)])
                backs = " ".join([cols[i].text.strip() for i in range(6, 8)])
                recent_data.append({"期号": qihao, "红球 (前区)": fronts, "蓝球 (后区)": backs})
                count += 1
                
            if count >= 10: break
                
        return recent_data, None
    except Exception as e:
        return None, f"抓取异常: {e}"

# ==========================================
# 界面渲染主逻辑
# ==========================================
if lottery_choice == "🔴 双色球 (SSQ)":
    st.title("🔴 双色球 (6+1) 分析与模拟")
    
    st.header("📊 最新真实开奖记录 (近10期)")
    with st.spinner("正在抓取双色球最新数据..."):
        data_ssq, err = fetch_lottery_data("ssq")
        if err:
            st.error(err)
        else:
            st.dataframe(pd.DataFrame(data_ssq), use_container_width=True, hide_index=True)
            
    st.divider()
    st.header("🎰 深度投资模拟器：坚守一注号码")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 帮我机选一注双色球"):
            st.session_state['ssq_red'] = sorted(random.sample(range(1, 34), 6))
            st.session_state['ssq_blue'] = random.randint(1, 16)
        my_red = st.session_state.get('ssq_red', [1, 2, 3, 4, 5, 6])
        my_blue = st.session_state.get('ssq_blue', 7)
        st.info(f"投注号码：\n\n🔴 **红球**：{' '.join([f'{n:02d}' for n in my_red])}\n\n🔵 **蓝球**：{my_blue:02d}")

    with col2:
        sim_count = st.select_slider("模拟购买期数 (每期2元)：", options=[100, 1000, 5000, 10000, 50000, 100000], value=1000, key="ssq_sim")
        st.write(f"💵 预计投入成本：**{sim_count * 2} 元**")

    if st.button("🚀 开始双色球模拟", key="ssq_btn"):
        with st.spinner("光速开奖中..."):
            prizes = {"一等奖":0, "二等奖":0, "三等奖":0, "四等奖":0, "五等奖":0, "六等奖":0, "未中奖":0}
            total_win = 0
            my_red_set = set(my_red)
            
            for _ in range(sim_count):
                draw_r = set(random.sample(range(1, 34), 6))
                draw_b = random.randint(1, 16)
                r_hits = len(my_red_set.intersection(draw_r))
                b_hit = (my_blue == draw_b)
                
                # 双色球真实中奖规则
                if r_hits == 6 and b_hit: prizes["一等奖"] += 1; total_win += 5000000
                elif r_hits == 6 and not b_hit: prizes["二等奖"] += 1; total_win += 150000
                elif r_hits == 5 and b_hit: prizes["三等奖"] += 1; total_win += 3000
                elif (r_hits == 5 and not b_hit) or (r_hits == 4 and b_hit): prizes["四等奖"] += 1; total_win += 200
                elif (r_hits == 4 and not b_hit) or (r_hits == 3 and b_hit): prizes["五等奖"] += 1; total_win += 10
                elif b_hit: prizes["六等奖"] += 1; total_win += 5
                else: prizes["未中奖"] += 1
                    
            c1, c2, c3 = st.columns(3)
            c1.metric("投入总计", f"{sim_count * 2} 元")
            c2.metric("奖金总计", f"{total_win} 元", delta=f"{total_win - (sim_count*2)} 元")
            c3.metric("综合中奖率", f"{(sim_count - prizes['未中奖']) / sim_count * 100:.2f} %")
            
            df_show = pd.DataFrame(list(prizes.items()), columns=["奖项", "次数"])
            df_show = df_show[df_show["奖项"] != "未中奖"]
            fig = px.bar(df_show, x="奖项", y="次数", text="次数", title="各奖项中签分布", color="次数", color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
elif lottery_choice == "🔵 大乐透 (DLT)":
    st.title("🔵 大乐透 (5+2) 分析与模拟")
    
    st.header("📊 最新真实开奖记录 (近10期)")
    with st.spinner("正在抓取大乐透最新数据..."):
        data_dlt, err = fetch_lottery_data("dlt")
        if err:
            st.error(err)
        else:
            st.dataframe(pd.DataFrame(data_dlt), use_container_width=True, hide_index=True)

    st.divider()
    st.header("🎰 深度投资模拟器：坚守一注号码")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 帮我机选一注大乐透"):
            st.session_state['dlt_front'] = sorted(random.sample(range(1, 36), 5))
            st.session_state['dlt_back'] = sorted(random.sample(range(1, 13), 2))
        my_front = st.session_state.get('dlt_front', [1, 2, 3, 4, 5])
        my_back = st.session_state.get('dlt_back', [6, 7])
        st.info(f"投注号码：\n\n🔴 **前区**：{' '.join([f'{n:02d}' for n in my_front])}\n\n🔵 **后区**：{' '.join([f'{n:02d}' for n in my_back])}")

    with col2:
        sim_count = st.select_slider("模拟购买期数 (每期2元)：", options=[100, 1000, 5000, 10000, 50000, 100000], value=1000, key="dlt_sim")
        st.write(f"💵 预计投入成本：**{sim_count * 2} 元**")

    if st.button("🚀 开始大乐透模拟", key="dlt_btn"):
        with st.spinner("光速开奖中..."):
            prizes = {"一等奖":0, "二等奖":0, "三等奖":0, "四等奖":0, "五等奖":0, "六等奖":0, "七等奖":0, "八等奖":0, "九等奖":0, "未中奖":0}
            total_win = 0
            my_f_set = set(my_front)
            my_b_set = set(my_back)
            
            for _ in range(sim_count):
                draw_f = set(random.sample(range(1, 36), 5))
                draw_b = set(random.sample(range(1, 13), 2))
                
                f_hits = len(my_f_set.intersection(draw_f))
                b_hits = len(my_b_set.intersection(draw_b))
                
                # 大乐透真实中奖规则 (基础投注奖金估算)
                if f_hits == 5 and b_hits == 2: prizes["一等奖"] += 1; total_win += 10000000
                elif f_hits == 5 and b_hits == 1: prizes["二等奖"] += 1; total_win += 100000
                elif f_hits == 5 and b_hits == 0: prizes["三等奖"] += 1; total_win += 10000
                elif f_hits == 4 and b_hits == 2: prizes["四等奖"] += 1; total_win += 3000
                elif f_hits == 4 and b_hits == 1: prizes["五等奖"] += 1; total_win += 300
                elif f_hits == 3 and b_hits == 2: prizes["六等奖"] += 1; total_win += 200
                elif f_hits == 4 and b_hits == 0: prizes["七等奖"] += 1; total_win += 100
                elif (f_hits == 3 and b_hits == 1) or (f_hits == 2 and b_hits == 2): prizes["八等奖"] += 1; total_win += 15
                elif (f_hits == 3 and b_hits == 0) or (f_hits == 1 and b_hits == 2) or (f_hits == 2 and b_hits == 1) or (f_hits == 0 and b_hits == 2): prizes["九等奖"] += 1; total_win += 5
                else: prizes["未中奖"] += 1
                    
            c1, c2, c3 = st.columns(3)
            c1.metric("投入总计", f"{sim_count * 2} 元")
            c2.metric("奖金总计", f"{total_win} 元", delta=f"{total_win - (sim_count*2)} 元")
            # 大乐透的小奖相对容易中，综合中奖率通常比双色球高一点点
            c3.metric("综合中奖率", f"{(sim_count - prizes['未中奖']) / sim_count * 100:.2f} %") 
            
            df_show = pd.DataFrame(list(prizes.items()), columns=["奖项", "次数"])
            df_show = df_show[df_show["奖项"] != "未中奖"]
            fig = px.bar(df_show, x="奖项", y="次数", text="次数", title="各奖项中签分布", color="次数", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

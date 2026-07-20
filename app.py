import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="美股期权大单扫描", layout="wide")

st.title("🦅 美股期权异动分析网页版")

ticker = st.text_input("输入股票代码 (如 AAPL, TSLA, NVDA)", value="ORCL").upper()

if ticker:
    try:
        tk = yf.Ticker(ticker)
        price = tk.fast_info['lastPrice']
        st.subheader(f"{ticker} 当前股价: ${price:.2f}")

        # 获取期权到期日
        exps = tk.options
        if not exps:
            st.error("未找到该股票的期权数据")
        else:
            # 筛选前 3 个到期日以提高加载速度
            selected_exps = exps[:3]
            all_data = []

            for exp in selected_exps:
                chain = tk.option_chain(exp)
                calls = chain.calls
                puts = chain.puts
                calls['Type'] = 'Call'
                puts['Type'] = 'Put'
                df = pd.concat([calls, puts])
                df['Expiry'] = exp
                # 计算预计成交额
                df['Premium'] = df['volume'] * ((df['bid'] + df['ask']) / 2) * 100
                all_data.append(df)

            full_df = pd.concat(all_data)
            
            # 筛选大额单：成交额 > 20万美元 或 成交量 > 持仓量 1.5倍
            whales = full_df[
                (full_df['Premium'] > 200000) | 
                (full_df['volume'] > full_df['openInterest'] * 1.5)
            ].sort_values(by='Premium', ascending=False)

            st.write("### 🚨 今日异动/大额订单 (Top 20)")
            st.dataframe(whales[['Type', 'Expiry', 'strike', 'volume', 'openInterest', 'Premium']].head(20).style.format({"Premium": "${:,.0f}"}))
            
            st.info("注：Premium 为估算成交权利金；异动包含成交量远超持仓量的合约。")
    except Exception as e:
        st.error(f"数据加载出错: {e}")

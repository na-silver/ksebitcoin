#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 AI 트레이딩 투자 결과 대시보드
Trading Results Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import TradingDatabase

# 페이지 설정
st.set_page_config(
    page_title="📊 AI 트레이딩 투자 결과",
    page_icon="💰", 
    layout="wide"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #FF6B35;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        margin: 0.5rem 0;
    }
    .success-card {
        border-left-color: #00D084;
    }
    .danger-card {
        border-left-color: #FF4757;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_trading_data():
    """거래 데이터 로드"""
    try:
        # TradingDatabase 클래스 사용
        db = TradingDatabase("trading_enhanced.db")
        
        # 거래 내역 - 최근 1년간 데이터
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        trades_data = db.get_trades_by_date(start_date, end_date)
        trades_df = pd.DataFrame(trades_data)
        
        # 포트폴리오 히스토리
        portfolio_data = db.get_portfolio_history(100)
        portfolio_df = pd.DataFrame(portfolio_data)
        
        return {
            'trades': trades_df,
            'portfolio': portfolio_df,
            'status': 'success'
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def calculate_performance_metrics(trades_df):
    """성과 지표 계산"""
    if trades_df.empty:
        return {}
    
    # 기본 통계
    total_trades = len(trades_df)
    buy_trades = trades_df[trades_df['trade_type'] == 'buy']
    sell_trades = trades_df[trades_df['trade_type'] == 'sell']
    
    total_buy_value = buy_trades['total_value'].sum() if not buy_trades.empty else 0
    total_sell_value = sell_trades['total_value'].sum() if not sell_trades.empty else 0
    total_fees = trades_df['fee'].sum()
    
    # 수익률 계산
    net_profit = total_sell_value - total_buy_value
    roi = (net_profit / total_buy_value * 100) if total_buy_value > 0 else 0
    
    return {
        'total_trades': total_trades,
        'buy_count': len(buy_trades),
        'sell_count': len(sell_trades),
        'total_buy_value': total_buy_value,
        'total_sell_value': total_sell_value,
        'total_fees': total_fees,
        'net_profit': net_profit,
        'roi': roi
    }

def render_performance_overview(metrics):
    """성과 개요"""
    st.markdown('<h2 style="color: #00D084;">📈 투자 성과 개요</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="총 거래 횟수",
            value=f"{metrics['total_trades']}회",
            delta=f"매수 {metrics['buy_count']} / 매도 {metrics['sell_count']}"
        )
    
    with col2:
        profit_color = "normal" if metrics['net_profit'] >= 0 else "inverse"
        st.metric(
            label="순손익",
            value=f"₩{metrics['net_profit']:,.0f}",
            delta=f"{metrics['roi']:+.2f}%",
            delta_color=profit_color
        )
    
    with col3:
        st.metric(
            label="총 매수금액",
            value=f"₩{metrics['total_buy_value']:,.0f}"
        )
    
    with col4:
        st.metric(
            label="총 수수료",
            value=f"₩{metrics['total_fees']:,.0f}"
        )

def render_trades_table(trades_df):
    """거래 내역 테이블"""
    st.markdown('<h2 style="color: #00D084;">📋 거래 내역</h2>', unsafe_allow_html=True)
    
    if trades_df.empty:
        st.warning("거래 내역이 없습니다.")
        return
    
    # 데이터 전처리
    display_df = trades_df.copy()
    display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    display_df['price'] = display_df['price'].apply(lambda x: f"₩{x:,.0f}")
    display_df['amount'] = display_df['amount'].apply(lambda x: f"{x:.6f}")
    display_df['total_value'] = display_df['total_value'].apply(lambda x: f"₩{x:,.0f}")
    display_df['fee'] = display_df['fee'].apply(lambda x: f"₩{x:,.0f}")
    
    # 컬럼 선택 및 이름 변경
    display_df = display_df[['timestamp', 'trade_type', 'price', 'amount', 'total_value', 'fee', 'success']]
    display_df.columns = ['시간', '타입', '가격', '수량(BTC)', '총액', '수수료', '성공']
    
    st.dataframe(display_df, use_container_width=True, height=400)

def render_portfolio_chart(portfolio_df):
    """포트폴리오 변화 차트"""
    st.markdown('<h2 style="color: #00D084;">📊 포트폴리오 변화</h2>', unsafe_allow_html=True)
    
    if portfolio_df.empty:
        st.warning("포트폴리오 히스토리가 없습니다.")
        return
    
    # 시간순 정렬 (date 컬럼 사용)
    portfolio_df = portfolio_df.sort_values('date')
    portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
    
    # 차트 생성
    fig = go.Figure()
    
    # 총 자산 가치
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=portfolio_df['total_value'],
        mode='lines+markers',
        name='총 자산',
        line=dict(color='#FF6B35', width=3),
        marker=dict(size=6)
    ))
    
    # KRW 잔고
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=portfolio_df['krw_balance'],
        mode='lines',
        name='KRW 잔고',
        line=dict(color='#00D084', width=2)
    ))
    
    # BTC 가치 계산 (btc_balance * btc_avg_price)
    if 'btc_balance' in portfolio_df.columns and 'btc_avg_price' in portfolio_df.columns:
        portfolio_df['btc_value_krw'] = portfolio_df['btc_balance'] * portfolio_df['btc_avg_price']
        fig.add_trace(go.Scatter(
            x=portfolio_df['date'],
            y=portfolio_df['btc_value_krw'],
            mode='lines',
            name='BTC 가치',
            line=dict(color='#FFA500', width=2)
        ))
    
    fig.update_layout(
        title="포트폴리오 가치 변화",
        xaxis_title="날짜",
        yaxis_title="가치 (KRW)",
        template="plotly_dark",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_monthly_performance(trades_df):
    """월별 성과"""
    st.markdown('<h2 style="color: #00D084;">📅 월별 거래 성과</h2>', unsafe_allow_html=True)
    
    if trades_df.empty:
        st.warning("거래 데이터가 없습니다.")
        return
    
    # 월별 집계 (timestamp 컬럼 사용)
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    trades_df['month'] = trades_df['timestamp'].dt.to_period('M')
    
    # 성공한 거래만 집계
    successful_trades = trades_df[trades_df['success'] == True]
    
    if successful_trades.empty:
        st.warning("성공한 거래가 없습니다.")
        return
    
    monthly_stats = successful_trades.groupby('month').agg({
        'trade_type': 'count',
        'total_value': 'sum',
        'fee': 'sum'
    }).rename(columns={'trade_type': 'trade_count'})
    
    # 월별 차트
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[str(m) for m in monthly_stats.index],
        y=monthly_stats['trade_count'],
        name='거래 횟수',
        marker_color='#FF6B35'
    ))
    
    fig.update_layout(
        title="월별 거래 횟수",
        xaxis_title="월",
        yaxis_title="거래 횟수",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    """메인 대시보드"""
    st.markdown('<h1 class="main-header">📊 AI 트레이딩 투자 결과</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #888;">Investment Performance Dashboard</p>', unsafe_allow_html=True)
    
    # 데이터 로드
    data = load_trading_data()
    
    if data['status'] != 'success':
        st.error("❌ 데이터 로드 실패")
        st.error(f"오류: {data.get('error', '알 수 없음')}")
        return
    
    trades_df = data['trades']
    portfolio_df = data['portfolio']
    
    # 성과 지표 계산
    metrics = calculate_performance_metrics(trades_df)
    
    if not metrics:
        st.warning("⚠️ 거래 데이터가 없습니다.")
        return
    
    # 대시보드 렌더링
    render_performance_overview(metrics)
    
    st.markdown("---")
    
    # 탭으로 구성
    tab1, tab2, tab3 = st.tabs(["📋 거래 내역", "📊 포트폴리오 변화", "📅 월별 성과"])
    
    with tab1:
        render_trades_table(trades_df)
    
    with tab2:
        render_portfolio_chart(portfolio_df)
    
    with tab3:
        render_monthly_performance(trades_df)
    
    # 새로고침 버튼
    st.sidebar.title("🔄 제어판")
    if st.sidebar.button("데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()
    
    # 정보
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 대시보드 정보**")
    st.sidebar.info(f"📅 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not trades_df.empty:
        latest_trade = pd.to_datetime(trades_df['timestamp']).max()
        st.sidebar.info(f"🔄 최근 거래: {latest_trade.strftime('%Y-%m-%d %H:%M')}")
        
        # 추가 통계 정보
        total_trades = len(trades_df)
        successful_trades = len(trades_df[trades_df['success'] == True])
        st.sidebar.info(f"📊 총 거래: {total_trades}건 (성공: {successful_trades}건)")

if __name__ == "__main__":
    main() 
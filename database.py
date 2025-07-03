import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TradingDatabase:
    def __init__(self, db_path: str = "trading_data.db"):
        """매매 데이터 SQLite 데이터베이스 초기화"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 매매 분석 로그 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    krw_balance REAL,
                    btc_balance REAL,
                    total_portfolio_value REAL,
                    investment_status_json TEXT,
                    ai_decision TEXT NOT NULL,
                    ai_reason TEXT,
                    ai_confidence TEXT,
                    ai_analysis_full_json TEXT,
                    market_data_json TEXT,
                    analysis_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 실제 거래 기록 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actual_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    trade_type TEXT NOT NULL, -- 'buy' or 'sell'
                    price REAL NOT NULL,
                    amount REAL NOT NULL,
                    total_value REAL NOT NULL,
                    fee REAL DEFAULT 0,
                    order_id TEXT,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 포트폴리오 스냅샷 테이블 (일별 포트폴리오 가치 추적용)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    krw_balance REAL NOT NULL,
                    btc_balance REAL NOT NULL,
                    btc_avg_price REAL,
                    total_value REAL NOT NULL,
                    profit_loss REAL DEFAULT 0,
                    profit_loss_percent REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI 자기반성 테이블 (과거 매매 결과 분석 및 학습)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS self_reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reflection_date TEXT NOT NULL,
                    analysis_period_start TEXT NOT NULL,
                    analysis_period_end TEXT NOT NULL,
                    total_trades_analyzed INTEGER DEFAULT 0,
                    successful_trades INTEGER DEFAULT 0,
                    failed_trades INTEGER DEFAULT 0,
                    total_profit_loss REAL DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    market_conditions_then TEXT,
                    market_conditions_now TEXT,
                    reflection_content TEXT NOT NULL,
                    lessons_learned TEXT,
                    improvement_suggestions TEXT,
                    confidence_adjustment REAL DEFAULT 0,
                    strategy_modifications TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print(f"데이터베이스 초기화 완료: {self.db_path}")
    
    def save_analysis_log(self, market_data: Dict, ai_analysis: Dict, timestamp: str, analysis_type: str = "enhanced") -> int:
        """AI 분석 결과를 데이터베이스에 저장"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            investment_status = market_data.get('investment_status', {})
            
            cursor.execute('''
                INSERT INTO trading_logs (
                    timestamp, current_price, krw_balance, btc_balance, 
                    total_portfolio_value, investment_status_json,
                    ai_decision, ai_reason, ai_confidence,
                    ai_analysis_full_json, market_data_json, analysis_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                market_data.get('current_price', 0),
                investment_status.get('krw_balance', 0),
                investment_status.get('btc_balance', 0),
                investment_status.get('total_portfolio_value', 0),
                json.dumps(investment_status, ensure_ascii=False),
                ai_analysis.get('decision', ''),
                ai_analysis.get('reason', ''),
                ai_analysis.get('confidence', ''),
                json.dumps(ai_analysis, ensure_ascii=False),  # 전체 AI 분석 결과 저장
                json.dumps(market_data, ensure_ascii=False),  # 전체 마켓 데이터 저장
                analysis_type
            ))
            
            log_id = cursor.lastrowid
            conn.commit()
            print(f"분석 로그 저장 완료 (ID: {log_id}) - 전체 분석 결과 포함")
            return log_id
    
    def save_trade(self, trade_type: str, price: float, amount: float, 
                   total_value: float, fee: float = 0, order_id: str = None, 
                   success: bool = True, error_message: str = None, trade_time: str = None) -> int:
        """실제 거래 내역을 데이터베이스에 저장"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 거래 시간 처리 (전달받은 시간이 있으면 사용, 없으면 현재 시간)
            trade_timestamp = trade_time if trade_time else datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO actual_trades (
                    timestamp, trade_type, price, amount, total_value,
                    fee, order_id, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_timestamp,
                trade_type,
                price,
                amount, 
                total_value,
                fee,
                order_id,
                success,
                error_message
            ))
            
            trade_id = cursor.lastrowid
            conn.commit()
            print(f"거래 내역 저장 완료 (ID: {trade_id}, {trade_type.upper()}: {price:,}원 x {amount} BTC)")
            return trade_id
    
    def save_portfolio_snapshot(self, date: str, krw_balance: float, btc_balance: float,
                              btc_avg_price: float = 0, total_value: float = 0,
                              profit_loss: float = 0, profit_loss_percent: float = 0):
        """일별 포트폴리오 스냅샷 저장"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO portfolio_snapshots (
                    date, krw_balance, btc_balance, btc_avg_price,
                    total_value, profit_loss, profit_loss_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, krw_balance, btc_balance, btc_avg_price,
                total_value, profit_loss, profit_loss_percent
            ))
            
            conn.commit()
            print(f"포트폴리오 스냅샷 저장 완료 ({date})")
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict]:
        """최근 분석 로그 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trading_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_logs_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """날짜 범위별 분석 로그 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trading_logs 
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at ASC
            ''', (start_date, end_date))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_trades_by_date(self, start_date: str, end_date: str = None) -> List[Dict]:
        """날짜별 거래 내역 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if end_date:
                cursor.execute('''
                    SELECT * FROM actual_trades 
                    WHERE DATE(created_at) BETWEEN ? AND ?
                    ORDER BY created_at DESC
                ''', (start_date, end_date))
            else:
                cursor.execute('''
                    SELECT * FROM actual_trades 
                    WHERE DATE(created_at) = ?
                    ORDER BY created_at DESC
                ''', (start_date,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_portfolio_history(self, days: int = 30) -> List[Dict]:
        """포트폴리오 변화 이력 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM portfolio_snapshots 
                ORDER BY date DESC 
                LIMIT ?
            ''', (days,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_trading_stats(self) -> Dict:
        """거래 통계 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 총 거래 횟수
            cursor.execute('SELECT COUNT(*) as total_trades FROM actual_trades WHERE success = 1')
            total_trades = cursor.fetchone()[0]
            
            # 매수/매도 횟수
            cursor.execute('SELECT trade_type, COUNT(*) as count FROM actual_trades WHERE success = 1 GROUP BY trade_type')
            trade_counts = dict(cursor.fetchall())
            
            # 총 수수료
            cursor.execute('SELECT SUM(fee) as total_fee FROM actual_trades WHERE success = 1')
            total_fee = cursor.fetchone()[0] or 0
            
            # AI 결정 통계
            cursor.execute('SELECT ai_decision, COUNT(*) as count FROM trading_logs GROUP BY ai_decision')
            ai_decisions = dict(cursor.fetchall())
            
            return {
                'total_trades': total_trades,
                'buy_count': trade_counts.get('buy', 0),
                'sell_count': trade_counts.get('sell', 0),
                'total_fee': total_fee,
                'ai_decisions': ai_decisions
            }
    
    def analyze_trading_performance(self, days_back: int = 7) -> Dict:
        """과거 매매 성과 분석"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 분석 기간 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # 해당 기간의 거래 조회
            cursor.execute('''
                SELECT * FROM actual_trades 
                WHERE created_at BETWEEN ? AND ? AND success = 1
                ORDER BY created_at
            ''', (start_date.isoformat(), end_date.isoformat()))
            
            trades = cursor.fetchall()
            
            if not trades:
                return {
                    'total_trades': 0,
                    'total_profit_loss': 0,
                    'win_rate': 0,
                    'successful_trades': 0,
                    'failed_trades': 0,
                    'analysis_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                }
            
            # 매매 성과 계산 (간단한 방식)
            total_profit_loss = 0
            successful_trades = 0
            failed_trades = 0
            
            # BTC 보유량과 평균 매수가격 추적
            btc_balance = 0
            krw_balance = 1000000  # 초기 자본 (시뮬레이션)
            
            for trade in trades:
                if trade[2] == 'buy':  # trade_type
                    btc_bought = trade[4] / trade[3]  # total_value / price
                    btc_balance += btc_bought
                    krw_balance -= trade[4]  # total_value
                elif trade[2] == 'sell':  # trade_type
                    btc_sold = trade[4]  # amount
                    btc_balance -= btc_sold
                    krw_balance += trade[5]  # total_value
                    
                    # 간단한 수익 계산 (매도 시점에서)
                    profit = trade[5] - (btc_sold * trade[3])  # 매도금액 - (수량 * 매도가격)
                    total_profit_loss += profit
                    
                    if profit > 0:
                        successful_trades += 1
                    else:
                        failed_trades += 1
            
            total_trades = len(trades)
            win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'failed_trades': failed_trades,
                'total_profit_loss': total_profit_loss,
                'win_rate': win_rate,
                'analysis_period_start': start_date.strftime('%Y-%m-%d'),
                'analysis_period_end': end_date.strftime('%Y-%m-%d'),
                'trades_data': trades
            }
    
    def save_reflection(self, reflection_data: Dict) -> int:
        """AI 자기반성 내용을 데이터베이스에 저장"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO self_reflections (
                    reflection_date, analysis_period_start, analysis_period_end,
                    total_trades_analyzed, successful_trades, failed_trades,
                    total_profit_loss, win_rate, market_conditions_then,
                    market_conditions_now, reflection_content, lessons_learned,
                    improvement_suggestions, confidence_adjustment, strategy_modifications
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reflection_data.get('reflection_date', datetime.now().isoformat()),
                reflection_data.get('analysis_period_start', ''),
                reflection_data.get('analysis_period_end', ''),
                reflection_data.get('total_trades_analyzed', 0),
                reflection_data.get('successful_trades', 0),
                reflection_data.get('failed_trades', 0),
                reflection_data.get('total_profit_loss', 0),
                reflection_data.get('win_rate', 0),
                reflection_data.get('market_conditions_then', ''),
                reflection_data.get('market_conditions_now', ''),
                reflection_data.get('reflection_content', ''),
                reflection_data.get('lessons_learned', ''),
                reflection_data.get('improvement_suggestions', ''),
                reflection_data.get('confidence_adjustment', 0),
                reflection_data.get('strategy_modifications', '')
            ))
            
            reflection_id = cursor.lastrowid
            conn.commit()
            print(f"자기반성 저장 완료 (ID: {reflection_id})")
            return reflection_id
    
    def get_recent_reflections(self, limit: int = 5) -> List[Dict]:
        """최근 자기반성 내용 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM self_reflections 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_market_context(self, timestamp: str) -> Dict:
        """특정 시점의 시장 상황 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trading_logs 
                WHERE timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (timestamp,))
            
            row = cursor.fetchone()
            if row:
                log = dict(row)
                # 시장 데이터 파싱
                try:
                    market_data = json.loads(log.get('market_data_json', '{}'))
                    return {
                        'price': log.get('current_price', 0),
                        'technical_indicators': market_data.get('technical_indicators', {}),
                        'fear_greed': market_data.get('fear_greed_index', []),
                        'timestamp': log.get('timestamp', '')
                    }
                except:
                    return {'price': log.get('current_price', 0), 'timestamp': log.get('timestamp', '')}
            return {}

    def migrate_from_json(self, json_file_path: str):
        """기존 JSON 로그를 SQLite로 마이그레이션"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        self.save_analysis_log(
                            data.get('market_data', {}),
                            data.get('ai_analysis', {}),
                            data.get('timestamp', datetime.now().isoformat())
                        )
            print(f"JSON 데이터 마이그레이션 완료: {json_file_path}")
        except FileNotFoundError:
            print(f"JSON 파일을 찾을 수 없습니다: {json_file_path}")
        except Exception as e:
            print(f"마이그레이션 중 오류 발생: {e}") 
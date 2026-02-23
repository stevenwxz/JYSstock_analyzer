#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信小程序后端API服务
提供股票分析数据的RESTful API接口
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import sys
import os
from datetime import datetime, timedelta
import json

# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.analysis.market_analyzer import MarketAnalyzer
from src.data.data_fetcher import StockDataFetcher
from config.config import LOG_CONFIG

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': '股票分析API服务'
    })


@app.route('/api/stocks/recommend', methods=['GET'])
def get_recommended_stocks():
    """
    获取推荐股票列表
    返回当日推荐的强势股票
    """
    try:
        logger.info("收到推荐股票请求")

        analyzer = MarketAnalyzer()
        result = analyzer.run_daily_analysis()

        if not result:
            return jsonify({
                'code': 500,
                'message': '分析失败',
                'data': None
            }), 500

        selected_stocks = result.get('selected_stocks', [])
        market_summary = result.get('market_overview', {})  # 修复: 使用正确的键名

        # 格式化返回数据
        stocks_data = []
        for stock in selected_stocks:
            score_detail = stock.get('strength_score_detail', {})
            breakdown = score_detail.get('breakdown', {})

            stocks_data.append({
                'rank': stock.get('rank', 0),
                'code': stock.get('code', ''),
                'name': stock.get('name', ''),
                'price': round(stock.get('price', 0), 2),
                'changePct': round(stock.get('change_pct', 0), 2),
                'peRatio': round(stock.get('pe_ratio', 0), 2),
                'pbRatio': round(stock.get('pb_ratio', 0), 2),
                'roe': round(stock.get('roe', 0), 2),
                'momentum20d': round(stock.get('momentum_20d', 0), 2),
                'strengthScore': round(stock.get('strength_score', 0), 1),
                'grade': score_detail.get('grade', ''),
                'scoreBreakdown': {
                    'technical': breakdown.get('technical', 0),
                    'valuation': breakdown.get('valuation', 0),
                    'profitability': breakdown.get('profitability', 0),
                    'safety': breakdown.get('safety', 0),
                    'dividend': breakdown.get('dividend', 0)
                },
                'selectionReason': stock.get('selection_reason', ''),
                'industry': stock.get('industry', '未知')
            })

        return jsonify({
            'code': 200,
            'message': '成功',
            'data': {
                'stocks': stocks_data,
                'marketSummary': {
                    'totalStocks': market_summary.get('total_stocks', 0),
                    'risingStocks': market_summary.get('rising_stocks', 0),
                    'fallingStocks': market_summary.get('falling_stocks', 0),
                    'avgChangePct': round(market_summary.get('avg_change_pct', 0), 2)
                },
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"获取推荐股票失败: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@app.route('/api/stocks/detail/<stock_code>', methods=['GET'])
def get_stock_detail(stock_code):
    """
    获取单只股票的详细信息
    参数: stock_code - 股票代码(如 sh000001)
    """
    try:
        logger.info(f"收到股票详情请求: {stock_code}")

        fetcher = StockDataFetcher()
        stock_data = fetcher.get_stock_data(stock_code)

        if not stock_data:
            return jsonify({
                'code': 404,
                'message': '股票不存在',
                'data': None
            }), 404

        # 格式化股票详情
        detail = {
            'code': stock_data.get('code', ''),
            'name': stock_data.get('name', ''),
            'price': round(stock_data.get('price', 0), 2),
            'changePct': round(stock_data.get('change_pct', 0), 2),
            'changeAmount': round(stock_data.get('change_amount', 0), 2),
            'volume': stock_data.get('volume', 0),
            'turnover': stock_data.get('turnover', 0),
            'turnoverRate': round(stock_data.get('turnover_rate', 0), 2),
            'peRatio': round(stock_data.get('pe_ratio', 0), 2),
            'pbRatio': round(stock_data.get('pb_ratio', 0), 2),
            'high': round(stock_data.get('high', 0), 2),
            'low': round(stock_data.get('low', 0), 2),
            'open': round(stock_data.get('open', 0), 2),
            'previousClose': round(stock_data.get('previous_close', 0), 2),
        }

        return jsonify({
            'code': 200,
            'message': '成功',
            'data': detail
        })

    except Exception as e:
        logger.error(f"获取股票详情失败: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@app.route('/api/market/overview', methods=['GET'])
def get_market_overview():
    """获取市场概览数据"""
    try:
        logger.info("收到市场概览请求")

        fetcher = StockDataFetcher()
        overview = fetcher.get_market_overview()

        if not overview:
            return jsonify({
                'code': 500,
                'message': '获取市场数据失败',
                'data': None
            }), 500

        return jsonify({
            'code': 200,
            'message': '成功',
            'data': {
                'totalStocks': overview.get('total_stocks', 0),
                'risingStocks': overview.get('rising_stocks', 0),
                'fallingStocks': overview.get('falling_stocks', 0),
                'avgChangePct': round(overview.get('avg_change_pct', 0), 2),
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"获取市场概览失败: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@app.route('/api/analysis/history', methods=['GET'])
def get_analysis_history():
    """
    获取历史分析记录
    查询参数:
    - days: 查询天数(默认7天)
    """
    try:
        days = request.args.get('days', 7, type=int)
        logger.info(f"收到历史分析请求: {days}天")

        # 读取历史分析文件
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs', 'analysis')

        if not os.path.exists(logs_dir):
            return jsonify({
                'code': 200,
                'message': '成功',
                'data': []
            })

        history = []
        files = sorted(os.listdir(logs_dir), reverse=True)

        for filename in files[:days]:
            if filename.endswith('.json'):
                file_path = os.path.join(logs_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 格式化日期显示为友好格式
                        analysis_date = data.get('analysis_date', '')
                        analysis_time = data.get('analysis_time', '')

                        # 转换为 "12月2日 10:28" 格式
                        if analysis_date:
                            try:
                                from datetime import datetime as dt
                                date_obj = dt.strptime(analysis_date, '%Y-%m-%d')
                                time_part = analysis_time.split(':')[:2]  # 只取时:分
                                date_str = f"{date_obj.month}月{date_obj.day}日 {':'.join(time_part)}"
                            except:
                                date_str = f"{analysis_date} {analysis_time}"
                        else:
                            date_str = ''

                        history.append({
                            'date': date_str,
                            'stockCount': len(data.get('selected_stocks', [])),
                            'topStock': data.get('selected_stocks', [{}])[0].get('name', '') if data.get('selected_stocks') else '',
                            'filename': filename.replace('.json', '')  # 添加文件名(去掉.json),用于详情查询
                        })
                except Exception as e:
                    logger.warning(f"读取历史文件失败 {filename}: {e}")
                    continue

        return jsonify({
            'code': 200,
            'message': '成功',
            'data': history
        })

    except Exception as e:
        logger.error(f"获取历史分析失败: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@app.route('/api/analysis/detail/<filename>', methods=['GET'])
def get_analysis_detail(filename):
    """
    获取历史分析详情
    参数: filename - 分析文件名(不含.json后缀)
    """
    try:
        logger.info(f"收到历史详情请求: {filename}")

        # 读取指定的分析文件
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs', 'analysis')
        file_path = os.path.join(logs_dir, f"{filename}.json")

        if not os.path.exists(file_path):
            return jsonify({
                'code': 404,
                'message': '分析记录不存在',
                'data': None
            }), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        selected_stocks = data.get('selected_stocks', [])
        market_overview = data.get('market_overview', {})

        # 格式化股票数据(与推荐接口保持一致)
        stocks_data = []
        for stock in selected_stocks:
            score_detail = stock.get('strength_score_detail', {})
            breakdown = score_detail.get('breakdown', {})

            stocks_data.append({
                'rank': stock.get('rank', 0),
                'code': stock.get('code', ''),
                'name': stock.get('name', ''),
                'price': round(stock.get('price', 0), 2),
                'changePct': round(stock.get('change_pct', 0), 2),
                'peRatio': round(stock.get('pe_ratio', 0), 2),
                'pbRatio': round(stock.get('pb_ratio', 0), 2),
                'roe': round(stock.get('roe', 0), 2),
                'momentum20d': round(stock.get('momentum_20d', 0), 2),
                'strengthScore': round(stock.get('strength_score', 0), 1),
                'grade': score_detail.get('grade', ''),
                'scoreBreakdown': {
                    'technical': breakdown.get('technical', 0),
                    'valuation': breakdown.get('valuation', 0),
                    'profitability': breakdown.get('profitability', 0),
                    'safety': breakdown.get('safety', 0),
                    'dividend': breakdown.get('dividend', 0)
                },
                'selectionReason': stock.get('selection_reason', ''),
                'industry': stock.get('industry', '未知')
            })

        return jsonify({
            'code': 200,
            'message': '成功',
            'data': {
                'analysisDate': data.get('analysis_date', ''),
                'analysisTime': data.get('analysis_time', ''),
                'stocks': stocks_data,
                'marketSummary': {
                    'totalStocks': market_overview.get('total_stocks', 0),
                    'risingStocks': market_overview.get('rising_stocks', 0),
                    'fallingStocks': market_overview.get('falling_stocks', 0),
                    'avgChangePct': round(market_overview.get('avg_change_pct', 0), 2)
                }
            }
        })

    except Exception as e:
        logger.error(f"获取历史详情失败: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'code': 404,
        'message': '接口不存在',
        'data': None
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'code': 500,
        'message': '服务器内部错误',
        'data': None
    }), 500


if __name__ == '__main__':
    logger.info("启动API服务器...")
    print("=" * 60)
    print("股票分析API服务已启动")
    print("=" * 60)
    print("访问地址: http://localhost:5000")
    print("API文档:")
    print("  - GET  /api/health              健康检查")
    print("  - GET  /api/stocks/recommend    获取推荐股票")
    print("  - GET  /api/stocks/detail/:code 获取股票详情")
    print("  - GET  /api/market/overview     获取市场概览")
    print("  - GET  /api/analysis/history    获取历史分析")
    print("=" * 60)

    # 开发环境使用debug模式,生产环境请关闭
    app.run(host='0.0.0.0', port=5000, debug=True)

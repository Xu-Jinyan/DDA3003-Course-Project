from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from data_service import DataService
import traceback

# 创建Flask应用实例
app = Flask(__name__, static_folder='.', static_url_path='')

# 启用CORS，允许前端跨域请求
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 创建数据服务实例
data_service = DataService()

# ==================== 前端路由 ====================

@app.route('/')
def index():
    """服务前端HTML文件"""
    return app.send_static_file('index.html')

# ==================== API路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': 'PFGW后端服务运行正常'
    })

@app.route('/api/date-range', methods=['GET'])
def get_date_range():
    """获取可用的时间范围"""
    try:
        date_range = data_service.get_date_range()
        
        if date_range is None:
            return jsonify({
                'error': 'No data available',
                'message': 'Flight data files not found'
            }), 500
        
        return jsonify(date_range)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/covid-data', methods=['GET'])
def get_covid_data():
    """获取指定日期的COVID-19数据"""
    try:
        date = request.args.get('date', None)
        
        if not date:
            return jsonify({
                'error': 'Date parameter is required',
                'usage': '/api/covid-data?date=YYYY-MM-DD'
            }), 400
        
        covid_data = data_service.get_covid_data_for_date(date)
        
        # 检查是否有错误
        if 'error' in covid_data:
            return jsonify(covid_data), 500
        
        return jsonify(covid_data)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/flights', methods=['GET'])
def get_flights():
    """获取指定日期的航班数据"""
    try:
        date = request.args.get('date', None)
        max_flights = request.args.get('max_flights', 50, type=int)
        
        if not date:
            return jsonify({
                'error': 'Date parameter is required',
                'usage': '/api/flights?date=YYYY-MM-DD&max_flights=50'
            }), 400
        
        flights_data = data_service.get_flights_for_date(date, max_flights)
        
        # 检查是否有错误
        if 'error' in flights_data:
            return jsonify(flights_data), 500
        
        return jsonify(flights_data)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/airports', methods=['GET'])
def get_airports():
    """获取机场数据"""
    try:
        airports = data_service.get_airport_data()
        return jsonify({
            'airports': airports,
            'count': len(airports)
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/snapshot', methods=['GET'])
def get_snapshot():
    """获取指定日期的完整快照（疫情+航班数据）"""
    try:
        date = request.args.get('date', None)
        max_flights = request.args.get('max_flights', 50, type=int)
        
        if not date:
            return jsonify({
                'error': 'Date parameter is required',
                'usage': '/api/snapshot?date=YYYY-MM-DD&max_flights=50'
            }), 400
        
        # 并行获取数据
        covid_data = data_service.get_covid_data_for_date(date)
        flights_data = data_service.get_flights_for_date(date, max_flights)
        
        # 检查错误
        errors = []
        if 'error' in covid_data:
            errors.append(f"COVID data error: {covid_data['error']}")
        if 'error' in flights_data:
            errors.append(f"Flights data error: {flights_data['error']}")
        
        response = {
            'date': date,
            'globalCases': covid_data.get('globalCases', 0),
            'countries': covid_data.get('countries', []),
            'flights': flights_data.get('flights', []),
            'totalFlights': flights_data.get('totalFlights', 0)
        }
        
        if errors:
            response['warnings'] = errors
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested resource does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred on the server'
    }), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    print("🚀 正在启动 PFGW 后端服务...")
    print("📊 正在加载数据，请稍候...")
    
    # 检查数据服务是否加载成功
    if data_service.get_date_range() is None:
        print("⚠️ 警告：航班数据未找到，部分功能可能受限")
    else:
        date_range = data_service.get_date_range()
        print(f"✅ 数据加载完成。日期范围: {date_range['start']} 至 {date_range['end']}")
    
    print("\n🔧 API端点:")
    print("  - 健康检查: GET /api/health")
    print("  - 日期范围: GET /api/date-range")
    print("  - 疫情数据: GET /api/covid-data?date=YYYY-MM-DD")
    print("  - 航班数据: GET /api/flights?date=YYYY-MM-DD")
    print("  - 机场数据: GET /api/airports")
    print("  - 完整快照: GET /api/snapshot?date=YYYY-MM-DD")
    print("\n🌐 服务器启动中...")
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
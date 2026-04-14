#!/usr/bin/env python3
"""
测试Flask API的脚本
用于验证后端是否正常工作
"""

import requests
import sys
import time
from datetime import datetime

def test_api():
    base_url = "http://localhost:5000"
    
    print("🚀 正在测试 PFGW API...\n")
    
    # 1. 测试健康检查
    print("1. 测试健康检查端点...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("   ✅ /api/health 工作正常")
        else:
            print(f"   ❌ /api/health 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ /api/health 请求失败: {e}")
        return False
    
    # 2. 测试日期范围
    print("2. 测试日期范围端点...")
    try:
        response = requests.get(f"{base_url}/api/date-range")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ /api/date-range 返回:")
            print(f"      开始: {data['start']}")
            print(f"      结束: {data['end']}")
            print(f"      总天数: {data['total_days']}")
        else:
            print(f"   ❌ /api/date-range 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ /api/date-range 请求失败: {e}")
        return False
    
    # 3. 测试疫情数据
    print("3. 测试疫情数据端点...")
    try:
        response = requests.get(f"{base_url}/api/covid-data?date=2020-03-15")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ /api/covid-data 返回:")
            print(f"      日期: {data['date']}")
            print(f"      全球病例: {data['globalCases']:,}")
            print(f"      国家数量: {len(data['countries'])}")
        else:
            print(f"   ❌ /api/covid-data 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ /api/covid-data 请求失败: {e}")
        return False
    
    # 4. 测试航班数据
    print("4. 测试航班数据端点...")
    try:
        response = requests.get(f"{base_url}/api/flights?date=2020-01-15")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ /api/flights 返回:")
            print(f"      日期: {data['date']}")
            print(f"      航班数量: {data['totalFlights']}")
        else:
            print(f"   ❌ /api/flights 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ /api/flights 请求失败: {e}")
        return False
    
    # 5. 测试机场数据
    print("5. 测试机场数据端点...")
    try:
        response = requests.get(f"{base_url}/api/airports")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ /api/airports 返回:")
            print(f"      机场总数: {data['count']}")
            if data['airports']:
                airport = data['airports'][0]
                print(f"      示例: {airport['airport']} @ {airport['coords']}")
        else:
            print(f"   ❌ /api/airports 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ /api/airports 请求失败: {e}")
        return False
    
    # 6. 测试快照数据
    print("6. 测试快照数据端点...")
    try:
        start = time.time()
        response = requests.get(f"{base_url}/api/snapshot?date=2020-03-15")
        elapsed = time.time() - start
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ /api/snapshot 返回 (耗时: {elapsed:.2f}秒):")
            print(f"      日期: {data['date']}")
            print(f"      全球病例: {data['globalCases']:,}")
            print(f"      国家数量: {len(data['countries'])}")
            print(f"      航班数量: {data['totalFlights']}")
        else:
            print(f"   ❌ /api/snapshot 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ /api/snapshot 请求失败: {e}")
        return False
    
    print("\n✅ 所有API测试通过!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    print(f"测试API地址: {base_url}\n")
    
    # 等待Flask服务器启动
    print("等待Flask服务器启动...")
    for i in range(30):
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Flaks服务器已启动!\n")
                break
        except:
            time.sleep(1)
            print(f"等待中... ({i+1}/30)")
    else:
        print("❌ Flask服务器未在30秒内启动")
        sys.exit(1)
    
    # 运行测试
    success = test_api()
    sys.exit(0 if success else 1)
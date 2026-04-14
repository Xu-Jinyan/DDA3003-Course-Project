# PFGW - Pandemic-Flight Global Watcher

> Python后端驱动的全球疫情航班可视化系统

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动后端
```bash
python3 app.py
```
服务器运行在: http://localhost:5000

### 3. 访问前端
打开浏览器: http://localhost:5000

## 🔧 API接口

- 健康检查: `GET /api/health`
- 日期范围: `GET /api/date-range`
- 疫情数据: `GET /api/covid-data?date=YYYY-MM-DD`
- 航班数据: `GET /api/flights?date=YYYY-MM-DD`
- 机场数据: `GET /api/airports`
- 完整快照: `GET /api/snapshot?date=YYYY-MM-DD`

## 📊 数据说明

- **WHO疫情数据**: 77,760条记录 (2020-01-05 至 2026-03-15)
- **航班数据**: 53个月份, 6.2GB Parquet格式
- **机场数据**: 11,347个机场

## 🛠️ 技术栈

- **后端**: Flask + Pandas + PyArrow
- **前端**: D3.js v7
- **数据库**: Parquet (航班) + Excel (疫情)

## ✨ 项目完成

- ✅ Flask后端应用
- ✅ 真实数据集成
- ✅ RESTful API
- ✅ 前端改造
- ✅ Bug修复 (NAType JSON序列化)
- ✅ 性能优化

访问 http://localhost:5000 体验完整的疫情航班可视化系统！

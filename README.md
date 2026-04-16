# PFGW — Pandemic-Flight Global Watcher

> 基于 Flask + D3.js 的全球疫情与航班数据交互式可视化系统

---

## 功能概览

- **疫情热力图**：按日期渲染各国累计/新增病例，颜色深浅反映严重程度
- **航班弧线**：展示当日全球飞行路线，按途经国家风险等级着色（蓝→红）
- **粒子动画**：飞行弧线上的动态粒子模拟实时航班流量
- **时间轴播放**：支持逐步/自动播放，可调节速度
- **趋势图**：时间轴上方实时绘制全球累计/新增趋势折线，支持悬停查看具体数值
- **国家详情面板**：点击国家查看完整历史曲线、峰值、死亡率
- **机场交互**：点击机场高亮其所有进出港航线
- **国家筛选**：多选下拉勾选，隐藏/显示指定国家
- **Top 10 排行榜**：当日新增病例最多的国家实时排名
- **明/暗主题切换**：偏好持久化至 localStorage
- **导出 JPG**：一键截图当前地图视图
- **使用说明**：内置帮助弹窗，介绍所有交互功能

---

## 快速开始

### 1. 准备数据

参见 [`data/readme.md`](data/readme.md) 下载并转换所需数据文件：

- WHO 疫情数据：`data/WHO-COVID-19-global-data.xlsx`
- 航班数据（转换后）：`data/clean/flightlist_*.parquet`

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python app.py
```

服务运行于 http://localhost:5000，前端与后端由同一进程提供。

---

## API 接口

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/date-range` | 可用数据的日期范围 |
| `GET /api/covid-data?date=YYYY-MM-DD` | 指定日期的疫情数据（全球 + Top 50 国家） |
| `GET /api/flights?date=YYYY-MM-DD&max_flights=50` | 指定日期的航班路线（采样） |
| `GET /api/airports` | 所有机场坐标 |
| `GET /api/snapshot?date=YYYY-MM-DD` | 疫情 + 航班合并快照 |
| `GET /api/global-trend` | 全时段全球累计/新增趋势（内存缓存） |
| `GET /api/country-history?country=USA` | 指定国家（ISO3）完整历史数据 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3 · Flask · Pandas · PyArrow |
| 前端 | D3.js v7 · 原生 CSS 变量 · Canvas-free SVG 动画 |
| 数据格式 | Parquet（航班）· Excel（疫情）· GeoJSON（地图） |

---

## 项目结构

```
├── app.py                  # Flask 应用，定义所有 API 路由
├── data_service.py         # 数据加载、查询、缓存逻辑
├── convert_to_parquet.py   # csv.gz → parquet 转换脚本
├── index.html              # D3.js 前端（单文件）
├── requirements.txt
├── static/
│   ├── data/world.geojson  # 世界地图 GeoJSON
│   └── js/d3.v7.min.js
└── data/
    ├── WHO-COVID-19-global-data.xlsx
    ├── flightlist_*.csv.gz
    └── clean/
        └── flightlist_*.parquet
```

---

## 数据来源

**航班数据（OpenSky Network）：**

> Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic and Matthias Wilhelm.
> "Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research".
> IPSN 2014.

> Xavier Olive. "traffic, a toolbox for processing and analysing air traffic data."
> Journal of Open Source Software 4(39), July 2019.

**疫情数据：** © World Health Organization — https://data.who.int/dashboards/covid19/data

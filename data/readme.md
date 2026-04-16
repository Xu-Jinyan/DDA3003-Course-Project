# 数据目录说明

## 目录结构

```
data/
├── readme.md                          # 本文件
├── WHO-COVID-19-global-data.xlsx      # WHO 疫情数据（需手动下载）
├── flightlist_YYYYMMDD_YYYYMMDD.csv.gz   # 原始航班数据（按月，需手动下载）
└── clean/
    └── flightlist_YYYYMMDD_YYYYMMDD.parquet  # 转换后的航班数据（由脚本生成）
```

---

## 一、WHO 疫情数据

**文件名：** `WHO-COVID-19-global-data.xlsx`

**下载地址：** https://data.who.int/dashboards/covid19/data

操作步骤：
1. 进入上方链接
2. 找到 "Cases and deaths by date reported" 部分
3. 点击下载 Excel 文件
4. 将文件重命名为 `WHO-COVID-19-global-data.xlsx`
5. 放入 `data/` 目录

---

## 二、航班数据

**来源：** OpenSky Network（COVID-19 期间全球航班数据集）

**下载地址：** https://zenodo.org/record/5092942

### 数据集说明

该数据集源自 OpenSky 完整数据，经清洗整理，用于展示 COVID-19 疫情期间全球航空流量变化。数据覆盖网络超过 2500 名成员所观测到的全部航班，时间跨度为 2020 年 1 月 1 日至疫情结束。

每个月的数据以独立 `.csv.gz` 文件提供，包含以下字段：

| 字段 | 说明 |
|------|------|
| `callsign` | ATC 屏幕上显示的航班标识符（前三位通常为航空公司代码） |
| `number` | 商业航班号（如有） |
| `icao24` | 应答机唯一识别码 |
| `registration` | 飞机尾号（如有） |
| `typecode` | 飞机机型（如有） |
| `origin` | 出发机场四字代码（如有） |
| `destination` | 目的机场四字代码（如有） |
| `firstseen` | OpenSky 网络首次收到消息的 UTC 时间戳 |
| `lastseen` | OpenSky 网络最后收到消息的 UTC 时间戳 |
| `day` | 最后一条消息的 UTC 日期 |

> **注意：** 出发/目的机场基于 ADS-B 轨迹在线推算，未与外部数据源交叉验证，字段可能为空。

### 下载与转换

操作步骤：
1. 进入上方链接，下载所需月份的 `.csv.gz` 文件
2. 将所有 `.csv.gz` 文件放入 `data/` 目录（**不要解压**）
3. 在项目根目录运行转换脚本，将 csv.gz 转换为后端所需的 Parquet 格式：

```bash
python convert_to_parquet.py
```

转换完成后，`data/clean/` 目录下会生成对应的 `.parquet` 文件。

> 如果中途中断，可以加 `--skip` 参数从断点继续：
> ```bash
> python convert_to_parquet.py --skip
> ```

**文件命名格式：** `flightlist_YYYYMMDD_YYYYMMDD.csv.gz`，每个文件对应一个月的数据。

**转换说明：** 脚本只保留后端实际使用的 7 列（origin、destination、latitude_1、longitude_1、latitude_2、longitude_2、day），转换后文件体积大幅缩小。

---

## 三、数据就绪确认

后端启动时会自动检测数据文件。若看到如下输出，说明数据加载成功：

```
WHO data loaded: 77760 records
Generated airport data: 11483 airports
Date range calculated: 2019-01-01 to 2022-12-01
✅ 数据加载完成
```

若缺少 WHO 文件，疫情热力图和国家详情功能将不可用。  
若缺少 Parquet 文件，航班路线和机场功能将不可用。

---

## 四、数据来源与引用

**航班数据（OpenSky Network）：**

> Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic and Matthias Wilhelm.
> "Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research".
> In Proceedings of the 13th IEEE/ACM International Symposium on Information Processing in Sensor Networks (IPSN), pages 83-94, April 2014.

> Xavier Olive.
> "traffic, a toolbox for processing and analysing air traffic data."
> Journal of Open Source Software 4(39), July 2019.

更多可视化示例与数据详细说明：https://traffic-viz.github.io/scenarios/covid19.html

**疫情数据：** © World Health Organization

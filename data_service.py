import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path
import pyarrow.parquet as pq
from functools import lru_cache

class DataService:
    def __init__(self):
        self.data_dir = Path("data")
        self.clean_data_dir = self.data_dir / "clean"

        # 缓存WHO数据（数据量小，可以全部加载到内存）
        self.who_data = None
        self.who_country_mapping = None

        # 机场数据缓存
        self.airports_df = None

        # 日期范围缓存
        self.date_range = None

        # 疫情数据缓存
        self.covid_cache = {}

        # 航班数据缓存
        self.flight_cache = {}

        # 全局趋势缓存
        self._global_trend_cache = None

        # ISO2到ISO3国家代码映射（WHO数据使用ISO2，GeoJSON使用ISO3）
        self.iso2_to_iso3_mapping = {
            'AF': 'AFG', 'AL': 'ALB', 'DZ': 'DZA', 'AS': 'ASM', 'AD': 'AND', 'AO': 'AGO',
            'AI': 'AIA', 'AG': 'ATG', 'AR': 'ARG', 'AM': 'ARM', 'AU': 'AUS', 'AT': 'AUT',
            'AZ': 'AZE', 'BS': 'BHS', 'BH': 'BHR', 'BD': 'BGD', 'BB': 'BRB', 'BY': 'BLR',
            'BE': 'BEL', 'BZ': 'BLZ', 'BJ': 'BEN', 'BM': 'BMU', 'BT': 'BTN', 'BO': 'BOL',
            'BA': 'BIH', 'BW': 'BWA', 'BR': 'BRA', 'BN': 'BRN', 'BG': 'BGR', 'BF': 'BFA',
            'BI': 'BDI', 'KH': 'KHM', 'CM': 'CMR', 'CA': 'CAN', 'CV': 'CPV', 'KY': 'CYM',
            'CF': 'CAF', 'TD': 'TCD', 'CL': 'CHL', 'CN': 'CHN', 'CO': 'COL', 'KM': 'COM',
            'CD': 'COD', 'CG': 'COG', 'CR': 'CRI', 'CI': 'CIV', 'HR': 'HRV', 'CU': 'CUB',
            'CW': 'CUW', 'CY': 'CYP', 'CZ': 'CZE', 'DK': 'DNK', 'DJ': 'DJI', 'DM': 'DMA',
            'DO': 'DOM', 'EC': 'ECU', 'EG': 'EGY', 'SV': 'SLV', 'GQ': 'GNQ', 'ER': 'ERI',
            'EE': 'EST', 'SZ': 'SWZ', 'ET': 'ETH', 'FJ': 'FJI', 'FI': 'FIN', 'FR': 'FRA',
            'GA': 'GAB', 'GM': 'GMB', 'GE': 'GEO', 'DE': 'DEU', 'GH': 'GHA', 'GR': 'GRC',
            'GD': 'GRD', 'GU': 'GUM', 'GT': 'GTM', 'GN': 'GIN', 'GW': 'GNB', 'GY': 'GUY',
            'HT': 'HTI', 'HN': 'HND', 'HK': 'HKG', 'HU': 'HUN', 'IS': 'ISL', 'IN': 'IND',
            'ID': 'IDN', 'IR': 'IRN', 'IQ': 'IRQ', 'IE': 'IRL', 'IL': 'ISR', 'IT': 'ITA',
            'JM': 'JAM', 'JP': 'JPN', 'JO': 'JOR', 'KZ': 'KAZ', 'KE': 'KEN', 'KI': 'KIR',
            'KP': 'PRK', 'KR': 'KOR', 'KW': 'KWT', 'KG': 'KGZ', 'LA': 'LAO', 'LV': 'LVA',
            'LB': 'LBN', 'LS': 'LSO', 'LR': 'LBR', 'LY': 'LBY', 'LI': 'LIE', 'LT': 'LTU',
            'LU': 'LUX', 'MO': 'MAC', 'MG': 'MDG', 'MW': 'MWI', 'MY': 'MYS', 'MV': 'MDV',
            'ML': 'MLI', 'MT': 'MLT', 'MH': 'MHL', 'MR': 'MRT', 'MU': 'MUS', 'MX': 'MEX',
            'FM': 'FSM', 'MD': 'MDA', 'MC': 'MCO', 'MN': 'MNG', 'ME': 'MNE', 'MS': 'MSR',
            'MA': 'MAR', 'MZ': 'MOZ', 'MM': 'MMR', 'NA': 'NAM', 'NR': 'NRU', 'NP': 'NPL',
            'NL': 'NLD', 'NZ': 'NZL', 'NI': 'NIC', 'NE': 'NER', 'NG': 'NGA', 'MK': 'MKD',
            'NO': 'NOR', 'OM': 'OMN', 'PK': 'PAK', 'PW': 'PLW', 'PS': 'PSE', 'PA': 'PAN',
            'PG': 'PNG', 'PY': 'PRY', 'PE': 'PER', 'PH': 'PHL', 'PL': 'POL', 'PT': 'PRT',
            'QA': 'QAT', 'RO': 'ROU', 'RU': 'RUS', 'RW': 'RWA', 'KN': 'KNA', 'LC': 'LCA',
            'VC': 'VCT', 'WS': 'WSM', 'SM': 'SMR', 'ST': 'STP', 'SA': 'SAU', 'SN': 'SEN',
            'RS': 'SRB', 'SC': 'SYC', 'SL': 'SLE', 'SG': 'SGP', 'SX': 'SXM', 'SK': 'SVK',
            'SI': 'SVN', 'SB': 'SLB', 'SO': 'SOM', 'ZA': 'ZAF', 'SS': 'SSD', 'ES': 'ESP',
            'LK': 'LKA', 'SD': 'SDN', 'SR': 'SUR', 'SE': 'SWE', 'CH': 'CHE', 'SY': 'SYR',
            'TW': 'TWN', 'TJ': 'TJK', 'TZ': 'TZA', 'TH': 'THA', 'TL': 'TLS', 'TG': 'TGO',
            'TK': 'TKL', 'TO': 'TON', 'TT': 'TTO', 'TN': 'TUN', 'TR': 'TUR', 'TM': 'TKM',
            'TV': 'TUV', 'UG': 'UGA', 'UA': 'UKR', 'AE': 'ARE', 'GB': 'GBR', 'US': 'USA',
            'UY': 'URY', 'UZ': 'UZB', 'VU': 'VUT', 'VE': 'VEN', 'VN': 'VNM', 'YE': 'YEM',
            'ZM': 'ZMB', 'ZW': 'ZWE'
        }

        # 加载WHO数据
        self._load_who_data()

        # 加载机场数据（只加载一次）
        self._load_airport_data()

        # 确定可用日期范围
        self._calculate_date_range()
    
    def _load_who_data(self):
        """加载WHO COVID-19数据"""
        who_file = self.data_dir / "WHO-COVID-19-global-data.xlsx"
        
        if who_file.exists():
            print(f"Loading WHO data from {who_file}")
            self.who_data = pd.read_excel(who_file)
            
            # 转换日期格式
            self.who_data['Date_reported'] = pd.to_datetime(self.who_data['Date_reported'])
            
            # 创建国家映射（从WHO数据中提取国家代码和名称）
            self.who_country_mapping = self.who_data[['Country_code', 'Country']].drop_duplicates()
            
            print(f"WHO data loaded: {self.who_data.shape[0]} records")
        else:
            print(f"Warning: WHO data file not found at {who_file}")
    
    def _load_airport_data(self):
        """从航班数据中提取机场信息"""
        print("Generating airport data from sample flight data...")
        
        # 读取一个样本月份的数据来获取机场坐标 - 使用一个确定存在的月份
        sample_file = self.clean_data_dir / "flightlist_20200301_20200331.parquet"
        if not sample_file.exists():
            # 回退到任何存在的文件
            parquet_files = list(self.clean_data_dir.glob("flightlist_*.parquet"))
            if parquet_files:
                sample_file = parquet_files[0]
            else:
                print("警告: 找不到任何航班数据文件")
                sample_file = None

        if sample_file and sample_file.exists():
            df_sample = pd.read_parquet(sample_file, columns=['origin', 'destination', 
                                                               'latitude_1', 'longitude_1', 
                                                               'latitude_2', 'longitude_2'])
            
            # 提取起点机场（origin的坐标是latitude_1, longitude_1）
            origin_airports = df_sample[['origin', 'latitude_1', 'longitude_1']].copy()
            origin_airports.columns = ['airport', 'latitude', 'longitude']
            origin_airports = origin_airports.dropna().drop_duplicates(subset=['airport'])
            
            # 提取终点机场（destination的坐标是latitude_2, longitude_2）
            dest_airports = df_sample[['destination', 'latitude_2', 'longitude_2']].copy()
            dest_airports.columns = ['airport', 'latitude', 'longitude']
            dest_airports = dest_airports.dropna().drop_duplicates(subset=['airport'])
            
            # 合并所有机场
            all_airports = pd.concat([origin_airports, dest_airports]).drop_duplicates(subset=['airport'])
            
            self.airports_df = all_airports
            print(f"Generated airport data: {len(self.airports_df)} airports")
        else:
            print("Warning: Sample flight data not found, cannot load airport info")
            # 使用预设的机场作为回退
            self.airports_df = pd.DataFrame([
                {'airport': 'PEK', 'latitude': 40.08, 'longitude': 116.59},
                {'airport': 'JFK', 'latitude': 40.64, 'longitude': -73.77},
                {'airport': 'LHR', 'latitude': 51.47, 'longitude': -0.45},
                {'airport': 'MXP', 'latitude': 45.63, 'longitude': 8.72},
                {'airport': 'GRU', 'latitude': -23.43, 'longitude': -46.47},
                {'airport': 'SYD', 'latitude': -33.94, 'longitude': 151.17},
                {'airport': 'JNB', 'latitude': -26.13, 'longitude': 28.24}
            ])
    
    def _calculate_date_range(self):
        """从文件名中解析可用日期范围"""
        parquet_files = list(self.clean_data_dir.glob("flightlist_*.parquet"))

        if not parquet_files:
            print("Warning: No flight data files found")
            self.date_range = None
            return

        dates = []
        for file in parquet_files:
            # 文件名格式: flightlist_YYYYMMDD_YYYYMMDD.parquet
            file_name = file.stem
            # 提取开始日期（第一个日期序列） - 在第二个underscore后面
            parts = file_name.split('_')
            if len(parts) >= 3:
                date_str = parts[1]  # 获取YYYYMMDD格式的开始日期
                try:
                    date = datetime.strptime(date_str, '%Y%m%d')
                    dates.append(date)
                except ValueError:
                    # 备用：检查第三部分
                    try:
                        date_str = parts[2]
                        date = datetime.strptime(date_str, '%Y%m%d')
                        dates.append(date)
                    except ValueError:
                        print(f"警告: 无法解析文件名中的日期: {file_name}")
        
        dates.sort()
        self.date_range = {
            'start': dates[0],
            'end': dates[-1],
            'all_dates': dates
        }
        
        print(f"Date range calculated: {self.date_range['start'].date()} to {self.date_range['end'].date()}")
    
    def get_date_range(self):
        """返回可用的时间范围"""
        if self.date_range is None:
            return None
        
        return {
            'start': self.date_range['start'].isoformat(),
            'end': self.date_range['end'].isoformat(),
            'total_days': (self.date_range['end'] - self.date_range['start']).days + 1
        }
    
    def get_covid_data_for_date(self, date_str):
        """获取指定日期的COVID-19数据 - 带缓存"""
        if self.who_data is None:
            return {'error': 'WHO data not loaded'}

        # 使用缓存
        if date_str in self.covid_cache:
            return self.covid_cache[date_str]

        try:
            date = pd.to_datetime(date_str).date()

            # 按日期过滤数据
            day_data = self.who_data[self.who_data['Date_reported'].dt.date == date]

            if day_data.empty:
                # 如果没有精确匹配，找最近有数据的日期
                available_dates = self.who_data['Date_reported'].dt.date.unique()
                closest_date = min(available_dates, key=lambda d: abs((d - date).days))
                day_data = self.who_data[self.who_data['Date_reported'].dt.date == closest_date]

                if day_data.empty:
                    result = {'date': date_str, 'globalCases': 0, 'countries': []}
                    self.covid_cache[date_str] = result
                    return result

            # 计算全球总病例数（使用累计病例）
            global_cases = day_data['Cumulative_cases'].sum()

            # 整理国家数据
            countries = []
            for _, row in day_data.iterrows():
                # 只包含有病例的国家，并确保所有字段有效
                try:
                    cumulative_cases = int(row['Cumulative_cases']) if pd.notna(row['Cumulative_cases']) else 0

                    if cumulative_cases > 0:  # 只包含有病例的国家
                        # 转换ISO2到ISO3国家代码（WHO数据使用ISO2，GeoJSON使用ISO3）
                        iso2_code = str(row['Country_code']) if pd.notna(row['Country_code']) else 'XXX'
                        iso3_code = self.iso2_to_iso3_mapping.get(iso2_code, iso2_code)  # 如果找不到映射，保持原值

                        # 安全地获取国家名称
                        country_name = str(row['Country']) if pd.notna(row['Country']) else 'Unknown'

                        # 安全地获取新增病例数
                        new_cases = int(row['New_cases']) if pd.notna(row['New_cases']) else 0

                        countries.append({
                            'countryCode': iso3_code,
                            'countryName': country_name,
                            'cases': cumulative_cases,
                            'newCases': new_cases
                        })
                except (ValueError, TypeError) as e:
                    # 如果数据转换失败，跳过这条记录
                    print(f"警告：跳过无效的疫情数据行 - {e}")
                    continue

            # 返回所有有病例的国家（避免数据过大，但确保显示更多国家）
            countries = sorted(countries, key=lambda x: x['cases'], reverse=True)

            # 如果数据量超过200个，只返回前200个
            if len(countries) > 200:
                print(f"Warning: Too many countries ({len(countries)}), limiting to top 200")
                countries = countries[:200]

            result = {
                'date': date.isoformat(),
                'globalCases': int(global_cases),
                'countries': countries
            }

            # 存入缓存
            self.covid_cache[date_str] = result
            return result

        except Exception as e:
            return {'error': str(e)}
    
    def get_flights_for_date(self, date_str, max_flights=50):
        """获取指定日期的航班数据 - 修复日期过滤兼容性问题"""
        try:
            date = pd.to_datetime(date_str).date()

            # 找到对应的Parquet文件（按月存储）
            year_month = date.strftime('%Y%m')
            parquet_file = self.clean_data_dir / f"flightlist_{year_month}01_{year_month}31.parquet"

            if not parquet_file.exists():
                # 尝试查找月份起始日不同的文件（有些月份31天，有些是30天）
                possible_files = list(self.clean_data_dir.glob(f"flightlist_{year_month}*.parquet"))
                if not possible_files:
                    return {'date': date_str, 'flights': [], 'totalFlights': 0}
                parquet_file = possible_files[0]

            try:
                # 尝试使用PyArrow filters进行日期过滤
                target_date_start = pd.Timestamp(date, tz='UTC')
                target_date_end = pd.Timestamp(date + timedelta(days=1), tz='UTC')
                # 读取数据（只选择需要的列）
                df = pd.read_parquet(
                    parquet_file,
                    columns=['origin', 'destination', 'latitude_1', 'longitude_1',
                             'latitude_2', 'longitude_2', 'day'],
                    filters=[
                        ('day', '>=', target_date_start),
                        ('day', '<', target_date_end)
                    ]
                )
                print(f"使用PyArrow filters成功: {len(df)} 条记录")
            except Exception as filter_error:
                # 如果filters失败，回退到读取完整数据后再过滤
                print(f"PyArrow filters失败，使用回退方法: {filter_error}")
                df = pd.read_parquet(
                    parquet_file,
                    columns=['origin', 'destination', 'latitude_1', 'longitude_1',
                             'latitude_2', 'longitude_2', 'day']
                )

                # 将日期列转换为datetime并过滤
                df['day_date'] = pd.to_datetime(df['day']).dt.date
                df = df[df['day_date'] == date]
                df = df.drop('day_date', axis=1)

            if df.empty:
                return {'date': date_str, 'flights': [], 'totalFlights': 0}

            # 随机抽样，避免数据过大
            if len(df) > max_flights:
                df = df.sample(n=max_flights, random_state=42)

            # 转换为前端需要的格式
            flights = []
            for _, row in df.iterrows():
                # 确保所有字段都有有效值（不包括NA/NaN）
                try:
                    # 先检查是否所有坐标值都是有效的数字
                    lon1 = float(row['longitude_1']) if pd.notna(row['longitude_1']) else None
                    lat1 = float(row['latitude_1']) if pd.notna(row['latitude_1']) else None
                    lon2 = float(row['longitude_2']) if pd.notna(row['longitude_2']) else None
                    lat2 = float(row['latitude_2']) if pd.notna(row['latitude_2']) else None

                    # 只有当所有坐标都有效时才添加到结果中
                    if all(v is not None and not pd.isna(v) for v in [lon1, lat1, lon2, lat2]):
                        origin = str(row['origin']).strip() if pd.notna(row['origin']) else 'UNKNOWN'
                        destination = str(row['destination']).strip() if pd.notna(row['destination']) else 'UNKNOWN'

                        flights.append({
                            'source': [lon1, lat1],
                            'target': [lon2, lat2],
                            'origin': origin,
                            'destination': destination
                        })
                except (ValueError, TypeError, AttributeError) as e:
                    # 如果转换失败，跳过这条记录
                    print(f"警告：跳过无效的行数据 - {e}")
                    continue

            return {
                'date': date_str,
                'flights': flights,
                'totalFlights': len(flights)
            }

        except Exception as e:
            print(f"Error loading flights for {date_str}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e), 'date': date_str, 'flights': [], 'totalFlights': 0}
    
    def get_airport_data(self):
        """返回所有机场数据"""
        if self.airports_df is None:
            return []
        
        airports = []
        for _, row in self.airports_df.iterrows():
            try:
                # 安全地获取经纬度，确保是有效的数字
                lon = float(row['longitude']) if pd.notna(row['longitude']) else None
                lat = float(row['latitude']) if pd.notna(row['latitude']) else None

                # 只有当坐标有效时才添加到结果
                if lon is not None and lat is not None and not pd.isna(lon) and not pd.isna(lat):
                    airport_code = str(row['airport']).strip() if pd.notna(row['airport']) else 'UNKNOWN'
                    airports.append({
                        'airport': airport_code,
                        'coords': [lon, lat]  # [经度, 纬度] 格式
                    })
            except (ValueError, TypeError, AttributeError) as e:
                # 如果转换失败，跳过这个机场
                print(f"警告：跳过无效的机场数据 - {e}")
                continue
        
        return airports

    def get_global_trend(self):
        """返回全局疫情趋势（按日期汇总所有国家），带缓存"""
        if self.who_data is None:
            return []
        if self._global_trend_cache is not None:
            return self._global_trend_cache
        try:
            trend_df = self.who_data.groupby('Date_reported').agg(
                globalCases=('Cumulative_cases', 'sum'),
                globalNewCases=('New_cases', 'sum')
            ).reset_index().sort_values('Date_reported')

            result = []
            for _, row in trend_df.iterrows():
                result.append({
                    'date': row['Date_reported'].strftime('%Y-%m-%d'),
                    'globalCases': int(row['globalCases']) if pd.notna(row['globalCases']) else 0,
                    'globalNewCases': int(row['globalNewCases']) if pd.notna(row['globalNewCases']) else 0
                })
            self._global_trend_cache = result
            return result
        except Exception as e:
            print(f"Error computing global trend: {e}")
            return []

    def get_country_history(self, iso3_code):
        """返回指定国家（ISO3代码）的全部历史疫情数据"""
        if self.who_data is None:
            return []
        try:
            iso2_code = None
            for k, v in self.iso2_to_iso3_mapping.items():
                if v == iso3_code:
                    iso2_code = k
                    break
            if iso2_code is None:
                return []

            country_df = self.who_data[
                self.who_data['Country_code'] == iso2_code
            ].sort_values('Date_reported')

            if country_df.empty:
                return []

            result = []
            for _, row in country_df.iterrows():
                entry = {
                    'date': row['Date_reported'].strftime('%Y-%m-%d'),
                    'cases': int(row['Cumulative_cases']) if pd.notna(row['Cumulative_cases']) else 0,
                    'newCases': int(row['New_cases']) if pd.notna(row['New_cases']) else 0,
                }
                for col, key in [('Cumulative_deaths', 'deaths'), ('New_deaths', 'newDeaths')]:
                    if col in self.who_data.columns:
                        entry[key] = int(row[col]) if pd.notna(row[col]) else 0
                result.append(entry)
            return result
        except Exception as e:
            print(f"Error getting country history for {iso3_code}: {e}")
            return []
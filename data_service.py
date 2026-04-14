import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path
import pyarrow.parquet as pq

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
        
        # 读取一个样本月份的数据来获取机场坐标
        sample_file = self.clean_data_dir / "flightlist_20200101_20200131.parquet"
        if sample_file.exists():
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
            # 提取开始日期（第一个日期序列）
            date_str = file_name.split('_')[1]  # 获取YYYYMMDD
            date = datetime.strptime(date_str, '%Y%m%d')
            dates.append(date)
        
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
        """获取指定日期的COVID-19数据"""
        if self.who_data is None:
            return {'error': 'WHO data not loaded'}
        
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
                    return {'date': date_str, 'globalCases': 0, 'countries': []}
            
            # 计算全球总病例数（使用累计病例）
            global_cases = day_data['Cumulative_cases'].sum()
            
            # 整理国家数据
            countries = []
            for _, row in day_data.iterrows():
                if row['Cumulative_cases'] > 0:  # 只包含有病例的国家
                    countries.append({
                        'countryCode': row['Country_code'],
                        'countryName': row['Country'],
                        'cases': int(row['Cumulative_cases']),
                        'newCases': int(row['New_cases']) if pd.notna(row['New_cases']) else 0
                    })
            
            # 返回Top 50严重国家（避免数据过大）
            countries = sorted(countries, key=lambda x: x['cases'], reverse=True)[:50]
            
            return {
                'date': date.isoformat(),
                'globalCases': int(global_cases),
                'countries': countries
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_flights_for_date(self, date_str, max_flights=50):
        """获取指定日期的航班数据"""
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
            
            # 读取Parquet文件并按日期过滤
            # 转换为TAI时间戳以匹配Parquet中的UTC时间格式
            target_date_start = pd.Timestamp(date, tz='UTC')
            target_date_end = pd.Timestamp(date + timedelta(days=1), tz='UTC')
            
            # 读取数据（只选择需要的列）
            df = pd.read_parquet(
                parquet_file,
                columns=['origin', 'destination', 'latitude_1', 'longitude_1', 
                        'latitude_2', 'longitude_2'],
                filters=[
                    ('day', '>=', target_date_start),
                    ('day', '<', target_date_end)
                ]
            )
            
            if df.empty:
                return {'date': date_str, 'flights': [], 'totalFlights': 0}
            
            # 随机抽样，避免数据过大
            if len(df) > max_flights:
                df = df.sample(n=max_flights, random_state=42)  # 使用固定随机种子保证可重复性
            
            # 转换为前端需要的格式
            flights = []
            for _, row in df.iterrows():
                # 确保所有字段都有有效值（不包括NA/NaN）
                if pd.notna(row['latitude_1']) and pd.notna(row['longitude_1']) and \
                   pd.notna(row['latitude_2']) and pd.notna(row['longitude_2']) and \
                   pd.notna(row['origin']) and pd.notna(row['destination']):
                    flights.append({
                        'source': [float(row['longitude_1']), float(row['latitude_1'])],  # [经度, 纬度]
                        'target': [float(row['longitude_2']), float(row['latitude_2'])],
                        'origin': str(row['origin']).strip(),
                        'destination': str(row['destination']).strip()
                    })
            
            return {
                'date': date_str,
                'flights': flights,
                'totalFlights': len(flights)
            }
            
        except Exception as e:
            print(f"Error loading flights for {date_str}: {str(e)}")
            return {'error': str(e), 'date': date_str, 'flights': [], 'totalFlights': 0}
    
    def get_airport_data(self):
        """返回所有机场数据"""
        if self.airports_df is None:
            return []
        
        airports = []
        for _, row in self.airports_df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                airports.append({
                    'airport': row['airport'],
                    'coords': [row['longitude'], row['latitude']]  # [经度, 纬度] 格式
                })
        
        return airports
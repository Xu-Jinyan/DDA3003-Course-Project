"""
将 data/*.csv.gz 转换为 data/clean/*.parquet
只保留 data_service.py 需要的列，节省磁盘空间。

用法:
    python convert_to_parquet.py            # 转换所有文件
    python convert_to_parquet.py --skip     # 跳过已存在的 parquet（断点续传）
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# 只保留 data_service.py 实际读取的列
KEEP_COLS = ['origin', 'destination', 'latitude_1', 'longitude_1',
             'latitude_2', 'longitude_2', 'day']

def convert(src: Path, dst: Path):
    print(f"  读取 {src.name} ...", end=' ', flush=True)
    df = pd.read_csv(src, usecols=KEEP_COLS, parse_dates=['day'])

    # 确保 day 列带 UTC 时区（PyArrow filter 需要带时区的 Timestamp）
    if df['day'].dt.tz is None:
        df['day'] = df['day'].dt.tz_localize('UTC')
    else:
        df['day'] = df['day'].dt.tz_convert('UTC')

    df.to_parquet(dst, index=False, engine='pyarrow')
    mb = dst.stat().st_size / 1024 / 1024
    print(f"完成 ({len(df):,} 行, {mb:.1f} MB)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', action='store_true', help='跳过已存在的 parquet 文件')
    args = parser.parse_args()

    data_dir  = Path('data')
    clean_dir = Path('data/clean')
    clean_dir.mkdir(exist_ok=True)

    files = sorted(data_dir.glob('flightlist_*.csv.gz'))
    if not files:
        print('未找到 csv.gz 文件，请确认运行目录为项目根目录。')
        sys.exit(1)

    print(f'找到 {len(files)} 个文件，输出目录: {clean_dir}\n')
    ok = skipped = failed = 0

    for src in files:
        dst = clean_dir / (src.stem.replace('.csv', '') + '.parquet')
        if args.skip and dst.exists():
            print(f"  跳过 {src.name}（已存在）")
            skipped += 1
            continue
        try:
            convert(src, dst)
            ok += 1
        except Exception as e:
            print(f"  失败: {e}")
            failed += 1

    print(f'\n完成: {ok} 成功 / {skipped} 跳过 / {failed} 失败')

if __name__ == '__main__':
    main()

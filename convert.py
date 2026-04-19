#!/usr/bin/env python3
"""
日別売上CSVをdata/sales.jsonに変換するスクリプト
GitHub Actionsから自動実行される
"""
import csv, io, json, glob, os, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CSV_DIR = ROOT / "csv"
OUT_FILE = ROOT / "data" / "sales.json"

PRESIDENT_CODES = {'101','102','103','109','111','113','112','034'}  # 第2営業部：ぷれじでんと系＋琥虎ノ門＋華恵比寿
SUMI_CODES = {'704'}
# ららぽーと甲子園(702)は第1営業部に統合

def get_division(store_code, gyotai):
    if gyotai == '千房FC':
        return 'FC'
    if gyotai == '千房フロンティア':
        return 'IZAKAYA'
    if store_code in SUMI_CODES:
        return 'おでんすみ吉'
    if store_code in PRESIDENT_CODES:
        return '第2営業部'
    return '第1営業部'

def safe_float(v):
    try:
        return float(v) if v and v.strip() else 0.0
    except:
        return 0.0

def parse_csv(path):
    records = []
    for enc in ('cp932', 'utf-8-sig', 'utf-8'):
        try:
            with open(path, 'rb') as f:
                raw = f.read()
            text = raw.decode(enc)
            reader = csv.DictReader(io.StringIO(text))
            for r in reader:
                if r.get('売上分類', '').strip() != '計':
                    continue
                sc = r.get('店舗コード', '').strip()
                gyotai = r.get('業態名称', '').strip()
                date = r.get('営業日', '').strip()
                if not date:
                    continue
                records.append({
                    '_id': f'{date}_{sc}',
                    'date': date,
                    'ym': date[:7],
                    'dow': r.get('曜日', ''),
                    'dow_type': r.get('曜日区分', ''),
                    'gyotai': gyotai,
                    'store_code': sc,
                    'store': r.get('店舗名称', '').strip(),
                    'division': get_division(sc, gyotai),
                    'sales': safe_float(r.get('売上実績')),
                    'sales_budget': safe_float(r.get('売上月次予算')),
                    'sales_prev': safe_float(r.get('売上前年')),
                    'customers': safe_float(r.get('客数実績')),
                    'customers_budget': safe_float(r.get('客数月次予算')),
                    'customers_prev': safe_float(r.get('客数前年')),
                    'unit_price': safe_float(r.get('客数客単価')),
                })
            return records
        except Exception as e:
            continue
    print(f"  WARNING: {path} を読み込めませんでした", file=sys.stderr)
    return []

def main():
    csv_files = sorted(glob.glob(str(CSV_DIR / "*.csv")))
    if not csv_files:
        print("csvフォルダにCSVファイルがありません")
        sys.exit(1)

    all_records = {}
    total = 0
    for path in csv_files:
        print(f"処理中: {os.path.basename(path)}")
        records = parse_csv(path)
        for r in records:
            key = f"{r['date']}_{r['store_code']}"
            all_records[key] = r
        total += len(records)
        print(f"  → {len(records)}件読み込み")

    records_list = sorted(all_records.values(), key=lambda r: (r['date'], r['store_code']))

    dates = sorted(set(r['date'] for r in records_list))
    stores = sorted(set(r['store'] for r in records_list))

    meta = {
        'generated_at': __import__('datetime').datetime.now().isoformat(),
        'total_records': len(records_list),
        'date_range': {'start': dates[0] if dates else '', 'end': dates[-1] if dates else ''},
        'total_stores': len(stores),
        'total_files': len(csv_files),
    }

    output = {'meta': meta, 'records': records_list}
    OUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    print(f"\n完了: {len(records_list)}件 → data/sales.json")
    print(f"期間: {meta['date_range']['start']} 〜 {meta['date_range']['end']}")

if __name__ == '__main__':
    main()

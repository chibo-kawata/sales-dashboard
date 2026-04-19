#!/usr/bin/env python3
"""
日別売上CSVをindex.htmlに直接埋め込むスクリプト
GitHub Actionsから自動実行される
csv/ フォルダの全CSVを読み込み → index.htmlのデータを更新
"""
import csv, io, json, glob, os, sys, re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
CSV_DIR  = ROOT / "csv"
HTML_FILE = ROOT / "index.html"
JSON_FILE = ROOT / "data" / "sales.json"

PRESIDENT_CODES = {'101','102','103','109','111','113','112','034'}
SUMI_CODES = {'704'}

def get_division(store_code, gyotai):
    if gyotai == '千房FC':       return 'FC'
    if gyotai == '千房フロンティア': return 'IZAKAYA'
    if store_code in SUMI_CODES:  return 'おでんすみ吉'
    if store_code in PRESIDENT_CODES: return '第2営業部'
    return '第1営業部'

def safe_float(v):
    try:
        s = str(v).strip().replace(',','').replace('－','0').replace('-','0').replace('−','0')
        return float(s) if s else 0.0
    except:
        return 0.0

def normalize_date(d):
    """日付を YYYY/MM/DD 形式に統一"""
    d = d.strip()
    for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%Y%m%d'):
        try:
            return datetime.strptime(d, fmt).strftime('%Y/%m/%d')
        except:
            continue
    return d

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
                sc    = r.get('店舗コード', '').strip()
                gyotai = r.get('業態名称', '').strip()
                date  = r.get('営業日', '').strip()
                if not date:
                    continue
                date = normalize_date(date)
                ym   = date[:7]  # YYYY/MM
                sales = safe_float(r.get('売上実績'))
                cust  = safe_float(r.get('客数実績'))
                records.append({
                    '_id': f'{date}_{sc}',
                    'date': date,
                    'ym': ym,
                    'dow': r.get('曜日', '').strip(),
                    'dow_type': r.get('曜日区分', '').strip(),
                    'gyotai': gyotai,
                    'store_code': sc,
                    'store': r.get('店舗名称', '').strip(),
                    'division': get_division(sc, gyotai),
                    'sales': sales,
                    'sales_budget': safe_float(r.get('売上月次予算')),
                    'sales_prev': safe_float(r.get('売上前年')),
                    'customers': cust,
                    'customers_budget': safe_float(r.get('客数月次予算')),
                    'customers_prev': safe_float(r.get('客数前年')),
                    'unit_price': round(sales / cust, 1) if cust > 0 else 0.0,
                })
            return records
        except Exception as e:
            continue
    print(f"  WARNING: {path} 読み込み失敗", file=sys.stderr)
    return []

def embed_into_html(records, meta):
    """index.html の _SALES_RECORDS / _SALES_META を新データで置換"""
    if not HTML_FILE.exists():
        print("ERROR: index.html が見つかりません", file=sys.stderr)
        sys.exit(1)

    html = HTML_FILE.read_text(encoding='utf-8')
    records_json = json.dumps(records, ensure_ascii=False, separators=(',',':'))
    meta_json    = json.dumps(meta,    ensure_ascii=False, separators=(',',':'))

    html = re.sub(r'window\._SALES_META = \{.*?\};',
                  f'window._SALES_META = {meta_json};', html)
    html = re.sub(r'window\._SALES_RECORDS = \[.*?\];',
                  f'window._SALES_RECORDS = {records_json};',
                  html, flags=re.DOTALL)

    HTML_FILE.write_text(html, encoding='utf-8')
    print(f"index.html 更新完了 ({len(html):,} bytes)")

def main():
    csv_files = sorted(glob.glob(str(CSV_DIR / "*.csv")))
    if not csv_files:
        print("csvフォルダにCSVファイルがありません")
        sys.exit(1)

    all_records = {}
    for path in csv_files:
        print(f"処理中: {os.path.basename(path)}")
        recs = parse_csv(path)
        for r in recs:
            all_records[r['_id']] = r
        print(f"  → {len(recs)}件")

    records_list = sorted(all_records.values(), key=lambda r: (r['date'], r['store_code']))
    dates  = sorted(set(r['date'] for r in records_list))
    stores = set(r['store'] for r in records_list)

    meta = {
        'generated_at': datetime.now().isoformat(),
        'total_records': len(records_list),
        'date_range': {'start': dates[0] if dates else '', 'end': dates[-1] if dates else ''},
        'total_stores': len(stores),
        'total_files': len(csv_files),
    }

    # sales.json も更新（バックアップ用）
    JSON_FILE.parent.mkdir(exist_ok=True)
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump({'meta': meta, 'records': records_list}, f, ensure_ascii=False, separators=(',',':'))

    # index.html にデータ埋め込み
    embed_into_html(records_list, meta)

    print(f"\n✅ 完了: {len(records_list)}件")
    print(f"   期間: {meta['date_range']['start']} 〜 {meta['date_range']['end']}")
    print(f"   店舗: {len(stores)}店")

if __name__ == '__main__':
    main()

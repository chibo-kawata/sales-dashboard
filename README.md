# 売上サマリーダッシュボード

千房グループ 日別売上実績ダッシュボード

## データ更新方法

### 方法①：GitHubのブラウザで更新（推奨・PCのみ）

1. GitHubリポジトリを開く
2. `csv/` フォルダをクリック
3. 右上の **「Add file」→「Upload files」** をクリック
4. 日別売上CSVをドラッグ＆ドロップ
5. 下部の **「Commit changes」** ボタンを押す
6. 約1〜2分後にダッシュボードへ反映

### 方法②：手動でActionsを実行

1. GitHubリポジトリの **「Actions」** タブを開く
2. 左メニューの **「Update Sales Data」** をクリック
3. **「Run workflow」** → **「Run workflow」** ボタンを押す

## ファイル構成

```
csv/         ← 日別CSVをここに置く（ShiftJIS対応）
data/        ← 変換済みJSON（自動生成・触らない）
scripts/     ← 変換スクリプト
index.html   ← ダッシュボード本体
```

## CSVの注意事項

- ファイル名は何でもOK（例：`日別売上実績表_20260501.csv`）
- 文字コードは ShiftJIS / UTF-8 どちらも対応
- `売上分類 = 計` の行のみ使用
- 同じ日付のデータは新しいCSVで上書きされる

## GitHub Pages 設定

Settings → Pages → Source: `Deploy from branch` → Branch: `main` `/root`

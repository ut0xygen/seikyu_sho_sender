# S3 (Seikyu-Sho Sender)

## 出来ること

- 請求書を自動生成（template.html のプレースホルダーをコンフィグの内容で置換）
- Chrome を使って前工程の HTML を PDF で出力
- .env で設定した SMTP サーバを経由してコンフィグで指定したメールアドレスに請求メールを送信

## Python 開発環境セットアップ　 on Windows (cmd.exe)

### uv をインストール

```shell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
powershell -c "[System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + '\.local\bin;' + [System.Environment]::GetEnvironmentVariable('path', 'User'), 'User')"
```

### プロジェクトを初期化

```shell
uv sync
```

### プロジェクトを初期化（メモ）

空ディレクトリから開発を始めるまでに打ったコマンドを念のためメモしておく。

```shell
# プロジェクトを初期化
uv init

# NOTE: インストールされている Python バージョン一覧を表示する。
#       uv python list
# NOTE: インストール可能な Python バージョン一覧を表示する。
#       uv python list --all-versions
# プロジェクトで使用する Python バージョンを指定
uv python pin 3.13.2
uv sync

# パッケージをインストール
uv add python-dotenv
```

### 実行

#### .env, configs/config.json, main.py を自分の環境に合わせて変更

- .env はメールサーバに接続するための情報、Google Chrome のパスを設定するファイル。（.env.example を参照）
- configs/config.json は請求情報を設定するファイル。（configs/config_example.json を参照）
- main.py はメインコードだが、署名に仮データが埋め込まれているため、任意のデータに置き換える必要がある。

#### コマンドラインから実行

```shell
uv run main.py configs/config_example.json
```

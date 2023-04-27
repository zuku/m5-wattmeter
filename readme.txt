m5-wattmeter
-----

M5StickC Plus + Wi-SUN HATキットを使用して家庭用の電力メーターから取得した情報を表示するアプリケーション

プロジェクトページ
https://github.com/zuku/m5-wattmeter

# 動作環境
* M5StickC Plus 1.1
  * Wi-SUN通信モジュール BP35A1
  * Wi-SUN HATキット
* UIFlow_StickC_Plus v.1.11.5


# ファイル構成
```
─ /
  ├ misc/
  │  ├ wattmeter.py
  │  └ wmconfig.full.json
  ├ release/
  │  ├ apps/
  │  │  └ m5wm.py
  │  ├ wattmeter.mpy
  │  └ wmconfig.json
  ├ LICENSE
  └ readme.txt
```

## ファイル,ディレクトリの説明
* /misc/wattmeter.py
  * wattmeter.mpyの生成元ファイル
  * デバッグ等に使用
* /misc/wmconfig.full.json
  * 全項目を記述した設定サンプルファイル
* /release/
  * M5StickC Plusに転送するファイルを格納したディレクトリ
* /release/apps/m5wm.py
  * アプリケーション起動時に実行するPythonファイル
* /release/wattmeter.mpy
  * アプリケーションの主要な処理が実装された.mpyファイル
  * wattmeter.pyから生成されたバイナリコンテナファイル
* /release/wmconfig.json
  * 必須項目のみが記述されたアプリケーションの設定サンプルファイル
  * 内容を書き換えてからM5StickC Plusに転送する
* LICENSE
  * ライセンスファイル
* readme.txt
  * このファイル


# 使用方法
1. 電力会社にスマートメーターのBルート使用開始を申し込みIDとパスワードを取得する
2. M5StickC PlusにUIFlow_StickC_Plusファームウェアを書き込む
3. Wi-SUN HATキットを組み立てM5StickC Plusに接続する
4. 取得したBルートID,パスワード及び契約アンペア数を元に設定ファイルを書き換える
5. コンピュータ(Windows/Mac等)からM5StickC Plusに必要なファイルを転送する
6. M5StickC PlusのAPPモードでアプリケーションを起動する

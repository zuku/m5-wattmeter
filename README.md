M5 Wattmeter
-----

M5 WattmeterはM5StickC Plusで消費電力量等を表示するアプリケーションです。

rin_ofumi氏製作の[Wi-SUN HATキット](https://kitto-yakudatsu.com/archives/7206)を使用するアプリケーションの実装のひとつです。
MicroPythonで実装されています。

<img src="https://user-images.githubusercontent.com/359700/231117382-a7e43c4f-b37d-44df-bb3f-8dd4244f88b5.jpg" width="400">

# 特徴

* フリッカーフリー表示
* 注意, 警告時に表示変更とビープ音
* 画面消灯のスケジュール指定
* 複数の画面表示方法
* Wi-Fi接続先を設定ファイルから指定可能

# 動作環境

* M5StickC Plus 1.1
    * Wi-SUN HATキット
    * Wi-SUN対応無線モジュール ROHM BP35A1
* UIFlow_StickC_Plus v1.11.5
    * (MicroPython 1.12)

設置されている電力メーターが920MHz帯のWi-SUN規格の無線を使用するスマートメーターである必要があります。

# 使用方法

1. 電力会社にBルートの使用開始申請を行いID, パスワードを取得する
2. 必要なハードウェアを揃えて組み立てる
3. M5StickC PlusにUIFlow_StickC_Plusファームウェアを書き込む
4. M5 Wattmeterパッケージを[ダウンロード](https://github.com/zuku/m5-wattmeter/releases/latest)する
5. 取得したBルートID, パスワードと契約アンペア数をもとに設定ファイルを書き換える
6. M5StickC PlusとコンピュータをUSB接続してパッケージ内の必要なファイルを転送する
7. M5StickC PlusのAPPモードでM5 Wattmeterアプリケーションを起動する

詳細についてはWikiの[準備](https://github.com/zuku/m5-wattmeter/wiki/Preparation)と[使用方法](https://github.com/zuku/m5-wattmeter/wiki/Usage)を参照してください。

# ライセンス

M5 WattmeterにはMITライセンスが適用されます。

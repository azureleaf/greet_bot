# バス検索用 LINE ボット

あなたの現在地と目的地の GPS 情報を伝えると、その検索時刻の時点で最善のバス停を教えてくれます。（※現時点ではバス停検索のみ。時刻検索部分は実装中）

## Description

出発地バス停と目的地バス停を指定すると、最短ルートを教えてくれる web サービスは既にあります。しかし「自分がどのバス停から乗るべきなのか、どこで降りるべきなのか、がそもそもわからない」という場面は多いです。見知らぬ土地にいるときや、付近に複数のルート候補があるときなどには尚更です。

- バス停の GPS 座標情報は、国土交通省国土数値情報の宮城県内バス停留所データに拠ります。元データの XML 形式は扱いにくいので、`process_xml.py`で SQLite DB に変換しています。
- 現在の天気情報は OpenWeather API から取得します。

![スクリーンショット](screenshot.jpg)

## Requirements

1. `pipenv shell`
1. `pipenv install`

## Usage: Deploy on Heroku

1. LINE Developer と OpenWeather のアカウントを作り、新しい LINE ボットを作成します。
1. このプログラムを Heroku などにデプロイします。
1. アカウント作成時に発行された API キーをサーバの環境変数に設定します。
   - OpenWeather の API キー
   - LINE アクセストークン
   - LINE チャンネル ID
1. bot を LINE の友だちに追加します。
   - 位置情報を送ると、近辺のバス停とそこまでの直線距離を返します。
   - 「天気」という単語を含むメッセージを送ると、現在の仙台の気温と天気を返します。

## Usage: Parse Original Data

- Create SQLite DB `positions.db` at root directory first

### Save subway timetables to SQLite

1. `python3 get_subway_timetable.py`

### Save positions of subway stations & bus stops to SQLite

1. Download the source data:
   - [国土数値情報　バス停留所データ](http://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P11.html)
   - [国土数値情報　鉄道データ](http://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v2_3.html)
2. Locate the files in `constants.py`
3. `python3 get_busstop_pos.py`
4. `python3 get_station_pos.py`

## Dev Notes

### Run Flask

1. `export FLASK_APP=app.py`
1. `flask run` (`python3 app.py` is deprecated)

## Todo

- 目的地情報を入力させる欄を作る
- 現在地から直近バス停までのルートについては、Google Map アプリにデータを投げてスマホに表示するようにする
- 時刻検索機能をつける
  - 宮城交通や仙台市交通局は時刻表データの一括ダウンロードデータなどを公開していないので、NAVITIME にクエリ（出発地&目的地バス停）を投げて、検索結果のウェブページをがんばって Scraping するしかなさそう
  - もしくは、仙台市交通局ウェブサイトのクローラを作り、時刻表データを力技で収集する。（やりすぎたら IP が ban されそうだが）
- 自然言語処理系の学習済みモデルなどを使って、もうちょっと高度な会話をしてほしい
  - Hachidori とか、Dialogflow とか、そのへん

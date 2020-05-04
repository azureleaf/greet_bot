# 仙台生活ユーティリティ LINE ボット

- 話しかけると、仙台の現在の天気情報と６時間毎の予報をダイジェストで教えてくれます。
- 現在地の GPS 情報を伝えると、そこから近い地下鉄駅の名前と直線距離、および直近の発車時刻を教えてくれます。
- 現在地の GPS 情報を伝えると、そこから近いバス停の名前と直線距離を教えてくれます。

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
2. `export FLASK_DEBUG=1`
3. `flask run` (`python3 app.py` is deprecated)

### LINE Messaging API

- `event.reply_token`
  - Reply token is required to reply
  - Reply token changed every time you get the message
  - Reply token can be used only once
  - Reply token expires soon; reply as quickly as possible

### Visit LINE developer website

- Note "LINE Channel Secret"
- Note "LINE Channel Access Token"
- Webhook URL
  - `https://appnamehere.herokuapp.com/callback`

### Heroku Setup

- ~~`pip freeze >> requirements.txt`~~ (Seemingly, Heroku can detect Pipfile)
- `echo web: gunicorn app:app --log-file - >> Procfile`
- `echo python-3.7.6 >> runtime.txt`
  - Note that some Python versions aren't available on Heroku
- Turn on / off the web app
  - `heroku ps:scale web=1 -a appnamehere` or start on Heroku website
  - `heroku ps:scale web=0 -a appnamehere` or stop on Heroku website
- `heroku config:set LINE_CHANNEL_SECRET=foo`
- `heroku config:set LINE_CHANNEL_ACCESS_TOKEN=bar`
- Set OpenWeather API key as well
- Add `.slugignore` and specify files which aren't necessary for the bot app
- `heroku open -a appnamehere`
  - Check if it shows "hello world"

### gunicorn

- HTTP WSGI server for Python
- WSGI (Web Server Gateway Interface) is an interface for Python
- WSGI links Web Server & Web app
- Flask development server can't be used for production, so you need this

### Test app before deploying to Heroku

1. `sudo snap install ngrok`
2. `ngrok http 5000` (5000 is the flask port num)
3. Write down the HTTPS address shown on the terminal: e.g. `https://abc123xy.ngrok.io/`
4. Set the webhook URL on LINE developer page: `https://abc123xy.ngrok.io/callback`
   - Because routing is `@app.route("./callback")` in my `app.py`
5. Run Flask

- Trouble Shooting: `Address already in use` on `flask run`

1. `netstat -tulpn | grep LISTEN` to find the Flask run process
2. `kill -9` that process

### Deploy to Heroku

1. `sudo snap install --classic heroku` : Install Heroku CLI on Ubuntu
2. `heroku login` for the 1st time; you'll be prompted to login on the browser
3. Setup project
   - `heroku create my_heroku_app` if you create the project
   - ~~`heroku git:clone -a my_heroku_app` if you need to clone from Heroku~~ (According to Heroku doc, this is NOT RECOMMENDED)
   - `git remote add heroku https://git.heroku.com/my_heroku_app.git` if you push the existing project
4. `git push heroku master`

- `heroku logs --tail -a appnamehere`
  - Show realtime log

## Reference

- LINE Bot SDK: https://github.com/line/line-bot-sdk-python/blob/master/examples/flask-kitchensink/app.py

## Todo

- 目的地情報を入力させる欄を作る
- 現在地から直近バス停までのルートについては、Google Map アプリにデータを投げてスマホに表示するようにする
- 時刻検索機能をつける
  - 宮城交通や仙台市交通局は時刻表データの一括ダウンロードデータなどを公開していないので、NAVITIME にクエリ（出発地&目的地バス停）を投げて、検索結果のウェブページをがんばって Scraping するしかなさそう
  - もしくは、仙台市交通局ウェブサイトのクローラを作り、時刻表データを力技で収集する。（やりすぎたら IP が ban されそうだが）
- 自然言語処理系の学習済みモデルなどを使って、もうちょっと高度な会話をしてほしい
  - Hachidori とか、Dialogflow とか、そのへん

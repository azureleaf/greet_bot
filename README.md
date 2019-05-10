バス検索用LINEボット
====

あなたの現在位置の情報、目的地のGPS情報を伝えると、その時点で最短のバス停を教えてくれます。（現時点ではバス停検索のみ、時刻検索部分は実装中）

## Description

出発地バス停と目的地バス停を指定すると最短ルートを教えてくれるwebサービスは既にあります（NAVITIMEなど）。しかし、実用上は「自分がそもそもどのバス停から乗るべきなのか、どこで降りるべきなのか、よくわからない」などという場面が多いです。自分が新しい土地にいるときや、付近に複数のバス路線系統があるために時間帯によって乗るべきバス停が変わってくるときなどには尚更です。

バス停のGPS位置情報については、国土交通省の国土数値情報の宮城県内バス停留所データを利用します（ただし、2010年時点でのデータ）。提供されているXML形式は扱いにくいので、`process_xml.py`ではsqliteのデータベースに変換しています。

またOpenWeather APIにより、現在の天気情報等も取得します。

## Usage

1. LINE Developerアカウントを作り、新しいボットを作成します。
1. このプログラムをHerokuなどにデプロイします。
1. 発行されたLINEアクセストークンとLINEチャンネルIDをサーバの環境変数に設定します。
1. botをLINEの友だちに追加します。
    - 位置情報を送ると、近辺のバス停とそこまでの直線距離を返します。
    - 「天気」という単語を含むメッセージを送ると、現在の仙台の気温と天気を返します。


## Requirements

`requirement.txt`を参照

## Todo 

- 目的地情報を入力させる欄を作る
- 現在地から直近バス停までのルートについては、Google Mapアプリにデータを投げてスマホに表示するようにする
- 時刻検索機能をつける
    - 宮城交通や仙台市交通局は時刻表データの一括ダウンロードデータなどを公開していないので、NAVITIMEにクエリ（出発地&目的地バス停）を投げて、検索結果のウェブページをがんばってScrapingするしかなさそう
    - もしくは、仙台市交通局ウェブサイトのクローラを作り、時刻表データを力技で収集する。（やりすぎたらIPがbanされそうだが）
- 自然言語処理系の学習済みモデルなどを使って、もうちょっと高度な会話をしてほしい
    - Hachidoriとか、Dialogflowとか、そのへん
- 天気予報、熱中症アドバイスとかも一応つけたい
- Google Calenderの予定確認とか、離れた場所にあるラズパイを操作するとか、実用的な機能をボットにつけたい
- Slack向けボットも作る

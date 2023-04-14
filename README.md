# ShutterDiary

『ShutterDiary』は写真を気軽に公開・共有できる画像ブログアプリです。

PythonのWebアプリケーションフレームワーク、Flaskで制作されています。

主な機能は下記の通りです。

- 会員登録（アカウントの作成）
- アカウント情報の変更・削除
- ログイン・ログアウト
- 記事の作成
- 作成済み記事の編集・削除
- コメント投稿
- キーワード検索
- サムネイルの自動生成

なお、トップページのヘッダー画像は、商用無料の画像素材サイトの『Unsplash』様よりお借りしたものです。  
画像の著作権は著作者に帰属します。

https://unsplash.com/

---

## 使用しているフレームワーク・ライブラリ

- Python
    - Flask
    - Flask-SQLAlchemy
    - Flask-Login
    - Pillow

- JavaScript
    - JQuery
    - jquery-pwd-measure

- CSS
    - Bootstrap

---

## ローカルでの実行方法
1. ShutterDiaryフォルダの直下に仮想環境を構築します。
    > python -m venv .venv 

2. 仮想環境を実行します。
    - Mac
        > source .venv/bin/activate 

    - Windows
        > .venv\Scripts\activate.bat
3. 必要なライブラリをインストールします。
    >pip install -r requirements.txt
4. 簡易サーバーを立ち上げます。
    - Mac
        >export FLASK_APP=flask_app  
        >flask run
    - Windows
        >set FLASK_APP=flask_app  
        >flask run"# ShutterDiary" 
"# ShutterDiary" 

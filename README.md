## ShutterDiary

『ShutterDiary』は写真を気軽に公開・共有できるブログアプリです。

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

### 使用しているフレームワーク・ライブラリ

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

### ローカルでの実行方法
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
        >flask run

---

## ShutterDiary

_ShutterDiary_ is a blog app where you can easily post and share your photos.

This app is made with Flask, a web application flamework for Python.

The main functions are as follows:

- Signup（Create an account）
- Edit and delete the account information
- Login and Logout
- Create articles
- Edit and delete posted articles
- Post comments
- Search by keywords
- Generate thumbnails automatically

The header image on the top page is bollowed from Unsplash, a stock photography site whose images are free for commercial use.
All images are copyright to their respective owners.

https://unsplash.com/

---

## Used Frameworkds and Libraries

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

## How to run locally
1. Create an virtual enviroment directly under ShutterDiary folder.
    > python -m venv .venv 

2. Activate the virtual enviroment.
    - Mac
        > source .venv/bin/activate 

    - Windows
        > .venv\Scripts\activate.bat
        
3. Install all required libraries.
    >pip install -r requirements.txt
    
4. Run the builtin server.
    - Mac
        >export FLASK_APP=flask_app  
        >flask run
    - Windows
        >set FLASK_APP=flask_app  
        >flask run

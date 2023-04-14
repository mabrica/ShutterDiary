from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import and_, or_, desc
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest
from imghdr import what
from datetime import datetime
from uuid import uuid1
from PIL import Image
import re
import os


#### Flaskオブジェクトの生成 ####
app = Flask(__name__, static_folder='static', template_folder='templates')


#### SQLAlchemy ####
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
# app.config['SECRET_KEY'] = os.urandom(24)
app.config['SECRET_KEY'] = "hogehogehogehoge"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)


### DB初期化 ###
@app.before_first_request
def init():
    db.create_all()


### ログインマネージャ ###
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


### テーブル定義 ###
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    email = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    profile = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.Text)
    deleted_at = db.Column(db.Text)

class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    original_filename = db.Column(db.Text)
    saved_filename = db.Column(db.Text)
    thumbnail_filename = db.Column(db.Text)
    category_id = db.Column(db.Integer)
    tags = db.Column(db.Text)
    is_private = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.Text)
    deleted_at = db.Column(db.Text)

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.Text, nullable=False)

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.Text, nullable=False)


### 定数 ###
USER_IMG_DIR = os.path.join('static', 'user_img')
USER_THUMBNAILS_DIR = os.path.join('static', 'user_thumbnails')
USER_AVATAR_DIR = os.path.join('static', 'avatars')
THUMBNAIL_WIDTH = 480
THUMBNAIL_HEIGHT = 360
AVATAR_SIZE = 200
ITEMS_PER_PAGE = 12


### トップページ ###
@app.route('/')
def index():

    posts = Post.query.filter(Post.deleted_at == None, Post.saved_filename != None,\
        Post.is_private == 0).order_by(desc(Post.id)).limit(12).all()

    return render_template(
        'index.html',
        posts=posts
        )

### ヘルプページ ###
@app.route('/help')
def help():

    return render_template('help.html')


### 会員登録ページ ###
@app.route('/signup', methods=['POST', 'GET'])
def signup():

    # 変数の初期化
    email = ''
    username = ''
    password = ''
    password2 = ''
    is_valid = {}
    is_valid['email'] = ''
    is_valid['username'] = ''
    is_valid['password'] = ''
    is_valid['password2'] = ''
    email_exists = False
    username_exists = False
    exceeds_text_limit = {}
    is_not_email = False
    is_mismatched = False

    if request.method == 'POST':

        # 入力値を取得
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        password2 = request.form.get('password2', '').strip()

        # 確認画面
        if request.form.get('mode') == 'confirm':

            # バリデーション
            validate = ValidateSignup(email, username, password, password2)
            errors, is_valid, is_not_email, email_exists, username_exists, \
                exceeds_text_limit, is_mismatched = validate.get_results()

            # バリデーションに問題が無ければ、確認画面を表示
            if errors == 0:
                return render_template(
                    'signup_confirm.html',
                    email=email,
                    username=username,
                    password=password,
                    password2=password2
                    )

        # 登録ボタンが押されたら完了画面を表示
        if request.form.get('mode') == 'completed':

            # 再バリデーション
            validate = ValidateSignup(email, username, password, password2)
            errors, is_valid, is_not_email, email_exists, username_exists, \
                exceeds_text_limit, is_mismatched = validate.get_results()

            # 再バリデーションに問題が無ければ、完了画面を表示
            if errors == 0:
                created_at = datetime.now()
                user = User(
                    email=email,
                    username=username,
                    password=generate_password_hash(password, method='sha256'),
                    created_at=created_at
                    )
                try:
                    db.session.add(user)
                    db.session.commit()
                    return render_template('signup_completed.html', username=username)
                except:
                    # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                    db.session.rollback()
                    return render_template('error.html')
            else:
                # 再バリデーションに問題があればエラー画面表示
                return render_template('page_not_found.html')

    # フォーム画面を表示
    return render_template(
        'signup_terms.html',
        email=email,
        username=username,
        password=password,
        password2=password2,
        is_valid=is_valid,
        email_exists=email_exists,
        username_exists=username_exists,
        exceeds_text_limit=exceeds_text_limit,
        is_not_email=is_not_email,
        is_mismatched=is_mismatched
        )


### ログインページ ###
@app.route('/login', methods=['POST', 'GET'])
def login():

    # 変数の初期化
    email = ''
    password = ''
    is_valid = {}
    is_valid['email'] = ''
    is_valid['password'] = ''
    email_notfound = False
    is_not_email = False
    is_wrong_password = False
    remember = False

    # ログインフォーム以外からのPOST情報を受け取らない
    if request.method == 'POST' and request.form.get('mode') == 'login':

        # 入力値を取得
        email = request.form.get('email','')
        password = request.form.get('password','')
        remember = request.form.get('remember-me', 0)

        # ユーザー情報
        user = User.query.filter_by(email=email).one_or_none()

        # バリデーション
        validate = ValidateLogin(email, password)
        errors, is_valid, email_notfound, is_not_email, is_wrong_password = validate.get_results()

        # バリデーションに問題がなければログイン
        if errors == 0:
            login_user(user, remember=remember)
            return redirect('/')

    # ログイン画面を表示
    return render_template(
        'login.html',
        email=email,
        password=password,
        is_valid=is_valid,
        email_notfound=email_notfound,
        is_not_email=is_not_email,
        is_wrong_password=is_wrong_password,
        remember=remember
        )


### ログアウト ###
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


### 記事の作成 ###
@app.route('/create', methods=['POST', 'GET'])
@login_required
def create():

    # 変数の初期化
    file = None
    title = ''
    body = ''
    category_id = 0
    tags = ''
    tag_list = []
    is_private = 0
    is_valid = {}
    is_valid['file'] = ''
    is_valid['body'] = ''
    is_valid['tags'] = ''
    is_not_image = False
    exceeds_text_limit = {}
    exceeds_tags_limit = 0
    errors = 0

    # カテゴリー一覧取得
    categories = Category.query.all()

    if request.method == "POST":

        # 確認画面
        if request.form.get('mode') == 'confirm':

            # 入力値を取得
            file = request.files.get('file', None)
            title = request.form.get('title', '')
            body = request.form.get('body','')
            category_id = int(request.form.get('category_id', 0))
            tags = request.form.get('tags','')
            is_private = int(request.form.get('is_private', 0))

            # バリデーション
            validate = ValidatePost(file, title, body, tags, check=True)
            errors, is_valid, is_not_image, exceeds_text_limit, exceeds_tags_limit = validate.get_results()

            # バリデーションに問題が無い場合
            if errors == 0:

                # 画像ファイルがあれば、仮のファイル名で保存
                if file:
                    original_filename = secure_filename(file.filename) #ファイル名をサニタイズ
                    extension = get_extension(original_filename)
                    temp_filename = f"temp_{current_user.id}{extension}"
                    file_path = os.path.join(USER_IMG_DIR, temp_filename)
                    file.save(file_path)
                    file_path = '../' + convert_separators(file_path)
                else:
                    original_filename = ''
                    extension = ''
                    temp_filename = ''
                    file_path = ''

                # カテゴリーが選択されていれば、カテゴリー名を取得
                if category_id:
                    selected_category = Category.query.filter_by(id=category_id).one_or_none()
                    category_name = selected_category.name
                else:
                    category_name = ''

                # タグがあれば、リストに分割
                if tags:
                    tag_list = tags.split()

                #確認画面のレンダリング
                return render_template(
                    'create_confirm.html',
                    original_filename=original_filename,
                    temp_filename=temp_filename,
                    extension=extension,
                    file_path=file_path,
                    title=title,
                    body=body,
                    category_id=category_id,
                    category_name=category_name,
                    tags=tags,
                    tag_list=tag_list,
                    is_private=is_private,
                    )

        # 投稿完了
        if request.form.get('mode') == 'completed':

            #前画面から値を継承
            original_filename = secure_filename(request.form.get('original_filename'))
            temp_filename = request.form.get('temp_filename')
            extension = request.form.get('extension')
            title = request.form.get('title')
            body = request.form.get('body')
            category_id = int(request.form.get('category_id'))
            tags = request.form.get('tags')
            is_private = request.form.get('is_private')

            # 再バリデーション
            validate = ValidatePost(file, title, body, tags, check=False)
            errors, is_valid, is_not_image, exceeds_text_limit, exceeds_tags_limit = validate.get_results()

            # 再バリデーションに問題が無ければ次の処理
            if errors == 0:

                # 画像ファイルがある場合
                if original_filename:

                    # 仮のファイル名をユニークなファイル名で書き換え
                    unique_id = str(uuid1())
                    saved_filename = unique_id + extension
                    temp_filepath = os.path.join(USER_IMG_DIR, temp_filename)
                    saved_filepath = os.path.join(USER_IMG_DIR, saved_filename)
                    os.rename(temp_filepath, saved_filepath)

                    # サムネイルを生成
                    original_img = Image.open(saved_filepath)
                    cropped_img = crop_max_rectangle(original_img).resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
                    thumbnail_filename = unique_id + '.webp'
                    thumbnail_filepath = os.path.join(USER_THUMBNAILS_DIR, thumbnail_filename)
                    cropped_img.save(thumbnail_filepath)

                else:
                    original_filename = None
                    saved_filename = None
                    thumbnail_filename = None

                # 投稿内容をDBに保存
                post = Post(
                    user_id=current_user.id,
                    title=title,
                    body=body,
                    original_filename=original_filename,
                    saved_filename=saved_filename,
                    thumbnail_filename=thumbnail_filename,
                    category_id=category_id,
                    tags=tags,
                    is_private=is_private,
                    created_at=datetime.now()
                    )
                try:
                    db.session.add(post)
                    db.session.flush()
                    post_id = post.id
                    db.session.commit()
                    return redirect(f"/view/{post_id}")
                except:
                    # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                    db.session.rollback()
                    return render_template('error.html')

            # 再バリデーションに問題があればエラー画面表示
            else:
                return render_template('error.html')

    # フォーム画面
    return render_template(
        'create_forms.html',
        categories=categories,
        title=title,
        body=body,
        category_id=category_id,
        tags=tags,
        is_private=is_private,
        is_valid=is_valid,
        is_not_image=is_not_image,
        exceeds_text_limit=exceeds_text_limit,
        exceeds_tags_limit=exceeds_tags_limit
        )


### 記事の編集 ###
@app.route('/edit/<int:post_id>', methods=['POST', 'GET'])
def edit(post_id):

    # DBから投稿記事のデータ取得
    post = Post.query.filter_by(id=post_id).one_or_none()

    # 変数の初期化
    post_id = post.id
    file = None
    existing_filename = post.original_filename
    if existing_filename:
        existing_filepath = '../' + convert_separators(os.path.join(USER_IMG_DIR, post.saved_filename))
    else:
        existing_filepath = None
    title = post.title
    body = post.body
    category_id = post.category_id
    tags = post.tags
    tag_list = []
    is_private = post.is_private
    is_valid = {}
    is_valid['file'] = ''
    is_valid['body'] = ''
    is_valid['tags'] = ''
    is_not_image = False
    exceeds_text_limit = {}
    exceeds_tags_limit = 0
    errors = 0

    # カテゴリー一覧取得
    categories = Category.query.all()

    if request.method == "POST":

        # 確認画面
        if request.form.get('mode') == 'confirm' and errors == 0:

            # 入力値を取得
            change_image = int(request.form.get('change_image', 0))
            file = request.files.get('file', None)
            title = request.form.get('title', '')
            body = request.form.get('body','')
            category_id = int(request.form.get('category_id', 0))
            tags = request.form.get('tags','')
            is_private = int(request.form.get('is_private', 0))

            # バリデーション
            if change_image:
                validate = ValidatePost(file, title, body, tags, check=True)
            else:
                validate = ValidatePost(file, title, body, tags, check=False)
            errors, is_valid, is_not_image, exceeds_text_limit, exceeds_tags_limit = validate.get_results()

            # バリデーションに問題が無い場合
            if errors == 0:

                # 画像ファイルがあれば、仮のファイル名で保存
                if file:
                    original_filename = secure_filename(file.filename) #ファイル名をサニタイズ
                    extension = get_extension(original_filename)
                    temp_filename = f"temp_{current_user.id}{extension}"
                    file_path = os.path.join(USER_IMG_DIR, temp_filename)
                    file.save(file_path)
                    file_path = '../' + convert_separators(file_path)
                elif change_image and not file:
                    original_filename = ''
                    extension = ''
                    temp_filename = ''
                    file_path = ''
                else:
                    original_filename = ''
                    extension = ''
                    temp_filename = ''
                    file_path = existing_filepath

                # カテゴリーが選択されていれば、カテゴリー名を取得
                if category_id:
                    selected_category = Category.query.filter_by(id=category_id).one_or_none()
                    category_name = selected_category.name
                else:
                    category_name = ''

                # タグがあれば、リストに分割
                if tags:
                    tag_list = tags.split()

                #確認画面のレンダリング
                return render_template(
                    'edit_confirm.html',
                    change_image=change_image,
                    post_id=post_id,
                    original_filename=original_filename,
                    temp_filename=temp_filename,
                    extension=extension,
                    file_path=file_path,
                    title=title,
                    body=body,
                    category_id=category_id,
                    category_name=category_name,
                    tags=tags,
                    tag_list=tag_list,
                    is_private=is_private,
                    )

        # 投稿完了
        if request.form.get('mode') == 'completed':

            #前画面から値を継承
            change_image = int(request.form.get('change_image', 0))
            original_filename = secure_filename(request.form.get('original_filename'))
            temp_filename = request.form.get('temp_filename')
            extension = request.form.get('extension')
            title = request.form.get('title')
            body = request.form.get('body')
            category_id = int(request.form.get('category_id'))
            tags = request.form.get('tags')
            is_private = request.form.get('is_private')

            # 再バリデーション
            if change_image:
                validate = ValidatePost(file, title, body, tags, check=True)
            else:
                validate = ValidatePost(file, title, body, tags, check=False)
            errors, is_valid, is_not_image, exceeds_text_limit, exceeds_tags_limit = validate.get_results()

            # 再バリデーションに問題が無い場合
            if errors == 0:

                if change_image and not original_filename:
                    original_filename = None
                    saved_filename = None
                    thumbnail_filename = None

                elif not change_image and not original_filename:
                    original_filename = existing_filename
                    saved_filename = post.saved_filename
                    thumbnail_filename = post.thumbnail_filename

                else:
                    # 仮のファイル名をユニークなファイル名で書き換え
                    unique_id = str(uuid1())
                    saved_filename = unique_id + extension
                    temp_filepath = os.path.join(USER_IMG_DIR, temp_filename)
                    saved_filepath = os.path.join(USER_IMG_DIR, saved_filename)
                    os.rename(temp_filepath, saved_filepath)
                    # サムネイルを生成
                    original_img = Image.open(saved_filepath)
                    cropped_img = crop_max_rectangle(original_img).resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
                    thumbnail_filename = unique_id + '.webp'
                    thumbnail_filepath = os.path.join(USER_THUMBNAILS_DIR, thumbnail_filename)
                    cropped_img.save(thumbnail_filepath)


                # 投稿内容をDBに保存
                try:
                    post.user_id = current_user.id
                    post.title = title
                    post.body =body
                    post.original_filename = original_filename
                    post.saved_filename = saved_filename
                    post.thumbnail_filename = thumbnail_filename
                    post.category_id = category_id
                    post.tags = tags
                    post.is_private = is_private
                    post.updated_at = datetime.now()
                    db.session.add(post)
                    db.session.commit()

                    return redirect(f"/view/{post_id}")
                except:
                    # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                    db.session.rollback()
                    return render_template('error.html')

            # 再バリデーションに問題があればエラー画面表示
            else:
                return render_template('error.html')

    # フォーム画面
    return render_template(
        'edit_forms.html',
        post_id=post_id,
        existing_filename=existing_filename,
        existing_filepath=existing_filepath,
        categories=categories,
        title=title,
        body=body,
        category_id=category_id,
        tags=tags,
        is_private=is_private,
        is_valid=is_valid,
        is_not_image=is_not_image,
        exceeds_text_limit=exceeds_text_limit,
        exceeds_tags_limit=exceeds_tags_limit
        )


### 記事の閲覧 ###
@app.route('/view/<int:post_id>', methods=['POST', 'GET'])
def view(post_id):

    # 変数の初期化
    posted_comments = []
    input_comment = ''
    is_valid = {}
    is_valid['comment'] = False
    exceeds_text_limit = {}

    # DBから投稿記事のデータ取得
    post = Post.query.filter_by(id=post_id).one_or_none()
    if post:
        user = User.query.filter_by(id=post.user_id).one_or_none()

    # 記事が削除または投稿者が存在していない・退会している場合
    if post is None or post.deleted_at or user.deleted_at:
        return render_template('page_not_found.html')
    # 記事が他の投稿ユーザーの投稿でプライベートモードの場合
    elif post.is_private and current_user.id != post.user_id or post.is_private and not current_user.is_authenticated:
        return render_template('private.html')
    # それ以外の閲覧できる記事の場合
    else:
        # 記事投稿者のアバター
        avatar_file_name = f"avatar_{user.id}.webp"
        avatar_file_path = os.path.join(USER_AVATAR_DIR, avatar_file_name)
        if os.path.isfile(avatar_file_path):
            avatar = '../' + avatar_file_path.replace(os.path.sep, '/')
        else:
            avatar = ''
        # 記事投稿者のユーザー名
        poster = user.username
        # 記事投稿者のプロフィール
        profile = user.profile
        # 画像ファイル
        if post.saved_filename:
            file_path = os.path.join(USER_IMG_DIR, post.saved_filename)
            file_path = '../' + convert_separators(file_path)
        else:
            file_path = ''
        # 日付
        if post.updated_at:
            dt_obj = datetime.strptime(post.updated_at, '%Y-%m-%d %H:%M:%S.%f')
            posted_at = dt_obj.strftime('%Y年%m月%d日 %H:%M') + '（更新）'
        else:
            dt_obj = datetime.strptime(post.created_at, '%Y-%m-%d %H:%M:%S.%f')
            posted_at = dt_obj.strftime('%Y年%m月%d日 %H:%M')
        # カテゴリ
        category_name = ''
        if post.category_id:
            category = Category.query.filter_by(id=post.category_id).one_or_none()
            category_name = category.name

        # タグ
        tag_list = post.tags.split()

        # 投稿されたコメント
        comment_objs = Comment.query.filter_by(post_id=post_id).all()
        for i, comment_obj in enumerate(comment_objs):
            posted_comments.append({})
            posted_comments[i]['user_id'] = comment_obj.user_id
            user_obj = User.query.filter_by(id=comment_obj.user_id).one_or_none()
            posted_comments[i]['username'] = user_obj.username
            posted_comments[i]['avatar'] = os.path.isfile(os.path.join(USER_AVATAR_DIR, f"avatar_{comment_obj.user_id}.webp"))
            posted_comments[i]['body'] = comment_obj.body
            posted_comments[i]['created_at'] = comment_obj.created_at

        ## コメントフォーム ##
        if request.method == 'POST':

            # 入力値を取得
            input_comment = request.form.get('input_comment', '')

            # バリデーション
            validate = ValidateComment(input_comment)
            errors, is_valid, exceeds_text_limit = validate.get_results()

            # バリデーションに問題が無ければ、DBを更新して完了画面表示
            if errors == 0:
                comment = Comment(
                    post_id=post_id,
                    user_id=current_user.id,
                    body=input_comment,
                    created_at=datetime.now()
                    )
                try:
                    db.session.add(comment)
                    db.session.commit()
                    return redirect(f"/view/{post_id}")
                except:
                    # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                    db.session.rollback()
                    return render_template('error.html')


        # 閲覧ページを表示
        return render_template(
            'view.html',
            poster_id=post.user_id,
            post_id=post_id,
            avatar=avatar,
            poster=poster,
            profile=profile,
            file_path=file_path,
            title=post.title,
            body=post.body,
            category_name=category_name,
            tag_list=tag_list,
            is_private=post.is_private,
            posted_at=posted_at,
            posted_comments=posted_comments,
            input_comment=input_comment,
            is_valid=is_valid,
            exceeds_text_limit=exceeds_text_limit
            )


### 記事の削除 ###
@app.route('/delete', methods=['POST', 'GET'])
@login_required
def delete():

    if request.method == 'POST':

        post_id = request.form.get('post_id')
        post = Post.query.filter_by(id=post_id).one_or_none()

        if post.user_id == current_user.id:
            post.deleted_at = datetime.now()
            db.session.add(post)
            db.session.commit()
            return render_template('delete_completed.html')
        else:
            return render_template('error.html')

    return render_template('error.html')


### ユーザーの記事一覧 ###
@app.route('/user/<int:user_id>')
def user(user_id):

    # DBから記事投稿者のデータ取得
    user = User.query.filter_by(id=user_id).one_or_none()

    # 投稿者が退会している、または存在していない場合
    if user is None or user.deleted_at:
        return render_template('user_not_found.html')

    # ユーザーのアバター
    avatar_file_name = f"avatar_{user.id}.webp"
    avatar_file_path = os.path.join(USER_AVATAR_DIR, avatar_file_name)
    if os.path.isfile(avatar_file_path):
        avatar = '../' + avatar_file_path.replace(os.path.sep, '/')
    else:
        avatar = ''
    # 記事投稿者のユーザー名
    poster = user.username
    # 記事投稿者のプロフィール
    profile = user.profile

    # 記事一覧取得（プライベートモードONの記事は他ユーザーは見れない）
    page_num = request.args.get('page', 1)
    if current_user.is_authenticated and user.id == current_user.id:
        pages = Post.query.filter(and_(Post.user_id == user_id, Post.deleted_at == None))\
            .order_by(desc(Post.id)).paginate(page=int(page_num), per_page=ITEMS_PER_PAGE, error_out=False)
    else:
        pages = Post.query.filter(and_(Post.user_id == user_id, Post.deleted_at == None, \
            Post.is_private == 0)).order_by(desc(Post.id)).paginate(page=int(page_num), per_page=ITEMS_PER_PAGE, error_out=False)

    return render_template(
        'user.html',
        user_id=user_id,
        avatar=avatar,
        poster=poster,
        profile=profile,
        pages=pages
    )

### キーワード検索 ###
@app.route('/search', methods=['POST', 'GET'])
def search():

    # 入力値を取得
    keywords = request.args.get('keywords', '')
    keyword_list = keywords.split()
    keyword_args = '+'.join(keyword_list)

    # 条件式をリスト化
    conditions = [or_(
        Post.title.like(f"%{keyword}%"),
        Post.body.like(f"%{keyword}%"),
        Post.tags.like(f"%{keyword}%")
    ) for keyword in keyword_list]

    # 検索結果を取得
    page_num = request.args.get('page', 1)
    pages = Post.query.filter(and_(Post.is_private == 0, Post.deleted_at == None, or_(*conditions))).order_by(desc(Post.id))\
        .paginate(page=int(page_num), per_page=ITEMS_PER_PAGE, error_out=False)

    # 検索結果を表示
    return render_template(
        'search.html',
        pages=pages,
        keywords=keywords,
        keyword_args=keyword_args
    )


### アカウント設定ページ（メイン） ###
@app.route('/account')
@login_required
def account():
    return render_template('account_main.html')


### アカウント設定ページ（メールアドレス変更） ###
@app.route('/account/email', methods=['POST', 'GET'])
@login_required
def account_email():

    # 変数の初期化
    email = ''
    password = ''
    is_valid = {}
    is_valid['email'] = ''
    is_valid['password'] = ''
    is_not_email = False
    email_exists = False
    is_wrong_password = False

    if request.method == 'POST':

        # 入力値を取得
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # バリデーション
        validate = ValidateChangeEmail(email, password)
        errors, is_valid, is_not_email, email_exists, is_wrong_password = validate.get_results()

        # バリデーションに問題が無ければ、DBを更新して完了画面表示
        if errors == 0:
            user = User.query.filter_by(id=current_user.id).one_or_none()
            try:
                user.email = email
                user.updated_at = datetime.now()
                db.session.add(user)
                db.session.commit()
                return render_template('account_completed.html', completed='email')
            except:
                # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                db.session.rollback()
                return render_template('error.html')

    # 現在のパスワード変更画面を表示
    return render_template(
        'account_email.html',
        email=email,
        password=password,
        is_valid=is_valid,
        is_not_email=is_not_email,
        email_exists=email_exists,
        is_wrong_password=is_wrong_password
        )


### アカウント設定ページ（パスワード変更） ###
@app.route('/account/password', methods=['POST', 'GET'])
@login_required
def account_password():

    # 画面切替用フラグ変数
    render_flag = 'current'

    # 変数の初期化
    password = ''
    password2 = ''
    is_valid = {}
    is_valid['password'] = ''
    is_valid['password2'] = ''
    exceeds_text_limit = {}
    is_wrong_password = False
    is_mismatched = False

    # 現在のパスワード入力画面からの場合
    if request.method == 'POST' and request.form.get('input_from', 'current') == 'current':

        # 入力値を取得
        password = request.form.get('password', '').strip()

        # バリデーション
        validate = ValidateCurrentPassword(password)
        errors, is_valid, is_wrong_password = validate.get_results()

        # バリデーションに問題がなければフラグの更新・変数の初期化
        if errors == 0:
            render_flag = 'new'
            is_valid['password'] = ''
            password = ''

    # 新しいパスワード入力画面からの場合
    if request.method == 'POST' and request.form.get('input_from', 'current') == 'new':

        # フラグ変数を更新
        render_flag = 'new'

        # 入力値を取得
        password = request.form.get('password', '').strip()
        password2 = request.form.get('password2', '').strip()

        # バリデーション
        validate = ValidateNewPassword(password, password2)
        errors, is_valid, exceeds_text_limit, is_wrong_password, is_mismatched = validate.get_results()

        # バリデーションに問題がなければ、パスワードを変更して完了画面表示
        if errors == 0:
            user = User.query.filter_by(id=current_user.id).one_or_none()
            try:
                user.password = generate_password_hash(password, method='sha256')
                user.updated_at = datetime.now()
                db.session.add(user)
                db.session.commit()
                return render_template('account_completed.html', completed='password')
            except:
                # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                db.session.rollback()
                return render_template('error.html')

    # 現在のパスワード入力画面を表示
    if render_flag == 'current':
        return render_template(
            'account_password_current.html',
            password=password,
            is_valid=is_valid,
            is_wrong_password=is_wrong_password,
            )

    # 新しいパスワード入力画面を表示
    if render_flag == 'new':
        return render_template(
            'account_password_new.html',
            password=password,
            password2=password2,
            is_valid=is_valid,
            exceeds_text_limit=exceeds_text_limit,
            is_wrong_password=is_wrong_password,
            is_mismatched=is_mismatched
            )


### アカウント設定ページ（プロフィールの登録・変更） ###
@app.route('/account/profile', methods=['POST', 'GET'])
@login_required
def account_profile():

    # 変数の初期化
    profile = ''
    is_valid = {}
    is_valid['profile'] = False
    exceeds_text_limit = {}

    # ログイン中のユーザー情報
    user = User.query.filter_by(id=current_user.id).one_or_none()

    # 既に登録されている自己紹介があれば変数に渡す
    if user.profile:
        profile = user.profile

    if request.method == 'POST':

        # 入力値を取得
        profile = request.form.get('profile', '')

        # バリデーション
        validate = ValidateProfile(profile)
        errors, is_valid, exceeds_text_limit = validate.get_results()

        # バリデーションに問題が無ければ、DBを更新して完了画面表示
        if errors == 0:
            try:
                user.profile = profile
                user.updated_at = datetime.now()
                db.session.add(user)
                db.session.commit()
                return render_template('account_completed.html', completed='profile')
            except:
                # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                db.session.rollback()
                return render_template('error.html')

    # 自己紹介入力画面を表示
    return render_template(
        'account_profile.html',
        profile=profile,
        is_valid=is_valid,
        exceeds_text_limit=exceeds_text_limit
    )


### アカウント設定ページ（アバターの変更） ###
@app.route('/account/avatar', methods=['POST', 'GET'])
@login_required
def account_avatar():

    # 変数の初期化
    avatar = ''
    is_valid = {}
    is_valid['file'] = ''
    is_not_image = False

    # アバター画像用変数
    avatar_file_name = f"avatar_{current_user.id}.webp"
    avatar_file_path = os.path.join(USER_AVATAR_DIR, avatar_file_name)

    # 既に登録されているアバターがあれば変数に渡す
    if os.path.isfile(avatar_file_path):
        avatar = '../' + avatar_file_path.replace(os.path.sep, '/')

    if request.method == 'POST':

        # 入力値を取得
        file = request.files.get('file', None)

        # ファイルが選択されていれば、バリデーションして保存
        if file:

            # バリデーション
            validate = ValidateAvatar(file)
            errors, is_valid, is_not_image = validate.get_results()

            # バリデーションに問題が無ければ、切り抜き＆縮小
            if errors == 0:

                # 元画像を一旦保存
                extension = get_extension(file.filename)
                original_file_name = f"avatar_{current_user.id}{extension}"
                original_file_path = os.path.join(USER_AVATAR_DIR, original_file_name)
                file.save(original_file_path)
                # 切り抜き＆縮小してWebp形式で再度保存
                original_img = Image.open(original_file_path)
                cropped_img = crop_max_square(original_img).resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
                cropped_img.save(avatar_file_path)
                # 元画像は削除
                os.remove(original_file_path)

                # 完了画面を表示
                return render_template('account_completed.html', completed='avatar')

        # ファイルが選択されていなければ、アバター画像削除もしくはエラー表示
        else:
            if avatar:
                os.remove(avatar_file_path)
                return render_template('account_completed.html', completed='avatar')
            else:
                is_valid['file'] = 'is-invalid'

    # アバター変更画面を表示
    return render_template(
        'account_avatar.html',
        avatar=avatar,
        is_valid=is_valid,
        is_not_image=is_not_image
    )


### 退会（アカウントの削除）ページ ###
@app.route('/account/delete', methods=['POST', 'GET'])
@login_required
def account_delete():

    # 変数の初期化
    password = ''
    is_valid = {}
    is_valid['password'] = False
    is_wrong_password = False

    if request.method == 'POST':

        # 入力値を取得
        password = request.form.get('password', '')

        # バリデーション
        validate = ValidateDelete(password)
        errors, is_valid, is_wrong_password = validate.get_results()

        # バリデーションに問題が無ければ、アカウントを削除（deleted_atを追加）
        if errors == 0:
            user = User.query.filter_by(id=current_user.id).one_or_none()
            try:
                user.deleted_at = datetime.now()
                db.session.add(user)
                db.session.commit()
                logout_user()
                return render_template('account_completed.html', completed='delete')
            except:
                # DB更新中にエラーが発生した場合はロールバックして、エラー画面表示
                db.session.rollback()
                return render_template('error.html')

    # 退会画面を表示
    return render_template(
        'account_delete.html',
        password=password,
        is_valid=is_valid,
        is_wrong_password=is_wrong_password
    )

### 400エラー ###
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return render_template('error.html')


### 404エラー ###
@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


### ファイルサイズ超過エラー ###
@app.errorhandler(RequestEntityTooLarge)
def handle_over_max_file_size(error):
    return render_template('error.html')


### ユーティリティ関数 ###

# パス区切りを/に変換
def convert_separators(path):
    return path.replace(os.path.sep, '/')

# 拡張子を.付きの文字列で取得
def get_extension(filename):
    return os.path.splitext(filename)[1]

# 画像の中心の領域を切り出す
def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))
# 最大の正方形を切り出す
def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))
# 最大の長方形(4:3)を切り出す
def crop_max_rectangle(pil_img):
    img_width, img_height = pil_img.size
    crop_height = round(img_width*0.75)
    crop_width = round(img_height*1.33)
    if crop_height <= img_height:
        return crop_center(pil_img, img_width, crop_height)
    else:
        return crop_center(pil_img, crop_width, img_height)


class Validate:
    """各種フォームの入力値のバリデーションを行う。

    Attributes
    ----------
    _errors : int
        バリデーション結果のエラー総数。

    """
    # ユーザー名の最大文字数
    USERNAME_MAX_LENGTH = 10
    # パスワードの最少文字数
    PASSWORD_MIN_LENGTH = 6
    # 記事タイトルの最大文字数
    TITLE_MAX_LENGTH = 50
    # 記事本文の最大文字数
    BODY_MAX_LENGTH = 500
    # コメントの最大文字数
    COMMENT_MAX_LENGTH = 300
    # 登録できる最大タグ数
    TAGS_MAX_LENGTH = 10
    # 自己紹介の最大文字数
    PROFILE_MAX_LENGTH = 100


    def __init__(self):
        # エラー総数
        self._errors = 0


    def set_errors(self, count=1):
        """エラー数をセットする

        Parameters:
        ----------
        count : int
            追加するエラー数

        """

        self._errors += count


    def get_errors(self):
        """エラー数を取得する

        Returns:
        ----------
        self.errors : int
            発生したエラー数

        """

        return self._errors


    def check_blanks(self, return_value='both', check_type='each', check_list='*'):
        """空欄かどうかを判定する

        Parameters:
        ----------
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        check_type : str
            判定方法を変えるオプション
            【each】それぞれ個別に空欄かどうかを判定。
            【any】いずれかに値があれば、対象のフォーム全てが有効判定。

        check_list : str / list
            判定方法を変えるオプション
            【Noneの場合】全てのフォームをチェックする。
            【リスト型の場合】リストにあるフォームだけをチェックする。

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマーク表示
            【is-invalid】NG判定の!マーク表示

        Notes
        -----
            子クラスのexecuteメソッドで使う場合は、一番最初に呼び出すこと。
        """

        input_data = vars(self)
        is_valid = {}

        if check_type == "each":
            for key, value in dict.items(input_data):
                if check_list == '*' or type(check_list) is list and key in check_list:
                    if key != '_errors':
                        if value:
                            if return_value == 'both':
                                is_valid[key] = 'is-valid'
                        else:
                            is_valid[key] = 'is-invalid'
                            self.set_errors()

        if check_type == "any":
            valid_list = []
            for key, value in dict.items(input_data):
                if check_list == '*' or type(check_list) is list and key in check_list:
                    if key != '_errors' and value:
                        valid_list.append(key)
                        if return_value == 'both':
                            is_valid[key] = 'is-valid'
            if not valid_list:
                if check_list == '*':
                    for key in dict.keys(input_data):
                        is_valid[key] = 'is-invalid'
                if type(check_list) is list:
                    for key in check_list:
                        is_valid[key] = 'is-invalid'
                self.set_errors()

        return is_valid


    def check_email_atmark(self, return_value='both'):
        """メールアドレスに@があるかどうか判定する。

        Parameters:
        ----------
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマーク表示をする。
            【is-invalid】NG判定の!マークを表示する。
        is_not_email : bool
            メールアドレスではない場合はTrueを返す。self._errors
            Trueの場合はページ内のエラーメッセージが切り替わる。
        """

        is_valid = {}
        is_not_email = False

        if self.email:
            if not re.match('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', self.email):
                is_valid['email'] = 'is-invalid'
                is_not_email = True
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['email'] = 'is-valid'

        return is_valid, is_not_email


    def check_email_used(self, return_value='both'):
        """メールアドレスが既に使われているかどうかチェックする。

        Parameters:
        ----------
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマーク表示を表示する。
            【is-invalid】NG判定の!マーク表示を表示する。
        email_exists : bool
            メールアドレスが既に使われている場合はTrueを返す。
            Trueの場合はページ内のエラーメッセージが切り替わる。
        """

        is_valid = {}
        email_exists = False

        if self.email:
            if User.query.filter_by(email=self.email).one_or_none():
                is_valid['email'] = 'is-invalid'
                email_exists = True
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['email'] = 'is-valid'

        return is_valid, email_exists


    def check_username_used(self, return_value="both"):
        """ユーザー名が既に使われているかどうかチェックする。

        Parameters:
        ----------
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマークを表示する。
            【is-invalid】NG判定の!マークを表示する。
        username_exists : bool
            ユーザー名が既に使われている場合はTrueを返す。
            Trueの場合はページ内のエラーメッセージが切り替わる。
        """

        is_valid = {}
        username_exists = False

        if self.username:
            if User.query.filter_by(username=self.username).one_or_none():
                is_valid['username'] = 'is-invalid'
                username_exists = True
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['email'] = 'is-valid'

        return is_valid, username_exists


    def check_password_confirm(self, return_value='both'):
        """メールアドレスの入力欄と確認入力欄が一致しているか判定する。

        Parameters:
        ----------
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマークを表示する。
            【is-invalid】NG判定の!マークを表示する。
        is_mismatched : bool
            一致しない場合はTrueを返す。
            Trueの場合はページ内のエラーメッセージが切り替わる。
        """

        is_valid = {}
        is_mismatched = False

        if self.password2:
            if self.password != self.password2:
                is_valid['password2'] = "is-invalid"
                is_mismatched = True
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['password2'] = 'is-valid'

        return is_valid, is_mismatched


    def check_email_notfound(self, return_value='both'):
        """DB上に存在しないメールアドレスかどうかチェックする。

        Parameters:
        ----------
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマークを表示する。
            【is-invalid】NG判定の!マークを表示する。
        email_notfound : bool
            メールアドレスが存在しない場合はTrueを返す。
            Trueの場合はページ内のエラーメッセージが切り替わる。
        """

        is_valid = {}
        email_notfound = False
        user = User.query.filter_by(email=self.email).one_or_none()

        if self.email:
            if not user or user.deleted_at:
                is_valid['email'] = 'is-invalid'
                email_notfound = True
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['email'] = 'is-valid'

        return is_valid, email_notfound


    def check_password_used(self, method='email', check_type='normal', return_value='both'):
        """アカウントに登録されたパスワードかどうかチェックする。

        Parameters:
        ----------
        target : str
            パスワードの検索方法を変えるオプション
            【email】入力されたメールアドレスで検索
            【id】ログイン中のユーザーのIDで検索
        check_type : str
            エラー判定の方法を変えるオプション
            【normal】アカウントに登録されていない場合はエラー扱い
            【reversed】アカウントに登録されている場合はエラー扱い
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマークを表示する。
            【is-invalid】NG判定の!マークを表示する。
        is_wrong_password : bool
            アカウントに登録されたパスワードではない場合はTrueを返す。
            Trueの場合はページ内のエラーメッセージが切り替わる。
        """

        is_valid = {}
        is_wrong_password = False
        if method == 'email':
            user = User.query.filter_by(email=self.email).one_or_none()
        elif method == 'id':
            user = User.query.filter_by(id=current_user.id).one_or_none()

        if self.password:

            flag = True if user is None or \
                not check_password_hash(user.password, self.password) else False

            if check_type == 'reversed':
                flag = not flag

            if flag:
                is_valid['password'] = 'is-invalid'
                is_wrong_password = True
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['email'] = 'is-valid'

        return is_valid, is_wrong_password


    def check_file_format(self, return_value='both'):
        """アップロードされた画像ファイルが指定の形式かどうかチェックする。

        Parameters:
        ----------
        return_value : str
            戻り値を変えるオプション
            【"both"の場合】is-validとis-invalidの両方が辞書型に入る
            【"invalid"の場合】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマークを表示する。
            【is-invalid】NG判定の!マークを表示する。
        is_not_image : bool
            メールアドレスが存在しない場合はTrueを返す。
            Trueの場合はページ内のエラーメッセージが切り替わる。

        Notes
        -----
            指定のファイル形式はjpg(jpeg), gif, png
        """

        is_valid = {}
        is_not_image = False

        if self.file:
            ALLOWED_TYPES = ['jpeg', 'gif', 'png']
            file_type = what(self.file.stream)
            if not file_type in ALLOWED_TYPES:
                is_valid['file'] = 'is-invalid'
                is_not_image = True
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['file'] = 'is-valid'

        return is_valid, is_not_image


    def check_text_length(self, target, dict_key, limit, method='less', return_value='both'):
        """入力された文字数が規定内どうかチェックする。

        Parameters:
        ----------
        target : str
            チェックしたい文字列。
        dict_key : str
            Viewに渡す変数（辞書型）のキーを指定
        limit : int
            入力できる文字数の上限。
        method : str
            数値をどうチェックするか指定する。
            【less】limit以下かどうか
            【more】limit以上かどうか
            【equal】limitと同じかどうか
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマークを表示する。
            【is-invalid】NG判定の!マークを表示する。
            is_valid[dict_key] = True/Falseの形で受け取ることが出来る。
        exceeds_text_limit : dict
            文字数がオーバーしている場合は規定文字数を返す。
        """

        is_valid = {}
        flag = False
        exceeds_text_limit = 0

        if target:
            if method == 'less':
                flag = True if len(target) <= limit else False
            if method == 'more':
                flag = True if limit <= len(target) else False

            if not flag:
                is_valid[dict_key] = 'is-invalid'
                exceeds_text_limit = limit
                self.set_errors()
            else:
                if return_value  == 'both':
                    is_valid[dict_key] = 'is-valid'

        return is_valid, exceeds_text_limit


    def check_tags_numbers(self, limit, return_value='both'):
        """登録されたタグの数が規定内どうかチェックする。

        Parameters:
        ----------
        limit : int
            登録できるタグ数の上限。
        return_value : str
            戻り値を変えるオプション
            【both】is-validとis-invalidの両方が辞書型に入る
            【invalid】is-invalidのみが辞書型に入る

        Returns:
        ----------
        is_valid : dict
            判定結果をもとにViewに渡すbootstrap用のクラス名を入れる。
            【is-valid】OK判定のチェックマークを表示する。
            【is-invalid】NG判定の!マークを表示する。
        """

        is_valid = {}
        exceeds_tags_limit = 0

        if self.tags:
            tag_list = self.tags.split()
            if limit < len(tag_list):
                is_valid['tags'] = 'is-invalid'
                exceeds_tags_limit = limit
                self.set_errors()
            else:
                if return_value == 'both':
                    is_valid['tags'] = 'is-valid'

        return is_valid, exceeds_tags_limit


#### サインアップ用クラス ####
class ValidateSignup(Validate):
    """サインアップフォームの入力値のバリデーションを行う。

    Attributes
    ----------
    email : str
        入力されたメールアドレス
    username : str
        入力されたユーザー名（ハンドルネーム）
    password : str
        本フォームに入力されたパスワード
    password2 : str
        確認用フォームに入力されたパスワード
    """

    def __init__(self, email, username, password, password2):
        super().__init__()
        self.email = email
        self.username = username
        self.password = password
        self.password2 = password2

    def get_results(self):
        """サインアップ用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        is_not_email : bool
        email_exists : bool
        username_exists : bool
        is_mismatched : bool

        """

        # 空欄チェック
        is_valid = self.check_blanks()

        # メールアドレスかどうかチェック
        result = self.check_email_atmark()
        if is_valid['email'] == 'is-valid':
            is_valid |= result[0]
        is_not_email = result[1]

        # 既に使われているメールアドレスかチェック
        result = self.check_email_used()
        if is_valid['email'] == 'is-valid':
            is_valid |= result[0]
        email_exists = result[1]

        # 既に使われているユーザー名かチェック
        result = self.check_username_used()
        if is_valid['username'] == 'is-valid':
            is_valid |= result[0]
        username_exists = result[1]

        # ユーザー名の文字数をチェック
        result = self.check_text_length(
            target=self.username,
            dict_key='username',
            limit=Validate.USERNAME_MAX_LENGTH,
            )
        if is_valid['username'] == 'is-valid':
            is_valid |= result[0]
        exceeds_text_limit = {}
        exceeds_text_limit['username'] = result[1]

        # パスワードの文字数をチェック
        result = self.check_text_length(
            target=self.password,
            dict_key='password',
            limit=Validate.PASSWORD_MIN_LENGTH,
            method='more'
            )
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        exceeds_text_limit['password'] = result[1]

        # パスワード確認欄をチェック
        result = self.check_password_confirm()
        if is_valid['password2'] == 'is-valid':
            is_valid |= result[0]
        is_mismatched = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        # バリデーション結果を返す
        return errors, is_valid, is_not_email, email_exists, \
            username_exists, exceeds_text_limit, is_mismatched


class ValidateLogin(Validate):
    """ログインフォームの入力値のバリデーションを行う。

    Attributes
    ----------
    email : str
        入力されたメールアドレス
    username : str
        入力されたユーザー名（ハンドルネーム）
    password : str
        入力されたパスワード
    """

    def __init__(self, email, password):
        super().__init__()
        self.email = email
        self.password = password

    def get_results(self):
        """ログイン用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        email_notfound : bool
        is_not_email : bool
        is_mismatched : bool

        """
        # 空欄チェック
        is_valid = self.check_blanks()

        # メールアドレスかどうかチェック
        result = self.check_email_atmark()
        if is_valid['email'] == 'is-valid':
            is_valid |= result[0]
        is_not_email = result[1]

        # 登録されていないメールアドレスかどうかチェック
        result = self.check_email_notfound()
        if is_valid['email'] == 'is-valid':
            is_valid |= result[0]
        email_notfound = result[1]

        # アカウントに登録されたパスワードかチェック
        result = self.check_password_used()
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        is_wrong_password = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        # バリデーション結果を返す
        return errors, is_valid, email_notfound, is_not_email, is_wrong_password


class ValidatePost(Validate):
    """記事投稿・編集フォームの入力値のバリデーションを行う。

    Attributes
    ----------
    file : str
        選択された画像のファイル名
    title : str
        入力された記事タイトル
    body : str
        入力された記事本文
    tags : str
        入力されたタグ
    check : bool
        空欄チェックを変えるオプション
        【True】BLANK_CHECK_LISTの項目の空欄チェックをする。
        【False】空欄チェックしない
    """

    # 空欄チェックする項目
    BLANK_CHECK_LIST = ['file', 'body']

    def __init__(self, file, title, body, tags, check=True):
        super().__init__()
        self.file = file
        self.title = title
        self.body = body
        self.tags = tags
        self.check = check

    def get_results(self):
        """記事投稿・編集フォーム用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        is_not_image : bool
        exceeds_text_limit : dict

        """

        # 変数の初期化
        exceeds_text_limit = {}

        # 空欄チェック
        if self.check:
            is_valid = self.check_blanks(
                return_value='invalid',
                check_type='any',
                check_list=ValidatePost.BLANK_CHECK_LIST
                )
        else:
            is_valid = {}

        # ファイル形式チェック
        result = self.check_file_format(return_value='invalid')
        is_valid |= result[0]
        is_not_image = result[1]

        # 記事タイトルの文字数チェック
        result = self.check_text_length(
            target=self.title,
            dict_key='title',
            limit=Validate.TITLE_MAX_LENGTH,
            return_value='invalid')
        if 'title' not in is_valid or is_valid['title'] == 'is-valid':
            is_valid |= result[0]
        exceeds_text_limit['title'] = result[1]

        # 記事本文の文字数チェック
        result = self.check_text_length(
            target=self.body,
            dict_key='body',
            limit=Validate.BODY_MAX_LENGTH,
            return_value='invalid')
        if 'body' not in is_valid or is_valid['body'] == 'is-valid':
            is_valid |= result[0]
        exceeds_text_limit['body'] = result[1]

        # タグの数をチェック
        result = self.check_tags_numbers(limit=Validate.TAGS_MAX_LENGTH, return_value='invalid')
        is_valid |= result[0]
        exceeds_tags_limit = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        # バリデーション結果を返す
        return errors, is_valid, is_not_image, exceeds_text_limit, exceeds_tags_limit


class ValidateChangeEmail(Validate):
    """メールアドレス変更フォームの入力値のバリデーションを行う。

    Attributes
    ----------
    email : str
        入力されたメールアドレス
    password : str
        入力されたパスワード

    """

    def __init__(self, email, password):
        super().__init__()
        self.email = email
        self.password = password

    def get_results(self):
        """メールアドレス変更フォーム用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        is_not_email : bool
        email_exists : bool
        is_wrong_password : bool

        """

        # 空欄チェック
        is_valid = self.check_blanks()

        # アカウントに登録されたパスワードかチェック
        result = self.check_password_used(method='id')
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        is_wrong_password = result[1]

        # メールアドレスかどうかチェック
        result = self.check_email_atmark()
        if is_valid['email'] == 'is-valid':
            is_valid |= result[0]
        is_not_email = result[1]

        # 既に使われているメールアドレスかチェック
        result = self.check_email_used()
        if is_valid['email'] == 'is-valid':
            is_valid |= result[0]
        email_exists = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        # バリデーション結果を返す
        return errors, is_valid, is_not_email, email_exists, is_wrong_password


class ValidateCurrentPassword(Validate):
    """パスワード変更フォーム（現在のパスワード）の入力値のバリデーションを行う。

    Attributes
    ----------
    password : str
        入力されたパスワード
    """

    def __init__(self, password):
        super().__init__()
        self.password = password

    def get_results(self):
        """パスワード変更フォーム（新しいパスワード）用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        is_wrong_password : bool

        """

        # 空欄チェック
        is_valid = self.check_blanks()

        # アカウントに登録されたパスワードかチェック
        result = self.check_password_used(method='id')
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        is_wrong_password = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        # バリデーション結果を返す
        return errors, is_valid, is_wrong_password


class ValidateNewPassword(Validate):
    """パスワード変更フォーム（新しいパスワード）の入力値のバリデーションを行う。

    Attributes
    ----------
    password : str
        本フォームに入力されたパスワード
    password2 : str
        確認用フォームに入力されたパスワード
    """

    def __init__(self, password, password2):
        super().__init__()
        self.password = password
        self.password2 = password2

    def get_results(self):
        """パスワード変更フォーム（新しいパスワード）用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        exceeds_text_limit : dict
        is_wrong_password : bool
        is_mismatched : bool

        """

        # 空欄チェック
        is_valid = self.check_blanks()

        # パスワードの文字数をチェック
        result = self.check_text_length(
            target=self.password,
            dict_key='password',
            limit=Validate.PASSWORD_MIN_LENGTH,
            method='more'
            )
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        exceeds_text_limit = {}
        exceeds_text_limit['password'] = result[1]

        # アカウントに登録されたパスワードかチェック
        result = self.check_password_used(method='id', check_type='reversed')
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        is_wrong_password = result[1]

        # パスワード確認欄をチェック
        result = self.check_password_confirm()
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        is_mismatched = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        # バリデーション結果を返す
        return errors, is_valid, exceeds_text_limit, is_wrong_password, is_mismatched


class ValidateAvatar(Validate):
    """アバター設定フォームの入力値のバリデーションを行う。

    Attributes
    ----------
    file : str
        選択された画像のファイル名

    """

    def __init__(self, file):
        super().__init__()
        self.file = file

    def get_results(self):
        """アバター設定フォーム用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        is_not_image : bool

        """

        # ファイル形式チェック
        result = self.check_file_format(return_value='invalid')
        is_valid = {}
        is_valid |= result[0]
        is_not_image = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        return errors, is_valid, is_not_image



class ValidateProfile(Validate):
    """プロフィール設定フォームの入力値のバリデーションを行う。

    Attributes
    ----------
    profile : str
        フォームに入力された自己紹介

    """

    def __init__(self, profile):
        super().__init__()
        self.profile = profile

    def get_results(self):
        """プロフィール設定フォーム用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        exceeds_text_limit : dict

        """

        # 記事本文の文字数チェック
        result = self.check_text_length(
            target=self.profile,
            dict_key='profile',
            limit=Validate.PROFILE_MAX_LENGTH,
            return_value='invalid')
        is_valid = {}
        is_valid |= result[0]
        exceeds_text_limit = {}
        exceeds_text_limit['body'] = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        return errors, is_valid, exceeds_text_limit


class ValidateDelete(Validate):
    """退会フォームの入力値のバリデーションを行う。

    Attributes
    ----------
    password : str
        フォームに入力されたパスワード

    """
    def __init__(self, password):
        super().__init__()
        self.password = password

    def get_results(self):
        """退会フォーム用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        is_wrong_password : bool

        """

        # 空欄チェック
        is_valid = self.check_blanks()

        # アカウントに登録されたパスワードかチェック
        result = self.check_password_used(method='id')
        if is_valid['password'] == 'is-valid':
            is_valid |= result[0]
        is_wrong_password = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        # バリデーション結果を返す
        return errors, is_valid, is_wrong_password


class ValidateComment(Validate):
    """コメントフォームの入力値のバリデーションを行う。

    Attributes
    ----------
    comment : str
        フォームに入力されたコメント

    """
    def __init__(self, comment):
        super().__init__()
        self.comment = comment

    def get_results(self):
        """コメントフォーム用バリデーションを実行する

        Returns:
        ----------
        errors : int
        is_valid : dict
        exceeds_text_limit : dict

        """

        # 空欄チェック
        is_valid = self.check_blanks()

        # 記事本文の文字数チェック
        result = self.check_text_length(
            target=self.comment,
            dict_key='comment',
            limit=Validate.COMMENT_MAX_LENGTH,
            return_value='invalid')
        if is_valid['comment'] == 'is-valid':
            is_valid |= result[0]
        exceeds_text_limit = {}
        exceeds_text_limit['comment'] = result[1]

        # エラー総数を取得
        errors = self.get_errors()

        return errors, is_valid, exceeds_text_limit

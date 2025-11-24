import os
import re
import secrets
import sqlite3
import string
import hmac
import hashlib
from datetime import datetime, timedelta
from functools import wraps
import requests
from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_paginate import Pagination, get_page_args

# --- App Initialization ---
app = Flask(__name__)
SECRET_KEY_FROM_ENV = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY_FROM_ENV:
    raise ValueError("错误: 必须设置 FLASK_SECRET_KEY 环境变量! 使用 'python -c \"import secrets; print(secrets.token_hex(32))\"' 生成一个。")
app.config['SECRET_KEY'] = SECRET_KEY_FROM_ENV
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

DATABASE = '/app/data/tokens.db'
PER_PAGE = 10

# --- Environment Variable Loading ---
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
EMBY_SERVER_URL = os.getenv('EMBY_SERVER_URL', '').rstrip('/')
EMBY_API_KEY = os.getenv('EMBY_API_KEY')
COPY_FROM_USER_ID = os.getenv('COPY_FROM_USER_ID')
PUBLIC_ACCESS_URL = os.getenv('PUBLIC_ACCESS_URL', 'YOUR_DOMAIN.com')
# Moviepilot Integration (Optional)
MOVIEPILOT_URL = os.getenv('MOVIEPILOT_URL', '').rstrip('/')
MOVIEPILOT_USER = os.getenv('MOVIEPILOT_USER')
MOVIEPILOT_PASSWORD = os.getenv('MOVIEPILOT_PASSWORD')


if not all([ADMIN_PASSWORD, EMBY_SERVER_URL, EMBY_API_KEY, COPY_FROM_USER_ID]):
    raise ValueError("请设置所有必需的环境变量: ADMIN_PASSWORD, EMBY_SERVER_URL, EMBY_API_KEY, COPY_FROM_USER_ID")


# --- HMAC Signature Helpers ---
def _generate_signed_token(payload):
    signature = hmac.new(app.config['SECRET_KEY'].encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def _verify_signed_token(signed_token):
    if not signed_token or '.' not in signed_token: return None
    payload, signature = signed_token.rsplit('.', 1)
    expected_signature = hmac.new(app.config['SECRET_KEY'].encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    if hmac.compare_digest(expected_signature, signature): return payload
    return None

# --- Database Setup ---
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # 直接创建包含所有列的最终表结构
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_used BOOLEAN DEFAULT 0,
                registered_username TEXT
            )
            '''
        )
        db.commit()
        db.close()


# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Emby API Helper ---
def create_emby_user(username, password):
    headers = {'X-Emby-Token': EMBY_API_KEY, 'Content-Type': 'application/json'}
    create_url = f"{EMBY_SERVER_URL}/Users/New"
    create_payload = {"Name": username, "CopyFromUserId": COPY_FROM_USER_ID, "UserCopyOptions": ["UserConfiguration", "UserPolicy"]}
    try:
        response = requests.post(create_url, json=create_payload, headers=headers, timeout=15)
        response.raise_for_status()
        user_data = response.json()
        user_id = user_data.get('Id')
        if not user_id: return None, "创建用户成功，但在响应中未找到User ID。"
    except requests.RequestException as e:
        app.logger.error(f"步骤 1/2 - 创建用户 '{username}' 失败: {e}")
        try:
            if e.response is not None and "already exists" in e.response.text.lower(): return None, "用户名已存在"
        except (AttributeError, ValueError): pass
        return None, f"创建用户失败: {e}"
    try:
        set_password_url = f"{EMBY_SERVER_URL}/Users/{user_id}/Password"
        password_payload = {"Id": user_id, "NewPw": password}
        password_response = requests.post(set_password_url, json=password_payload, headers=headers, timeout=10)
        password_response.raise_for_status()
    except requests.RequestException as e:
        app.logger.error(f"步骤 2/2 - 为用户 '{username}' (ID: {user_id}) 设置密码失败: {e}")
        return None, "用户已创建但设置密码失败，请联系管理员。"
    return user_id, None

# --- Moviepilot API Helpers ---
def get_moviepilot_access_token():
    """Logs in to the Moviepilot API to get a temporary access token."""
    login_url = f"{MOVIEPILOT_URL}/api/v1/login/access-token"
    login_data = {'username': MOVIEPILOT_USER, 'password': MOVIEPILOT_PASSWORD}
    try:
        response = requests.post(login_url, data=login_data, timeout=15)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get('access_token')
        if not access_token:
            app.logger.error("Moviepilot登录失败: 响应中未找到 'access_token'。")
            return None
        return access_token
    except requests.RequestException as e:
        app.logger.error(f"Moviepilot登录失败: {e}")
        return None

def create_moviepilot_user(username, password):
    """Attempts to create a new user in Moviepilot using an access token."""
    access_token = get_moviepilot_access_token()
    if not access_token:
        return False, "获取Moviepilot Access Token失败，请检查管理���凭据。"

    headers = {'Authorization': f"Bearer {access_token}", 'Content-Type': 'application/json'}
    create_user_url = f"{MOVIEPILOT_URL}/api/v1/user/"
    payload = {
        "name": username,
        "username": username,
        "password": password,
        "email": f"{username}@moviepilot.org",
        "is_active": True,
        "is_superuser": False,
        "permission": 1,
        "plugins": ["sub_share", "emby", "slack", "push", "telegram", "wechat", "movie_robot"]
    }
    try:
        response = requests.post(create_user_url, json=payload, headers=headers, timeout=20)
        if response.status_code == 201:
            app.logger.info(f"成功为 '{username}' 创建Moviepilot用户。")
            return True, None
        else:
            response.raise_for_status()
    except requests.RequestException as e:
        error_message = f"调用Moviepilot API时发生网络错误: {e}"
        if e.response is not None:
            try:
                error_detail = e.response.json().get('detail', e.response.text)
                if "already exists" in str(error_detail):
                    app.logger.warning(f"Moviepilot用户 '{username}' 已存在，跳过创建。")
                    return True, "用户已存在"
                error_message = f"Moviepilot API错误: {error_detail}"
            except ValueError:
                error_message = f"Moviepilot API错误: {e.response.text}"
        app.logger.error(f"创建Moviepilot用户 '{username}' 失败: {error_message}")
        return False, error_message
    return False, "未知错误"

# --- Routes ---
@app.route('/')
def index(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session.permanent = True  
            session['logged_in'] = True
            flash('登录成功!', 'success')
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='密码错误')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('您已退出登录。', 'info')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    db = get_db()
    
    # 3. Get total count for pagination object
    total = db.execute('SELECT COUNT(*) FROM tokens').fetchone()[0]

    # 4. Get current page from request args (e.g., /admin?page=2)
    page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page', 
                                           per_page=PER_PAGE)

    # 5. Fetch only the records for the current page
    tokens_from_db = db.execute(
        'SELECT id, token, is_used, registered_username FROM tokens ORDER BY created_at DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    db.close()

    # 6. Create the pagination object
    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap5',
                            record_name='tokens')

    # Process the (now smaller) list of tokens
    processed_tokens = []
    for token_row in tokens_from_db:
        processed_tokens.append({
            'id': token_row['id'],
            'full_signed_token': _generate_signed_token(token_row['token']),
            'is_used': token_row['is_used'],
            'username': token_row['registered_username']
        })
        
    # 7. Pass both tokens and pagination object to the template
    return render_template(
        'admin.html',
        tokens=processed_tokens,
        pagination=pagination,
        public_access_url=PUBLIC_ACCESS_URL
    )

@app.route('/admin/generate', methods=['POST'])
@login_required
def generate_token():
    nonce = secrets.token_urlsafe(16); db = get_db()
    db.execute('INSERT INTO tokens (token) VALUES (?)', (nonce,)); db.commit(); db.close()
    flash(f'新 Token 已生成!', 'success'); return redirect(url_for('admin'))

@app.route('/admin/delete/<int:token_id>', methods=['POST'])
@login_required
def delete_token(token_id):
    db = get_db(); db.execute('DELETE FROM tokens WHERE id = ?', (token_id,)); db.commit(); db.close()
    flash('Token 已成功删除。', 'info'); return redirect(url_for('admin'))

@app.route('/emby', methods=['GET', 'POST'])
def emby_register():
    error_msg_template = "您使用的注册链接无效、已被篡改或已过期。"
    full_token_str = request.form.get('token') if request.method == 'POST' else request.args.get('token')
    if not full_token_str:
        return render_template('error.html', error_message="链接不完整，缺少参数。")
    token_payload = _verify_signed_token(full_token_str)
    if not token_payload:
        return render_template('error.html', error_message=error_msg_template)
    
    db = get_db()
    token_data = db.execute('SELECT * FROM tokens WHERE token = ? AND is_used = 0', (token_payload,)).fetchone()
    if not token_data:
        db.close()
        return render_template('error.html', error_message=error_msg_template)

    # Check if Moviepilot integration is enabled
    moviepilot_enabled = all([MOVIEPILOT_URL, MOVIEPILOT_USER, MOVIEPILOT_PASSWORD])

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        create_moviepilot = request.form.get('create_moviepilot') == 'on'

        if not re.match(r'^[a-zA-Z0-9]{4,32}$', username):
            return render_template('register.html', token=full_token_str, error="用户名不合法：长度需为4-32位，且只能包含英文字母和数字。", moviepilot_enabled=moviepilot_enabled)
        if len(password) < 6:
            return render_template('register.html', token=full_token_str, error="密码长度至少6位。", moviepilot_enabled=moviepilot_enabled)
        if len(password) > 32:
            return render_template('register.html', token=full_token_str, error="密码长度不能超过32位。", moviepilot_enabled=moviepilot_enabled)
        
        weak_passwords = ['123456', '123456789', '12345678', '1234567', '123123', 'password', 'qwerty', 'abc123', '111111', '000000', '1qaz2wsx', 'admin', 'root', '888888', '666666']
        if password.lower() in weak_passwords:
            return render_template('register.html', token=full_token_str, error="密码过于简单，请使用更安全的密码。", moviepilot_enabled=moviepilot_enabled)
        
        user_id, error_msg = create_emby_user(username, password)
        if not user_id:
            db.close()
            return render_template('register.html', token=full_token_str, error=error_msg, moviepilot_enabled=moviepilot_enabled)

        mp_success_msg = None
        if moviepilot_enabled and create_moviepilot:
            mp_success, mp_error_msg = create_moviepilot_user(username, password)
            if mp_success:
                mp_success_msg = "Moviepilot用户也已成功创建。"
            else:
                mp_success_msg = f"注意：Emby用户已创建，但Moviepilot用户创建失败：{mp_error_msg}"
        
        db.execute('UPDATE tokens SET is_used = 1, registered_username = ? WHERE id = ?', (username, token_data['id']))
        db.commit()
        db.close()
        
        return render_template('success.html', username=username, password=password, emby_url=EMBY_SERVER_URL, mp_message=mp_success_msg)
    
    db.close()
    return render_template('register.html', token=full_token_str, moviepilot_enabled=moviepilot_enabled)

# --- Main Execution ---
if __name__ == '__main__': 
    init_db()
    app.run(host='0.0.0.0', port=5000)
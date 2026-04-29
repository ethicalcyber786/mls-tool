import os, subprocess, time
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mls_hacker_gold_786_secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mls_users.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = 'login'

VAULT, FINAL = 'mls_vault', 'mls_final'
os.makedirs(VAULT, exist_ok=True); os.makedirs(FINAL, exist_ok=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    credits = db.Column(db.Integer, default=50)
    user_ip = db.Column(db.String(100)) # IP tracking column

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

def get_duration(path):
    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{path}\""
    return float(subprocess.check_output(cmd, shell=True))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get User IP (Handling proxy for cloud hosting)
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Check if IP already has 2 accounts
        ip_count = User.query.filter_by(user_ip=user_ip).count()
        if ip_count >= 2:
            return "<h1>ACCESS DENIED</h1><p>Bhai, ek device se sirf 2 accounts allowed hain.</p><a href='/login'>Login Karein</a>"

        pw = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        new_user = User(
            username=request.form.get('username'),
            password=pw,
            user_ip=user_ip
        )
        db.session.add(new_user); db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
            login_user(user); return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
@login_required
def index(): return render_template('index.html', user=current_user)

@app.route('/upgrade')
@login_required
def upgrade(): return render_template('upgrade.html', user=current_user)

@app.route('/edit', methods=['POST'])
@login_required
def edit_sync():
    if current_user.credits < 25 and not current_user.is_premium:
        return jsonify({"success": False, "error": "CREDIT_EXPIRED", "msg": "UPGRADE PLAN TO CONTINUE LIFE TIME"})

    try:
        v_file = request.files['video']; a_file = request.files['audio']
        v_path = os.path.join(VAULT, secure_filename(v_file.filename))
        a_path = os.path.join(VAULT, secure_filename(a_file.filename))
        v_file.save(v_path); a_file.save(a_path)

        out_name = f"MLS_RESULT_{int(time.time())}.mp4"
        out_path = os.path.join(FINAL, out_name)

        socketio.emit('progress', {'perc': 20, 'msg': 'SCANNING_SILENCE...'})
        processed_audio = os.path.join(VAULT, "clean.mp3")
        subprocess.run(['ffmpeg', '-y', '-i', a_path, '-af', 'silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-40dB', processed_audio],>

        v_dur = get_duration(v_path); a_dur = get_duration(processed_audio)
        speed = v_dur / a_dur

        socketio.emit('progress', {'perc': 60, 'msg': 'SYNCING_V2_ACTIVE...'})
        cmd = ['ffmpeg', '-y', '-i', v_path, '-i', processed_audio, '-filter_complex', f"[0:v]setpts={1/speed}*PTS,drawbox=y=0:h=ih*0.15:color=black@1>
        subprocess.run(cmd, check=True)

        current_user.credits -= 25
        db.session.commit()

        socketio.emit('progress', {'perc': 100, 'msg': 'CORE_STABILIZED!'})
        return jsonify({"success": True, "download_url": f"/download/{out_name}", "new_credits": current_user.credits})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/download/<filename>')
@login_required
def download(filename): return send_file(os.path.join(FINAL, filename), as_attachment=True)

@app.route('/logout')
def logout(): logout_user(); return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    port = int(os.environ.get("PORT", 5500))
    socketio.run(app, host='0.0.0.0', port=port)

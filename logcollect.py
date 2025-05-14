import os, re, datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
LOG_DIR = os.environ.get('LOG_DIR', r'D:/Intern/logs')

class LogSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(15), nullable=False)
    count = db.Column(db.Integer, default=0)

class FileLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(15), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime)

# Initialize once
initialized = False
@app.before_request
def init_db():
    global initialized
    if not initialized:
        db.create_all()
        initialized = True

# Parse logs from SFTP folder
def parse_logs():
    events = []
    ip_re = re.compile(r"\[INFO\]\s*Sending to (\d+\.\d+\.\d+\.\d+)")
    put_re = re.compile(r"put\s+(.+\.txt)")
    time_re = re.compile(r"_(\d{8})_(\d{6})")

    for fname in os.listdir(LOG_DIR):
        if not fname.endswith('.log'): continue
        host = fname.rsplit('.',1)[0]
        last_ip = None
        with open(os.path.join(LOG_DIR, fname)) as f:
            for line in f:
                m_ip = ip_re.search(line)
                if m_ip:
                    last_ip = m_ip.group(1)
                    continue
                m_put = put_re.search(line)
                if m_put and last_ip:
                    fn = os.path.basename(m_put.group(1))
                    ts = None
                    m_time = time_re.search(fn)
                    if m_time:
                        dt_str = f"{m_time.group(1)} {m_time.group(2)}"
                        ts = datetime.datetime.strptime(dt_str, "%Y%m%d %H%M%S")
                    events.append({
                        'hostname': host,
                        'username': host,
                        'ip': last_ip,
                        'filename': fn,
                        'timestamp': ts
                    })
    return events

@app.route('/refresh')
def refresh():
    events = parse_logs()
    LogSummary.query.delete()
    FileLog.query.delete()
    counts = {}
    for e in events:
        key = (e['hostname'], e['ip'])
        counts[key] = counts.get(key,0) + 1
    for (h,ip),c in counts.items():
        db.session.add(LogSummary(hostname=h, ip=ip, count=c))
    for e in events:
        db.session.add(FileLog(**e))
    db.session.commit()
    return jsonify(status='ok')

# Summary view
@app.route('/')
def summary_view():
    refresh()

    # Забираємо фільтри
    hostname  = request.args.get('hostname')
    ip        = request.args.get('ip')
    date_from = request.args.get('from')  # формат 'YYYY-MM-DD'
    date_to   = request.args.get('to')

    # Збираємо дані з FileLog, а не з LogSummary —
    # щоб фільтрувати по датах
    q = db.session.query(
        FileLog.hostname,
        FileLog.ip,
        func.count(FileLog.id).label('count')
    )

    # Фільтруємо по парс-даті
    if hostname:
        q = q.filter(FileLog.hostname == hostname)
    if ip:
        q = q.filter(FileLog.ip == ip)
    if date_from:
        dt_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        q = q.filter(FileLog.timestamp >= dt_from)
    if date_to:
        # додаємо 1 день, щоб включити весь «to»-день
        dt_to = datetime.datetime.strptime(date_to, '%Y-%m-%d') + datetime.timedelta(days=1)
        q = q.filter(FileLog.timestamp < dt_to)

    # Групуємо за користувачем і IP
    q = q.group_by(FileLog.hostname, FileLog.ip)
    rows = q.all()

    # Підтягнемо варіанти для селектів
    hostnames = db.session.query(FileLog.hostname).distinct().all()
    ips       = db.session.query(FileLog.ip).distinct().all()

    # Підбираємося до структури, яку потребує report.html
    data = [{'hostname': r.hostname, 'ip': r.ip, 'count': r.count} for r in rows]

    return render_template(
        'report.html',
        data=data,
        hostnames=hostnames,
        ips=ips,
        filters={
            'hostname': hostname or '',
            'ip': ip or '',
            'from': date_from or '',
            'to': date_to or ''
        }
    )

# JSON for Chart.js
@app.route('/api/report')
def api_report():
    # так само фільтруємо за GET-параметрами
    hostname = request.args.get('hostname')
    ip       = request.args.get('ip')
    date_from= request.args.get('from')
    date_to  = request.args.get('to')

    q = db.session.query(
        FileLog.hostname,
        FileLog.ip,
        func.count(FileLog.id).label('count')
    )
    if hostname:
        q = q.filter(FileLog.hostname==hostname)
    if ip:
        q = q.filter(FileLog.ip==ip)
    if date_from:
        dtf = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        q = q.filter(FileLog.timestamp>=dtf)
    if date_to:
        dtt = datetime.datetime.strptime(date_to, '%Y-%m-%d') + datetime.timedelta(days=1)
        q = q.filter(FileLog.timestamp<dtt)

    q = q.group_by(FileLog.hostname, FileLog.ip)
    rows = q.all()
    return jsonify([{'hostname':r.hostname,'ip':r.ip,'count':r.count} for r in rows])

# User detail view
@app.route('/user/<username>')
def user_view(username):
    # щоб дані були актуальні
    refresh()

    # фільтри з GET-параметрів
    ip_filter   = request.args.get('ip')
    date_from   = request.args.get('from')  # формат YYYY-MM-DD
    date_to     = request.args.get('to')

    # базовий запит по юзеру
    q = FileLog.query.filter_by(username=username)

    # застосовуємо фільтр за IP
    if ip_filter:
        q = q.filter(FileLog.ip == ip_filter)

    # фільтруємо за початковою датою
    if date_from:
        dt_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        q = q.filter(FileLog.timestamp >= dt_from)

    # фільтруємо за кінцевою датою (включно)
    if date_to:
        dt_to = datetime.datetime.strptime(date_to, '%Y-%m-%d') + datetime.timedelta(days=1)
        q = q.filter(FileLog.timestamp < dt_to)

    logs = q.order_by(FileLog.timestamp.desc()).all()

    # список IP для селекту
    ips = db.session.query(FileLog.ip)\
        .filter(FileLog.username==username)\
        .distinct().all()

    return render_template(
        'user.html',
        username=username,
        logs=logs,
        ips=ips,
        filters={
            'ip': ip_filter or '',
            'from': date_from or '',
            'to': date_to or ''
        }
    )

@app.route('/api/user/<username>')
def api_user(username):
    data = db.session.query(FileLog.ip, func.count(FileLog.id))\
        .filter(FileLog.username==username).group_by(FileLog.ip).all()
    return jsonify([{'ip':ip,'count':c} for ip,c in data])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
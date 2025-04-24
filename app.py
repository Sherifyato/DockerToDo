from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

task_priorities = ('low', 'medium', 'high')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    done = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='medium')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'done': self.done,
            'priority': self.priority
        }

@app.before_first_request
def create_tables():
    db.create_all()

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        abort(400, description='Invalid date format; use YYYY-MM-DD.')

@app.route('/tasks', methods=['GET'])
def get_tasks():
    query = Task.query
    completed = request.args.get('completed')
    if completed is not None:
        if completed.lower() not in ('true', 'false'):
            abort(400, description='completed must be true or false')
        query = query.filter_by(done=(completed.lower() == 'true'))
    due = request.args.get('due_date')
    if due:
        due_date = parse_date(due)
        query = query.filter_by(due_date=due_date)
    priority = request.args.get('priority')
    if priority:
        if priority not in task_priorities:
            abort(400, description=f'priority must be one of {task_priorities}')
        query = query.filter_by(priority=priority)
    tasks = query.all()
    return jsonify([t.to_dict() for t in tasks]), 200

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json() or {}
    title = data.get('title')
    if not title:
        abort(400, description='Title is required')
    desc = data.get('description')
    due_date = parse_date(data['due_date']) if data.get('due_date') else None
    priority = data.get('priority', 'medium')
    if priority not in task_priorities:
        abort(400, description=f'priority must be one of {task_priorities}')
    task = Task(title=title, description=desc, due_date=due_date, priority=priority)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict()), 200

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or {}
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'due_date' in data:
        task.due_date = parse_date(data['due_date'])
    if 'done' in data:
        task.done = bool(data['done'])
    if 'priority' in data:
        if data['priority'] not in task_priorities:
            abort(400, description=f'priority must be one of {task_priorities}')
        task.priority = data['priority']
    db.session.commit()
    return jsonify(task.to_dict()), 200

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

@app.route('/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = True
    db.session.commit()
    return jsonify(task.to_dict()), 200

@app.route('/tasks/<int:task_id>/incomplete', methods=['PUT'])
def incomplete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = False
    db.session.commit()
    return jsonify(task.to_dict()), 200

@app.route('/tasks/<int:task_id>/priority', methods=['PUT'])
def update_priority(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or {}
    new_prio = data.get('priority')
    if not new_prio or new_prio not in task_priorities:
        abort(400, description=f'priority must be one of {task_priorities}')
    task.priority = new_prio
    db.session.commit()
    return jsonify(task.to_dict()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

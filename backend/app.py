from flask import Flask, jsonify, request
from flask_cors import CORS
from plan_generator import generate_plan
import pymysql
from config import DB_CONFIG, PLAN_TABLE

app = Flask(__name__)
CORS(app)

def get_plan_from_db():
    connection = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {PLAN_TABLE} ORDER BY id ASC")
            plan = cursor.fetchall()
        return plan
    finally:
        connection.close()

@app.route('/api/plan', methods=['GET'])
def get_plan():
    plan = get_plan_from_db()
    return jsonify(plan)

@app.route('/api/plan/generate', methods=['POST'])
def generate_plan_endpoint():
    _ = generate_plan()
    plan = get_plan_from_db()
    return jsonify(plan)

if __name__ == '__main__':
    app.run(port=5000, debug=True)

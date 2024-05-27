from flask import Flask, request, abort, jsonify

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import time
import traceback
import sqlite3
#======python的函數庫==========


app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount INTEGER NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 插入交易记录
def insert_transaction(trans_type, category, amount, date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('INSERT INTO transactions (type, category, amount, date) VALUES (?, ?, ?, ?)', 
              (trans_type, category, amount, date))
    conn.commit()
    conn.close()

# 查询当天总支出
def query_today_total(date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM transactions WHERE date = ? AND type = "支出"', (date,))
    total_expense = c.fetchone()[0] or 0
    conn.close()
    return total_expense

# 查询本月结余
def query_monthly_balance(month):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM transactions WHERE date LIKE ? AND type = "支出"', (f'{month}%',))
    total_expense = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE date LIKE ? AND type = "收入"', (f'{month}%',))
    total_income = c.fetchone()[0] or 0
    conn.close()
    balance = total_income - total_expense
    return total_income, total_expense, balance

# 生成多样版组合按钮消息
def generate_template_message(alt_text, title, text, actions):
    return {
        "type": "template",
        "altText": alt_text,
        "template": {
            "type": "buttons",
            "title": title,
            "text": text,
            "actions": actions
        }
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data['events'][0]['message']['text']
    reply_token = data['events'][0]['replyToken']
    response_message = ""

    if message == "記帳":
        actions = [
            {"type": "message", "label": "支出", "text": "支出"},
            {"type": "message", "label": "收入", "text": "收入"}
        ]
        response_message = generate_template_message("記帳", "記帳選單", "請選擇支出或收入", actions)
    elif message == "支出":
        actions = [
            {"type": "message", "label": "飲食類", "text": "飲食類"},
            {"type": "message", "label": "日常類", "text": "日常類"},
            {"type": "message", "label": "娛樂類", "text": "娛樂類"},
            {"type": "message", "label": "其他", "text": "其他"}
        ]
        response_message = generate_template_message("支出", "支出選單", "請選擇支出類別", actions)
    elif message == "查看帳本":
        actions = [
            {"type": "message", "label": "查詢本日累積", "text": "查詢本日累積"},
            {"type": "message", "label": "統計本月結餘", "text": "統計本月結餘"}
        ]
        response_message = generate_template_message("查看帳本", "查看帳本選單", "請選擇查詢方式", actions)
    elif message in ["飲食類", "日常類", "娛樂類", "其他"]:
        response_message = {
            "type": "text",
            "text": f"請輸入 {message} 支出金額，例如: {message} 100 元"
        }
    elif "元" in message:
        parts = message.split()
        category = parts[0]
        amount = int(parts[1].replace("元", ""))
        date = datetime.now().strftime("%Y-%m-%d")
        insert_transaction("支出", category, amount, date)
        response_message = {
            "type": "text",
            "text": f"已記錄 {category} 支出 {amount} 元"
        }
    elif message == "查詢本日累積":
        date = datetime.now().strftime("%Y-%m-%d")
        total_expense = query_today_total(date)
        response_message = {
            "type": "text",
            "text": f"今日支出總和為 {total_expense} 元"
        }
    elif message == "統計本月結餘":
        month = datetime.now().strftime("%Y-%m")
        total_income, total_expense, balance = query_monthly_balance(month)
        response_message = {
            "type": "text",
            "text": f"本月收入總和為 {total_income} 元，支出總和為 {total_expense} 元，結餘為 {balance} 元"
        }
    else:
        response_message = {
            "type": "text",
            "text": "無效的指令"
        }

    return jsonify({
        'replyToken': reply_token,
        'messages': [response_message]
    })

if __name__ == '__main__':
    app.run(port=5000)


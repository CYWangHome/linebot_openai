from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

app = Flask(__name__)
# Channel Access Token
line_bot_api = LineBotApi('dR8PuPiW2RtOoJiBdPttAWPYH4hLrc0VJZBUGyMh3p2t9ySc+ktRH91CbyBc62kXEJJbCM4QyFZQm6HhatTLZlCvtDPfF2honnDhtCZLuS8gMkt9rmh+Cc/R+UDPJiYRyXEnJQ2j6uATOaSDGCSSdQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('a8a76843cdb27f5cf9c0f72958cb9e4e')

# 初始化資料庫和靜態目錄
def init_app():
    init_db()
    if not os.path.exists('static'):
        os.makedirs('static')

# 建立資料庫
def init_db():
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            type TEXT,
            category TEXT,
            amount INTEGER,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def insert_transaction(user_id, trans_type, category, amount, date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)',
              (user_id, trans_type, category, amount, date))
    conn.commit()
    conn.close()

def query_today_total(user_id, date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date = ? AND type = "支出"', (user_id, date))
    total_expense = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date = ? AND type = "收入"', (user_id, date))
    total_income = c.fetchone()[0] or 0
    conn.close()
    balance = total_income - total_expense
    return total_income, total_expense, balance

def query_monthly_balance(user_id, month):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date LIKE ? AND type = "支出"', (user_id, f'{month}%'))
    total_expense = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date LIKE ? AND type = "收入"', (user_id, f'{month}%'))
    total_income = c.fetchone()[0] or 0
    conn.close()
    balance = total_income - total_expense
    return total_income, total_expense, balance

def query_expenses_by_category(user_id, month):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT category, SUM(amount) FROM transactions WHERE user_id = ? AND date LIKE ? AND type = "支出" GROUP BY category', 
              (user_id, f'{month}%'))
    result = c.fetchall()
    conn.close()
    return result

def plot_expense_pie_chart(user_id, month):
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    data = query_expenses_by_category(user_id, month)
    if not data:
        return None
    categories, amounts = zip(*data)
    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    file_path = f'./static/{user_id}_expense_pie_chart.png'
    plt.savefig(file_path)
    plt.close()
    return file_path

def generate_template_message(alt_text, title, text, actions):
    return TemplateSendMessage(
        alt_text=alt_text,
        template=ButtonsTemplate(
            title=title,
            text=text,
            actions=actions
        )
    )

def generate_pie_chart(user_id):
    date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND date = ? GROUP BY type', (user_id, date))
    result = c.fetchall()
    conn.close()

    if not result:
        return None

    labels, amounts = zip(*result)
    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    file_path = f'./static/{user_id}_daily_pie_chart.png'
    plt.savefig(file_path)
    plt.close()
    return file_path

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Signature verification failed', 400

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message = event.message.text
    reply_token = event.reply_token
    
    if message == "記帳":
        actions = [
            MessageAction(label="支出", text="支出"),
            MessageAction(label="收入", text="收入")
        ]
        response_message = generate_template_message("記帳", "記帳選單", "請選擇支出或收入", actions)
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "支出":
        actions = [
            MessageAction(label="飲食類", text="飲食類"),
            MessageAction(label="日常類", text="日常類"),
            MessageAction(label="娛樂類", text="娛樂類"),
            MessageAction(label="其他", text="其他")
        ]
        response_message = generate_template_message("支出", "支出選單", "請選擇支出類別", actions)
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "收入":
        response_message = TextSendMessage(text="請輸入收入金額，例如: 收入 1000 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "查看帳本":
        actions = [
            MessageAction(label="查詢本日累積", text="查詢本日累積"),
            MessageAction(label="統計本月結餘", text="統計本月結餘"),
            MessageAction(label="支出圓形圖", text="支出圓形圖"),
        ]
        response_message = generate_template_message("查看帳本", "查看帳本選單", "請選擇查詢方式", actions)
        line_bot_api.reply_message(reply_token, response_message)
    elif message in ["飲食類", "日常類", "娛樂類", "其他"]:
        response_message = TextSendMessage(text=f"請輸入 {message} 支出金額，例如: {message} 100 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif "元" in message and any(category in message for category in ["飲食類", "日常類", "娛樂類", "其他"]):
        parts = message.split()
        category = parts[0]
        try:
            amount = int(parts[1].replace("元", ""))
            date = datetime.now().strftime("%Y-%m-%d")
            insert_transaction(user_id, "支出", category, amount, date)
            response_message = TextSendMessage(text=f"已記錄 {category} 支出 {amount} 元")
        except ValueError:
            response_message = TextSendMessage(text="請確保金額為有效的整數，例如: 飲食類 100 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif "收入" in message:
        parts = message.split()
        try:
            amount = int(parts[1].replace("元", ""))
            date = datetime.now().strftime("%Y-%m-%d")
            insert_transaction(user_id, "收入", "收入", amount, date)
            response_message = TextSendMessage(text=f"已記錄收入 {amount} 元")
        except ValueError:
            response_message = TextSendMessage(text="請確保金額為有效的整數，例如: 收入 1000 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "查詢本日累積":
        date = datetime.now().strftime("%Y-%m-%d")
        total_income, total_expense, balance = query_today_total(user_id, date)
        if total_income == 0 and total_expense == 0:
            response_message = TextSendMessage(text="目前並無紀錄！")
        else:
            response_message = TextSendMessage(text=f"今日收入總和為 {total_income} 元，支出總和為 {total_expense} 元，結餘為 {balance} 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "統計本月結餘":
        month = datetime.now().strftime("%Y-%m")
        total_income, total_expense, balance = query_monthly_balance(user_id, month)
        if total_income == 0 and total_expense == 0:
            response_message = TextSendMessage(text="目前並無紀錄！")
        else:
            response_message = TextSendMessage(text=f"本月收入總和為 {total_income} 元，支出總和為 {total_expense} 元，結餘為 {balance} 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "支出圓形圖":
        month = datetime.now().strftime("%Y-%m")
        chart_path = plot_expense_pie_chart(user_id, month)
        if chart_path:
            image_message = ImageSendMessage(original_content_url=f"{request.url_root}static/{os.path.basename(chart_path)}",
                                             preview_image_url=f"{request.url_root}static/{os.path.basename(chart_path)}")
            line_bot_api.reply_message(reply_token, image_message)
        else:
            response_message = TextSendMessage(text="目前並無支出紀錄！")
            line_bot_api.reply_message(reply_token, response_message)
    else:
        response_message = TextSendMessage(text="無效的指令")
        line_bot_api.reply_message(reply_token, response_message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

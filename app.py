from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 設置 Channel Access Token 和 Channel Secret
line_bot_api = LineBotApi('dR8PuPiW2RtOoJiBdPttAWPYH4hLrc0VJZBUGyMh3p2t9ySc+ktRH91CbyBc62kXEJJbCM4QyFZQm6HhatTLZlCvtDPfF2honnDhtCZLuS8gMkt9rmh+Cc/R+UDPJiYRyXEnJQ2j6uATOaSDGCSSdQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('a8a76843cdb27f5cf9c0f72958cb9e4e')  # 你需要將這個值替換為你的 Channel Secret

def insert_transaction(trans_type, category, amount, date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('INSERT INTO transactions (type, category, amount, date) VALUES (?, ?, ?, ?)', (trans_type, category, amount, date))
    conn.commit()
    conn.close()

def query_today_total(date):
    conn = sqlite3.connect('accounting.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM transactions WHERE date = ? AND type = "支出"', (date,))
    total_expense = c.fetchone()[0] or 0
    conn.close()
    return total_expense

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

def generate_template_message(alt_text, title, text, actions):
    return TemplateSendMessage(
        alt_text=alt_text,
        template=ButtonsTemplate(
            title=title,
            text=text,
            actions=actions
        )
    )

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
    elif message == "查看帳本":
        actions = [
            MessageAction(label="查詢本日累積", text="查詢本日累積"),
            MessageAction(label="統計本月結餘", text="統計本月結餘")
        ]
        response_message = generate_template_message("查看帳本", "查看帳本選單", "請選擇查詢方式", actions)
        line_bot_api.reply_message(reply_token, response_message)
    elif message in ["飲食類", "日常類", "娛樂類", "其他"]:
        response_message = TextSendMessage(text=f"請輸入 {message} 支出金額，例如: {message} 100 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif "元" in message:
        parts = message.split()
        category = parts[0]
        amount = int(parts[1].replace("元", ""))
        date = datetime.now().strftime("%Y-%m-%d")
        insert_transaction("支出", category, amount, date)
        response_message = TextSendMessage(text=f"已記錄 {category} 支出 {amount} 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "查詢本日累積":
        date = datetime.now().strftime("%Y-%m-%d")
        total_expense = query_today_total(date)
        response_message = TextSendMessage(text=f"今日支出總和為 {total_expense} 元")
        line_bot_api.reply_message(reply_token, response_message)
    elif message == "統計本月結餘":
        month = datetime.now().strftime("%Y-%m")
        total_income, total_expense, balance = query_monthly_balance(month)
        response_message = TextSendMessage(text=f"本月收入總和為 {total_income} 元，支出總和為 {total_expense} 元，結餘為 {balance} 元")
        line_bot_api.reply_message(reply_token, response_message)
    else:
        response_message = TextSendMessage(text="無效的指令")
        line_bot_api.reply_message(reply_token, response_message)

if __name__ == '__main__':
    app.run(port=5000)

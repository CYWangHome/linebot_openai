from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
# openai.api_key = os.getenv('OPENAI_API_KEY')


def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # 獲取請求體
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    if re.match('支出', user_message):  # Use user_message for clarity
        try:
            carousel_template_message = TemplateSendMessage(
                alt_text='Expense Category Selection',  # English translation
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            thumbnail_image_url='https://i.imgur.com/wpM584d.jpg',
                            title='Choose Expense Category',  # English translation
                            text='Available Categories',  # English translation
                            actions=[
                                MessageAction(
                                    label='Food',
                                    text='食物'  # Keep in Chinese for category
                                ),
                                MessageAction(
                                    label='Drinks',
                                    text='飲品'  # Keep in Chinese for category
                                )
                            ]
                        )
                    ]
                )
            )
            line_bot_api.reply_message(
                event.reply_token, carousel_template_message)
        except Exception as e:
            # Handle potential errors during message processing (optional)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text="An error occurred. Please try again."))
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=user_message))
pos_acc = {}
neg_acc = {}
@handler.add(MessageEvent, message=TextMessage)

def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if text == "記帳":
        reply_text = "請輸入「支出」或「收入」"
    elif text == "查看帳本":
        reply_text = check_account(user_id)
    elif text.startswith("收入") or text.startswith("支出"):
        reply_text = handle_account_input(user_id, text)
    else:
        reply_text = "請使用「記帳」或「查看帳本」"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def check_account(user_id):
    if user_id in pos_acc or user_id in neg_acc:
        pos_total = sum(pos_acc.get(user_id, []))
        neg_total = sum(neg_acc.get(user_id, []))
        total = pos_total - neg_total
        if total > 0:
            return f"目前淨收入：{total} 元"
        elif total == 0:
            return f"目前收支平衡"
        else:
            bad_total = -total
            return f"目前透支：{bad_total} 元"
    else:
        return "目前無任何記錄"

def handle_account_input(user_id, text):
    if text.startswith("收入"):
        try:
            amount = int(text.split(" ")[1])
            if user_id in pos_acc:
                pos_acc[user_id].append(amount)
            else:
                pos_acc[user_id] = [amount]
            return f"已紀錄：{amount} 元"
        except (IndexError, ValueError):
            return "格式錯誤！請輸入'收入 XXX'"
    elif text.startswith("支出"):
        try:
            amount = int(text.split(" ")[1])
            if user_id in neg_acc:
                neg_acc[user_id].append(amount)
            else:
                neg_acc[user_id] = [amount]
            return f"已紀錄：{amount} 元"
        except (IndexError, ValueError):
            return "格式錯誤！請輸入'支出 XXX'"
    else:
        return "格式錯誤！請輸入「支出」或「收入」"


import os
if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5000))
    app.run(debug = True, host='0.0.0.0', port=80)

from flask import Flask, request, abort

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
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
# openai.api_key = os.getenv('OPENAI_API_KEY')


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

pos_acc = {}
neg_acc = {}
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if text == "支出":
        try:
            carousel_template_message = TemplateSendMessage(
                alt_text='選擇支出的類別',
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            thumbnail_image_url='https://img.ltn.com.tw/Upload/health/page/800/2022/03/10/phpiUjDmR.jpg',
                            title='飲食類',
                            text='請選擇以下支出類別',
                            actions=[
                                MessageAction(label='食物', text='食物'),
                                MessageAction(label='飲品', text='飲品')
                            ]
                        ),
                        CarouselColumn(
                            thumbnail_image_url='https://i.pinimg.com/564x/84/b2/4f/84b24faffd26e09b6492ff7ce73706a4.jpg',
                            title='日常類',
                            text='請選擇以下支出類別',
                            actions=[
                                MessageAction(label='交通', text='交通'),
                                MessageAction(label='日常用品', text='日常用品'),
                                MessageAction(label='居家', text='居家')
                            ]
                        ),
                        CarouselColumn(
                            thumbnail_image_url='https://i.pinimg.com/564x/50/f6/f7/50f6f731a2ca23aa58cfe4f776ca80a8.jpg',
                            title='娛樂類',
                            text='請選擇以下支出類別',
                            actions=[
                                MessageAction(label='衣服配件', text='衣服配件'),
                                MessageAction(label='交際娛樂', text='交際娛樂')
                            ]
                        ),
                        CarouselColumn(
                            thumbnail_image_url='https://i.pinimg.com/564x/42/c5/b6/42c5b646d387eedfaf212624f3699a92.jpg',
                            title='其他',
                            text='請選擇以下支出類別',
                            actions=[
                                MessageAction(label='醫療', text='醫療'),
                                MessageAction(label='其他', text='其他')
                            ]
                        )
                    ]
                )
            )
            line_bot_api.reply_message(event.reply_token, carousel_template_message)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text=f"An error occurred: {str(e)}. Please try again."))
            app.logger.error(f"Error: {traceback.format_exc()}")

    elif text == "記帳":
        reply_text = "請輸入「支出」或「收入」"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    
    elif text == "查看帳本":
        reply_text = check_account(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    
    elif text == "收入" or text == "支出":
        reply_text = handle_account_input(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    
    else:
        reply_text = "請使用「記帳」或「查看帳本」"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))


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
            return f"已紀錄：-{amount} 元"
        except (IndexError, ValueError):
            return "格式錯誤！請輸入'支出 XXX'"
    else:
        return "格式錯誤！請輸入「支出」或「收入」"


import os
if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5000))
    app.run(debug = True, host='0.0.0.0', port=80)

from telethon import TelegramClient, events
from telethon.tl.types import User, MessageMediaPhoto
from dotenv import load_dotenv
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
import time
import logging
import sys
import pyautogui

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
target_group = int(os.getenv('TARGET_GROUP'))
excluded_group_ids = os.getenv('EXCLUDED_GROUP_IDS', '').split(',')

user_client = TelegramClient('user_session', api_id, api_hash)

bot_client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

keyword = 'open.kakao.com'  # 감지하고자 하는 키워드
exclude_keywords = ['하양이아빠', 'XPLA', '크몽', '젬하다']  # 제외할 키워드 목록

image_dir = 'image/'

if getattr(sys, 'frozen', False):
    chromedriver_path = os.path.join(sys._MEIPASS, 'chromedriver-win64', 'chromedriver.exe')
else:
    chromedriver_path = os.path.abspath('chromedriver-win64/chromedriver.exe').replace("\\", "/")

chrome_service = ChromeService(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=chrome_service)

def extract_urls(text):
    url_pattern = re.compile(r'(https?://\S+)')
    return url_pattern.findall(text)

def extract_hyperlink_urls(message):
    urls = []
    if message.entities:
        for entity in message.entities:
            if hasattr(entity, 'url'):
                urls.append(entity.url)
    return urls

async def send_message_via_bot(bot_client, target_group, message_text, media=None):
    try:
        await bot_client.send_message(target_group, message_text, file=media)
        logging.info(f"Bot sent message to {target_group}")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def perform_clicks():
    coordinates = [(2037, 580), (2157, 306), (2048, 503)]
    interval = 0.2

    for x, y in coordinates:
        pyautogui.moveTo(x, y, duration=0.1)
        pyautogui.click()
        time.sleep(interval)

@user_client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    sender_id = event.chat_id

    if isinstance(sender, User) and sender.bot:
        return

    if str(sender_id) in excluded_group_ids:
        logging.info(f"Message from excluded group/channel {sender_id} ignored.")
        return

    message_text = event.message.message

    if any(exclude_keyword in message_text for exclude_keyword in exclude_keywords):
        logging.info(f"Message containing exclude keywords {exclude_keywords} ignored.")
        return

    # 메시지에서 URL 추출
    urls = extract_urls(message_text)
    # 메시지의 텍스트 하이퍼링크에서 URL 추출
    urls.extend(extract_hyperlink_urls(event.message))
    
    # 메시지 미디어에서 URL 추출
    if event.message.media:
        if hasattr(event.message.media, 'webpage') and hasattr(event.message.media.webpage, 'url'):
            urls.append(event.message.media.webpage.url)
    
    # 특정 키워드가 포함된 링크가 있는지 확인
    keyword_urls = [url for url in urls if keyword in url]
    
    # 중복 제거
    keyword_urls = list(set(keyword_urls))

    if keyword_urls:
        # 메시지 재구성 및 전송 (봇이 메시지 전송)
        try:
            message_to_send = f"Keyword detected message:\n{message_text}\n\nLinks:\n"
            for url in keyword_urls:
                message_to_send += f"{url}\n"
            
            # 이미지가 있는 경우 이미지와 함께 전송
            if event.message.media and isinstance(event.message.media, MessageMediaPhoto):
                # 이미지 저장 디렉토리 생성
                if not os.path.exists(image_dir):
                    os.makedirs(image_dir)
                
                photo_path = await event.download_media(file=image_dir)
                await send_message_via_bot(bot_client, target_group, message_to_send, media=photo_path)
            else:
                await send_message_via_bot(bot_client, target_group, message_to_send)
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

        # 키워드가 포함된 링크에 접속
        for url in keyword_urls:
            try:
                driver.get(url)
                logging.info(f'Opened URL: {url}')
                time.sleep(2.5)  # 페이지 로드 대기
                # 버튼 클릭
                try:
                    button = driver.find_element(By.CSS_SELECTOR, 'button')
                    button.click()
                    logging.info('Clicked the button')
                    time.sleep(2.5)
                    # 특정 좌표로 이동 및 클릭
                    perform_clicks()
                except Exception as e:
                    logging.error(f'Failed to click the button: {e}')
            except Exception as e:
                logging.error(f'Failed to open URL: {e}')

async def main():
    async with user_client, bot_client:
        await user_client.start()
        logging.info("User client started")
        await bot_client.start(bot_token=bot_token)
        logging.info("Bot client started")
        await user_client.run_until_disconnected()

if __name__ == '__main__':
    try:
        user_client.loop.run_until_complete(main())
    finally:
        driver.quit()
        bot_client.disconnect()

from telethon import TelegramClient, events
from telethon.tl.types import User, MessageMediaPhoto
from telethon.tl.functions.messages import ForwardMessagesRequest
from dotenv import load_dotenv
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
import time
import logging
import sys

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 설정
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
target_channel = int(os.getenv('TARGET_CHANNEL'))
excluded_group_ids = os.getenv('EXCLUDED_GROUP_IDS', '').split(',')

# 클라이언트 초기화
client = TelegramClient('session_name', api_id, api_hash)

keyword = 'open.kakao.com'  # 감지하고자 하는 키워드
exclude_keyword = '하양이아빠'  # 제외할 키워드

# 실행 파일이 위치한 디렉토리 경로
if getattr(sys, 'frozen', False):
    chromedriver_path = os.path.join(sys._MEIPASS, 'chromedriver-win64', 'chromedriver.exe')
else:
    chromedriver_path = os.path.abspath('chromedriver-win64/chromedriver.exe').replace("\\", "/")

chrome_service = ChromeService(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=chrome_service)

def extract_urls(text):
    url_pattern = re.compile(r'(https?://\S+)')
    return url_pattern.findall(text)

@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    sender_id = event.chat_id

    # 발신자가 사용자이고, 봇이 보낸 메시지는 무시
    if isinstance(sender, User) and sender.bot:
        return

    # 제외할 그룹 및 채널에서의 메시지는 무시
    if str(sender_id) in excluded_group_ids:
        logging.info(f"Message from excluded group/channel {sender_id} ignored.")
        return

    message_text = event.message.message

    # 제외할 키워드가 포함된 메시지는 무시
    if exclude_keyword in message_text:
        logging.info(f"Message containing exclude keyword '{exclude_keyword}' ignored.")
        return

    # 메시지에서 URL 추출
    urls = extract_urls(message_text)
    
    # 메시지 미디어에서 URL 추출
    if event.message.media:
        if hasattr(event.message.media, 'webpage') and hasattr(event.message.media.webpage, 'url'):
            urls.append(event.message.media.webpage.url)
    
    # 특정 키워드가 포함된 링크가 있는지 확인
    keyword_urls = [url for url in urls if keyword in url]

    if keyword_urls:
        # 메시지 포워딩
        try:
            await client(ForwardMessagesRequest(
                from_peer=event.chat_id,
                id=[event.message.id],
                to_peer=target_channel
            ))
            logging.info(f"Forwarded message to {target_channel}")
        except Exception as e:
            logging.error(f"Failed to forward message: {e}")

        # 키워드가 포함된 링크에 접속
        for url in keyword_urls:
            try:
                driver.get(url)
                logging.info(f'Opened URL: {url}')
                time.sleep(3)  # 페이지 로드 대기
                # 버튼 클릭
                try:
                    button = driver.find_element(By.CSS_SELECTOR, 'button')
                    button.click()
                    logging.info('Clicked the button')
                except Exception as e:
                    logging.error(f'Failed to click the button: {e}')
            except Exception as e:
                logging.error(f'Failed to open URL: {e}')

async def main():
    async with client:
        await client.start()
        logging.info("Client Created")
        await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        client.loop.run_until_complete(main())
    finally:
        driver.quit()

import os
import time
import requests
from urllib.parse import urljoin, unquote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Chrome WebDriver 설정
BASE_URL = "https://www.koreaboardgames.com"
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rulebooks')

# Selenium WebDriver 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 화면 없이 실행
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

def download_rulebook(game_name, url):
    game_dir = os.path.join(PDF_DIR, game_name)
    os.makedirs(game_dir, exist_ok=True)
    driver.get(url)
    try:
        # PDF 링크가 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "body > div.wrapper > div.container > section > div.file_wrap > div > a")
            )
        )
        # 모든 PDF 링크 가져오기
        pdf_links = driver.find_elements(
            By.CSS_SELECTOR, "body > div.wrapper > div.container > section > div.file_wrap > div > a"
        )
        for pdf_link in pdf_links:
            pdf_url = pdf_link.get_attribute("href")
            filename = unquote(pdf_url.split("orgFileName=")[-1].split("&")[0])
            response = requests.get(pdf_url, stream=True)
            if response.status_code == 200:
                filepath = os.path.join(game_dir, filename)
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"Downloaded: {filename}")
            else:
                print(f"Failed to download: {url}")

    except Exception as e:
        print(f"PDF 링크를 찾을 수 없음: {url}, 오류: {e}")

def crawl_rulebooks():
    """규칙서 크롤링"""
    os.makedirs(PDF_DIR, exist_ok=True)
    print("규칙서 크롤링 시작")

    list_url = urljoin(BASE_URL, "magazine/magazineMenu")
    driver.get(list_url)

    # roleList가 로드될 때까지 대기
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "roleList")))

    # 동적으로 로드된 리스트 가져오기
    items = driver.find_elements(By.CSS_SELECTOR, "#roleList li > a")
    urls = []
    for item in items:
        title = item.find_element(By.CSS_SELECTOR, "div.info > strong").get_attribute("innerText")
        print(title)
        if not "규칙서" in title:
            continue
        game_name = title.split("규칙서")[0].strip()
        url = item.get_attribute("href")
        urls.append((game_name, url))
    
    for game_name, url in urls:
        download_rulebook(game_name, url)

if __name__ == "__main__":
    crawl_rulebooks()
    driver.quit()
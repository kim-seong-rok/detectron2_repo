import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
import urllib.request
# mysqlclient install error 발생 시 sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
import MySQLdb
import boto3
from botocore.client import Config
import schedule

# 네이버 쇼핑 크롤링 함수 생성
def naver_crawling():
    # MySQL접속
    conn = MySQLdb.connect(
        user="admin",
        passwd="rladbdbsDL!",
        host="db-3team-project.ckirsmdzwudh.ap-northeast-2.rds.amazonaws.com",
        db="security"
    )
    # 커서 생성
    cursor = conn.cursor()
    # 실행시마다 다른 값이 나오지 않게 테이블 제거
    # cursor.execute("DROP TABLE IF EXISTS imgs")
    cursor.execute("DROP TABLE IF EXISTS test_imgs1")
    # 테이블 생성하기
    # cursor.execute("CREATE TABLE imgs (name text, url text)")
    cursor.execute("CREATE TABLE test_imgs1 (name text, url text)")

    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # driver = ChromeDriverManager 최신화 및 기본설정(아래 options 없으면 에러)
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    # crawling_data = [["남자","반팔", 500],["남자","긴팔티", 250],["남자","맨투맨", 250],["남자","셔츠", 250],
    #                 ["남자","후드", 250],["남자","아우터", 500],["남자","반바지", 500],["남자","바지", 500],
    #                 ["남자","청바지", 500],["여자","반팔", 500],["여자","긴팔티", 250],["여자","맨투맨", 250],
    #                 ["여자","셔츠", 250],["여자","후드", 250],["여자","원피스", 500],["여자","아우터", 500],
    #                 ["여자","반바지", 500],["여자","바지", 500],["여자","청바지", 500],["여자","치마", 500]]
    crawling_data = [["남자", "가디건", 10], ["여자", "코트", 10]]

    for search_sex, search_category, category_count in crawling_data:

        driver.get("https://shopping.naver.com/home")

        # 검색창 찾기 및 검색창에 검색어 입력
        elem = driver.find_element(
            By.CLASS_NAME, "_searchInput_search_text_3CUDs")
        elem.send_keys(search_sex + " " + search_category)
        elem.send_keys(Keys.RETURN)

        # 가격비교 페이지 클릭
        driver.find_element(
            By.XPATH, '//*[@id="__next"]/div/div[2]/div[2]/div[3]/div[1]/div[1]/ul/li[2]/a').click()
        # 파일명을 위한 설정
        if search_sex == "남자":
            search_sex = "men"
        else:
            search_sex = "women"

        if search_category == "반팔":
            search_category = "shortsleeve"
        elif search_category == "긴팔티":
            search_category = "longsleeve"
        elif search_category == "맨투맨":
            search_category = "sweatshirt"
        elif search_category == "셔츠":
            search_category = "shirt"
        elif search_category == "후드":
            search_category = "hoodie"
        elif search_category == "원피스":
            search_category = "onepiece"
        elif search_category == "아우터":
            search_category = "outer"
        elif search_category == "반바지":
            search_category = "shorts"
        elif search_category == "바지":
            search_category = "pants"
        elif search_category == "청바지":
            search_category = "jeans"
        elif search_category == "치마":
            search_category = "skirt"

        max_count = 1

        while True:
            # 스크롤 최하단으로 내려 정보 로드 후 다시 최상단으로 올리기.
            # driver.execute_script: 자바스크립트를 파이썬으로 받기.
            # return document.body.scrollHeight: 현재 스크롤 높이.
            last_height = driver.execute_script(
                "return document.body.scrollHeight")
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0)")
            scroll_location = driver.execute_script(
                "return window.pageYOffset")

            count = 0
            # 네이버 쇼핑 검색 리스트가 40개씩 나옴. 페이지당 정보 가져오는 반복문.
            images = driver.find_elements(
                By.CLASS_NAME, "thumbnail_thumb__Bxb6Z")
            for image in images:
                try:
                    str_count = str(count+1)
                    # 스크롤 천천히 내리기.
                    scroll_height = driver.execute_script(
                        "return document.body.scrollHeight")
                    if scroll_location == scroll_height:
                        break
                    else:
                        driver.execute_script(
                            "window.scrollTo(0,{})".format(scroll_location + 180))
                        time.sleep(1)
                        scroll_location = driver.execute_script(
                            "return window.pageYOffset")

                    # 해당 이미지 상품 판매 url
                    imgUrl = driver.find_element(
                        By.XPATH, '//*[@id="__next"]/div/div[2]/div[2]/div[3]/div[1]/ul/div/div['+str_count+']/li/div/div[1]/div/a').get_attribute("href")

                    image.click()
                    time.sleep(1)

                    # 클릭한 url로 접속한 탭으로 driver 변경
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(1)

                    # 이미지 자체 path
                    imgPath = driver.find_element(
                        By.XPATH, '//*[@id="__next"]/div/div[2]/div[2]/div[2]/div[1]/div/div[1]/div/div/img').get_attribute("src")

                    # 파일명
                    imgname = search_sex + "_" + search_category + \
                        "_" + str(max_count) + ".jpg"

                    # 저장(저장하는 파일 경로, 파일명)
                    urllib.request.urlretrieve(imgPath, imgname)

                    # s3 접속 경로
                    bucket = 'image-storage01'
                    s3 = boto3.resource(
                        's3',
                        aws_access_key_id='AKIAQ6KXNZNKVYPMXE5Y',
                        aws_secret_access_key='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',
                        config=Config(signature_version='s3v4')
                    )

                    # S3 파일 업로드
                    data = open(imgname, 'rb')
                    s3.Bucket(bucket).put_object(
                        Key=imgname, Body=data, ContentType='image/jpg')

                    # MySQL DB에 데이터 저장
                    # cursor.execute(f"INSERT INTO imgs VALUES(\"{imgname}\",\"{imgUrl}\")")
                    cursor.execute(
                        f"INSERT INTO test_imgs1 VALUES(\"{imgname}\",\"{imgUrl}\")")
                    conn.commit()

                    count = count + 1
                    max_count = max_count+1
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    if max_count > category_count:
                        # return False
                        break_flag = True
                        break

                except Exception as e:
                    print(e)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[-1])
                    continue
            if break_flag:
                break_flag = False
                break  # while문 빠져 나가기.
            # 다음페이지 클릭
            driver.find_element(
                By.CLASS_NAME, 'pagination_next__pZuC6').click()

    driver.close()
    conn.close()


# schedule.every().wednesday.at("15:06").do(naver_crawling)
# while True:
#     schedule.run_pending()
#     time.sleep(1)

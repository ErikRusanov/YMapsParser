from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime, timezone

# Remove the chromedriver_binary import as we'll use webdriver-manager instead
# import chromedriver_binary  # Adds chromedriver binary to path

import traceback
import argparse, sys
import json_pattern
import util_module
from infogetter import InfoGetter


class GrabberApp:
    def __init__(self, cities, search, count, output_file, columns, driver_name):
        self.cities = cities
        self.search = search
        self.output_file = output_file
        self.count = count
        self.columns = columns
        self.driver_name = driver_name

    def grab_data(self):
        open(self.output_file, "w").close()


        if self.driver_name == "chrome":
            chrome_options = webdriver.ChromeOptions()
#            chrome_options.add_argument("--window-size=1420,1080")
        #        chrome_options.add_argument("--no-sandbox")
        #        chrome_options.add_argument("--headless")
        #        chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--lang=ru")
            chrome_options.add_argument("--accept-lang=ru")
#            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            # Use webdriver-manager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

        if self.driver_name == "safari":
            driver = webdriver.Safari()

        driver.maximize_window()

        for city in self.cities:
            city = city.strip()

            if city == "":
                raise Exception("City is empty")

            for search in self.search:
                search = search.strip()

                if search == "":
                    print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". Search is empty")
                    continue

                driver.get(
                    "https://yandex.ru/maps/1/a/search/"
                    + city
                    + ", "
                    + search
                    + "/"
                )

                sleep(0.8)

                InfoGetter.check_captcha(driver)

                soup = BeautifulSoup(driver.page_source, "lxml")

                print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". Start parse city " + city+ ". Search " + search+". Url "+driver.current_url)

                items_in_page = 0
                old_items_in_page = 0
                cityErrors = 0

                try:
                    for i in range(int(self.count)):

                        try:
                            if (i + 4) > old_items_in_page:
                                items_in_page = driver.execute_script(
                                    "document.getElementsByClassName('search-business-snippet-view')[document.getElementsByClassName('search-business-snippet-view').length -1].scrollIntoView();return document.getElementsByClassName('search-business-snippet-view').length;"
                                )
                                sleep(0.2)

                                if old_items_in_page == items_in_page:
                                    soup = BeautifulSoup(driver.page_source, "lxml")
                                    if not soup.body.findAll(text='если не нашли их на карте'):
                                        print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". old_items_in_page == items_in_page. Load finish")
                                    else:
                                        print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". old_items_in_page == items_in_page. sleep 2")
                                        sleep(2)

                                old_items_in_page = items_in_page

                                print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". Items in page " + str(items_in_page))
                        except Exception as e:
                            print(traceback.format_exc())
                            sleep(1)


                        try:
                            driver.execute_script(
                                "document.getElementsByClassName('search-business-snippet-view')["+ str(i) + "].click();"
                            )
                        except Exception as e:
                            print(traceback.format_exc())
                            print("---------------------------")
                            print("---------------------------")
                            print("---------------------------")
                            break

                        sleep(0.2)

                        soup = BeautifulSoup(driver.page_source, "lxml")

                        InfoGetter.check_captcha(driver)

                        ypage = InfoGetter.get_company_url(soup)

                        print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". "+str(i) + ". "+city+". Get company " + ypage)

                        name = InfoGetter.get_name(soup)
                        address = InfoGetter.get_address(soup)
                        website = InfoGetter.get_website(soup)
                        company_id = InfoGetter.get_company_id(soup)
                        rating = InfoGetter.get_rating(soup)

                        # Проверяем адрес с учетом регистра и разных вариантов написания города
                        city_in_address = (city.lower() in address.lower() or 
                                         city.title() in address or 
                                         city.capitalize() in address)
                        
                        if not city_in_address:
                            cityErrors += 1
                            print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". -- "+ city+". Invalid city in address "+address+". Errors count "+str(cityErrors))
                            print("---------------------------")
                            print("---------------------------")
                            print("---------------------------")

                            if cityErrors < 3:
                                print("continue")
                                continue
                            break


                        cityErrors = 0

                        phones = []
                        # По умолчанию всегда парсим телефоны
                        print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". -- Get phones")
                        phones = InfoGetter.get_search_phones(soup, driver, i)

                        print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". -- Phones " + str(phones))

                        opening_hours = []
                        if "opening_hours" in self.columns:
                            print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". -- Get opening hours")
                            opening_hours = InfoGetter.get_opening_hours(soup)

                        categories = []
                        if "categories" in self.columns:
                            print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". -- Get categories")
                            categories = InfoGetter.get_categories(soup, driver)

                        goods = []
                        if "goods" in self.columns:
                            print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". -- Get goods")
                            try:
                                from selenium.webdriver.common.by import By
                                menu = driver.find_element(
                                    By.CLASS_NAME, "card-feature-view__main-content"
                                )
                                menu_text = driver.find_element(
                                    By.CLASS_NAME, "card-feature-view__main-content"
                                ).text

                                if ("товары и услуги" in menu_text.lower()) or (
                                    "меню" in menu_text.lower()
                                ):
                                    # Нажимаем на кнопку "Меню"/"Товары и услуги"
                                    menu.click()
                                    sleep(2)
                                    soup = BeautifulSoup(driver.page_source, "lxml")
                                    goods = InfoGetter.get_goods(soup)
                            except NoSuchElementException:
                                pass

                        reviews = []
                        if "reviews" in self.columns:
                            reviews = InfoGetter.get_reviews(soup, driver)

                        if company_id:
                            # Записываем данные в OUTPUT.json
                            output = json_pattern.into_json(
                                company_id,
                                name,
                                city.strip().title(),
                                address,
                                website,
                                ypage,
                                rating,
                                phones,
                                categories,
                                reviews,
                                goods,
                                opening_hours,
                            )
                            util_module.JSONWorker("set", output, self.output_file)
                            print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". -- Added " + name + ". " + ypage)

                except Exception as e:
                    print(traceback.format_exc())
                    pass

                print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". Saved to " + self.output_file)
        driver.quit()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--cities", help="Do the city list name option")
    parser.add_argument("--cities_file", help="Do the city file list name option")
    parser.add_argument("--search", help="Do the search option")
    parser.add_argument("--search_file", help="Do the search file list option")
    parser.add_argument("--output", help="Do the output file option")
    parser.add_argument("--count", help="Do the count companies option")
    parser.add_argument("--driver", help="Do the browser name option")
    parser.add_argument(
        "--columns",
        help="Do the optional columns option. reviews, categories, goods, opening_hours, phones",
    )

    args = parser.parse_args()



    cities = []
    search = []

    driver = "safari"
    if args.driver:
        if args.driver == "chrome" or args.driver == "safari":
            driver = args.driver
        else:
            raise Exception("Invalid driver param")

    if not args.columns:
        columns = []
    else:
        columns = args.columns.split(",")

    if not args.output:
        output = "../out/" + args.search + ".json"
    else:
        output = args.output


    if args.cities:
        cities = args.cities.split(",")

    if args.cities_file:
        f = open(args.cities_file, encoding = 'utf-8')
        cities = f.readlines()

    if not cities:
        raise Exception("Cites list is empty")


    if args.search:
        search.append(args.search)

    if args.search_file:
        f = open(args.search_file, encoding = 'utf-8')
        search = f.readlines()

    if not search:
        raise Exception("search list is empty")

    grabber = GrabberApp(cities, search, args.count, output, columns, driver)
    grabber.grab_data()


if __name__ == "__main__":
    main()

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from datetime import datetime, timezone
from pygame import mixer
import json
import re

class InfoGetter(object):
    """ Класс с логикой парсинга данных из объекта BeautifulSoup"""

    @staticmethod
    def get_name(soup_content):
        """ Получение названия организации """

        try:
            for data in soup_content.find_all("h1", {"class": "card-title-view__title"}):
                name = data.getText()
                return name  # Возвращаем первое найденное название

            return ""  # Если ничего не найдено
        except Exception:
            return ""

    @staticmethod
    def check_captcha(driver):
        """ Проверка капчи """
        soup = BeautifulSoup(driver.page_source, "lxml")
        print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". Check")
        if soup.find_all("div", {"class": "CheckboxCaptcha"}) or soup.find_all("div", {"class": "AdvancedCaptcha"}) :
            print(datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]+". Captcha. Wait 20s")
            mixer.init()
            mixer.music.load('../dist/alert.wav')
            mixer.music.play()
            sleep(20)
            InfoGetter.check_captcha(driver)


    @staticmethod
    def get_address(soup_content):
        """ Получение адреса организации """

        try:
            for data in soup_content.find_all("div", {"class": "business-contacts-view__address-link"}):
                address = data.getText()
                return address  # Возвращаем первый найденный адрес

            return ""  # Если ничего не найдено
        except Exception:
            return ""

    @staticmethod
    def get_company_url(soup_content):
        """ Получение url"""

        try:
            for data in soup_content.find_all("a", {"class": "card-title-view__title-link"}):
                url = "https://yandex.ru"+data.get('href')
                return url  # Возвращаем первый найденный URL

            return ""  # Если ничего не найдено
        except Exception as e:
            print('get_company_url error '+getattr(e, 'message', repr(e)))
            return ""

    @staticmethod
    def get_company_id(soup_content):
        """ Получение id"""

        try:
            for data in soup_content.find_all("div", {"class": "business-card-view"}):
                website = data.get('data-id')
                return website  # Возвращаем первый найденный ID

            return ""  # Если ничего не найдено
        except Exception as e:
            print('get_company_id error '+getattr(e, 'message', repr(e)))
            return ""

    @staticmethod
    def get_website(soup_content):
        """ Получение сайта организации"""

        try:
            for data in soup_content.find_all("span", {"class": "business-urls-view__text"}):
                website = data.getText()
                return website  # Возвращаем первый найденный сайт

            return ""  # Если ничего не найдено
        except Exception:
            return ""

    @staticmethod
    def get_opening_hours(soup_content):
        """ Получение графика работы"""

        opening_hours = []
        try:
            for data in soup_content.find_all("meta", {"itemprop": "openingHours"}):
                opening_hours.append(data.get('content'))

            return opening_hours
        except Exception as e:
            print('get_categories error '+getattr(e, 'message', repr(e)))
            return ""

    @staticmethod
    def get_goods(soup_content):
        """ Получение списка товаров и услуг"""

        dishes = []
        prices = []

        try:
            # Получаем название блюда/товара/услуги (из меню-витрины)
            for dish_s in soup_content.find_all("div", {"class": "related-item-photo-view__title"}):
                dishes.append(dish_s.getText())

            # Получаем цену блюда/товара/услуги (из меню-витрины)
            for price_s in soup_content.find_all("span", {"class": "related-product-view__price"}):
                prices.append(price_s.getText())

            # Получаем название блюда/товара/услуги (из меню-списка)
            for dish_l in soup_content.find_all("div", {"class": "related-item-list-view__title"}):
                dishes.append(dish_l.getText())

            # Получаем цену блюда/товара/услуги (из меню-списка)
            for price_l in soup_content.find_all("div", {"class": "related-item-list-view__price"}):
                prices.append(price_l.getText())

        # Если меню организации полностью представлено в виде списка
        except NoSuchElementException:
            try:
                # Получаем название блюда/товара/услуги (из меню-списка)
                for dish_l in soup_content.find_all("div", {"class": "related-item-list-view__title"}):
                    dishes.append(dish_l.getText())

                # Получаем цену блюда/товара/услуги (из меню-списка)
                for price_l in soup_content.find_all("div", {"class": "related-item-list-view__price"}):
                    prices.append(price_l.getText())
            except Exception:
                pass

        except Exception:
            return {}

        return dict(zip(dishes, prices))

    @staticmethod
    def get_search_phones(soup_content, driver, i):
        """ Получение номеров из карточки на странице поиска"""
        phones = []

        try:
            # Ищем все номера телефонов в span элементах с itemprop="telephone"
            span_phones = soup_content.find_all("span", {"itemprop": "telephone"})
            
            for data in span_phones:
                phone_number = data.getText().strip()
                if phone_number:  # Проверяем, что номер не пустой
                    phones.append(phone_number)

            # Также ищем телефоны в других возможных местах
            # Ищем в div элементах с itemprop="telephone"
            for data in soup_content.find_all("div", {"itemprop": "telephone"}):
                phone_number = data.getText().strip()
                if phone_number:
                    phones.append(phone_number)

            # Ищем в a элементах с itemprop="telephone"
            for data in soup_content.find_all("a", {"itemprop": "telephone"}):
                phone_number = data.getText().strip()
                if phone_number:
                    phones.append(phone_number)

            # Ищем телефоны по тексту, содержащему номер телефона
            import re
            phone_pattern = re.compile(r'[\+]?[0-9\s\-\(\)]{7,}')
            
            # Ищем во всех текстовых элементах
            for element in soup_content.find_all(text=True):
                if element.parent and element.parent.name in ['span', 'div', 'a', 'p']:
                    text = element.strip()
                    if text and len(text) > 5:  # Ищем только в достаточно длинных текстах
                        matches = phone_pattern.findall(text)
                        for match in matches:
                            # Очищаем номер от лишних символов
                            clean_phone = re.sub(r'[^\d\+\(\)\-\s]', '', match).strip()
                            if len(clean_phone) >= 7:  # Минимальная длина номера
                                phones.append(clean_phone)

            # Убираем дубликаты и пустые значения
            phones = list(set([phone for phone in phones if phone and len(phone.strip()) > 0]))
            
            # Если телефоны не найдены в текущем soup, попробуем обновить страницу
            if not phones:
                sleep(0.5)
                soup_content = BeautifulSoup(driver.page_source, "lxml")
                
                # Повторяем поиск в обновленном soup
                for data in soup_content.find_all("span", {"itemprop": "telephone"}):
                    phone_number = data.getText().strip()
                    if phone_number:
                        phones.append(phone_number)

            return phones
        except Exception as e:
            err = getattr(e, 'message', repr(e))
            print('get_phones error '+err)
            return []


    @staticmethod
    def get_categories(soup_content, driver):
        """ Получение категорий"""
        categories = []

        try:
            for data in soup_content.find_all("a", {"class": "business-categories-view__category"}):
                categories.append(data.getText())

            categories = list(set(categories))
            return categories
        except Exception as e:
            print('get_categories error '+getattr(e, 'message', repr(e)))
            return []



    @staticmethod
    def get_rating(soup_content):
        """ Получение рейтинга организации"""
        rating = ""
        try:
            elem = soup_content.find("div", {"class": "business-card-title-view__header-rating"})
            for data in elem.find_all("span", {"class": "business-rating-badge-view__rating-text"}):
                rating += data.getText()
            return rating
        except Exception as e:
            print('get_rating error '+getattr(e, 'message', repr(e)))
            return ""

    @staticmethod
    def get_reviews(soup_content, driver):
        """ Получение отзывов о организации"""
        print("Get reviews")

        driver.execute_script("document.getElementsByClassName('_name_reviews')[0].click();")
        sleep(1)

        reviews = []

        # Узнаём количество отзывов
        try:
            reviews_count = int(soup_content.find_all("div", {"class": "tabs-select-view__counter"})[-1].text)
            print("reviews count" + str(reviews_count))
        except ValueError:
            reviews_count = 0

        except AttributeError:
            reviews_count = 0

        except Exception:
            return []

        if reviews_count > 150:
            find_range = range(100)
        else:
            find_range = range(30)

        for i in find_range:
            try:
                driver.execute_script("document.getElementsByClassName('scroll__container')[1].scrollTop="+str(500*i)+";")

            except MoveTargetOutOfBoundsException:
                break

        try:
            soup_content = BeautifulSoup(driver.page_source, "lxml")
            for data in soup_content.find_all("span", {"class": "business-review-view__body-text"}):
                reviews.append(data.getText())

            return reviews
        except Exception as e:
            print('get_reviews error '+getattr(e, 'message', repr(e)))
            return []

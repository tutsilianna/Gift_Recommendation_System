import time
import json
import pandas as pd
from playwright.sync_api import sync_playwright


class OzonParse():
    
    def __init__(self) -> None:
        self.ozon = "https://ozon.ru"
        self.datas_path = 'D:/python_projects/Gift_Recommendation_System/datas/'
        self.stop_categories = ['Электроника', 'Автомобили', 'Автотовары', 'Аксессуары', "Аптека", "Бытовая химия и гигиена", "Мебель", "Обувь",
                                "Одежда", "Строительство и ремонт", "Товары для взрослых", "Туризм, рыбалка, охота", "Ozon fresh"]
        self.tag_names = ['.x4i.ix5', '.x0i.x1i.tile-root',  '.x0i.xi1.tile-root']
        self.categories_true = ["Игры и консоли", "Книги", "Хобби и творчество", "Антиквариат и коллекционирование", "Музыка и видео"]

    def __catalog_to_json(self) -> None:
        catalog = self.__parse_menu()
        self.__to_json(catalog)
        if catalog:
            # второй уровень вложенности каталога
            for category in catalog:
                category_i = self.__parse_category(url=catalog[category], names=[category])
                if category_i:
                    catalog[category] = category_i
                    self.__to_json(catalog)
                    # третий уровень вложенности каталога (если есть еще глубже, они не будут учитываться)
                    for category_ in category_i:
                        category_ii = self.__parse_category(url=category_i[category_], names=[category, category_])
                        if category_ii:
                            category_i[category_] = category_ii
                            catalog[category] = category_i
                            self.__to_json(catalog)
            self.__to_json(catalog)

    def __to_json(self, data: dict) -> None:
        with open("data/raw/catalog.json", "a+", encoding='utf-8') as outfile: 
            json.dump(data, outfile, ensure_ascii=False, indent=4)


    def __parse_menu(self) -> dict:
        time.sleep(10)
        self.page.wait_for_load_state("load") 
        # нажатие на кнопку меню 
        self.page.click(".b200-a0.b200-b5") 
        self.page.wait_for_load_state("load") 
        third_ul = self.page.query_selector('(//ul)[3]')
        catalog = {}
        if third_ul:
            list_items = third_ul.query_selector_all('li')
            for item in list_items:
                text_and_link = item.evaluate("""
                    el => ({
                        text: el.innerText,
                        link: el.querySelector('a') ? el.querySelector('a').href : null
                    })
                """)
                print(f"Текст: {text_and_link['text']}, Ссылка: {text_and_link['link']}")
                catalog[text_and_link['text']] = text_and_link['link']
        else:
            print("На странице нет третьего элемента <ul>")
        return catalog

    def __parse_category(self, url: str, names: list[str]) -> dict:
        category = {}
        self.page.goto(url)
        self.page.wait_for_load_state("load") 
        list_items = self.page.query_selector_all('.dx5.tsBody500Medium')
        for item in list_items:
            text_and_link = item.evaluate("""
                el => ({
                        text: el.innerText,
                        link: el.href 
                    })
            """)
            if text_and_link['text'] not in names :
                category[text_and_link['text']] = text_and_link['link']
        return category

    def __check_filtres(self) -> bool:
        time.sleep(3)
        if self.page.query_selector('.aab4'): # обработка плохих фильтров
            print("По вашим параметрам ничего не нашлось. Попробуйте сбросить фильтры.")
            return False
        else:
            return True

    def __get_product(self, url: str, tovar: dict, key1: str, key2: str, key3: str) -> dict:
        self.page.goto(url)  # переходим по ссылке
        self.page.wait_for_load_state("load") 
        time.sleep(5)
        # ищем товары
        if not self.__check_filtres(): # обработка плохих фильтров
            return tovar
        products = self.page.query_selector_all(self.tag_names[0])
        if not products:
            products = self.page.query_selector_all(self.tag_names[1])
        if not products:
            products = self.page.query_selector_all(self.tag_names[2])
        for product in products:
            try:
                info = product.evaluate("""
                    card => {
                        const reviewsElement = card.querySelector('.tsBodyMBold .t8:last-child span');
                        const ratingElement  = card.querySelector('.tsBodyMBold .t8:first-child span');
                        return {
                            name:           card.querySelector('.a8b.ba9.ac.iu6>span').innerText,
                            link:           'https://www.ozon.ru' + card.querySelector('.tile-hover-target.iu6.ui6').getAttribute('href'),
                            price:          card.querySelector('.c3P9465-a0>.tsHeadline500Medium').innerText.trim().replace(/[^0-9]/g,""),
                            reviews:        reviewsElement ? reviewsElement.innerText.trim().replace(/[^0-9]/g,"") : '0',
                            rating:         ratingElement ? ratingElement.innerText.trim().replace(/[^0-9,.]/g,"") : '0'
                        };
                    }
                """)
                tovar['название'].append(info['name'])
                tovar['оценка'].append(info['rating'])
                tovar['количество отзывов'].append(info['reviews'])
                tovar['цена'].append(info['price'])
                tovar['ссылка'].append(info['link'])
                tovar['описание'].append("")
                tovar['код товара'].append("")
                tovar['категория'].append(key1)
                tovar['подкатегория'].append(key2)
                tovar['подподкатегория'].append(key3)
                # print(f"{info['name']} {info['link']}")
            except Exception as er:
                print("ошибка из get_product")
                print(er)
        return tovar 
    
    def __next_page(self, i: int) -> None:
        pages = self.page.query_selector_all('.n1e')
        if pages:
            if i < len(pages):
                self.page.query_selector_all('.n1e')[i].click()
                self.page.wait_for_load_state("load") 
                time.sleep(5)
                print(f'    страница {i+1}')
                return True
            else:
                return False
        else:
            return False

    def __test(self) -> None:
        url = 'https://www.ozon.ru/category/nastolnye-igry-13507/'
        sort_params =  ['&sorting=score', '&sorting=new']
        price_params = ['?currency_price=0.000%3B500.000', '?currency_price=501.000%3B1000.000', '?currency_price=1000.000%3B10000000.000']
        self.page.goto(url)
        tovar = {'название': [],
                 'описание': [], 
                 'код товара': [],
                 'оценка': [],
                 'количество отзывов': [],
                 'цена': [],
                 'категория': [],
                 'подкатегория': [],
                 'подподкатегория': [],
                 'ссылка': []
                 }
        for sort_param in sort_params:
            for price_param in price_params:
                tovar = self.__get_product(url = url + price_param + sort_param, tovar=tovar, key1="key1", key2="key2", key3="key3")
                df = pd.DataFrame(tovar)
                df.to_csv('data/ozon_data.csv', index=False, encoding='utf-8')
                """if self.__check_filtres():
                    for i in range(1, 11):
                        if self.__next_page(i=i):
                            tovar = self.__get_product(url = self.page.url, tovar=tovar, key1="key1", key2="key2", key3="key3")
                            df = pd.DataFrame(tovar)
                            df.to_csv('data/ozon_data.csv', index=False, encoding='utf-8')
                        else: 
                            break"""
                

    def __parse_products(self) -> None:
        with open("data/raw/catalog_.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        # отсортируем ненужные категории
        # data = {key: data[key] for key in data if key not in self.stop_categories}
        # data = {key: data[key] for key in data if key in self.categories_true}
        # популяные и новые товары: фильтрация
        sort_params =  ['&sorting=score'] #, '&sorting=new']
        # до 500 руб, 500-1000 руб, от 1000 руб
        # price_params = ['?currency_price=0.000%3B500.000', '?currency_price=501.000%3B1000.000', '?currency_price=1000.000%3B10000000.000']
        price_params = ['?currency_price=0.000%3B1000.000', '?currency_price=1000.000%3B10000000.000']
        for key1 in data:                                   
            if isinstance(data[key1], dict):
                for key2 in data[key1]:                    
                    if isinstance(data[key1][key2], dict):
                        for key3 in data[key1][key2]:
                            for sort_param in sort_params:
                                print(f' *{sort_param}')
                                for price_param in price_params:
                                    print(f'  *{price_param}')
                                    try:
                                        tovar = {'название': [], 'описание': [], 'код товара': [],'оценка': [], 'количество отзывов': [], 'цена': [], 'категория': [], 'подкатегория': [], 'подподкатегория': [], 'ссылка': []}
                                        tovar = self.__get_product(url = data[key1][key2][key3] + price_param + sort_param, tovar=tovar, key1=key1, key2=key2, key3=key3)
                                        df = pd.DataFrame(tovar)
                                        df.to_csv('data/raw/ozon_data.csv', index=False, encoding='utf-8', mode='a+', header=False)
                                        if self.__check_filtres():
                                            print("    страница 1")
                                            for i in range(1, 3):
                                                if self.__next_page(i=i):
                                                    tovar = self.__get_product(url = self.page.url, tovar=tovar, key1=key1, key2=key2, key3=key3)
                                                    df = pd.DataFrame(tovar)
                                                    df.to_csv('data/raw/ozon_data.csv', index=False, encoding='utf-8', mode='a+', header=False)
                                                else:
                                                    break
                                            
                                    except Exception as er:
                                        print("ошибка из parse_products")
                                        print(er)
                            print(f'{key1}-{key2}-{key3} [+]')
                    else: 
                        for price_param in price_params:
                            for sort_param in sort_params:
                                try:
                                    tovar = {'название': [], 'описание': [], 'код товара': [],'оценка': [], 'количество отзывов': [], 'цена': [], 'категория': [], 'подкатегория': [], 'подподкатегория': [], 'ссылка': []}
                                    tovar = self.__get_product(url = data[key1][key2] + price_param + sort_param, tovar=tovar, key1=key1, key2=key2, key3="")
                                    df = pd.DataFrame(tovar)
                                    df.to_csv('data/raw/ozon_data.csv', index=False, encoding='utf-8', mode='a+', header=False)
                                    if self.__check_filtres():
                                        for i in range(1, 3):
                                            if self.__next_page(i=i):
                                                tovar = self.__get_product(url = self.page.url, tovar=tovar, key1=key1, key2=key2, key3="")
                                                df = pd.DataFrame(tovar)
                                                df.to_csv('data/raw/ozon_data.csv', index=False, encoding='utf-8', mode='a+', header=False)
                                            else:
                                                break
                                except Exception as er:
                                    print("ошибка из parse_products")
                                    print(er)
                        print(f'{key1}-{key2} [+]')
            else:
                for price_param in price_params:
                    for sort_param in sort_params:
                        try:
                            tovar = {'название': [], 'описание': [], 'код товара': [],'оценка': [], 'количество отзывов': [], 'цена': [], 'категория': [], 'подкатегория': [], 'подподкатегория': [], 'ссылка': []}
                            tovar = self.__get_product(url = data[key1] + price_param + sort_param, tovar=tovar, key1=key1, key2="", key3="")
                            df = pd.DataFrame(tovar)
                            df.to_csv('data/raw/ozon_data.csv', index=False, encoding='utf-8', mode='a+', header=False)
                            if self.__check_filtres():
                                for i in range(1, 3):
                                    if self.__next_page(i=i):
                                        tovar = self.__get_product(url = self.page.url, key1=key1, key2="", key3="")
                                        df = pd.DataFrame(tovar)
                                        df.to_csv('data/raw/ozon_data.csv', index=False, encoding='utf-8', mode='a+', header=False)
                                    else:
                                        break
                        except Exception as er:
                            print("ошибка из parse_products")
                            print(er)
                print(f'{key1} [+]')

    def __parse_info_product(self, row): # -> tuple(str, str):
        self.page.goto(url=row['ссылка'])
        self.page.wait_for_load_state("load") 
        time.sleep(5)

        code = self.page.query_selector('.vk6')
        if code:
            row['код товара'] = code.inner_text()

        description = self.page.query_selector('.RA-a1')
        if description:
            row['описание'] = description.inner_text()

        return row

    def __get_info_product(self):
        data = pd.read_csv('data/raw/ozon_data.csv', encoding='utf-8')
        data = data.apply(self.__parse_info_product, axis=1)
        data.to_csv('data/raw/ozon_data.csv', index=False, encoding='utf-8')

    def parse(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            self.context = browser.new_context()
            self.page = self.context.new_page()
            self.page.goto(self.ozon)
            time.sleep(10)
            # self.__catalog_to_json()
            # self.__parse_products()
            self.__get_info_product()



            # self.__test()
            # self.__parse_menu()
            # self.__parse_category()
            # self.page.get_by_placeholder("Искать на Ozon").type(text=self.keyword, delay=0.3)
            # self.page.query_selector("button[type='submit']").click()
            # self.__get_links()


if __name__ == "__main__":
    OzonParse().parse()
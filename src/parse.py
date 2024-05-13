import time
import json
import itertools
import pandas as pd
import numpy as np
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor


class OzonParse():
    
    def __init__(self) -> None:
        self.ozon            = "https://ozon.ru"
        self.stop_categories = ['Электроника', 'Автомобили', 'Автотовары', 'Аксессуары', 
                                "Аптека", "Бытовая химия и гигиена", "Мебель", "Обувь",
                                "Одежда", "Строительство и ремонт", "Товары для взрослых",
                                "Туризм, рыбалка, охота", "Ozon fresh"]
        self.tag_names       = ['.x4i.ix5', '.x0i.x1i.tile-root',  '.x0i.xi1.tile-root']
        self.data_path       = 'data/raw/ozon_data.csv'
        self.menu_tag        = ".b200-a0.b200-b5"
        self.category_tag    = '.dx5.tsBody500Medium'
        self.pages_tag       = '.n1e'
        self.code_tag        = '.ga13-a2.tsBodyControl400Small' # '.vk6'
        self.description_tag = '.RA-a1'
        self.bad_filtres     = '.aab4'
        self.proxy           = [{'username': '6NeZMV', 'password': 'iSxcP9mEj0', 'server': '185.181.246.178:5500'}, 
                                {'username': '6NeZMV', 'password': 'iSxcP9mEj0', 'server': '188.130.137.120:5500'},
                                {'username': '6NeZMV', 'password': 'iSxcP9mEj0', 'server': '188.130.128.44:5500'},
                                {'username': '6NeZMV', 'password': 'iSxcP9mEj0', 'server': '109.248.138.231:5500'}]
        self.price_params    = ['?currency_price=0.000%3B1000.000', '?currency_price=1000.000%3B10000000.000'] # ['?currency_price=0.000%3B500.000', '?currency_price=501.000%3B1000.000', '?currency_price=1000.000%3B10000000.000']
        self.sort_params     =  ['&sorting=score'] # ['&sorting=score', '&sorting=new']
        self.js_code         = """
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
                               """

    def __to_json(self, data: dict) -> None:
        """
            метод, который записывает каталог в формате json
        """
        with open("data/raw/catalog.json", "a+", encoding='utf-8') as outfile: 
            json.dump(data, outfile, ensure_ascii=False, indent=4)

    def __parse_menu(self) -> dict:
        """
            метод, в котором происходит нажатие на кнопку "меню" 
            и собирает первый уровень вложенности каталога 
        """
        time.sleep(10)
        self.page.wait_for_load_state("load") 
        # нажатие на кнопку меню 
        self.page.click(self.menu_tag) 
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
        """
            метод, который собирает подкатегории
        """
        category = {}
        self.page.goto(url)
        self.page.wait_for_load_state("load") 
        list_items = self.page.query_selector_all(self.category_tag)
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
    
    def __catalog_to_json(self) -> None:
        """
            метод, который будет собирать католог с уровнем вложенности 3 
            (т.е. Категория -> Подкатегория -> Подподкатегория, 
            если есть подкатегории у подподкатегорий, то они будут учтены в подподкатегории)
        """
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

    def __check_filtres(self) -> bool:
        """
            метод, который проверяет есть ли товары по фильтру
        """
        time.sleep(3)
        if self.page.query_selector(self.bad_filtres): # обработка плохих фильтров
            print("По вашим параметрам ничего не нашлось. Попробуйте сбросить фильтры.")
            return False
        else:
            return True

    def __get_product(self, url: str, tovar: dict, key1: str, key2: str, key3: str) -> dict:
        """
            метод, который собирает все товары со страницы
        """
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
                info = product.evaluate(self.js_code)
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
            except Exception as er:
                print("ошибка из get_product")
                print(er)
        return tovar 
    
    def __next_page(self, i: int) -> bool:
        """
            метод, который переходит на следующую страницу, если такие есть
        """
        pages = self.page.query_selector_all(self.pages_tag)
        if pages:
            if i < len(pages):
                self.page.query_selector_all(self.pages_tag)[i].click()
                self.page.wait_for_load_state("load") 
                time.sleep(5)
                print(f'    страница {i+1}')
                return True
            else:
                return False
        else:
            return False

    def __parse_products_helping(self, url, key1, key2, key3) -> None:
        """
            вспомогальтельный метод, который собирает товары из каждой категории каталога
        """
        for price_param in self.price_params:
            for sort_param in self.sort_params:
                print(f' *{sort_param}')
                for price_param in self.price_params:
                    print(f'  *{price_param}')
                    try:
                        tovar = {'название': [], 'описание': [], 'код товара': [],'оценка': [], 'количество отзывов': [], 'цена': [], 'категория': [], 'подкатегория': [], 'подподкатегория': [], 'ссылка': []}
                        tovar = self.__get_product(url = url + price_param + sort_param, tovar=tovar, key1=key1, key2=key2, key3=key3)
                        df = pd.DataFrame(tovar)
                        df.to_csv(self.data_path, index=False, encoding='utf-8', mode='a+', header=False)
                        if self.__check_filtres():
                            print("    страница 1")
                            for i in range(1, 3):
                                if self.__next_page(i=i):
                                    tovar = self.__get_product(url = self.page.url, tovar=tovar, key1=key1, key2=key2, key3=key3)
                                    df = pd.DataFrame(tovar)
                                    df.to_csv(self.data_path, index=False, encoding='utf-8', mode='a+', header=False)
                                else:
                                    break
                            
                    except Exception as er:
                        print("ошибка из parse_products_helping")
                        print(er)
          
    def __parse_products(self) -> None:
        """
            метод, который проходится по всему каталогу и собирает товары из каждой категории
        """
        with open("data/raw/catalog_.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        for key1 in data:                                   
            if isinstance(data[key1], dict):
                for key2 in data[key1]:                    
                    if isinstance(data[key1][key2], dict):
                        for key3 in data[key1][key2]:
                            self.__parse_products_helping(data[key1][key2][key3], key1, key2, key3)
                            print(f'{key1}-{key2}-{key3} [+]')
                    else: 
                        self.__parse_products_helping(data[key1][key2], key1, key2, "")
                        print(f'{key1}-{key2} [+]')
            else:
                self.__parse_products_helping(data[key1], key1, "", "")
                print(f'{key1} [+]')

    def __parse_info_product(self, row): # -> tuple(str, str):
        """
            метод, который проходится по собранным данным и дополняет код товара и описание
        """
        print(row.name)
        self.page.goto(url=row['ссылка'], timeout=6000)
        self.page.wait_for_load_state("load") 
        time.sleep(5)
        try:
            code = self.page.query_selector_all(self.code_tag)[3]
            if code:
                row['код товара'] = code.inner_text()
        except:
            pass
        
        try:
            description = self.page.query_selector(self.description_tag)
            if description:
                row['описание'] = description.inner_text()
        except:
            pass
        return row

    def __get_info_product(self):
        data = pd.read_csv(self.data_path, encoding='utf-8')
        data_ = data_.apply(self.__parse_info_product, axis=1)
        # data.to_csv(self.data_path, index=False, encoding='utf-8')
        data_.to_csv('data/raw/ozon_data_.csv', index=False, encoding='utf-8', mode='a+', header=False)
    

    def for_parallel(self, proxy: dict[str], data):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False) # {"server": proxy['server'], "username": proxy['username'], "password": proxy['password']}
            self.context = browser.new_context()
            self.page = self.context.new_page()
            self.page.wait_for_load_state("load")
            self.page.goto(self.ozon)
            time.sleep(10)
            data = data.apply(self.__parse_info_product, axis=1)
            data.to_csv('data/raw/ozon_data_.csv', index=False, encoding='utf-8', mode='a+', header=False)


    def parallel(self):
        data = pd.read_csv(self.data_path, encoding='utf-8')
        data_chunks = [data.iloc[0:2], data.iloc[2:4]] # np.array_split(data, 10000)
        print(len(data_chunks))
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = executor.map(lambda args: self.for_parallel(*args), 
                                   zip(self.proxy, data_chunks))

    def parse(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            self.context = browser.new_context()
            self.page = self.context.new_page()
            self.page.goto(self.ozon, timeout=6000)
            time.sleep(10)
            # self.__catalog_to_json()
            # self.__parse_products()
            self.__get_info_product()
            # self.__parse_menu()
            # self.__parse_category()
            browser.close()
        time.sleep(30)


if __name__ == "__main__":
    OzonParse().parse()
    # OzonParse().parallel()
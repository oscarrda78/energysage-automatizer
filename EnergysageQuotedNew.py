from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from openpyxl import Workbook
import time
from datetime import date, datetime
import chromedriver_autoinstaller
from bs4 import BeautifulSoup

ENERGY_SAGE_MAIL = "energysage@solarunion.com"
ENERGY_SAGE_PASSWORD = "Gridparity01"
INCLUDE_STALE_LEADS = "True"


class LeadDealer:
    main_url = "https://www.energysage.com/"
    current_url = ""

    def __init__(self):
        self.awaiting_quotes_workbook = None
        self.awaiting_quotes_sheet = None
        chromedriver_autoinstaller.install()
        service = Service(r"chromedriver.exe")
        self.driver = webdriver.Chrome(service=service)

    def set_up_awaiting_quotes_workbook(self):
        self.awaiting_quotes_workbook = Workbook()
        today = date.today()
        today_timestamp = int(time.mktime((datetime.strptime(str(today), '%Y-%m-%d').timetuple())))
        self.awaiting_quotes_sheet = self.awaiting_quotes_workbook.active
        self.awaiting_quotes_sheet["A1"] = "Date"
        self.awaiting_quotes_sheet["B1"] = "Last Name"
        self.awaiting_quotes_sheet["C1"] = "First Name"
        self.awaiting_quotes_sheet["D1"] = "Address"
        self.awaiting_quotes_sheet["E1"] = "City"
        self.awaiting_quotes_sheet["F1"] = "CA"
        self.awaiting_quotes_sheet["G1"] = "ZIP"
        self.awaiting_quotes_sheet["H1"] = "Phone"
        self.awaiting_quotes_sheet["I1"] = "E-Mail"
        self.awaiting_quotes_sheet["J1"] = "Esage Link"
        self.awaiting_quotes_sheet["K1"] = "Annual Usage"
        self.awaiting_quotes_sheet["L1"] = "Avg Bill"
        self.awaiting_quotes_sheet["M1"] = "Notes?"
        self.awaiting_quotes_sheet["N1"] = "Bill?"
        self.awaiting_quotes_sheet["O1"] = "Battery"
        self.awaiting_quotes_sheet["O1"] = "Beat my Quote"
        self.awaiting_quotes_workbook.save(filename="Quoted Leads - " + str(today_timestamp) + ".xlsx")

    def login(self):
        current_path = "login"
        self.current_url = self.main_url + current_path

        self.driver.get(self.current_url)

        wait = WebDriverWait(self.driver, 10)
        email_login_input = wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[@id='id_email']")))
        email_login_input.send_keys(ENERGY_SAGE_MAIL)

        password_login_input = wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[@id='id_password']")))
        password_login_input.send_keys(ENERGY_SAGE_PASSWORD)

        signin_login_button = wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[@id='jsid_sign-in']")))
        signin_login_button.click()

    def awaiting_quotes(self):
        wait = WebDriverWait(self.driver, 10)
        exist_available_leads = True
        awaiting_quotes_page = 1
        quoted_leads = []
        while exist_available_leads:
            self.current_url = self.main_url + "/market/properties/intent/?page=" + str(awaiting_quotes_page) + \
                               "&include_stale_leads=" + INCLUDE_STALE_LEADS
            self.driver.refresh()
            self.driver.get(self.current_url)
            wait.until(ec.url_to_be(self.current_url))

            try:
                self.driver.implicitly_wait(10)
                leads_not_quoted_table = self.driver.find_element(by=By.ID, value="ra-body")
                leads_not_quoted_table_inner_html = leads_not_quoted_table.get_attribute('innerHTML')

                soup = BeautifulSoup(leads_not_quoted_table_inner_html, 'html.parser')
                quoted_links = soup.find_all("a", "flex-icon__text clickable-link")

                for quoted_link in quoted_links:
                    try:
                        if quoted_link["href"] not in quoted_leads:
                            self.current_url = self.main_url + quoted_link["href"]
                            self.driver.get(self.current_url)
                            wait.until(ec.url_to_be(self.current_url))
                            self.driver.refresh()
                            quoted_leads.append(quoted_link["href"])
                            exist_available_leads = True
                        else:
                            exist_available_leads = False

                    except Exception as ex:
                        print(ex)
                awaiting_quotes_page += 1
            except Exception as ex:
                print(ex)
        print(quoted_leads)

    def tear_down(self):
        self.driver.close()

    def start(self):
        self.login()
        self.awaiting_quotes()
        # self.tearDown()


if __name__ == "__main__":
    process = LeadDealer()
    process.start()

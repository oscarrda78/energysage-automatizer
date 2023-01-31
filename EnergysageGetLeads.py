import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from datetime import date
import json
import math
import sqlite3
import traceback
from setup_logger import logger

from EnergysageLeadModel import Lead
from EnergysageGenerateReport import Report

load_dotenv()

ENERGY_SAGE_MAIL = os.getenv('ENERGY_SAGE_MAIL')
ENERGY_SAGE_PASSWORD = os.getenv('ENERGY_SAGE_PASSWORD')
INCLUDE_STALE_LEADS = os.getenv('INCLUDE_STALE_LEADS')
CUSHION_PERCENTAGE = os.getenv('CUSHION_PERCENTAGE')
KWH_REGULAR = os.getenv('KWH_REGULAR')
KWH_PRODUCTION_FACTOR = os.getenv('KWH_PRODUCTION_FACTOR')
PANASONIC_WATTAGE = os.getenv('PANASONIC_WATTAGE')
ANNUAL_ISOLATION = os.getenv('ANNUAL_ISOLATION')
PEAK_ADJUSTMENT_FACTOR = os.getenv('PEAK_ADJUSTMENT_FACTOR')
GUARANTEED_PERFORMANCE_RATIO = os.getenv('GUARANTEED_PERFORMANCE_RATIO')
REGULAR_COST_PER_WATT = os.getenv('REGULAR_COST_PER_WATT')
SAN_FRANCISCO_COST_PER_WATT = os.getenv('SAN_FRANCISCO_COST_PER_WATT')
MINIMUM_SYSTEM_SIZE = os.getenv('MINIMUM_SYSTEM_SIZE')
ADDITION_FOR_GROSS_SYSTEM_COST = os.getenv('ADDITION_FOR_GROSS_SYSTEM_COST')
BATTERY_GROSS_COST = os.getenv('BATTERY_GROSS_COST')
READ_QUOTED = os.getenv('READ_QUOTED')


class LeadDealer(object):
    main_url = "https://www.energysage.com/"
    current_url = ""

    def __init__(self):
        chromedriver_autoinstaller.install()
        service = Service(r"chromedriver.exe")
        self.driver = webdriver.Chrome(service=service)
        self.actions = ActionChains(self.driver)
        self.logger = logger

        self.inside_consultant_cities = []
        self.production_factor_cities = []
        self.read_cities()

        self.connection = sqlite3.connect("energy-sage.db")
        self.cursor = self.connection.cursor()

        self.cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='leads' ''')

        if self.cursor.fetchone()[0] != 1:
            self.cursor.execute("CREATE TABLE leads(id, created_date, last_name, first_name, address, city, state,"
                                "zip_code, phone, email, e_sage_link, annual_usage,"
                                "effective_electricity_cost, average_bill, one_year_estimated, panel_number,"
                                "system_size, want_financial, has_bill, has_notes, has_battery,"
                                "has_beat_my_quote, is_inside_consultant, is_quoted)")

        else:
            logger.info("Lead Table Already exists")

    def log_traceback(self, ex, ex_traceback=None):
        if ex_traceback is None:
            ex_traceback = ex.__traceback__
        tb_lines = [line.rstrip('\n') for line in
                    traceback.format_exception(ex.__class__, ex, ex_traceback)]
        self.logger.error(tb_lines)

    def read_cities(self):
        try:
            f = open('inside_consultant_cities.json')
            fa = open('production_factor_cities.json')

            inside_consultant_data_json = json.load(f)
            production_factor_data_json = json.load(fa)

            self.inside_consultant_cities = inside_consultant_data_json["cities"]
            self.production_factor_cities = production_factor_data_json["cities"]

            f.close()
            fa.close()
        except Exception as ex:
            self.log_traceback(ex)

    def login(self):
        try:
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

        except Exception as ex:
            self.log_traceback(ex)

    def get_leads(self, page_number):
        wait = WebDriverWait(self.driver, 10)

        self.driver.refresh()
        self.driver.get(self.current_url)
        wait.until(ec.url_to_be(self.current_url))

        quoted_links = []

        try:
            leads_not_quoted_table = wait.until(
                ec.element_to_be_clickable((By.ID, "ra-body")))
            leads_not_quoted_table_inner_html = leads_not_quoted_table.get_attribute('innerHTML')

            soup = BeautifulSoup(leads_not_quoted_table_inner_html, 'html.parser')
            quoted_links = soup.find_all("a", "flex-icon__text clickable-link")

            quoted_links_size = len(quoted_links)
            page_info = "PAGE: #" + str(page_number)
            self.logger.info(page_info)
            leads_number_info = "N° LEADS: " + str(quoted_links_size)
            self.logger.info(leads_number_info)

        except Exception as ex:
            self.log_traceback(ex)

        return quoted_links

    def get_number_of_pages(self):

        wait = WebDriverWait(self.driver, 10)

        self.driver.refresh()
        self.driver.get(self.current_url)
        wait.until(ec.url_to_be(self.current_url))

        number_of_pages_text = "0"
        try:
            number_of_pages = wait.until(
                ec.element_to_be_clickable((By.XPATH, "//div[@class='pagination']/a[@class='page'][last()]")))

            number_of_pages_text = number_of_pages.text

        except Exception as ex:
            self.log_traceback(ex)

        return int(number_of_pages_text)

    def get_lead_body(self, lead_id):
        wait = WebDriverWait(self.driver, 10)
        self.driver.get(self.current_url)
        wait.until(ec.url_to_be(self.current_url))
        self.driver.refresh()

        current_lead_body = wait.until(
            ec.element_to_be_clickable((By.XPATH, "//div[@class='ra-container ra-container-full']")))
        lead_soup = BeautifulSoup(current_lead_body.get_attribute('innerHTML'), 'html.parser')

        today = date.today()

        lead_date = ""
        try:
            lead_date = today.strftime("%m/%d/%y")
        except Exception as ex:
            self.log_traceback(ex)

        lead_contact_info = lead_soup.find("div", "contact-preferences")
        lead_full_name = ""
        try:
            lead_full_name = lead_contact_info.find("h3").get_text()
        except Exception as ex:
            self.log_traceback(ex)

        lead_full_name_split = lead_full_name.split()

        lead_first_name = ""
        try:
            lead_first_name = " ".join(lead_full_name_split[0:-1]).capitalize()
        except Exception as ex:
            self.log_traceback(ex)

        lead_last_name = ""
        try:
            lead_last_name = lead_full_name_split[-1].capitalize()

            if lead_last_name == lead_first_name:
                lead_last_name = ""
        except Exception as ex:
            self.log_traceback(ex)

        lead_address_split = ""
        try:
            lead_address_split = [lead_address_split_element.strip() for lead_address_split_element
                                  in lead_soup.find("h2", "prop-address").get_text().split(",")]

        except Exception as ex:
            self.log_traceback(ex)

        lead_address = ""
        try:
            lead_address = lead_address_split[0]
        except Exception as ex:
            self.log_traceback(ex)

        lead_city = ""
        try:
            lead_city = lead_address_split[1]
        except Exception as ex:
            self.log_traceback(ex)

        lead_state = ""
        try:
            lead_state = lead_address_split[2]
        except Exception as ex:
            self.log_traceback(ex)

        lead_zip_code = ""
        try:
            lead_zip_code = lead_address_split[3]
        except Exception as ex:
            self.log_traceback(ex)

        lead_e_sage_link = ""
        try:
            lead_e_sage_link = self.current_url
        except Exception as ex:
            self.log_traceback(ex)

        lead_properties = lead_soup.find("div", "property-details")

        lead_properties_elements = []
        try:
            lead_properties_elements = lead_properties.find_all("li", "prop-detail")
        except Exception as ex:
            self.log_traceback(ex)

        lead_properties_elements_dict = dict()

        lead_has_battery = False

        lead_has_bill = False
        try:
            for el in lead_properties_elements:
                try:
                    lead_battery_element = el.find("div", "storage-interest")
                    if lead_battery_element is not None:
                        lead_has_battery = True
                except Exception as ex:
                    self.log_traceback(ex)

                try:
                    lead_bill_element = el.find("span", "prop-file-download").text
                    lead_has_bill = True
                except Exception as ex:
                    self.log_traceback(ex)

                try:
                    label = el.find("p", "prop-detail-label").text.strip().split("\n")[0]
                    val = el.find("div", "prop-detail-val").text.strip().split("\n")[0]
                    lead_properties_elements_dict[label] = val
                except:
                    label = el.find("p", "prop-detail-vertical-label").text.strip().split("\n")[0]
                    val = el.find("div", "prop-detail-vertical-val").text.strip().split("\n")[0]
                    lead_properties_elements_dict[label] = val

        except Exception as ex:
            self.log_traceback(ex)

        lead_monthly_bill_div = lead_soup.find("div", "monthly-bill")

        lead_monthly_bill = ""
        try:
            lead_monthly_bill = lead_monthly_bill_div.find("span").text
        except Exception as ex:
            self.log_traceback(ex)

        lead_annual_usage = ""
        lead_annual_usage_int = 0
        try:
            lead_annual_usage = lead_properties_elements_dict["Annual electricity usage:"]
            lead_annual_usage_int = int(lead_annual_usage.split()[0]
                                        .replace(',', '')
                                        .replace("'", ''))
        except Exception as ex:
            self.log_traceback(ex)

        effective_electricity_cost = ""
        effective_electricity_cost_int = 0.0
        try:
            effective_electricity_cost = lead_properties_elements_dict["Effective electricity cost:"]
            effective_electricity_cost_int = float(effective_electricity_cost.split()[0]
                                                   .replace(',', '')
                                                   .replace("'", ''))
        except Exception as ex:
            self.log_traceback(ex)

        lead_has_comments = False
        try:
            lead_comments = lead_properties_elements_dict["Customer notes:"]
            lead_has_comments = True
        except Exception as ex:
            self.log_traceback(ex)

        lead_has_beat_my_quote = False
        try:
            lead_beat_my_quote = lead_properties_elements_dict["Requesting “Beat My Quote”:"]
            lead_has_beat_my_quote = True
        except Exception as ex:
            self.log_traceback(ex)

        is_inside_consultant = False

        if lead_city.upper().strip() in self.inside_consultant_cities:
            is_inside_consultant = True

        lead_want_financial = False
        try:
            lead_financial = lead_properties_elements_dict["Financing preference:"]
            if lead_financial.upper().strip() == "SOLAR LOAN":
                lead_want_financial = True
        except Exception as ex:
            self.log_traceback(ex)

        cushion_value_base = float(CUSHION_PERCENTAGE) * lead_annual_usage_int
        KWH_value = float(KWH_REGULAR)

        if lead_city.upper().strip() in self.production_factor_cities:
            KWH_value = float(KWH_PRODUCTION_FACTOR)

        W_value_base = (cushion_value_base / (KWH_value * 0.8) * 1000)

        panel_number = math.ceil(W_value_base / int(PANASONIC_WATTAGE))
        system_size = panel_number * int(PANASONIC_WATTAGE)
        one_year_estimated = \
            int((system_size * int(ANNUAL_ISOLATION) / int(PEAK_ADJUSTMENT_FACTOR)) * float(
                GUARANTEED_PERFORMANCE_RATIO))

        lead_is_quoted = False
        try:
            lead_is_quoted_element = lead_soup.find("div", {"class": "menu-supplier-prop-detail menu-take-action"})
            if lead_is_quoted_element is not None:
                lead_is_quoted = True
        except Exception as ex:
            self.log_traceback(ex)

        lead_phone = ""
        try:
            lead_phone_icon_element = lead_soup.find("i", {"class": "icon icon-phone"})
            lead_phone_element_parent = lead_phone_icon_element.parent
            lead_phone_element_grand_parent = lead_phone_element_parent.parent
            lead_phone_element = lead_phone_element_grand_parent.find("span", {"class": "contact-data"})
            lead_phone = lead_phone_element.text

        except Exception as ex:
            self.log_traceback(ex)

        lead_email = ""

        try:
            lead_email_element = lead_soup.find("span", {"class": "m-type-link m-clipboard-link"})
            lead_email = lead_email_element.attrs["data-clipboard-text"]

        except Exception as ex:
            self.log_traceback(ex)

        return Lead(lead_id, lead_date, lead_last_name, lead_first_name, lead_address, lead_city, lead_state,
                    lead_zip_code, lead_phone, lead_email, lead_e_sage_link, lead_annual_usage,
                    effective_electricity_cost, lead_monthly_bill, one_year_estimated, panel_number,
                    system_size, lead_want_financial, lead_has_bill, lead_has_comments, lead_has_battery,
                    lead_has_beat_my_quote, is_inside_consultant, lead_is_quoted)

    def send_lead_quote(self, lead):

        wait = WebDriverWait(self.driver, 10)

        is_san_francisco = False

        if "SAN FRANCISCO" == lead.city.upper().strip():
            is_san_francisco = True

        try:
            if not lead.is_inside_consultant:
                current_lead_inside_consultant = wait.until(
                    ec.element_to_be_clickable(
                        (By.XPATH,
                         "//select[@class='lead-owner-select']/option[text()='Josh Rhoades']")))
                current_lead_inside_consultant.click()

                current_lead_inside_consultant_yes = wait.until(
                    ec.element_to_be_clickable(
                        (By.XPATH,
                         "//a[@class='lead-owner-confirm-submit btn-yes-no btn-yes']")))
                current_lead_inside_consultant_yes.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            submit_quote_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH,
                     "//*[@id='ra-installer-project-detail']/div/div[1]/div[2]/div/div["
                     "2]/div/a/span")))

            submit_quote_button.click()

            submit_standard_quote_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH,
                     "//*[@id='ra-installer-project-detail']/div/div[1]/div[2]/div/div["
                     "2]/div/ul/li[1]/a")))
            submit_standard_quote_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            equipment_pricing_select = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_equipment_package_chzn")))
            equipment_pricing_select.click()

            if lead.has_battery:
                equipment_pricing_select_value = wait.until(
                    ec.element_to_be_clickable(
                        (By.ID, "id_equipment_package_chzn_o_1")))
                equipment_pricing_select_value.click()
            else:
                equipment_pricing_select_value = wait.until(
                    ec.element_to_be_clickable(
                        (By.ID, "id_equipment_package_chzn_o_2")))
                equipment_pricing_select_value.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            financing_select = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_financing_package_plus_chzn")))
            financing_select.click()
            if lead.want_financial:
                financing_select_value = wait.until(
                    ec.element_to_be_clickable(
                        (By.ID, "id_financing_package_plus_chzn_o_1")))
                financing_select_value.click()
            else:
                financing_select_value = wait.until(
                    ec.element_to_be_clickable(
                        (By.ID, "id_financing_package_plus_chzn_o_0")))
                financing_select_value.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            panel_number_input = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_panel_number")))
            panel_number_input.clear()
            panel_number_input.send_keys(str(lead.panel_number))
        except Exception as ex:
            self.log_traceback(ex)

        try:
            annual_prod_estimation_input = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_annual_prod_est_kwh")))
            one_year_estimated_str = str(lead.one_year_estimated)
            annual_prod_estimation_input.clear()
            annual_prod_estimation_input.send_keys(one_year_estimated_str)
        except Exception as ex:
            self.log_traceback(ex)

        try:
            if lead.has_battery:
                battery_number_input = wait.until(
                    ec.visibility_of_element_located(
                        (By.ID, "id_storage_product_number")))
                battery_number_input.clear()
                battery_number_input.send_keys("1")
                time.sleep(2)
        except Exception as ex:
            self.log_traceback(ex)

        try:
            cost_per_watt_input = wait.until(
                ec.visibility_of_element_located(
                    (By.ID, "id_ov_cost_per_watt_dc")))

            if is_san_francisco:
                time.sleep(2)
                cost_per_watt_input.send_keys(Keys.CONTROL + "a")
                cost_per_watt_input.send_keys(Keys.DELETE)
                cost_per_watt_input.send_keys(Keys.TAB)
                cost_per_watt_input.send_keys(SAN_FRANCISCO_COST_PER_WATT)
            else:
                time.sleep(2)
                cost_per_watt_input.send_keys(Keys.CONTROL + "a")
                cost_per_watt_input.send_keys(Keys.DELETE)
                cost_per_watt_input.send_keys(Keys.TAB)
                cost_per_watt_input.send_keys(REGULAR_COST_PER_WATT)
            cost_per_watt_input.send_keys(Keys.TAB)
        except Exception as ex:
            self.log_traceback(ex)

        try:
            if lead.system_size <= int(MINIMUM_SYSTEM_SIZE):
                gross_cost_input = wait.until(
                    ec.visibility_of_element_located(
                        (By.ID, "id_ov_pur_gross_cost")))

                gross_cost = float(gross_cost_input.get_attribute('value'))
                gross_cost += int(ADDITION_FOR_GROSS_SYSTEM_COST)
                time.sleep(2)
                gross_cost_input.send_keys(Keys.CONTROL + "a")
                gross_cost_input.send_keys(Keys.DELETE)
                gross_cost_input.send_keys(Keys.TAB)
                gross_cost_input.send_keys(str(int(gross_cost)))
                gross_cost_input.send_keys(Keys.TAB)
        except Exception as ex:
            self.log_traceback(ex)

        try:
            if lead.has_battery:
                battery_gross_cost_input = wait.until(
                    ec.element_to_be_clickable(
                        (By.ID, "id_storage_pur_gross_cost")))
                time.sleep(2)
                battery_gross_cost_input.send_keys(Keys.CONTROL + "a")
                battery_gross_cost_input.send_keys(Keys.DELETE)
                battery_gross_cost_input.send_keys(Keys.TAB)
                battery_gross_cost_input.send_keys(BATTERY_GROSS_COST)
                battery_gross_cost_input.send_keys(Keys.TAB)
        except Exception as ex:
            self.log_traceback(ex)

        try:
            review_and_confirm_button = wait.until(
                ec.visibility_of_element_located(
                    (By.ID, "review-confirm-button")))

            review_and_confirm_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            customization_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//*[@id='qq-package-review']/div[1]/div[4]/div[1]/a")))

            customization_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            next_page_one_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//*[@id='details_form']/div/input")))

            next_page_one_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            is_monitoring_system_button = wait.until(
                ec.visibility_of_element_located(
                    (By.ID, "id_system_design-is_monitoring_system_installed")))
            is_monitoring_system_button.click()

            monitoring_system_select = wait.until(
                ec.visibility_of_element_located(
                    (By.XPATH, "//*[@id='id_system_design_monitor_brand_chzn']")))

            self.actions.move_to_element(monitoring_system_select).perform()

            monitoring_system_select.click()
            monitoring_system_select.click()
            is_monitoring_system_search_input = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//*[@id='id_system_design_monitor_brand_chzn']/div/div/input")))
            is_monitoring_system_search_input.send_keys("SolarEdge Technologies")

            is_monitoring_system_search_selected_value = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH,
                     "//*[@id='id_system_design_monitor_brand_chzn_o_597']")))
            is_monitoring_system_search_selected_value.click()

        except Exception as ex:
            self.log_traceback(ex)

        try:
            next_page_two_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//*[@id='installer-process-detail']/div[1]/div[2]/form/div[5]/input")))

            next_page_two_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            purchase_with_loan_checklist = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_financing_options-is_payment_pln")))

            if purchase_with_loan_checklist.is_selected():
                purchase_with_loan_checklist.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            time.sleep(2)
            next_page_three_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH,
                     "//input[@class='m-button m-button-primary l-button l-button-quote-wiz']")))

            next_page_three_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            battery_gross_cost_input = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_purchase-storage_pur_gross_cost")))
            time.sleep(2)
            battery_gross_cost_input.send_keys(Keys.CONTROL + "a")
            battery_gross_cost_input.send_keys(Keys.DELETE)
            battery_gross_cost_input.send_keys(Keys.TAB)
            battery_gross_cost_input.send_keys(BATTERY_GROSS_COST)
            battery_gross_cost_input.send_keys(Keys.TAB)
        except Exception as ex:
            self.log_traceback(ex)

        try:
            time.sleep(2)
            next_page_four_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH,
                     "//input[@class='m-button m-button-primary l-button l-button-quote-wiz']")))

            next_page_four_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            next_page_five_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//*[@id='purchase_form']/div[2]/input")))

            next_page_five_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            installed_system_attachment = wait.until(
                ec.presence_of_element_located(
                    (By.ID, "id_upload-upload_0")))

            installed_system_attachment.send_keys(os.getcwd() + "/src/banner.png")
        except Exception as ex:
            self.log_traceback(ex)

        try:
            has_additional_file_checklist = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_upload-is_files_to_upload")))

            has_additional_file_checklist.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            installed_system_attachment_one = wait.until(
                ec.presence_of_element_located(
                    (By.ID, "id_upload-upload_1")))

            installed_system_attachment_one.send_keys(os.getcwd() +
                                                      "/src/LGChemBattery_StorEdge_Optimized_Panasonic_400W DC_Coupled_Solution.pdf")
        except Exception as ex:
            self.log_traceback(ex)

        try:
            next_page_six_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//*[@id='installer-process-detail']/div[1]/div[2]/form/div[5]/input")))

            next_page_six_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            submit_quote_final_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH,
                     "//input[@class='m-button m-button-primary l-button l-button-quote-wiz l-button-quote-wiz-confirm']")))

            submit_quote_final_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            review_quote_final_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//a[@class='m-button m-button-primary l-button l-button-installer-thanks']")))

            review_quote_final_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            send_message_final_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//div[@class='engage__message']/a")))

            send_message_final_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            subject_final_input = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_subject")))
            subject_final_input.send_keys("Maximum Panel Count and Solar Access Analysis")
        except Exception as ex:
            self.log_traceback(ex)

        try:
            body_final_input = wait.until(
                ec.element_to_be_clickable(
                    (By.ID, "id_body")))
            body_final_input.clear()
            body_final_input.send_keys("""Hi """ + lead.first_name + """,

    Happy to connect you with one of our C46 solar licensed experts to fine tune our proposal / estimate to your needs. We would also discuss important topics such as the integrity / structure of your roof and the suitability of a solar connection into your main breakers’ box. The consultation ($150 value) comes at no cost to you since you are a local prospect.
    Please schedule your free 15’ phone consultation at https://calendly.com/solarunionconsultant
    Alternatively, please visit our website (www.solarunion.com) and (i) call the 800 number (24/7 line) listed there or (ii) fill out a form to request your free phone consultation.

    SolarUnion Customer Success | SolarUnion is a full-service, residential clean energy company founded in the heart of Silicon Valley. With solar at the center of its operations, SolarUnion delivers home energy control integration solutions to make California homes smart and sustainable.
    """)
        except Exception as ex:
            self.log_traceback(ex)

        try:
            send_email_final_button = wait.until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//input[@value='Send']")))

            send_email_final_button.click()
        except Exception as ex:
            self.log_traceback(ex)

        try:
            message_wait = wait.until(
                ec.visibility_of_element_located(
                    (By.XPATH, "//p[@class='message-for']")))

        except Exception as ex:
            self.log_traceback(ex)

        try:
            actual_lead = self.get_lead_body(lead.id)
            self.save_lead(actual_lead)
        except Exception as ex:
            self.log_traceback(ex)

    def tear_down(self):
        self.driver.close()
        self.connection.commit()
        self.connection.close()

    def save_lead(self, lead):
        try:
            self.cursor.execute("SELECT id FROM leads WHERE id = ?", (lead.id,))
            data = self.cursor.fetchall()
            if len(data) == 0:
                self.cursor.execute("INSERT INTO leads VALUES (:id, :created_date, :last_name, :first_name, :address,"
                                    ":city, :state, :zip_code, :phone, :email, :e_sage_link, :annual_usage,"
                                    ":effective_electricity_cost, :average_bill, :one_year_estimated, :panel_number,"
                                    ":system_size, :want_financial, :has_bill, :has_notes, :has_battery,"
                                    ":has_beat_my_quote, :is_inside_consultant, :is_quoted)"
                                    , lead.__dict__)
            else:
                self.cursor.execute("UPDATE leads SET phone = :phone, email = :email, is_quoted = :is_quoted"
                                    " WHERE id = :id"
                                    , lead.__dict__)

            self.connection.commit()

            self.logger.info("Lead Saved")

        except Exception as ex:
            self.log_traceback(ex)

    def generate_report(self):
        report = Report()
        self.cursor.execute("SELECT * FROM leads WHERE is_quoted = 1")
        rows = self.cursor.fetchall()
        leads = []
        for row in rows:
            lead = Lead(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                        row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15],
                        row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23])
            leads.append(lead)
        report.generate_report(leads)
        self.connection.commit()
        print(rows)
        self.tear_down()

    def start(self):

        self.login()

        actual_page = 1

        if READ_QUOTED == "F":
            self.current_url = self.main_url + "/market/properties/intent/?page=" + str(actual_page) + \
                               "&include_stale_leads=" + INCLUDE_STALE_LEADS
        else:
            self.current_url = self.main_url + "market/properties/quoted/?page=" + str(actual_page) + \
                               "&sb=order_received&q=&s=&pt=&f=&st="
        number_of_pages = self.get_number_of_pages()

        final_count = 0

        for page in range(1, number_of_pages + 1):
            if READ_QUOTED == "F":
                self.current_url = self.main_url + "/market/properties/intent/?page=" + str(page) + \
                                   "&include_stale_leads=" + INCLUDE_STALE_LEADS
            else:
                self.current_url = self.main_url + "market/properties/quoted/?page=" + str(page) + \
                                   "&sb=order_received&q=&s=&pt=&f=&st="

            count_processed = 0
            for quoted_link in self.get_leads(page):
                e_sage_link = quoted_link["href"]
                lead_id = -1
                try:
                    lead_id = int(e_sage_link.split('/')[-2].strip())
                    count_processed += 1
                    final_count += 1

                    self.current_url = self.main_url + quoted_link["href"]
                    self.logger.info("LEAD N° " + str(count_processed) + ": " + str(lead_id))

                except Exception as ex:
                    self.log_traceback(ex)
                if lead_id != -1:
                    actual_lead = self.get_lead_body(lead_id)

                    self.logger.info(actual_lead.to_string())
                    try:
                        self.save_lead(actual_lead)
                    except Exception as ex:
                        self.log_traceback(ex)

                    if READ_QUOTED == "F":
                        self.send_lead_quote(actual_lead)

        self.tear_down()


if __name__ == "__main__":
    process = LeadDealer()
    process.start()
    # process.generate_report()

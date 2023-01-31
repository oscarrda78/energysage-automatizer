from openpyxl.workbook import Workbook
from EnergysageLeadModel import Lead
import time
from datetime import date, datetime


class Report(object):
    def __init__(self):
        self.awaiting_quotes_sheet = None
        self.awaiting_quotes_workbook = None

    def set_up_awaiting_quotes_workbook(self):
        self.awaiting_quotes_workbook = Workbook()

        self.awaiting_quotes_sheet = self.awaiting_quotes_workbook.active
        self.awaiting_quotes_sheet["A1"] = "Date"
        self.awaiting_quotes_sheet["B1"] = "Last Name"
        self.awaiting_quotes_sheet["C1"] = "First Name"
        self.awaiting_quotes_sheet["D1"] = "Address"
        self.awaiting_quotes_sheet["E1"] = "City"
        self.awaiting_quotes_sheet["F1"] = "State"
        self.awaiting_quotes_sheet["G1"] = "Zip Code"
        self.awaiting_quotes_sheet["H1"] = "Phone"
        self.awaiting_quotes_sheet["I1"] = "E-Mail"
        self.awaiting_quotes_sheet["J1"] = "Esage Link"
        self.awaiting_quotes_sheet["K1"] = "Annual Usage"
        self.awaiting_quotes_sheet["L1"] = "Avg Bill"
        self.awaiting_quotes_sheet["M1"] = "Notes?"
        self.awaiting_quotes_sheet["N1"] = "Bill?"
        self.awaiting_quotes_sheet["O1"] = "Battery"
        self.awaiting_quotes_sheet["P1"] = "Beat my Quote"
        self.awaiting_quotes_sheet["Q1"] = "Is Inside Consultant"

    def generate_report(self, leads):
        self.set_up_awaiting_quotes_workbook()
        for lead_index, lead in enumerate(leads):
            val_index = lead_index + 2
            self.awaiting_quotes_sheet["A" + str(val_index)] = lead.created_date
            self.awaiting_quotes_sheet["B" + str(val_index)] = lead.last_name
            self.awaiting_quotes_sheet["C" + str(val_index)] = lead.first_name
            self.awaiting_quotes_sheet["D" + str(val_index)] = lead.address
            self.awaiting_quotes_sheet["E" + str(val_index)] = lead.city
            self.awaiting_quotes_sheet["F" + str(val_index)] = lead.state
            self.awaiting_quotes_sheet["G" + str(val_index)] = lead.zip_code
            self.awaiting_quotes_sheet["H" + str(val_index)] = lead.phone
            self.awaiting_quotes_sheet["I" + str(val_index)] = lead.email
            self.awaiting_quotes_sheet["J" + str(val_index)] = lead.e_sage_link
            self.awaiting_quotes_sheet["K" + str(val_index)] = lead.annual_usage
            self.awaiting_quotes_sheet["L" + str(val_index)] = lead.average_bill
            self.awaiting_quotes_sheet["M" + str(val_index)] = lead.has_notes
            self.awaiting_quotes_sheet["N" + str(val_index)] = lead.has_bill
            self.awaiting_quotes_sheet["O" + str(val_index)] = lead.has_battery
            self.awaiting_quotes_sheet["P" + str(val_index)] = lead.has_beat_my_quote
            self.awaiting_quotes_sheet["Q" + str(val_index)] = lead.is_inside_consultant

        today = date.today()
        today_timestamp = int(time.mktime((datetime.strptime(str(today), '%Y-%m-%d').timetuple())))
        self.awaiting_quotes_workbook.save(
            filename="Quoted Leads - " + str(today_timestamp) + ".xlsx")

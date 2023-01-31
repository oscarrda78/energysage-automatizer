class Lead(object):
    def __init__(self, lead_id, created_date, last_name, first_name, address, city, state,
                 zip_code, phone, email, e_sage_link, annual_usage,
                 effective_electricity_cost, average_bill, one_year_estimated, panel_number,
                 system_size, want_financial, has_bill, has_notes, has_battery,
                 has_beat_my_quote, is_inside_consultant, is_quoted):
        self.id = lead_id
        self.created_date = created_date
        self.last_name = last_name
        self.first_name = first_name
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.phone = phone
        self.email = email
        self.e_sage_link = e_sage_link
        self.annual_usage = annual_usage
        self.effective_electricity_cost = effective_electricity_cost
        self.average_bill = average_bill
        self.panel_number = panel_number
        self.system_size = system_size
        self.one_year_estimated = one_year_estimated
        self.want_financial = want_financial
        self.has_bill = has_bill
        self.has_notes = has_notes
        self.has_battery = has_battery
        self.has_notes = has_notes
        self.has_beat_my_quote = has_beat_my_quote
        self.is_inside_consultant = is_inside_consultant
        self.is_quoted = is_quoted

    def to_string(self):
        string_object = "\nCreated Date: " + str(self.created_date) + \
                        "\nLast Name: " + self.last_name + \
                        "\nFirst Name: " + self.first_name + \
                        "\nAddress: " + self.address + \
                        "\nCity: " + self.city + \
                        "\nState: " + self.state + \
                        "\nZip Code: " + self.zip_code + \
                        "\nPhone: " + self.phone + \
                        "\nEmail: " + self.email + \
                        "\nEsage Link: " + self.e_sage_link + \
                        "\nAnnual Usage: " + self.annual_usage + \
                        "\nEffective Electricity Cost: " + self.effective_electricity_cost + \
                        "\nAverage Bill: " + self.average_bill + \
                        "\nHas Comments?: " + str(self.has_notes) + \
                        "\nHas Battery?: " + str(self.has_battery) + \
                        "\nHas Notes?: " + str(self.has_notes) + \
                        "\nHas Beat My Quote?: " + str(self.has_beat_my_quote) + \
                        "\nIs Inside Consultant?: " + str(self.is_inside_consultant) + \
                        "\nIs Quoted?: " + str(self.is_quoted)

        return string_object

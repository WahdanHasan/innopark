from config.twilio import twilio_config as config
from classes.system_utilities.data_utilities import DatabaseUtilities as DU
from classes.system_utilities.helper_utilities import Constants

from twilio.rest import Client
import sys


def sendSmsToLicense(license_plate, tariff_amount):


    vehicle_registered_phone_number = DU.GetValueOfFieldOnArrayValueMatch(collection="government-registered-drivers",
                                                                match_key=Constants.gov_license_key,
                                                                match_value=license_plate,
                                                                get_value_key=Constants.gov_phone_number_key)



    if vehicle_registered_phone_number is None:
        print("[SMS] License plate is not registered to government database. This may be due to an incorrect plate number.", file=sys.stderr)
        return

    client = Client(config.account_sid, config.auth_token)

    message = client.messages.create(body=buildSmsPaymentMessage(license_plate, tariff_amount, "www.payflow.com"),
                                     from_="Innopark",
                                     to=vehicle_registered_phone_number
                                     )

    print("[SMS] SMS sent to " + vehicle_registered_phone_number, file=sys.stderr)


def buildSmsPaymentMessage(license_plate, tariff_amount, payment_link):
    return "Thank you for using Innopark parkings!\n\nYour total bill for the vehicle " + license_plate + " is " + \
           str(tariff_amount) + "AED.\nTo proceed to payment, tap " + payment_link

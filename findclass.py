"""
Determines if class is open, full, waitlist, or invalid given class number
Features checklist:
[ ] Support online classes
[ ] Support classes with TBD as time


IMPORTANT
This module imports spire_cred, a module
I made that contains username and password to log into spire_cred
You have to create your own module with your own credentials
to make it work.

"""

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import sys
import spire_cred
import time
import requests
import json
# -------------------ATTENTION--------------------
import signal
from classstatus import ClassStatus


def find_class(class_num):
    """
    Find class given class number
    :param class_num: spire class number
    :return: dictionary container class status, class number, class name
    """
    # -------------------ATTENTION--------------------
    # For AWS EC2
    browser = webdriver.PhantomJS(service_args=['--ssl-protocol=any'])
    # For my Windows
    # browser = webdriver.PhantomJS()
    browser.implicitly_wait(5)
    # Go to Spire
    umass_spire_webpage = 'https://www.spire.umass.edu/'
    browser.get(umass_spire_webpage)
    # Locate text fields
    username = browser.find_element_by_css_selector("#userid")
    password = browser.find_element_by_css_selector("#pwd")
    # Input info in text fields
    username.send_keys(spire_cred.get_username())
    password.send_keys(spire_cred.get_password())
    # Press log in
    browser.find_element_by_css_selector('#login > p:nth-child(5) > input[type="submit"]').submit()

    # Invalid, Open, Full, WaitList
    status = determine_class_type(browser, class_num)
    # -------------------ATTENTION--------------------
    # For AWS EC2
    browser.service.process.send_signal(signal.SIGTERM)
    browser.quit()

    return status


def determine_class_type(browser, class_num, wait=0.25):
    """
    Determine if class exists given class number
    :param browser: web driver
    :param class_num: given class number from user through Facebook
    :param wait: explicit wait for slow internet
    :return: a tuple with true (iff class exists) and class level (undergrad vs. grad.)
    """
    # Directly go to this link for searching class
    search_link = 'https://www.spire.umass.edu/' \
                  'psc/heproda/EMPLOYEE/HRMS/c/' \
                  'SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?' \
                  'Page=SSR_CLSRCH_ENTRY&Action=U'

    browser.get(search_link)
    # Make wait time for element to appear shorter (not sure if needed)
    browser.implicitly_wait(3)

    try:
        # Tick off 'Show Open Classes Only' checkbox
        checkbox = browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_SSR_OPEN_ONLY')
        # Click checkbox
        checkbox.click()
        # Spire requires more than one way to search for narrowing down search
        days_include = Select(browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_INCLUDE_CLASS_DAYS'))
        # Select include any day
        days_include.select_by_visible_text('include any of these days')
        # Click checkboxes for all week days
        click_all_week_days_checkbox(browser)

        return determine_class(browser, class_num, wait)

    except NoSuchElementException:
        # In case Selenium cannot find a certain element
        print('{}: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Cannot find element, repeating'))
        return determine_class_type(browser, class_num, wait=wait+0.1)


def determine_class(browser, class_num, wait=0.25):
    """
    Determine what kind of class it is
    This does not account for online classes with Day/Times being TBD
    Online classes/Online class with in person help will be a optional feature
    documented on the website that the flask app has (This decision is needed for
    :param browser: web driver
    :param class_num: class number given by user through Facebook
    :param wait: The wait time for some parts of the code
    :return: Invalid, Open, Full
    """
    # Locate the search button
    search_button = browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')
    # Locate the text field for class number (xpath is not recommended but it's not possible to use css in this case)
    class_number_input = browser.find_element_by_xpath('//input[@onchange="addchg_win0(this);oChange_win0=this;"]')
    # Input a certain class number given by parameter
    class_number_input.send_keys(class_num)
    # Find parent of search_button to focus on, ensuring button click
    button_parent = browser.find_element_by_css_selector('#win0divCLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')
    # Click parent
    button_parent.click()
    # Click search button (While a button is focused, press enter)
    search_button.click()
    # Page sometimes do not process properly if actions are not done in a slow manner (DOM cannot catch up)
    time.sleep(wait)
    # Find "The search returns no results that match the criteria specified." on web page (Check if invalid class #)
    valid_class = not browser.find_elements_by_css_selector('#DERIVED_CLSMSG_SSR_MSG_PB > img')
    # Determine status of class
    full_status, open_status, waitlist_status, class_name = determine_status_and_name(browser)
    # It's impossible for the following if expression to be true, if it is, something is wrong
    # This is necessary in case buttons are not clicked properly by Selenium
    if valid_class and not full_status and not open_status and not waitlist_status:
        # Directly go to this link for searching class
        return determine_class_type(browser, class_num, wait=wait+0.25)

    # repeating valid_class guarantees that it's a valid class, omitting it may still work
    if valid_class and full_status:
        return {'status': ClassStatus.full.value, "number": class_num, "name": class_name}
    if valid_class and open_status:
        return {'status': ClassStatus.open.value, "number": class_num, "name": class_name}
    if valid_class and waitlist_status:
        return {'status': ClassStatus.waitlist.value, "number": class_num, "name": class_name}
    return {'status': ClassStatus.invalid.value}


def determine_status_and_name(browser):
    """
    Determines status of class by locating specific symbols
    in spire that shows if the class is full, open, or in waitlist
    :param browser: the web driver
    :return: a tuple of 3 array and a string, the arrays represent full, open and waitlist respectively
    the string is the class name. (A nonempty array means "True" for that variable)
    """
    # Find Table and find "full" status image (grey square), it means class exists and the class is full
    full_status = []
    open_status = []
    waitlist_status = []
    class_name = ''
    table = browser.find_elements_by_xpath('//table[@id="ACE_$ICField102$0"]')
    if table:
        full_status = table[0].find_elements_by_xpath('.//img[@src="/cs/heproda/cache/PS_CS_STATUS_CLOSED_ICN_1.gif"]')
        open_status = table[0].find_elements_by_xpath('.//img[@src="/cs/heproda/cache/PS_CS_STATUS_OPEN_ICN_1.gif"]')
        waitlist_status = table[0].find_elements_by_xpath(
            './/img[@src="/cs/heproda/cache/PS_CS_STATUS_WAITLIST_ICN_1.gif"]')
        class_name = table[0].find_element_by_xpath('.//*[@id="DERIVED_CLSRCH_DESCR200$0"]').text
    return full_status, open_status, waitlist_status, class_name


def search_online_class(browser, wait=0.25):
    """
    See if class is actually an online class, because the previous search is done base on
    using weekdays as a factor to narrow down the search. Some/All online classes have their
    time set as TBD, making those classes invalid if searched with weekdays
    :param browser: the web driver
    :param wait: explicit wait
    """
    # Click all week days checkbox again to uncheck all checkbox for searching online TBD classes
    click_all_week_days_checkbox(browser)
    # Find the drop down menu for mode of instruction on Spire
    mode_of_instruction = Select(browser.find_element_by_css_selector('#UM_DERIVED_SR_UM_INSTRUCTIONMODE'))
    # Select Online
    mode_of_instruction.select_by_visible_text('Online')
    # Find search button for clicking
    search_button = browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')
    # Find parent of search_button to focus on, ensuring button click
    button_parent = browser.find_element_by_css_selector('#win0divCLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')
    # Click parent
    button_parent.click()
    # Click search button (While a button is focused, press enter)
    search_button.click()
    # Wait a bit so stuff are processed (weirdly works)
    time.sleep(wait)


def click_all_week_days_checkbox(browser):
    """
    Click all checkboxes for all weekdays (assuming browser is at Spire search class web page)
    :param browser: web driver
    """
    # Click checkboxes for all days
    browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_MON').click()
    browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_TUES').click()
    browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_WED').click()
    browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_THURS').click()
    browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_FRI').click()
    browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_SAT').click()
    browser.find_element_by_css_selector('#CLASS_SRCH_WRK2_SUN').click()


def send_request_to_host(host, port, fb_sender_id, status_dict):
    """
    Sends POST request to given host and port, notifying of
    class status
    :param host: the host the server is run on
    :param port: the port the server is run on
    :param fb_sender_id: facebook sender id
    :param status_dict: status of class
    """
    url = 'http://{}:{}'.format(host, port)
    status = status_dict["status"]

    fb_status_dict = {"object": "finder",
                      "class": {"status": status},
                      "sender": {"id": fb_sender_id}}
    if status != ClassStatus.invalid.value:
        fb_status_dict["class"]["number"] = status_dict["number"]
        fb_status_dict["class"]["name"] = status_dict["name"]

    requests.post(url,
                  headers={"Content-Type": "application/json"},
                  data=json.dumps(fb_status_dict))


def flags_and_args(args_list):
    flag_dict = {'f': 'force'}
    flags = []
    first_element_first_char = args_list[0][0]
    if '-' != first_element_first_char:
        return flags, args_list
    flag_string = args_list[0][1:]
    for letter in flag_string:
        if letter in flag_dict:
            flags.append(flag_dict[letter])
        if letter not in flag_dict:
            # Debug
            print('This flag, \'{}\' does not exists...ignoring flag'.format(letter))
    return flags, args_list[1:]


def class_status_changed(previous_status, current_status):
    return previous_status != current_status


if __name__ == "__main__":
    # Get rid of first element, the file name
    arguments = sys.argv[1:]
    # Finds flags, and separates arguments
    flags_list, arguments = flags_and_args(arguments)
    # the wait time after each class check
    wait_time = 5  # minutes
    # Set up variables
    host_name = arguments[0]
    port_num = arguments[1]
    class_number = arguments[2]
    sender_id = arguments[3]

    if len(arguments) == 5:
        # wait time can be modified by providing a fifth optional argument
        wait_time = arguments[4]
    full_class = False
    if len(flags_list) == 0:
        status_dictionary = find_class(class_number)
        # Send the status of class and additional info to Flask app given host, and port
        send_request_to_host(host_name, port_num, sender_id, status_dictionary)
        # Determine if status is full
        full_class = ClassStatus.full.value == status_dictionary['status']
    # If it's not a full class, exit
    if not full_class:
        exit(0)
    # So far, the force flag can be omitted out of implementation until needed
    wait_time = wait_time * 60  # convert minute to seconds
    class_is_full = True
    time.sleep(wait_time)
    while True:
        status_dictionary = find_class(class_number)
        class_is_full_current = True if ClassStatus.full.value == status_dictionary["status"] else False
        # For debugging
        # print('{} : {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), status_dictionary))
        if class_status_changed(class_is_full, class_is_full_current):
            send_request_to_host(host_name, port_num, sender_id, status_dictionary)
            # Debug
            # print('status message sent')
        class_is_full = class_is_full_current
        time.sleep(wait_time)

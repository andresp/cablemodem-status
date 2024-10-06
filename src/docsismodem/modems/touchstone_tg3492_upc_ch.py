from .observablemodem import ObservableModem
from bs4 import BeautifulSoup
from datetime import datetime
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from influxdb_client import Point

class TouchstoneTG3492UPCCH(ObservableModem):
    baseUrl = ""
    session = None
    seleniumUri = None
    loggedIn = False
    browser = None

    def __init__(self, config, logger):
        self.baseUrl = "http://" + config['Modem']['Host']
        self.seleniumUri = config['General'].get("SeleniumUri")

        super(TouchstoneTG3492UPCCH, self).__init__(config, logger)

    def __del__(self):
        if self.browser is not None:
            self.browser.quit()

    def formatUpstreamPoints(self, data, errorData, sampleTime):
        points = []
        for index in range(len(data)):

            row = data[index].select("td")
            errorDataRow = errorData[index].select("td")
            
            point = Point("upstreamQam") \
                .tag("channel", row[0].text) \
                .tag("lockStatus", "Locked") \
                .tag("modulation", row[4].text) \
                .tag("channelId", row[5].text) \
                .tag("symbolRate", int(row[3].text.split()[0])) \
                .tag("usChannelType", errorDataRow[1].text) \
                .tag("frequency", row[1].text) \
                .time(sampleTime) \
                .field("power", float(row[2].text))

            points.append(point)

        return points

    def formatDownstreamPoints(self, data, errorData, sampleTime):
        points = []

        for index in range(len(data)):

            row = data[index].select("td")
            errorDataRow = errorData[index].select("td")

            measurement = ""
            if row[4].text == "QAM256":
                measurement = "downstreamQam"
            else:
                continue
                
            point = Point(measurement) \
                .tag("channel", row[0].text) \
                .tag("modulation", row[4].text) \
                .tag("lockStatus", errorDataRow[1].text) \
                .tag("channelId", row[5].text) \
                .tag("frequency", row[1].text) \
                .time(sampleTime) \
                .field("power", float(row[2].text)) \
                .field("snr", float(row[3].text)) \
                .field("subcarrierRange", "") \
                .field("uncorrected", 0) \
                .field("correctables", int(errorDataRow[3].text)) \
                .field("uncorrectables", int(errorDataRow[4].text))

            points.append(point)

        return points

    def formatOfdmDownstreamPoints(self, data, errorData, sampleTime):
        points = []

        for index in range(len(data)):

            row = data[index].select("td")
            errorDataRow = errorData[index].select("td")

            measurement = ""
            if row[4].text == "QAM4096":
                measurement = "downstreamOFDM"
            else:
                continue
                
            point = Point(measurement) \
                .tag("channel", row[0].text) \
                .tag("modulation", row[4].text) \
                .tag("lockStatus", errorDataRow[1].text) \
                .tag("channelId", errorDataRow[0].text) \
                .tag("frequency", row[5].text + "000000") \
                .time(sampleTime) \
                .field("power", float(errorDataRow[3].text)) \
                .field("snr", float(errorDataRow[2].text)) \
                .field("subcarrierRange", row[3].text) \
                .field("uncorrected", 0) \
                .field("correctables", int(errorDataRow[4].text)) \
                .field("uncorrectables", int(errorDataRow[5].text))

            points.append(point)

        return points

    def login(self):
        self.logger.info("Logging into modem")

        if self.browser is None:
            if self.seleniumUri is None:
                raise ValueError("Must configure a value for General->SeleniumUri.")

            self.logger.info("Connecting to Selenium remote")
            self.browser = Remote(self.seleniumUri, DesiredCapabilities.CHROME)

        try:
            passwordInput = self.browser.find_element(By.ID, 'cableModemStatus')
            self.loggedIn = True
        except:
            self.loggedIn = False

        if self.loggedIn:
            return

        try:
            self.browser.get(self.baseUrl)

            passwordInput = self.browser.find_element(By.ID, 'Password')
            passwordInput.send_keys(self.config['Modem']['Password'])

            loginButton = self.browser.find_element(By.CLASS_NAME, 'submitBtn')
            loginButton.click()

            WebDriverWait(self.browser, 60).until(
                EC.presence_of_element_located((By.ID, "AdvancedSettings"))
            )

            self.logger.info("Navigating to modem status")
            self.browser.get(self.baseUrl + "?device_networkstatus&mid=NetworkStatus")

            WebDriverWait(self.browser, 60).until(
                EC.presence_of_element_located((By.ID, "cableModemStatus"))
            )
            self.logger.info("Login successful")
            self.loggedIn = True
        except Exception as ex:
            self.logger.error("Failed to log in: '%s'.", exc_info=ex)
            self.browser.quit()

    def collectStatus(self):
        self.logger.info("Refreshing modem status")

        refreshButton = self.browser.find_element(By.CLASS_NAME, 'refreshStatus')
        refreshButton.click()

        WebDriverWait(self.browser, 60).until(
            EC.presence_of_element_located((By.ID, "cableModemStatus"))
        )
        self.logger.info("Modem status refreshed")

        sampleTime = datetime.utcnow().isoformat()
        
        # Extract status data
        statusPage = BeautifulSoup(self.browser.page_source, features="lxml")

        downstreamData = statusPage.find(id="DownstremChannel").select("tbody > tr")
        codewordsData = statusPage.find(id="DownstremChannel2").select("tbody > tr")

        downstreamPoints = self.formatDownstreamPoints(downstreamData, codewordsData, sampleTime)

        # OFDM
        downstreamOfdmData = statusPage.find(id="DownstremChannel_31").select("tbody > tr")
        codewordsOfdmData = statusPage.find(id="DownstremChannel2_31").select("tbody > tr")

        downstreamOfdmPoints = self.formatOfdmDownstreamPoints(downstreamOfdmData, codewordsOfdmData, sampleTime)

        upstreamData = statusPage.find(id="UpstremChannel").select("tbody > tr")
        upstreamErrorData = statusPage.find(id="UpstremChannel1").select("tbody > tr")

        upstreamPoints = self.formatUpstreamPoints(upstreamData, upstreamErrorData, sampleTime)

        # Store data to InfluxDB
        self.timeseriesWriter.write(record=downstreamPoints)
        self.timeseriesWriter.write(record=downstreamOfdmPoints)
        self.timeseriesWriter.write(record=upstreamPoints)

    def collectLogs(self):
        # Not implemented yet
        return
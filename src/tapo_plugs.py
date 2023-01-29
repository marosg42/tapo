import logging
import os
import telepot
import time
import yaml
from PyP100 import PyP110

f = open("list.yaml", mode="r")
plugs = yaml.load(f, Loader=yaml.FullLoader)

bot = telepot.Bot(os.environ["TELEGRAM_BOT_ID"])
bot.sendMessage(os.environ["TELEGRAM_SEND_TO"], "Started")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

for plug in plugs:
    plug["tapo"] = PyP110.P110(
        plug["ip"], os.environ["TPLINK_LOGIN"], os.environ["TPLINK_PASSWORD"]
    )
    plug["sleep"] = 1800
    plug["is_on"] = False
    plug["below_threshold"] = 0
    plug["tapo"].handshake()
    plug["tapo"].login()
    plug["name"] = plug["tapo"].getDeviceName()

while True:
    for plug in plugs:
        try:
            usage = plug["tapo"].getEnergyUsage()["result"]
            current_w = usage["current_power"] / 1000.0
            logging.info(f"{plug['name']}: {current_w} W")
        except Exception:
            logging.info(f"{plug['name']}:   Connection error")
            continue
        if plug["is_on"]:
            if current_w < plug["threshold_down"]:
                if plug["below_threshold"] < 2:
                    plug["below_threshold"] += 1
                else:
                    plug["is_on"] = False
                    plug["sleep"] = 1800
                    logging.info(f"{plug['name']}:" + " " * 40 + "OFF")
                    bot.sendMessage(
                        os.environ["TELEGRAM_SEND_TO"], f"{plug['name']}: OFF"
                    )
            else:
                plug["below_threshold"] = 0
        else:
            if current_w > plug["threshold_up"]:
                plug["is_on"] = True
                plug["below_threshold"] = 0
                plug["sleep"] = 60
                logging.info(f"{plug['name']}:" + " " * 40 + "ON")
                bot.sendMessage(os.environ["TELEGRAM_SEND_TO"], f"{plug['name']}: ON")
    sleeptimes = [plug["sleep"] for plug in plugs]
    sleeptime = sorted(sleeptimes)[0]
    logging.info(f"Going to sleep for {sleeptime} seconds")
    time.sleep(sleeptime)

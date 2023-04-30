#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
from inky.inky_uc8159 import Inky, DESATURATED_PALETTE
from datetime import datetime
from PIL import Image, ImageFont, ImageDraw
import apikey, os
import sys
from dataclasses import dataclass
from typing import List, Optional, Union, Type
import cattrs
import datetime
from dataclasses import dataclass
import math
import requests

path = os.path.dirname(os.path.realpath(__file__))

ICON_SIZE = 100
TILE_WIDTH = 150
TILE_HEIGHT = 200
FONT_SIZE = 25
SPACE = 2
ROTATE = 0 # 180 = flip display
USE_INKY = True
SHOW_CLOCK = False
SLEEP_TIME = 3600
colours = ['Black', 'White', 'Green', 'Blue', 'Red', 'Yellow', 'Orange']
percipitation_colour = colours[0]
temp_colour = colours[4]
day_colour = colours[2]
presure_colour = colours[3]
LABELS = ['A','B','C','D']

time_colour = colours[4]

def serialize_datetime(dt):
    return dt.isoformat()

def deserialize_datetime(dt:Optional[Union[str,int]], target_type:Type[datetime.datetime]) -> Optional[datetime.datetime]:
    if not dt:
        return None
    if type(dt) == 'str':
        return datetime.datetime.fromisoformat(dt)
    return datetime.datetime.fromtimestamp(dt)

cattrs.register_structure_hook(datetime.datetime, deserialize_datetime)
cattrs.register_unstructure_hook(datetime.datetime, serialize_datetime)

@dataclass
class DailyForecast:
    time: datetime.datetime
    icon: str
    summary: str
    sunriseTime: datetime.datetime
    sunsetTime: datetime.datetime
    moonPhase: float
    precipIntensity: float
    precipIntensityMax: float
    precipIntensityMaxTime: datetime.datetime
    precipProbability: float
    precipAccumulation: float
    precipType: str
    temperatureHigh: float
    temperatureHighTime: datetime.datetime
    temperatureLow: float
    temperatureLowTime: datetime.datetime
    apparentTemperatureHigh: float
    apparentTemperatureHighTime: datetime.datetime
    apparentTemperatureLow: float
    apparentTemperatureLowTime: datetime.datetime
    dewPoint: float
    humidity: float
    pressure: float
    windSpeed: float
    windGust: float
    windGustTime: datetime.datetime
    windBearing: float
    cloudCover: float
    uvIndex: float
    uvIndexTime: datetime.datetime
    visibility: float
    temperatureMin: float
    temperatureMinTime: datetime.datetime
    temperatureMax: float
    temperatureMaxTime: datetime.datetime
    apparentTemperatureMin: float
    apparentTemperatureMinTime: datetime.datetime
    apparentTemperatureMax: float
    apparentTemperatureMaxTime: datetime.datetime

@dataclass
class ForecastData:
    # current: CurrentWeather
    daily: List[DailyForecast]=None
    # hourly: List[HourlyForecast]
    # minutely: List[MinutelyForecast]


def get_icon(name):
    return Image.open(name).convert("RGBA")

if (apikey.api_key == "<your API key>"):
    print("You forgot to enter your API key", file=sys.stderr)
    sys.exit(1)

palette_colors = [(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0) for c in DESATURATED_PALETTE[2:6] + [(0, 0, 0)]]

tile_positions = []
for i in range(2):
    for j in range(4):
        tile_positions.append((j * TILE_WIDTH, i * TILE_HEIGHT))

satuation = 0

font = ImageFont.truetype(path+
    "/fonts/BungeeColor-Regular_colr_Windows.ttf", FONT_SIZE)

weather_icons = {
    'clear-day': 'icons/wi-day-sunny.png',
    'clear-night': 'icons/wi-night-clear.png',
    'rain': 'icons/wi-rain.png',
    'snow': 'icons/wi-snow.png',
    'sleet': 'icons/wi-sleet.png',
    'wind': 'icons/wi-windy.png',
    'fog': 'icons/wi-fog.png',
    'cloudy': 'icons/wi-cloudy.png',
    'partly-cloudy-day': 'icons/wi-day-cloudy.png',
    'partly-cloudy-night': 'icons/wi-night-alt-cloudy.png'
}

def fetch_forecast(api_key:str, lat:float, lon:float) -> ForecastData:
    url = f"https://api.pirateweather.net/forecast/{apikey.api_key}/{apikey.lat},{apikey.lon}?units=us"
    response = requests.get(url)
    data = json.loads(response.text)

    ret = ForecastData()
    ret.daily = [
        cattrs.structure(day, DailyForecast)
        for day in data['daily']['data']
    ]

    return ret

def update(inky_display: Inky):
    data = fetch_forecast(apikey.api_key, apikey.lat, apikey.lon)

    img = Image.new("RGBA", inky_display.resolution, colours[1])
    draw = ImageDraw.Draw(img)

    for d,day in enumerate(data.daily[0:8]):
        icon = Image.open(weather_icons[day.icon]).convert("RGBA")

        x = tile_positions[d][0] + (TILE_WIDTH - ICON_SIZE) // 2
        y = tile_positions[d][1]
        img.paste(icon, (x, y))
        text = str(int(100 * day.precipProbability)) + "%"
        w, h = font.getsize(text)
        x = tile_positions[d][0] + (TILE_WIDTH - w) // 2
        y = tile_positions[d][1] + ICON_SIZE + SPACE
        draw.text((x, y), text, percipitation_colour, font)
        
        text = str(int(math.floor(day.apparentTemperatureMin))) + "°|" + str(int(math.ceil(day.apparentTemperatureMax))) + "°"
        w, h = font.getsize(text)
        x = tile_positions[d][0] + (TILE_WIDTH - w) // 2
        y += FONT_SIZE
        draw.text((x, y), text, temp_colour, font)
        press = str(int(day.pressure))
        text = str(press)+"hPa"
        w, h = font.getsize(text)
        x = tile_positions[d][0] + (TILE_WIDTH - w) // 2
        y += FONT_SIZE
        draw.text((x, y), text, presure_colour, font)
        ts = day.time
        day_name = day.time.strftime("%a")
        text = day_name
        w, h = font.getsize(text)
        x = tile_positions[d][0] + (TILE_WIDTH - w) // 2
        y += FONT_SIZE
        draw.text((x, y), text, day_colour, font)
        img.rotate(180)

    if (SHOW_CLOCK == True):
        now =  datetime.now()
        current_time = now.strftime("%H:%M")
        draw.text((245, 410), current_time, time_colour, font)
    if (USE_INKY):
        inky_display.set_border(colours[4])
        inky_display.set_image(img.rotate(ROTATE), saturation=0)
        inky_display.show()
    else:
        img.show()
  

if __name__ == '__main__':
    inky_display = Inky()
    update(inky_display)
import traceback

import pandas as pd
import requests
import json
import pymysql
import urllib

from pandas import json_normalize
from urllib import parse
from sqlalchemy import create_engine, text
from datetime import datetime

# MySQL 연결 설정
engine = create_engine('mysql+pymysql://root:kimbigdata201844006@3.36.126.107:42032/bigdata')
connection = engine.connect()

api_key = '9A099EDA0A1F21B5BDD61E64CFB9CA78'

def game_list_api(URL, params=None):
    headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}
    try:
        response = requests.get(URL, headers=headers, params=params)
        return response.json()
    except Exception as e:
        print(e)

def getSteamGameInfo():
    url = 'https://store.steampowered.com/api/appdetails'
    param = {
        'appids': '',
        'l':'korean'
    }
    sql_query = text("SELECT appid FROM steamGameID")

    # 데이터베이스에서 데이터 읽어오기
    result = connection.execute(sql_query)

    # fetchall()을 사용하여 값 리스트로 가져오기
    appid_list = [row[0] for row in result.fetchall()]
    SteamGameInfoDF = pd.DataFrame(columns=["appid", "is_free", "recommendations", "release_date", "release_status", "score", "price", "age"])
    SteamGameCateDF = pd.DataFrame(columns=['appid','categori'])
    SteamTypeDF = pd.DataFrame(columns=['appid', 'type'])
    appid_list = list(set(appid_list))
    save_flag = False
    for appid in appid_list:
        try:
            print(appid, end='\t')
            param['appids'] = str(appid)
            value = game_list_api(url, param)
            gameLoadSuccessDict = value[str(appid)]
            print(gameLoadSuccessDict)

            if not gameLoadSuccessDict['success']:
                continue

            gameInfoDataDict = gameLoadSuccessDict['data']

            SteamTypeDF.loc[len(SteamTypeDF)] = {'appid': appid, 'type':gameInfoDataDict['type']}

            if gameInfoDataDict['type'] != 'game' and gameInfoDataDict['type'] != 'dlc':
                continue

            score = -1
            price = 0
            if 'metacritic' in gameInfoDataDict:
                score = gameInfoDataDict['metacritic']['score']

            if 'price_overview' in gameInfoDataDict:
                price = gameInfoDataDict['price_overview']['final_formatted']

            SteamGameInfoDF.loc[len(SteamGameInfoDF)] =\
                {
                    'appid': appid,
                    'is_free': gameInfoDataDict['is_free'],
                    'recommendations': gameInfoDataDict['detailed_description'],
                    'release_date': gameInfoDataDict['release_date']['date'],
                    'release_status': gameInfoDataDict['release_date']['coming_soon'],
                    'score': score,
                    'price': price,
                    'age': gameInfoDataDict['required_age']
                }
            if 'categories' not in gameInfoDataDict:
                continue

            for cate in gameInfoDataDict['categories']:
                SteamGameCateDF.loc[len(SteamGameCateDF)] = \
                    {
                        'appid': appid,
                        'categori': cate['description']
                    }
            save_flag = False
        except Exception as e:
            print(f"ERROR: {appid}")
            if not save_flag:
                SteamGameCateDF.to_csv("SteamGameCateDF.csv", encoding="utf-8")
                SteamGameInfoDF.to_csv("SteamGameInfoDF.csv", encoding="utf-8")
                SteamTypeDF.to_csv("SteamTypeDF.csv", encoding="utf-8")
                save_flag = True
            with open('error_appid.txt', 'a') as error_file:
                error_file.write(f"{appid}, ")
                appid_list.append(appid)
            error_message = traceback.format_exc()
            with open('error_log.txt', 'a') as error_file:
                error_file.write(f"Error for appid {appid}: {str(e)}\n")
                error_file.write(f"Traceback: {error_message}\n")
            continue

    return SteamGameCateDF, SteamGameInfoDF, SteamTypeDF
df1, df2, df3 = getSteamGameInfo()
df1.to_csv("SteamGameCateDF_Final.csv", encoding="utf-8")
df2.to_csv("SteamGameInfoDF_Final.csv", encoding="utf-8")
df3.to_csv("SteamTypeDF.csv", encoding="utf-8")

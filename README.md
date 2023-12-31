# BigDataProject
스팀 리뷰 데이터를 읽고, (긍정/부정) 또는 사용자에게 맞는 게임 추천하기 

1. 데이터 수집 및 저장 (***Steam Web API***)
2. 데이터 정제
3. 시각화
4. 모델 구현
5. 모델 학습
6. **최종적으로 데이터를 바탕으로 API제작하기** (***시간고려하여 진행예정***)
    > 사용자가 보유중인 게임목록을 읽고 추천 게임을 반환   
    > 게임에 대해 긍정, 부정적인 리뷰 통계 반환

---
## Steam Web API
> API 수집기간 : 11.01 ~ 11.05

- 게임목록API
- 게임정보API
- 게임리뷰API
- 사용자정보API (**권한 관련 이슈**)   
**고려사항: API 요청시 초당 10개제한, 시간당 제한, 하루 요청 제한 등**

---
## ERD 설계
> ERD 설계기간 : 11.05 ~ 11.10
<img src='https://github.com/MMMMins/BigDataProject/assets/113413158/c99492ff-e85f-4df5-a637-5dee34f1dc15.png' width='500'>


## 데이터 수집 및 저장
> 수집기간 : 약 9일 정도 예상중   
> 클라우드 서버 이용하여, 24시간 수집   
> DB: Mysql 사용

---
## 데이터 수집
> 수집기한 : 11.09 ~ ing

```python
def game_list_api(URL, params=None):
    headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}
    try:
        response = requests.get(URL, headers=headers, params=params)
        return response.json()
    except Exception as e:
        print(e)
```

### 게임목록API (요청 URL: https://api.steampowered.com/ISteamApps/GetAppList/v2)   
``` python
# 코드
def getSteamGameID():
    """
    # table(steamGameID)
    """
    url = 'https://api.steampowered.com/ISteamApps/GetAppList/v2'
    value = game_list_api(url)
```
> value에 저장된 값   
> <img width="435" alt="스크린샷 2023-11-27 오후 3 11 32" src="https://github.com/MMMMins/BigDataProject/assets/113413158/75aca06d-fda6-456f-a805-d4b72c356c76">
``` python
    # None 제거
    steamGameId = pd.DataFrame(value['applist']['apps'])
    steamGameId = steamGameId[steamGameId['name'] != '']
    steamGameId = steamGameId.drop_duplicates(keep='first')
```
> 결측치 제거   
> <img width="435" alt="스크린샷 2023-11-27 오후 2 30 43" src="https://github.com/MMMMins/BigDataProject/assets/113413158/a8725205-fe5c-4290-b45e-2644b986c58c">
``` python
    # 중복 APPID 제거
    duplicate_index = steamGameId.index[steamReviewDf.index.duplicated()]
    df_no_duplicate_rows = steamGameId.drop_duplicates(keep='first')
    df_no_duplicate_rows
```
> 중복값 체크후 제거
> - 중복값 개수 
> > <img width="550" alt="스크린샷 2023-11-27 오후 1 49 25" src="https://github.com/MMMMins/BigDataProject/assets/113413158/ac41b6ad-e535-4ff8-8805-5669933012a8">
> - 제거 후 개수
> > <img width="550" alt="스크린샷 2023-11-27 오후 1 39 19" src="https://github.com/MMMMins/BigDataProject/assets/113413158/57b80509-74ce-497a-bbbc-036845f1aa7e">

``` python
    # 데이터베이스에 저장
    df_no_duplicate_rows.to_sql(name='steamGameID', con=engine, if_exists='append', index=False)
```

### 게임정보 API
``` python
def getSteamGameInfo():
    url = 'https://store.steampowered.com/api/appdetails'
    param = {
        'appids': '',
        'l':'korean'
    }
```

``` python
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
```
> **준비 단계**
> 1. 데이터 베이스에 저장된 APPID목록 전체 조회
> 2. 해당 API에서 얻을 수 있는 정보들을 담을 수 있는 데이터프레임 생성
>    1. SteamGameInfoDF : 게임에 대한 기본적인 내용
>    2. SteamGameCateDF : 게임에 대한 장르 정보 (게임과 장르는 1:n 관계로 별도의 데이터프레임으로 분리했다.)
>    3. SteamTypeDF : API호출로 얻은 APPID에 대한 Type정보 (Steam에 대한 타입은 game, dlc, music ... 이 있다.)
> 3. save_flag는 임시저장용도로 만들었으며, 본 프로그램이 실행중 에러가 날 경우 현재까지 정보를 저장한다.

### 게임상세정보 API
``` python
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
            with open('error_log.txt', 'a') as error_file:
                error_file.write(f"{appid}, ")
                appid_list.append(appid)
            continue
    return SteamGameCateDF, SteamGameInfoDF, SteamTypeDF
df1, df2, df3 = getSteamGameInfo()
df1.to_csv('SteamGameCateDF_final.csv', encoding="utf-8")
df2.to_csv('SteamGameInfoDF_final.csv', encoding="utf-8")
df3.to_csv('SteamTypeDF_final.csv', encoding="utf-8")
```

#### 1. SteamTypeDF.csv : 해당 AppID의 분류 [기준일 : 11.30]
```python
SteamTypeDF = pd.read_csv('SteamTypeDF.csv', encoding='utf-8')
SteamTypeDF
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/c1bbce03-4654-41c2-ad19-31b01395db68">

#### 인덱스 재설정
```python
SteamTypeDF.drop(columns=['Unnamed: 0'], inplace=True)
SteamTypeDF.tail(5)
```
<img width="600" alt="스크린샷 2023-12-01 오후 7 47 08" src="https://github.com/MMMMins/BigDataProject/assets/113413158/3779ec67-1c6c-4327-ad43-4f2c93be5bbf">

#### 타입별 퍼센트
```python
type_counts = SteamTypeDF['type'].value_counts()
labels = type_counts.index.tolist()
sizes = type_counts.values

total_size = sum(sizes)
small_indices = sizes / total_size < 1 / 100

resize_list = list()
reindex_list = list()
# 라벨 변경
for i in range(len(labels)):
    if small_indices[i]:
        reindex_list.append('etc')
        resize_list.append(sum(sizes[i:]))
        break
    else:
        reindex_list.append(labels[i])
        resize_list.append(sizes[i])


plt.pie(resize_list, labels=reindex_list, autopct='%1.1f%%', startangle=40, explode=[0, 0, 0, 0.2, 0.35, 0.45])
plt.axis('equal')
plt.show()
```
<img width="600" alt="도형" src="https://github.com/MMMMins/BigDataProject/assets/113413158/50c707a3-affe-42bd-96b6-e2b597c13fad">

#### 2. SteamGameInfoDF.csv : 해당 AppID의 분류 [기준일 : 11.30]
```python
SteamGameInfoDF = pd.read_csv('SteamGameInfoDF.csv', encoding='utf-8')
SteamGameInfoDF.drop(columns=['Unnamed: 0'], inplace=True)
SteamGameInfoDF
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/da1f7b7b-8f21-41c0-8867-ba64992ed517">

#### 3. Steam.csv : 해당 AppID의 분류 [기준일 : 11.30]
```python
SteamGameCateDF = pd.read_csv('SteamGameCateDF.csv', encoding='utf-8')
SteamGameCateDF.drop(columns=['Unnamed: 0'], inplace=True)
SteamGameCateDF
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/5d4962be-44da-4a86-a647-613d85eae11f">

#### 문제점
1.     
> <img width="600" alt="스크린샷 2023-12-01 오후 7 31 35" src="https://github.com/MMMMins/BigDataProject/assets/113413158/90545745-45e2-4bba-8d55-4fd481d56bdc"> 
>
>  ---   
>    
> 데이터 개수 15만개 + 분당 API 요청 제한으로 3일 이상 소요   
> - 에러 리스트   
> > <img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/80bd436c-d3a0-40e1-8644-55200ccd7944">   
> - 요청제한으로 취소된 API요청 못한 AppID목록   
> > <img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/9691efe8-5a01-4e45-8c6a-8c3a82121f1e">   

2. 기초 데이터를 기반으로 리뷰데이터를 수집해야하는데, 18만개 + a의 개수로 데이터 양이 방대하고 분당 API요청 제한으로 한계치가 있음
---

### 해결안
> 게임 3종만 추려서 리뷰데이터 분석 예정
> 게임 3종 (도타2, 엘든링, 카스2)

**리뷰데이터 수집API**
```python
def getGameReview(appid, filename):
    save_flag = True
    count = 0
    url_base = f'https://store.steampowered.com/appreviews/{appid}?json=1&l=korean&num_per_page=100&review_type=all&purchase_type=all&day_range=365&cursor='

    # first pass
    url = urllib.request.urlopen(
        f"https://store.steampowered.com/appreviews/{appid}?json=1&l=korean&num_per_page=100&review_type=all&purchase_type=all&day_range=365&cursor=*")
    data = json.loads(url.read().decode())
    next_cursor = data['cursor']
    df1 = json_normalize(data['reviews'])
    count += 100
    cursorList = []
    try:
        while True:
            url_temp = url_base + parse.quote(next_cursor)
            url = urllib.request.urlopen(url_temp)
            data = json.loads(url.read().decode())

            next_cursor = data['cursor']
            if next_cursor in cursorList:
                break
            cursorList.append(next_cursor)
            df2 = json_normalize(data['reviews'])
            df1 = pd.concat([df1, df2])
            count += 100
            print(f"{count}: {next_cursor}")
            df1.drop_duplicates(['recommendationid'],ignore_index=True, inplace=True)
            if not save_flag:
                save_flag = True
    except Exception as e:

        if save_flag:
            df1.to_csv(f"라벨링작업전/{filename}_er.csv", encoding='utf-8')
            save_flag = False
        with open('error_log.txt', 'a') as error_file:
            error_file.write(f"{count}: {next_cursor}\n")
    df1.to_csv(f"라벨링작업전/{filename}.csv", encoding='utf-8')
    return df1
```
```python
do = getGameReview(570, '도타')
el = getGameReview(1245620, '엘든링')
ca = getGameReview(730, '카스2')
```

#### 도타.csv DataFrame
```python
do.columns
do[['review','timestamp_created','voted_up', 'author.playtime_at_review']].head(5)
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/52561a5c-8ab3-48ff-949b-c8cb3bdc0703">

**라벨링 작업전**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/b8318bbb-50fc-413a-85eb-b8a110c00f1d">

**결측치 확인**
```python
print(do.isnull().sum())
```
>recommendationid                  0   
language                          0   
review                            0   
timestamp_created                 0   
timestamp_updated                 0   
voted_up                          0   
votes_up                          0   
votes_funny                       0   
weighted_vote_score               0   
comment_count                     0   
steam_purchase                    0   
received_for_free                 0   
written_during_early_access       0   
hidden_in_steam_china             0   
steam_china_location              0   
author.steamid                    0   
author.num_games_owned            0   
author.num_reviews                0   
author.playtime_forever           0   
author.playtime_last_two_weeks    0   
author.playtime_at_review         0   
author.last_played                0   
dtype: int64


**라벨링 작업후**   
```python
dol = pd.read_csv('라벨링작업후/도타리뷰.csv', encoding='utf-8')
dol[['review','timestamp_created','voted_up','label']].head(5)
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/916a693b-7477-40f8-876e-fcbb5518cb76">

**긍정/부정 비율**   
```python
sizes =dol['label'].value_counts().values
plt.pie(sizes, labels=['Positive','negative','-'], autopct='%1.1f%%', startangle=90, explode=[0,0,0.3])

labels = ['Positive','negative','-']
for i in range(len(labels)):
    height = sizes[i]
    plt.text(labels[i], height + 0.25, sizes[i], ha='center', va='bottom', size = 12)
plt.bar(height=sizes, x=labels)
```
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/8944b5f5-4326-4458-b2b7-7b08e0a754c8">
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/f0e91fb8-7bf4-4c04-839e-82155b02a705">

> -: 긍정/부정 아닌 이상한 리뷰들   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/964178ea-247b-4857-96e9-c65303454b0e">


#### 엘든링.csv DataFrame
```python
el.columns
el[['review','timestamp_created','voted_up', 'author.playtime_at_review']].head(5)
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/b9902949-2b7d-4530-9ffc-9cbeac39e46e">

**라벨링 작업전**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/0865c147-0e59-40c3-bc2a-d66faf4a89c5">

**결측치 확인**
```python
print(el.isnull().sum())
```
>recommendationid                  0   
language                          0   
review                            0   
timestamp_created                 0   
timestamp_updated                 0   
voted_up                          0   
votes_up                          0   
votes_funny                       0   
weighted_vote_score               0   
comment_count                     0   
steam_purchase                    0   
received_for_free                 0   
written_during_early_access       0   
hidden_in_steam_china             0   
steam_china_location              0   
author.steamid                    0   
author.num_games_owned            0   
author.num_reviews                0   
author.playtime_forever           0   
author.playtime_last_two_weeks    0   
author.playtime_at_review         0   
author.last_played                0   
dtype: int64   

**라벨링 작업후**   
```python
ell = pd.read_csv('라벨링작업후/엘등린리뷰.csv', encoding='utf-8')
ell[['review','timestamp_created','voted_up','label']].head(5)
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/3a5f5be1-0bc3-4c61-8f16-1c0bca7ae8b4">

**긍정/부정 비율**   
```python
sizes =ell['label'].value_counts().values
plt.pie(sizes, labels=['Positive','negative','-'], autopct='%1.1f%%', startangle=90, explode=[0,0,0.3])

labels = ['Positive','negative','-']
for i in range(len(labels)):
    height = sizes[i]
    plt.text(labels[i], height + 0.25, sizes[i], ha='center', va='bottom', size = 12)
plt.bar(height=sizes, x=labels)
```
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/f723e619-2278-4f77-9037-0834aeaddf22">
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/5d73916d-a9ac-47dc-8e30-670a840cfbfb">

> -: 긍정/부정 아닌 이상한 리뷰들   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/e214e726-fcef-4821-82d2-fc62fdea0687">


#### 카스2.csv DataFrame
```python
ca.columns
ca[['review','timestamp_created','voted_up', 'author.playtime_at_review']]
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/ca8660c0-28d4-4f89-b1b7-d7d2daeb8c6e">

**라벨링 작업전**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/4c4aab6e-2809-41d0-93f0-20511237f0ac">

**결측치 확인**
```python
print(ca.isnull().sum())
```
>recommendationid                  0   
language                          0   
review                            0   
timestamp_created                 0   
timestamp_updated                 0   
voted_up                          0   
votes_up                          0   
votes_funny                       0   
weighted_vote_score               0   
comment_count                     0   
steam_purchase                    0   
received_for_free                 0   
written_during_early_access       0   
hidden_in_steam_china             0   
steam_china_location              0   
author.steamid                    0   
author.num_games_owned            0   
author.num_reviews                0   
author.playtime_forever           0   
author.playtime_last_two_weeks    0   
author.playtime_at_review         0   
author.last_played                0   
dtype: int64   


**라벨링 작업후**
```python
cal = pd.read_csv('라벨링작업후/카스2리뷰.csv', encoding='utf-8')
cal[['review','timestamp_created','voted_up','label']]
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/f7b33920-fc07-440b-adb7-386dff97b90c">


**긍정/부정 비율**
```python
sizes =cal['label'].value_counts().values
plt.pie(sizes, labels=['Positive','negative','-'], autopct='%1.1f%%', startangle=90, explode=[0,0,0.3])

labels = ['Positive','negative','-']
for i in range(len(labels)):
    height = sizes[i]
    plt.text(labels[i], height + 0.25, sizes[i], ha='center', va='bottom', size = 12)
plt.bar(height=sizes, x=labels)
```
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/9a0273c5-14f8-4030-8a63-f3927c89ec14">
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/2a07ff1a-03b6-47b4-ad3a-27a72540bebc">

> -: 긍정/부정 아닌 이상한 리뷰들
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/5ae6645b-570f-46af-9947-6d2584a4aba1">

---
#### 결측치 라벨 제거
```python
dodrop = dol.drop(dol[dol['label'] == 2].index)
eldrop = ell.drop(ell[ell['label'] == 2].index)
cadrop =cal.drop(cal[cal['label'] == 2].index)
print(f'도타리뷰 데이터 \t | 삭제전 개수: {len(dol.index)} 삭제후 개수: {len(dodrop.index)}')
print(f'엘든링리뷰 데이터 \t | 삭제전 개수: {len(ell.index)} 삭제후 개수: {len(eldrop.index)}')
print(f'카스2리뷰 데이터 \t | 삭제전 개수: {len(cal.index)} 삭제후 개수: {len(cadrop.index)}')
```
>도타리뷰 데이터 	 | 삭제전 개수: 137 삭제후 개수: 132   
>엘든링리뷰 데이터 	 | 삭제전 개수: 555 삭제후 개수: 553   
>카스2리뷰 데이터 	 | 삭제전 개수: 438 삭제후 개수: 436   

#### 예상못한 결측치
> 한글 리뷰 분석으로 영어나 이상한 문자로 된 것은 삭제해서 라벨링을 했어야 했다.

```python
dodrop['review'] = dodrop['review'].apply(lambda x : re.sub(r'[^ ㄱ-ㅣ가-힣]+', "", x))
dodrop['review'] = dodrop['review'].apply(lambda x: None if len(x.strip())==0 else x )
dodrop[dodrop['review'].isnull()==True]
```
**도타 결측치 데이터**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/eb4d445b-c3a5-4f76-aed8-cfe077ba8103">



```python
dodrop.drop(columns='Column1', inplace=True)
dodrop.drop(index=dodrop[dodrop['review'].isnull()==True].index,inplace=True)
dodrop
```
**도타 제거후 데이터**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/36b2545f-a081-421a-a2bf-00bfb2c5872d">

---

```python
eldrop['review'] = eldrop['review'].apply(lambda x : re.sub(r'[^ ㄱ-ㅣ가-힣]+', "", x))
eldrop['review'] = eldrop['review'].apply(lambda x: None if len(x.strip())==0 else x )
eldrop[eldrop['review'].isnull()==True]
```
**엘든링 결측치 데이터**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/1f185913-54f6-4868-b7c3-9b09cbf167eb">



```python
eldrop.drop(columns='Column1', inplace=True)
eldrop.drop(index=eldrop[eldrop['review'].isnull()==True].index,inplace=True)
eldrop
```
**엘든링 제거후 데이터**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/8bd699d9-83c7-4f8e-8d0f-16d70aa9641e">

---

```python
cadrop['review'] = cadrop['review'].apply(lambda x : re.sub(r'[^ ㄱ-ㅣ가-힣]+', "", x))
cadrop['review'] = cadrop['review'].apply(lambda x: None if len(x.strip())==0 else x )
cadrop[cadrop['review'].isnull()==True]
```
**카스2 결측치 데이터**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/643c31c0-5c2f-471c-9cd6-acd8560a4f2b">



```python
cadrop.drop(columns='Column1', inplace=True)
cadrop.drop(index=cadrop[cadrop['review'].isnull()==True].index,inplace=True)
cadrop
```
**카스2 제거후 데이터**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/0d612d37-005d-47f1-9e4b-d3c7f52deb39">

---

#### 불용어 제거
*RANKS NL에 제공해주는 한국어 불용어 사전 활용*   
> https://www.ranks.nl/stopwords/korean   
```python
stopwords = pd.read_csv("https://raw.githubusercontent.com/yoonkt200/FastCampusDataset/master/korean_stopwords.txt").values.tolist()
stopwords
```
<img width="400" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/e5bc0940-4b2a-4b81-8bd8-42bd4cca1638">

#### 단어 빈도수 측정 [2가지 방법]

##### 카운터함수 사용
```python
from konlpy.tag import Okt
from collections import Counter

okt = Okt()
def frequency_text(df):
    corpus = "".join(df['review'].tolist())
    nouns = okt.nouns(corpus)
    counter = Counter(nouns)
    #available_counter = Counter({x: counter[x] for x in counter if len(x) > 1 or x =='핵'})
    available_counter = Counter({x: counter[x] for x in counter if x not in stopwords})
    print(available_counter.most_common(10))
    return counter, available_counter

dota_frequency = frequency_text(dodrop)
eldenring_frequency = frequency_text(eldrop)
cs2_frequency = frequency_text(cadrop)

```
**각 게임별 빈도 수**
> 도타   
> ![dota2_1_bar](https://github.com/MMMMins/BigDataProject/assets/113413158/3a699820-4edf-41a5-a7b4-155639e94315)  
> 엘든링    
> ![elden_1_bar](https://github.com/MMMMins/BigDataProject/assets/113413158/8df839a0-2429-4347-82c0-82895badc268)   
> 카스2
> ![cs2_1_bar](https://github.com/MMMMins/BigDataProject/assets/113413158/d978799f-7234-4d27-8a7f-758ae0085d18)

---

##### BoW벡터사용
```python
from konlpy.tag import Okt
from sklearn.feature_extraction.text import CountVectorizer

def frequency_text(corpus):
    okt = Okt()
    #corpus = "".join(df['review'].tolist())
    nouns = okt.nouns(corpus)
    #available_counter = Counter({x: counter[x] for x in counter if len(x) > 1 or x =='핵'})
    available_counter = {x: x for x in nouns if x not in stopwords}
    return available_counter

vect = CountVectorizer(tokenizer = lambda x: frequency_text(x))
dota_bow_vect = vect.fit_transform(dodrop['review'].tolist())
dota_word_list = vect.get_feature_names_out()
dota_count_list = dota_bow_vect.toarray().sum(axis=0)

vect = CountVectorizer(tokenizer = lambda x: frequency_text(x))
elden_bow_vect = vect.fit_transform(eldrop['review'].tolist())
elden_word_list = vect.get_feature_names_out()
elden_count_list = elden_bow_vect.toarray().sum(axis=0)

vect = CountVectorizer(tokenizer = lambda x: frequency_text(x))
cs2_bow_vect = vect.fit_transform(cadrop['review'].tolist())
cs2_word_list = vect.get_feature_names_out()
cs2_count_list = cs2_bow_vect.toarray().sum(axis=0)

def sorted_word_count(word_list, count_list):
    word_count_dict = dict(zip(word_list, count_list))
    word_count_dict = sorted(word_count_dict.items(), key=lambda x:x[1], reverse=True)
    return word_count_dict

dota_word_count = sorted_word_count(dota_word_list, dota_count_list)
elden_word_count = sorted_word_count(elden_word_list, elden_count_list)
cs2_word_count = sorted_word_count(cs2_word_list, cs2_count_list)
```

**각 게임별 빈도 수**
> 도타   
> ![dota2_bar](https://github.com/MMMMins/BigDataProject/assets/113413158/53491247-6cdd-4a85-bade-f5bbdf7e61fe)   
> 엘든링    
> ![elden_bar](https://github.com/MMMMins/BigDataProject/assets/113413158/a7b7200d-e75b-49d5-973a-789a3abbcbd8)   
> 카스2   
> ![cs2_bar](https://github.com/MMMMins/BigDataProject/assets/113413158/5bc5fff1-33c4-46f8-9027-2dfc1b621785)   

#### 불용어 추가
> 상위 15개 확인 결과 필요없는 단어 일부 발견   
> 게임, 정도, 진짜, 도타, 카스, 처음, 글옵 불용어 추가   
```python
stopwords = pd.read_csv("https://raw.githubusercontent.com/yoonkt200/FastCampusDataset/master/korean_stopwords.txt").values.tolist()
stopwords.extend(['게임','정도','진짜','도타','카스','처음','글옵'])
stopwords[:]
```
> 이후 코드 재실행

#### BoW벡터를 이용한 빈도수 측정값을 활용한 Word Cloud
> 도타   
> <img width="400" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/20759512-198f-47ee-ad65-855a3113f331">   
> 엘든링   
> <img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/105a54ae-ad41-4b5c-9f35-f16ae58b0126">   
> 카스2      
> <img width="800" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/d1a4b1b3-66be-417d-8864-a7070264af7b">   

---

#### TF-IDF 적용
>TF-IDF란?   
>정보 검색과 텍스트 마이닝에서 이용하는 가중치로, 여러 문서로 이루어진 문서군이 있을 때 어떤 단어가 특정 문서 내에서 얼마나 중요한 것인지를 나타내는 통계적 수치

```python
from sklearn.feature_extraction.text import TfidfTransformer

dota_tfidf_vectorizer = TfidfTransformer()
dota_tf_idf_vect = dota_tfidf_vectorizer.fit_transform(dota_bow_vect)

el_tfidf_vectorizer = TfidfTransformer()
el_tf_idf_vect = el_tfidf_vectorizer.fit_transform(elden_bow_vect)

cs_tfidf_vectorizer = TfidfTransformer()
cs_tf_idf_vect = cs_tfidf_vectorizer.fit_transform(cs2_bow_vect)
```

**변환후 shape**   
```python
print(f"dota: {dota_tf_idf_vect.shape}")
print(f"elden: {el_tf_idf_vect.shape}")
print(f"cs2: {cs_tf_idf_vect.shape}")
```
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/461fc3fd-3f57-4e70-88fa-68cfbf40e6ff">   

**첫번째 리뷰에서 모든 단어 중요도**   
```python
print(f"dota: \n{dota_tf_idf_vect[0]}")
print(f"elden: \n{el_tf_idf_vect[0]}")
print(f"cs2: \n{cs_tf_idf_vect[0]}")
```
<img width="450" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/807dfb8b-2cad-4fc9-8e37-1183045325dc">   

** {단어: 인덱스} -> {인덱스: 단어} 변경
```python
dota_invert_index_vectorizer = {v: k for k, v in vect_dota.vocabulary_.items()}
print("dota: "+str(dota_invert_index_vectorizer)[:100]+'...')

el_invert_index_vectorizer = {v: k for k, v in vect_el.vocabulary_.items()}
print("elden: "+str(el_invert_index_vectorizer)[:100]+'...')

cs2_invert_index_vectorizer = {v: k for k, v in vect_cs2.vocabulary_.items()}
print("cs2: "+str(cs2_invert_index_vectorizer)[:100]+'...')
```
>기존 매핑   
><img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/a7745901-0935-46b5-965b-92a8013fef3d">   
>변경 후   
><img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/444c0382-f138-4a8b-8851-9f300f7625e7">   


#### 리뷰 데이터 예측 모델 작성
 
**test/train 케이스 분류**   
```python
from sklearn.model_selection import train_test_split

def testandtrain(x, y):
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.3, random_state=1)
    return {"x_train":x_train, "x_test":x_test, "y_train":y_train, "y_test":y_test}

dota_case = testandtrain(dota_tf_idf_vect, dodrop['label'])
elden_case = testandtrain(el_tf_idf_vect, eldrop['label'])
cs2_case = testandtrain(cs_tf_idf_vect, cadrop['label'])
```
   
*x,y train shape*   
>dota_case: (87, 1117), (87,)   
>elden_case: (369, 2835), (369,)   
>cs2_case: (238, 1615), (238,)

**모델 학습**
```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def lrstart(case):
    lr = LogisticRegression(random_state = 0)
    lr.fit(case["x_train"], case["y_train"])

    y_pred = lr.predict(case["x_test"])
    print('accuracy: %.2f' % accuracy_score(case["y_test"], y_pred))
    print('precision: %.2f' % precision_score(case["y_test"], y_pred))
    print('recall: %.2f' % recall_score(case["y_test"], y_pred))
    print('F1: %.2f' % f1_score(case["y_test"], y_pred))
    return y_pred
```

##### 정확도
dota:   
accuracy: 0.82   
precision: 0.88   
recall: 0.74   
F1: 0.80   

---
elden:    
accuracy: 0.76   
precision: 0.76   
recall: 0.97   
F1: 0.85   

---
cs2:    
accuracy: 0.70   
precision: 0.77   
recall: 0.40   
F1: 0.52   

---

**예측결과 확인**
```python
from sklearn.metrics import confusion_matrix
import seaborn as sns

def pltshow(name, case, y_pred):
    confu = confusion_matrix(y_true = case["y_test"], y_pred = y_pred)
    
    plt.figure(figsize=(4, 3))
    sns.heatmap(confu, annot=True, annot_kws={'size':15}, cmap='OrRd', fmt='.10g')
    plt.title(f'{name}: Matrix')
    plt.show()
pltshow("도타", dota_case, dota_pred)
pltshow("엘든링", elden_case, elden_pred)
pltshow("카스2", cs2_case, cs2_pred)
```
![도타Matrix](https://github.com/MMMMins/BigDataProject/assets/113413158/89816413-241e-46ee-8a7c-dab26aeb607a)   
![엘든링Matrix](https://github.com/MMMMins/BigDataProject/assets/113413158/53929cf0-f2e8-4efc-8df8-367e665b88a0)   
![카스2Matrix](https://github.com/MMMMins/BigDataProject/assets/113413158/3d3c2410-bf57-4b7e-9de0-84b3efde651b)   

#### 모델작업에서 문제점
> 아무런 생각없이 각 게임마다 모델을 만들어서 모델을 활용할 수 가 없었다.
> 이를 위해 각 게임리뷰 데이터를 통합하여서 모델을 만드는 과정이 필요했다.


```python
col = ['review', 'label']
dodrop_df = dodrop[col]
cadrop_df = cadrop[col]
eldrop_df = eldrop[col]
concat_df = pd.concat([dodrop_df, cadrop_df, eldrop_df], axis=0)
```
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/f62a59c8-e5a9-4dab-a240-627136cd0cab">

```python
def no_label_data_result():
    concat_df['review'] = concat_df['review'].apply(lambda x : re.sub(r'[^ ㄱ-ㅣ가-힣]+', " ", x))
    concat_df['review'] = concat_df['review'].apply(lambda x: None if len(str(x).strip())<=1 else x )
    #concat_df.drop(columns='Column1', inplace=True)
    concat_df.drop(index=concat_df[concat_df['review'].isnull()==True].index,inplace=True)

    vect = CountVectorizer(tokenizer = lambda x: frequency_text_Bow(x))
    bow_vect = vect.fit_transform(concat_df['review'].tolist())
    word_list = vect.get_feature_names_out()
    count_list = bow_vect.toarray().sum(axis=0)

    word_count = sorted_word_count(word_list, count_list)
    word_cloud("no_label_data", word_count, "elden.jpeg")

    word_dict = dict(word_count)

    tfidf_vectorizer = TfidfTransformer()
    tf_idf_vect = tfidf_vectorizer.fit_transform(bow_vect)
    print(f"no_label_data: {tf_idf_vect.shape}")
    print(f"no_label_data: \n{tf_idf_vect[0]}")

    invert_index_vectorizer = {v: k for k, v in vect.vocabulary_.items()}
    print("dota: "+str(invert_index_vectorizer)[:100]+'...')
    case = testandtrain(tf_idf_vect, concat_df['label'])
    print(f"case: {case['x_train'].shape}, {case['y_train'].shape}")
    y_pred, lr = lrstart(case)
    pltshow("집합", case, y_pred)
    return case, tf_idf_vect
```
**결과**   
<img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/84f8f2db-68fc-4691-a44b-0d7672579f77">   

**클래스 재분류**   
```python
concat_df['label'].value_counts()
```
<img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/0226083a-ffca-4919-bb3a-713cf7acbce9">


1. 첫번째 방법
```python
positive_random_idx = concat_df[concat_df['label']==1.0].sample(407, random_state=12).index.tolist()
negative_random_idx = concat_df[concat_df['label']==0.0].sample(407, random_state=12).index.tolist()
random_idx = positive_random_idx + negative_random_idx
x = tf_idf_vect[random_idx]
y = concat_df['label'][random_idx]

print(x.shape, y.shape)
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=1)
lr2 = LogisticRegression(random_state = 0)
lr2.fit(x_train, y_train)
y_pred = lr2.predict(x_test)
```
> (814, 4085) (1708,)

2. 두번째 방법
```python
from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
trainX_over, trainY_over = smote.fit_resample(case["x_train"],case["y_train"])
lr2 = LogisticRegression(random_state = 0)
lr2.fit(trainX_over, trainY_over)
y_pred = lr2.predict(case['x_test'])
```
> <img width="300" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/a4a90e83-1044-413d-bcc7-89f1e6422f7d">


#### 모델 활용하여 데이터 예측

```python
#test
review_input = input()
review = vect.transform([review_input])
tf_idf_vect = tfidf_vectorizer.fit_transform(review)
y_pred = lr2.predict(tf_idf_vect)
print(f'사용자가 입력한 리뷰 "{review_input}"의 예측결과: {y_pred[0]}')
```

1. [예시1]
   - <img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/52f081b1-3caf-4e03-b80b-b9cf6429df72">
2. [예시2]
   - <img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/cd4bece0-5e7d-4bc3-9ac4-a25f5a888060">
3. [예시3]
   - <img width="600" alt="image" src="https://github.com/MMMMins/BigDataProject/assets/113413158/ef387d45-bc07-4419-913c-bfb2b6742ee5">

## 결론
원래 원하던 방향이 아니여서 많이 아쉽다.   
원래의 방향은 전게임 리뷰를 크롤링해서    
1. 사용자가 남긴 리뷰의 긍정/부정을 판별하여 기록하고
2. 게임에 대한 전체적인 리뷰의 긍정/부정의 수치를 보여준다.
3. 특정 사용자의 게임에 대한 선호 유형들을 보여준다
   - ex) 특정 사용자의 게임 카테고리 비율, 남긴 리뷰의 긍정/부정 수치 등

이런 프로세스를 가지고 시작하였는데, API 요청 제한을 예상못한 실수 및 데이터 양의 방대함을 제대로 확인못한 것이 큰거같다.   
급하게 리뷰 데이터를 분석하였는데, 리뷰데이터를 읽어보는데 아무래도 플랫폼이 해외 기업, 해외 게임사로 인해서 영어랑 섞인 데이터가 많았고 다국적의 데이터들이 너무많았다.    
또한 해당게임에서만 사용하는 특정 단어, 캐릭터 등에 대한 불용어 정의가 확실해야할 것 같았다   
그리고 특정 장르에서는 특정 리뷰가 긍정이지만, 다른 장르로 해석할 경우 부정으로 볼 수 있을 것 같아서 리뷰 분석시 장르랑 섞어서 문자열에 대한 라벨링을 할 수 있는 방향이 있으면 좋을것 같았다.


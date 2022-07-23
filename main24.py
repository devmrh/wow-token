from datetime import datetime
import os
from db import Mongo
import requests
import time

# send request to api every 20 min

save_count = 0
CLIENT_ID = "a55632c9c60441de99f95f7bb05ee985"
CLIENT_SECRET = "4g9apilzTLWwBhlv5zu1UOAtuzoLfCMc"


database = Mongo(db_name="digitogame")
golds_collection = database.set_collection("g.price")
token_collection = database.set_collection("token")


def save_to_mongo(data):

    global save_count
    save_count += 1
    golds_collection.insert_one(data)


def get_token_from_db():
    token = token_collection.find_one()
    if token is None:
        return generate_access_token()
    else:
        # check expire_in
        if token["expire_in"] < int(time.time()):
            return generate_access_token()
        else:
            return token["access_token"]


# generate access token
def generate_access_token():
    url = f"https://us.battle.net/oauth/token?grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    response = requests.post(url)
    if response.status_code == 200:
        expire_in = response.json()["expires_in"]
        access_token = response.json()["access_token"]

        # convert expire_in to unix timestamp
        expire_in = int(expire_in)
        expire_in = expire_in + int(time.time())

        # save to db
        # update or create record
        token_collection.delete_many({})
        token_collection.insert_one({"access_token": access_token, "expire_in": expire_in})

    else:
        return None


# use eu / us for region
def get_coin_history(region="us"):

    token = get_token_from_db()
    url = f"https://{region}.api.blizzard.com/data/wow/token/index?namespace=dynamic-{region}&locale=en_US&access_token={token}"
    response = requests.get(url)
    return response.json()


region_list = ["us", "eu"]

for region in region_list:
    data = get_coin_history(region)

    price = str(data["price"])
    price = price[:6]

    timestamp = int(time.time()) * 1000

    insert_data = {
        "region": region,
        "history24": [{"price": price, "timestamp": timestamp}]

    }

    # find if there is a record in db
    # if yes, update it
    # if no, create a new record

    golds = golds_collection.find_one({"region": region})
    if golds is None:
        golds_collection.insert_one(insert_data)
    else:
        golds_collection.update_one({"region": region}, {
                                    "$push": {"history24": {"price": price, "timestamp": timestamp}}})


    time.sleep(5)

cwd = os.path.dirname(os.path.realpath(__file__))
with open(f'{cwd}/result.txt', 'a') as fd:
    fd.write(
        f'\n (24 hours log) on: {datetime.today().strftime("%Y-%m-%d-%H:%M:%S")} 2 record has been updated')


database.close()
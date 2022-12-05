from flask import Flask, render_template, request, redirect, url_for, flash
import aiohttp

app = Flask(__name__)
# Use library to retrieve .env
import os
from dotenv import load_dotenv
load_dotenv()

import fillout

async def getxcsrf():
    async with aiohttp.ClientSession() as session:
        async with session.post("https://auth.roblox.com/",cookies={".ROBLOSECURITY":os.getenv("ROBLOSECURITY")}) as resp:
            await session.close()
    return resp.headers['x-csrf-token']


@app.route('/robloxRank',methods=['POST']) # The Marketeer webhook sends POST requests only. You can name this whatever you want if you modify this code.
async def robloxRank():
    # Get heaaders
    headers = request.headers
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://marketeer.dev/validateCode?code={headers['Authorization']}") as r:
            # If code is not 200, return 401
            if r.status != 200:
                return "Unauthorized", 401
            # Get the json
            json = await r.json()
            # CLose the session
            await session.close()
    if os.getenv("MAX_PREV_REQUESTS") != "None":
        if json['timesUsed'] > os.getenv("MAX_PREV_REQUESTS"):
            return "Unauthorized", 401
    role = await fillout.getRole(json['productId'])
    if role is None:
        return
    userId=int(json['webhookField'])
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://users.roblox.com/v1/users/{userId}") as r:
            if r.status != 200:
                return "User doesn't exist", 401
            robloxJson = await r.json()
            await session.close()
    groupId = os.getenv("GROUP_ID")
    # Send a request to Roblox and get every role in the group
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://groups.roblox.com/v1/groups/{groupId}/roles") as r:
            if r.status != 200:
                return "Group doesn't exist", 401
            robloxGroupJson = await r.json()
            await session.close()
    # Check if role name exists
    for i in robloxGroupJson['roles']:
        if i['name'] == role:
            roleId = i['id']
            rolePermissions = i['rank']
            break
    else:
        return "Role doesn't exist", 401
    # Check if users current role is higher than the role they're trying to get
    for i in robloxGroupJson['roles']:
        if i['group']['id'] == int(groupId):
            if i['rank'] > rolePermissions:
                return
    xcsrf = await getxcsrf()
    # Send a request to Roblox to set the users role
    async with aiohttp.ClientSession() as session:
        async with session.patch(f"https://groups.roblox.com/v1/groups/{groupId}/users/{userId}",headers={"x-csrf-token":xcsrf},cookies={".ROBLOSECURITY":os.getenv("ROBLOSECURITY")},json={"roleId":roleId}) as r:
            if r.status != 200:
                return "Failed to set role", 401
            await session.close()
    return "Success", 200


# Run app noting that we're using the async version of Flask
if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0", use_reloader=False, threaded=True)
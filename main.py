# pylint: disable=missing-module-docstring,missing-function-docstring,invalid-name,too-many-nested-blocks
from threading import Thread
from os import environ as env
from time import sleep
from traceback import format_exc
from slack_bolt import App
from dotenv import load_dotenv
from fpsql import sql

load_dotenv()

owner_id = env["OWNER_ID"]
app = App(token=env["SLACK_BOT_TOKEN"], signing_secret=env["SLACK_SIGNING_SECRET"])
client = app.client


@app.command("/watch-channel")
def handle_watch_channel(ack, body, respond):
    ack()
    user_id = body["user_id"]
    text = body["text"]
    channel_id = text.strip("<#@> ").split("|")[0]
    # print("/watch-channel")
    # print(f"CMD BODY: {body}")
    # print(f"Relevant data: {channel_id}")
    if user_id == owner_id:
        bot_db = sql("bot-banner.db")
        channels = bot_db["channels"]
        channels.append(channel_id)
        channels = list(set(channels))
        bot_db["channels"] = channels
        respond(
            f"Started watching <#{channel_id}> ({channel_id})",
            response_type="ephemeral",
        )
        bot_db.close()
    else:
        respond("You are not the owner", response_type="ephemeral")


@app.command("/unwatch-channel")
def handle_unwatch_channel(ack, body, respond):
    ack()
    user_id = body["user_id"]
    text = body["text"]
    channel_id = text.strip("<#@> ").split("|")[0]
    # print("/unwatch-channel")
    # print(f"CMD BODY: {body}")
    # print(f"Relevant data: {channel_id}")
    if user_id == owner_id:
        bot_db = sql("bot-banner.db")
        channels = bot_db["channels"]
        if channels.count(channel_id):
            channels.remove(channel_id)
            bot_db["channels"] = channels
            respond(
                f"Stopped watching <#{channel_id}> ({channel_id})",
                response_type="ephemeral",
            )
        else:
            respond(
                f"<#{channel_id}> ({channel_id}) was not watched",
                response_type="ephemeral",
            )
        bot_db.close()
    else:
        respond("You are not the owner", response_type="ephemeral")


@app.command("/list-watched-channels")
def handle_list_watched_channels(ack, body, respond):
    ack()
    user_id = body["user_id"]
    if user_id == owner_id:
        bot_db = sql("bot-banner.db")
        channels = bot_db["channels"]
        bot_db.close()
        channelString = ""
        for channel_id in channels:
            channelString = f"{channelString}\n - <#{channel_id}> ({channel_id})"
        if channelString == "":
            channelString = "No watched channels"
        respond(
            f"Watched channels: {channelString}",
            response_type="ephemeral",
        )
    else:
        respond("You are not the owner", response_type="ephemeral")


@app.command("/ban-bot")
def handle_ban_bot(ack, body, respond):
    ack()
    user_id = body["user_id"]
    text = body["text"]
    bot_id = text.strip("<#@> ").split("|")[0]
    # print("/ban-bot")
    # print(f"CMD BODY: {body}")
    # print(f"Relevant data: {bot_id}")
    if user_id == owner_id:
        bot_db = sql("bot-banner.db")
        bots = bot_db["bots"]
        bots.append(bot_id)
        bots = list(set(bots))
        bot_db["bots"] = bots
        respond(f"Banned <@{bot_id}> ({bot_id})", response_type="ephemeral")
        bot_db.close()
    else:
        respond("You are not the owner", response_type="ephemeral")


@app.command("/unban-bot")
def handle_unban_bot(ack, body, respond):
    ack()
    user_id = body["user_id"]
    text = body["text"]
    bot_id = text.strip("<#@> ").split("|")[0]
    # print("/unban-bot")
    # print(f"CMD BODY: {body}")
    # print(f"Relevant data: {bot_id}")
    if user_id == owner_id:
        bot_db = sql("bot-banner.db")
        bots = bot_db["bots"]
        if bots.count(bot_id):
            bots.remove(bot_id)
            bot_db["bots"] = bots
            respond(f"Unbanned <@{bot_id}> ({bot_id})", response_type="ephemeral")
        else:
            respond(f"<@{bot_id}> ({bot_id}) was not banned", response_type="ephemeral")
        bot_db.close()
    else:
        respond("You are not the owner", response_type="ephemeral")


@app.command("/list-banned-bots")
def handle_list_banned_bots(ack, body, respond):
    ack()
    user_id = body["user_id"]
    if user_id == owner_id:
        bot_db = sql("bot-banner.db")
        bots = bot_db["bots"]
        bot_db.close()
        botString = ""
        for bot_id in bots:
            botString = f"{botString}\n - <@{bot_id}> ({bot_id})"
        if botString == "":
            botString = "No banned bots"
        respond(
            f"Banned bots: {botString}",
            response_type="ephemeral",
        )
    else:
        respond("You are not the owner", response_type="ephemeral")

@app.command("/list-channel-members")
def handle_list_channel_members(ack, body, respond):
    ack()
    user_id = body["user_id"]
    if user_id == owner_id:
        channel = body["channel_id"]
        members = client.conversations_members(channel=channel).get("members")
        memberString = ""
        for member_id in members:
            memberString = f"{memberString}\n - <@{member_id}> ({member_id})"
        if memberString == "":
            memberString = "No channel members... what the fuck?"
        respond(
            f"Channel Members: {memberString}",
            response_type="ephemeral",
        )
    else:
        respond("You are not the owner", response_type="ephemeral")


def check_channel_members():
    thread_db = sql("bot-banner.db")
    while 1:
        # pylint: disable=bare-except
        try:
            kickCount = 0
            channels = thread_db["channels"]
            if not isinstance(channels, list):
                print("WARN: channels isn't a list, now it is")
                channels = []
                thread_db["channels"] = []
            bots = thread_db["bots"]
            if not isinstance(bots, list):
                print("WARN: bots isn't a list, now it is")
                bots = []
                thread_db["bots"] = []
            for channel in channels:
                members = client.conversations_members(channel=channel).get("members")
                if members:
                    for member in members:
                        if member in bots:
                            try:
                                client.conversations_kick(channel=channel, user=member)
                                kickCount += 1
                            except:
                                print("Caught error when trying to kick a bot:")
                                print(format_exc())
            if kickCount:
                print(f"Kicked {kickCount} total bots from all watched channels")
        except:
            print("Caught error when trying to ban bots:")
            print(format_exc())
        sleep(60)


Thread(target=check_channel_members, daemon=True).start()
app.start(port=int(env["PORT"]))

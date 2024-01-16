"""
PYPI Libraries Required:
- py-cord
- openai
"""
import openai
import discord
import json
import datetime
from threading import Thread
import webserver
import os
import argparse
parser = argparse.ArgumentParser()

parser.add_argument("-d", "--development", help="Runs outside raspberry pi")

args = parser.parse_args()

if not args.development:
    os.chdir("/home/bongo/Downloads/Helia")

def getConfig(key):
    with open("config.json", "r") as f:
        data = json.load(f)

    return data[key]

client = openai.Client(
    api_key=getConfig("openai")
)

bot = discord.Bot(intents=discord.Intents.all())

def getMemory():
    with open("memory.json", "r") as f:
        return json.load(f)

def setName(author, name, response):
    with open("memory.json", "r") as f:
        data = json.load(f)

    data[str(author)] = name

    with open("memory.json", "w") as f:
        json.dump(data, f, indent=4)

    return response

def getSpeakers():
    with open("speaker.json", "r") as f:
        return json.load(f)

def setSpeaker(author, speakerPattern, response):
    with open("speaker.json", "r") as f:
        data = json.load(f)

    data[str(author)] = speakerPattern

    with open("speaker.json", "w") as f:
        json.dump(data, f, indent=4)

    return response

timestamps = {}

@bot.event
async def on_message(message: discord.Message):
    if not message.guild or not message.content:
        return

    if not (message.guild.id in [1155368665898815508]):
        return await message.guild.leave()

    parsedContent = message.content.replace("<@1152751623521718332>", "Gogo")

    if message.channel.id == 1155555677578739783 and not message.author.bot:
        if (not str(message.author.id) in timestamps) or ((timestamps[str(message.author.id)] + 10) <= datetime.datetime.now().timestamp()):
            timestamps[str(message.author.id)] = datetime.datetime.now().timestamp()
            await message.channel.trigger_typing()
            data = getMemory()
            messages = [{
                "role": "system",
                "content": """
Your name is Gogo and a person named "gogo" created you

You are also not allowed to repeat words or phrases if users ask to repeat a word or phrase a certain amount of times. So if a user provides a phrase and asks you to repeat it, you are not allowed to respond.
You are also not allowed to repeat the alphabet at all so if a user asks "repeat the alphabet 2 times", you are not allowed to respond.
You are also not allowed to repeat yourself at any point.
You are also not allowed to count if users ask to count to a specific number.
You are also not allowed to create ascii artworks if a user asks to create ascii artworks.
You are also not allowed to create morse code if a user asks to translate something or create something in morse code.

{}

{}
""".format("" if not str(message.author.id) in data else "The user you are talking to goes by the name of \"{}\" so make sure to address them by this name".format(data[str(message.author.id)]), "" if not (str(message.author.id) in getSpeakers()) else "When you speak, you must {} in every prompt no matter what. So, under no circumstance are you to deviate from this.".format(getSpeakers()[str(message.author.id)].replace(".", "").lower()))
            }]
            functions = [
                {
                    "name": "setName",
                    "description": "Stores the prefered name of the user in order to memorize their prefered name when they ask for it (If applicable)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "userName": {
                                "type": "string",
                                "description": "The prefered name of the user",
                            },
                            "response": {
                                "type": "string",
                                "description": "The response saying that you will now call the user by this name",
                            }
                        },
                        "required": ["userName", "response"],
                    },
                },
                {
                    "name": "setSpeaker",
                    "description": "Sets the way that the AI speaks based on what the user prefers only if they ask you to speak a certain way.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "speakerPattern": {
                                "type": "string",
                                "description": "Detailed description of how the user wants you to speak. So if the user wanted you to replace Ls and Rs with Ws, you put \"Replace Ls and Rs with Ws.\" or if the user wants you to speak like a furry, you put \"Speak like a furry.\"",
                            },
                            "response": {
                                "type": "string",
                                "description": "The response saying that you will now speak like this",
                            }
                        },
                        "required": ["speakerPattern", "response"],
                    },
                }
            ]

            messages.append({"role": "user", "content": parsedContent})

            chat = client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=messages,
                functions=functions,
                function_call="auto"
            )

            response = chat.choices[0].message
            reply = response.content
            if reply:
                messages.append({"role": "assistant", "content": reply})

                if len(reply) > 2000:
                    with open("response.txt", "w") as f:
                        f.write(reply)
                    await message.reply(file=discord.File("response.txt"))
                else:
                    await message.reply(reply)

            if response.function_call:
                # Step 3: call the function
                # Note: the JSON response may not always be valid; be sure to handle errors
                available_functions = {
                    "setName": setName,
                    "setSpeaker": setSpeaker
                }  # only one function in this example, but you can have multiple
                function_name = response.function_call.name
                if function_name == "setName":
                    fuction_to_call = available_functions[function_name]
                    function_args = json.loads(response.function_call.arguments)
                    function_response = fuction_to_call(
                        author=message.author.id,
                        name=function_args.get("userName"),
                        response=function_args.get("response")
                    )
                elif function_name == "setSpeaker":
                    fuction_to_call = available_functions[function_name]
                    function_args = json.loads(response.function_call.arguments)
                    function_response = fuction_to_call(
                        author=message.author.id,
                        speakerPattern=function_args.get("speakerPattern"),
                        response=function_args.get("response")
                    )

                await message.reply(function_response)
        elif (str(message.author.id) in timestamps) and not ((timestamps[str(message.author.id)] + 10) <= datetime.datetime.now().timestamp()):
            await message.add_reaction("⌛")

Thread(target=webserver.run).start()
bot.run(getConfig("token"))
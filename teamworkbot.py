import discord
from discord.ext import commands
import requests
import re
import datetime

description = '''Searches through the teamwork question database to give you an answer.'''
bot = commands.Bot(command_prefix='.', description=description)
bot.remove_command('help')  # Will be overriding the default help function

client = discord.Client

qa_url = "http://pastebin.com/raw/7ASXKFzQ"
ss_url = "https://ssherder.com/data-api/characters/"
qa_f = None  # File object of QA text dump
ss_f = None  # File object of SSHerder API
qa_text = ""
ss_dict = {}
ss_image_dict = {}

quote = """```
{}
```"""

err_msg_1 = quote.format(">>> Too many answers. Please try another keyword.")
err_msg_2 = quote.format(">>> Nothing found. Please try another keyword.")
help_msg = """{}
For names/keywords with multiple words, enclose them with double quotes ("").
```diff
*** Examples ***
.tw elchitusa tree
.tw elchi tree
.tw "na yang ho" center
.tw lev "nadir forest" 
```""".format(quote.format('.tw [name] [keyword]'))


def do_update():
    global qa_f, qa_text, ss_f, ss_dict, ss_image_dict

    # Reinitialize before updating
    qa_f = None
    ss_f = None
    qa_text = ""
    ss_dict = {}
    ss_image_dict = {}

    ts = datetime.datetime.utcnow().strftime('%d %B %Y, %I:%M%p')
    print("*** Update called on {} (UTC+0) ***".format(ts))
    print("Reading from pastebin and SSHerder...")

    qa_f = requests.get(url=qa_url)
    qa_text = qa_f.content.decode('utf-8')

    ss_f = requests.get(url=ss_url)
    ss_dict = ss_f.json()

    for d in ss_dict:
        ss_image_dict[d['name']] = {'image_id': d['image_id'], 'element': d['element']}

    print("...done.")
    print('------------')


@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user.name))
    print('Bot user ID: {}'.format(bot.user.id))
    print('------------')
    await bot.change_presence(game=discord.Game(name='.help'))
    do_update()


@bot.command()
async def update():
    await bot.say("Reading from pastebin and SSHerder...")
    do_update()
    await bot.say("...done.")


@bot.command()
async def help():
    image_url = 'https://ssherder.com/static/img/characters/icons/60x60/15320.png'  # Cooker Green icon
    em = discord.Embed(title='TeamworkBot Help', description=help_msg, color=discord.Color.magenta())
    em.set_thumbnail(url=image_url)

    await bot.say(embed=em)


@bot.command()
async def tw(name: str, keyword: str):
    """Returns answer to teamwork question."""
    stub = '\\b(?:{}|{})'
    player = stub.format(name.title(), name.lower())
    query = stub.format(keyword.title(), keyword.lower())

    regex = '\[(.*{}.*)\](.*{}.*)\n\t(.*)'.format(player, query)
    tuple_res = re.findall(regex, qa_text)

    # We should only get one answer - if there is more than one, the
    # search term was too ambiguous. Tell user to try again.
    if len(tuple_res) > 1:
        await bot.say(err_msg_1)
    elif len(tuple_res) == 0:
        await bot.say(err_msg_2)
    else:
        found_name = tuple_res[0][0]
        found_qn = tuple_res[0][1]
        found_ans = tuple_res[0][2]

        line = 130 * ' '
        msg = "Q: {}\n~~{}~~\nA: {}".format(found_qn, line, found_ans)

        element = None
        if found_name in ss_image_dict:
            image_id = ss_image_dict[found_name]['image_id']
            element = ss_image_dict[found_name]['element']
            image_url = 'https://ssherder.com/static/img/characters/icons/60x60/{}.png'.format(image_id)
        else:
            image_url = 'http://i.imgur.com/Sq0aynm.png'  # Points to generic unknown player icon

        if element == 'Ardor':
            color = discord.Color.red()
        elif element == 'Whirlwind':
            color = discord.Color.green()
        elif element == 'Thunder':
            color = discord.Color.blue()
        elif element == 'Dark':
            color = discord.Color.purple()
        elif element == 'Light':
            color = discord.Color.gold()
        else:
            color = discord.Color.dark_grey()

        em = discord.Embed(title='{}'.format(found_name), description=msg, color=color)
        em.set_thumbnail(url=image_url)
        await bot.say(embed=em)


bot.run('token')

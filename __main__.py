with open("token.txt", 'r') as file:
    token = file.read()
token = token.replace('\n', '')

import discord
import discord.app_commands as ac
import gas

intents = discord.Intents.default()
intents.typing = True
intents.messages = True
intents.message_content = True
intents.dm_messages = True
intents.dm_typing = True

client = discord.Client(intents=intents)
comm = ac.CommandTree(client)

stocks = gas.get("stocks.json")
users = gas.get("users.json")
sales = gas.get("sales.json")

@comm.command()
async def stockquery(ctx, stock: str):
    """Tells the current value of a stock."""
    if stock.upper() in stocks.keys():
        await ctx.response.send_message("stock %s is currently at value Γ%d" % (stock.upper(), stocks[stock.upper()]))
    else:
        await ctx.response.send_message("that is not valid stock!")

@comm.command()
async def stocklist(ctx):
    """Lists available stocks and their current value.."""
    respo = ""
    for k, v in zip(stocks.keys(), stocks.values()):
        respo += "- `%s`: Γ%d\n" % (k, v)
    await ctx.response.send_message(respo)

@comm.command()
async def price(ctx, stock: str):
    """Tells a list of current prices for that stock."""
    stock = stock.upper()
    d = sales[stock]
    respo = "### top sales for `%s`:\n" % stock
    dv = d.values()
    i = 0
    for v in sorted(dv, reverse=True):
        respo += "- Γ%d\n" % (v[1])
        i += 1
        if i > 5:
            break
    respo += "highest price: %d\nlowest price: %d" % (max(dv,key=lambda x: x[1])[1], min(dv, key=lambda x: x[1])[1])
    await ctx.response.send_message(respo)

@comm.command()
async def buy(ctx, stock: str, amount: int):
    """Buy stocks at some price!"""
    userid = str(ctx.user.id)
    stock = stock.upper()
    if not stock in stocks.keys():
        await ctx.response.send_message("that is not valid stock!")
        return
    if not userid in users.keys():
        users[userid] = [360, {}]
    balance = users[userid][0]
    if amount > balance:
        await ctx.response.send_message("you dont have enough money!")
        return
    d = sales[stock]
    for k, v in zip(d.keys(), d.values()):
        if amount >= v[1] and k != userid:
            await ctx.response.send_message("you bought `%s` from <@%s> for Γ%d" % (stock, k, v[1]))
            users[userid][0] -= v[1]
            if stock in users[userid][1].keys():
                users[userid][1][stock] += 1
            else:
                users[userid][1][stock] = 1
            gas.store("users.json", users)
            sales[stock][k][0] -= 1
            if sales[stock][k][0] < 1:
                sales[stock].pop(k)
            gas.store("sales.json", sales)
            stocks[stock] = (stocks[stock] + v[1]) // 2
            gas.store("stocks.json", stocks)
            return
    else:
        await ctx.response.send_message("looks like no one is selling `%s` at that price \:(" % stock)

@comm.command()
async def sell(ctx, stock: str, price: int):
    """Sell your stocks at the given price."""
    userid = str(ctx.user.id)
    stock = stock.upper()
    if not userid in users.keys():
        await ctx.response.send_message("you dont have any stocks of that kind to sell!")
        return
    if stock in users[userid][1].keys():
        users[userid][1][stock] -= 1
        if users[userid][1][stock] < 1:
            users[userid][1].pop(stock)
        gas.store("users.json", users)
        if not userid in sales[stock].keys():
            sales[stock][userid] = [1, price]
        else:
            sales[stock][userid][1] = price
            sales[stock][userid][0] += 1
        await ctx.response.send_message("you are now selling %d `%s` stocks at Γ%d" % (sales[stock][userid][0], stock, sales[stock][userid][1]))
    else:
        await ctx.response.send_message("you dont have any stocks of that kind to sell!")

@comm.command()
async def balance(ctx):
    """Check your balance and owned stocks."""
    userid = str(ctx.user.id)
    respo = "your balance: Γ"
    respo += str(users[userid][0])
    respo += "\n"
    respo += "your owned stocks: \n"
    for k, v in zip(users[userid][1].keys(), users[userid][1].values()):
        respo += "- `%s`: %d\n" % (k, v)
    await ctx.response.send_message(respo)

@client.event
async def on_ready():
    await comm.sync()

client.run(token)
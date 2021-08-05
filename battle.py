from asyncio import tasks
import os
import random
from typing_extensions import final
import discord
import time
import asyncio
from PIL import Image
from io import BytesIO
from discord import player
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.command(name = 'battle')
@commands.max_concurrency(1, commands.BucketType.default)
async def battle(ctx, player1 : discord.Member):
  player2  = ctx.author
  await ctx.send(f"I have dmed {player2.mention}. When he responds I will dm {player1.mention}. After that the battle will begin.")

  #checks messages in dms for their class
  classes = ["knight", "fighter", "mage"]
  def check1(msg):
    return msg.author == player1 and msg.guild == None and msg.content.lower() in classes
  def check2(msg):
    return msg.author == player2 and msg.guild == None and msg.content.lower() in classes
  
  defaultstatuseffects = { 
    'fire': 0, #turns
    'miss': 0
  }

  #stats are organized [defence, attack, special attack, speed, health] total of 50, accuracy
  defaultknightstats = [20, 10, 5, 2.5, 10,25]
  defaultfighterstats = [10, 15,  2.5, 10, 10,25]
  defaultmagestats = [5, 2.5,  20, 12.5, 7.5,25]
  #move name: [attack type('p' for physical or 's' special or 'st' or status), power (0,100), accuracy (90 average), recoil damage, crit chance (15 average), damage reduction(20 average), pp (5-35), repeat times (0 = multiple times 1-5), chance for status [] = none if boost stat [1 or 0 for enemy reduction of stat, stat#1, chance, 0 or 1,stat#2, chance] if status [2, statustype, chance], always goes first('y' or 'n'), description]
  #list of all moves and specs
  knightmoveslist = ['sword attack', 'shield', 'spear jab', 'javelin throw', 'shield rush', 'dagger throw', 'strategize', 'joust', 'retreat', 'reinforcements']
  fightermoveslist = ['punch', 'kick', 'slap', 'focus', 'fire punch', 'uppercut', 'jab', 'dodge', 'taunt', 'double leg take down']
  magemoveslist =   ['fireball', 'strong wind', 'lightning strike', 'kinetic wave', 'wand smack', 'deal with the devil', 'super spell','alternate realm','light warrior'] #, 'healthswap']
  knightmoves = {
    'sword attack': ['p', 35, 90,  0, 15, 20, 30, 1, [], 'n', 'attack with your sword'], 
    'shield':       ['p', 0,  100,  0, 0, 95, 15, 1, [], 'y', 'use your shield to block almost almost all damage'],
    'spear jab':    ['p', 25, 100, 0, 0,  20, 30, 1, [], 'y', 'lunge at your target with your spear, always attacks first and never misses.'],
    'javelin throw':['p', 50, 75, 15, 20, 25, 5,  1, [], 'n', 'throw a javelin at your target. Does a lot of damage *when it hits*'],
    'shield rush':  ['p', 60, 70, 35, 25, 35, 5,  1, [], 'n', 'rush your target with your shield out. If you miss you take high recoil damage'],
    'dagger throw': ['p', 7.5, 90, 0, 15, 15, 15, 0, [], 'n', "Throw a random amout of knives from 1-5 at your opponent, don't worry, you have good aim."],
    'strategize':   ['st', 0,  95, 0,  0, 25, 20, 1, [1, 3, 100, 1, 1, 100], 'n', 'Increases your speed and attack.'],
    'joust':        ['p', 85,  60, 45, 5, 15,  5, 1, [], 'n', 'High attack and recoil. You charge at your opponent on a horse. Dont miss :D'],
    'retreat':      ['st', 0,  95, 0,  0, 25, 20, 1, [1, 0, 100, 0, 5, 100], 'n', 'You increase your defense and decrease the opponents accuracy'],
    'reinforcements':['p',125, 20, 0,  0,  0,  3, 1, [], 'n', 'You try to call for reinforcements.']
  }
  fightermoves = {
    'punch':        ['p', 35, 90, 0, 15, 20, 30, 1, [], 'n', 'punch your opponent'],
    'kick':         ['p', 40, 85, 0, 20, 20, 25, 1, [], 'n', 'kick your opponent'],
    'slap':         ['p', 7.5, 90, 0, 15, 15, 15, 0, [], 'n', 'slap you opponent 1-5 times'],
    'focus':        ['st', 0,  95, 0,  0, 25, 20, 1, [1, 3, 100, 1, 1, 100], 'n', 'Increases your speed and attack.'],
    'fire punch':   ['p', 30, 90, 15, 15, 15, 15, 1, [2, 'fire', 25], 'y', 'punch your opponent so fast that your hand is on fire'],
    'uppercut':     ['p', 55, 75, 0, 20, 5, 10, 1, [], 'n', 'high damage low accuracy uppercut'],
    'jab':          ['p', 20, 95, 0, 15, 0, 25, 1, [2, 'miss', 70], 'y', 'Always attacks first and throws your opponent off balance making them likely to miss' ],
    'dodge':        ['p', 0, 100, 0, 0, 95, 15, 1, [], 'y', 'you dodge the attack and negate almost all damage'],
    'taunt':        ['st', 0,  95, 0,  0, 25, 20, 1, [0, 5, 100, 0, 0, 100], 'n', 'you decrease the opponents accuracy and defense'],
    'double leg take down':['p',105,35,20,5,15,3,1, [], 'n', 'Grab your opponent by the legs and **throw them to the ground!** High risk high reward move.']
  }
  magemoves =   {
    'fireball':         ['s', 55, 75, 15, 0, 0, 5, 1, [2, 'fire', 35], 'n', 'shoot a fireball at your opponent'],
    'strong wind':      ['s', 35, 90, 0, 15, 20, 20, 1, [], 'n', 'summon a strong wind to attack your opponent'],
    'lightning strike': ['s', 70, 60, 35,2.5, 5,  3, 1, [0, 5, 30], 'n', 'You summon a Lightning strike down on your opponent, there may be some collateral damage. Has a chance to put your target off balance lowering their accuracy.'],
    'kinetic wave':     ['s', 15, 95, 0, 15, 0, 25, 1, [2, 'miss', 75], 'y', 'Always attacks first and puts your opponent off balance making them likely to miss' ],
    'wand smack':       ['p', 40, 80, 0, 25, 20, 35, 1, [], 'n', 'smack your opponent over the head with your wand'],
    'deal with the devil':['st',0, 100,45, 0, 30, 1, 3, [1, 0, 75, 1, 2, 75], 'n', 'You made a deal with the devil. Part of your life, for an increase in attack and defense. Was it worth it?'],
    'super spell':      ['st', 0,  95, 0,  0, 20, 20, 1, [1, 2, 100, 1, 1, 100], 'n', 'Increases your attack.'],
    'alternate realm':  ['st', 0, 100, 0, 15, 0, 5, 1, [0, 0, 100, 1, 0, 100], 'n', 'Opens an alternate realm  stealing some of your opponents defense stat and giving it to you.'],
    'light warrior':    ['p', 50 , 80, 25, 60, 10, 5, 1, [], 'n', 'Cover yourself in a shield of light during your attack. You are injured by the armor, but mostly protected from attacks']
    #special unique move
    #'healthswap':       ['special', 'swaps health of both players']
    }
  #chooses 4 random moves
  def getmoves(totalmoveslist):
    a=random.choice([0,1,2,3,4])
    moveslist = []
    random.shuffle(totalmoveslist)
    while len(moveslist) != 4:
      moveslist.append(totalmoveslist[a])
      a+=1
    return(moveslist)
  #assigns levels
  knightlevel1 = random.choice(range(1,6))
  fighterlevel1 = random.choice(range(1,6))
  magelevel1 = random.choice(range(1,6))
  knightlevel2 = random.choice(range(1,6))
  fighterlevel2 = random.choice(range(1,6))
  magelevel2 = random.choice(range(1,6))
  #send message to choose class
  await player2.send(f"choose a class. knight (level {knightlevel2}), fighter (level {fighterlevel2}), or mage (level {magelevel2}).")
  player2_choice = (await bot.wait_for('message', check = check2)).content
  await player1.send(f"choose a class. knight (level {knightlevel1}), fighter (level {fighterlevel1}), or mage (level {magelevel1}).")
  player1_choice = (await bot.wait_for('message', check = check1)).content
  #makes first embed with moves
  def embedmaker(playerinfo):
    embed = discord.Embed(title = f"{playerinfo['classname']} Level {playerinfo['level']}", color = 0x88068c)
    embed.add_field(name = f"{playerinfo['moves'][0]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][0]])[10]}", inline = False)
    embed.add_field(name = f"{playerinfo['moves'][1]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][1]])[10]}", inline = False)
    embed.add_field(name = f"{playerinfo['moves'][2]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][2]])[10]}", inline = False)
    embed.add_field(name = f"{playerinfo['moves'][3]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][3]])[10]}", inline = False)
    embed.set_thumbnail(url=playerinfo['icon1'])
    return embed
  #player1 gets info

  def playerinfomaker(classname, level, stats, movelist, movedict, icon1, playernumber, color):
      playerinfo = {
      'player': playernumber,
      'classname': classname,
      'level': level, 
      'stats':stats,  
      'moves': getmoves(movelist), 
      'movedict': movedict,
      'health': ((stats[4]*8) + (level * 5)),
      'statuseffects': defaultstatuseffects,
      'icon1':   icon1,
      'color':   color,
      'icon2':   f'{classname}'
      }
      return playerinfo

  #assigns player1 a class and stats
  if player1_choice == 'mage':
    player1info = playerinfomaker('Mage', magelevel1, defaultmagestats, magemoveslist, magemoves, 'https://cdn.discordapp.com/attachments/843173479063093271/847158509077921882/spritedemo.png', player1, 0x88068c)
    await player1.send(embed=embedmaker(player1info))
  elif player1_choice == 'fighter':
    player1info = playerinfomaker('Fighter', fighterlevel1, defaultfighterstats, fightermoveslist, fightermoves, "https://cdn.discordapp.com/attachments/843173479063093271/847497843119751188/fighter.png", player1, 0xcc7e00)
    await player1.send(embed=embedmaker(player1info))
  elif player1_choice == 'knight':
    player1info = playerinfomaker('Knight', knightlevel1, defaultknightstats, knightmoveslist, knightmoves, "https://cdn.discordapp.com/attachments/843173479063093271/847582273393262602/latest-removebg-preview.png", player1, 0x454545)
    await player1.send(embed=embedmaker(player1info))
  
  
  #player 2's turn 
  if player2_choice == 'mage':
    player2info = playerinfomaker('Mage', magelevel2, defaultmagestats, magemoveslist, magemoves, 'https://cdn.discordapp.com/attachments/843173479063093271/847158509077921882/spritedemo.png', player2, 0x88068c)
    await player2.send(embed=embedmaker(player2info))
  elif player2_choice == 'fighter':
    player2info = playerinfomaker('Fighter', fighterlevel2, defaultfighterstats, fightermoveslist, fightermoves, "https://cdn.discordapp.com/attachments/843173479063093271/847497843119751188/fighter.png", player2, 0xcc7e00)
    await player2.send(embed=embedmaker(player2info))
  elif player2_choice == 'knight':
    player2info = playerinfomaker('Knight', knightlevel2, defaultknightstats, knightmoveslist, knightmoves, "https://cdn.discordapp.com/attachments/843173479063093271/847582273393262602/latest-removebg-preview.png", player2, 0x454545)
    await player2.send(embed=embedmaker(player2info))
  #fix stats with incorporation of levels
  a = 0
  while a < 4:
    (player1info['stats'])[a] = (player1info['stats'])[a] * (1+player1info['level']/((random.choice(range(95,105)))/10))
    (player2info['stats'])[a] = (player2info['stats'])[a] * (1+player2info['level']/((random.choice(range(95,105)))/10))
    a+=1
  (player1info['stats'])[4] = player1info['health']
  (player2info['stats'])[4] = player2info['health']
  #start battling

  async def countdamage(move, playerinfo, opponentinfo, opponentmove):
   finaldamage = 0
   recoildamage = 0
   b = ((playerinfo['movedict'])[move])[7]
   def text2(number):
     occurence = ''
     if number == 0:#stats are organized [defence, attack, special attack, speed, health] total of 50, accuracy
       occurence = 'defense'
     elif number == 1:
       occurence = 'attack'
     elif number == 2:
       occurence = 'special attack'
     elif number == 3:
       occurence = 'speed'
     elif number == 5:
       occurence = 'accuracy'
     return(occurence)



   misschance = 1 

   if opponentinfo['statuseffects']['fire'] > 0:
      await ctx.send (f"{playerinfo['player'].mention}, you were hurt by your burn. ")
      finaldamage += opponentinfo['statuseffects']['fire'] * 10
      opponentinfo['statuseffects']['fire'] -= 1
   elif opponentinfo['statuseffects']['miss'] > 0:
      misschance -= opponentinfo['statuseffects']['miss']/10
      await ctx.send(f"{playerinfo['player'].mention}, you were suprised and have an increased chance to miss. ")
      opponentinfo['statuseffects']['miss'] -= 1
   
   yyy = random.choice(range(0,100))
   if yyy <= ((playerinfo['movedict'])[move])[2]* 25/(playerinfo['stats'])[5] * misschance: 
    if ((playerinfo['movedict'])[move])[0] == 'p':
      pastat = (playerinfo['stats'])[1]         #player attack stat is physical attack
    elif ((playerinfo['movedict'])[move])[0] == 's':
      pastat = (playerinfo['stats'])[2]         #player attack stat is special attack
    else:
      pastat = 0
    attackdamage = (((playerinfo['movedict'])[move])[1] * pastat/50)
    a = 1
    if ((playerinfo['movedict'])[move])[7] == 0:
      b = random.choice(range(0,10)) 

    while a <= b: #repeats the damage however many times it should with each having random damages and crit chances
      reducteddamage = attackdamage * (1-(opponentinfo['stats'])[0]/75) * (1-((opponentinfo['movedict'])[opponentmove])[5]/100)
      randomizedamage = reducteddamage * (1+random.choice(range(-50,50))/1000)
      critchance = random.choice(range(0,100))
      if critchance <= ((playerinfo['movedict'])[move])[4]:
        randomizedamage = randomizedamage * 1.5
      finaldamage += randomizedamage
      a+=1
    if ((playerinfo['movedict'])[move])[8] != []:
      if (((playerinfo['movedict'])[move])[8])[0] == 0: #opponent
        playeraffected = opponentinfo
        typeofeffect = 'stats'
      elif (((playerinfo['movedict'])[move])[8])[0] == 1: #player
        playeraffected = playerinfo
        typeofeffect = 'stats'
      elif (((playerinfo['movedict'])[move])[8])[0] == 2: #opponent
        playeraffected = opponentinfo
        typeofeffect = 'status'
      randomchance = random.choice(range(0,100))
      if randomchance <= (((playerinfo['movedict'])[move])[8])[2]:
        if typeofeffect == 'status':
         if random.choice(range(0,100)) <= (((playerinfo['movedict'])[move])[8])[2]:
          opponentinfo['statuseffects'][(((playerinfo['movedict'])[move])[8])[1]] = random.choice([1,2,3])
          if (((playerinfo['movedict'])[move])[8])[1] == 'miss':
            await ctx.send(f"{playerinfo['player']}, you put your opponent off balance increasing their chance to miss.")
          elif (((playerinfo['movedict'])[move])[8])[1] == 'fire':
            await ctx.send(f"{playerinfo['player']}, you set your opponent on fire!")

        else:          
          text2results = text2(((playerinfo['movedict'])[move])[8][1])
          if playeraffected == opponentinfo:
           if random.choice(range(0,100)) <= (((playerinfo['movedict'])[move])[8])[2]: 
            (opponentinfo['stats'])[(((playerinfo['movedict'])[move])[8])[1]] -= 2.5
            await ctx.send(f"{playerinfo['player'].mention}'s {text2results} was lowered")
          elif playeraffected == playerinfo:
           if random.choice(range(0,100)) <= (((playerinfo['movedict'])[move])[8])[2]:
            (playerinfo['stats'])[(((playerinfo['movedict'])[move])[8])[1]] *= 1.2
            await ctx.send(f"{opponentinfo['player'].mention}'s {text2results} was increased")

          if len(((playerinfo['movedict'])[move])[8]) > 3:
            if (((playerinfo['movedict'])[move])[8])[3] == 0: #opponent
              playeraffected = opponentinfo
            elif (((playerinfo['movedict'])[move])[8])[3] == 1: #player
              playeraffected = playerinfo



            text2results = text2(((playerinfo['movedict'])[move])[8][4])
            if playeraffected == opponentinfo:
              if random.choice(range(0,100)) <= (((playerinfo['movedict'])[move])[8])[5]: 
                (opponentinfo['stats'])[(((playerinfo['movedict'])[move])[8])[4]] -= 2.5
                await ctx.send(f"{opponentinfo['player'].mention}'s {text2results} was lowered")
            elif playeraffected == playerinfo:
              if random.choice(range(0,100)) <= (((playerinfo['movedict'])[move])[8])[5]:
                (playerinfo['stats'])[(((playerinfo['movedict'])[move])[8])[4]] *= 1.2
                await ctx.send(f"{playerinfo['player'].mention}'s {text2results} was increased")
        
    if b == 1: 
     if finaldamage > 0:
      await ctx.send(f"{playerinfo['player'].mention}'s attack did {round(finaldamage)} damage to {opponentinfo['player'].mention}. ")
     else:  
        print('no damage done :thonk:')
    elif b != 1:
      await ctx.send(f"{playerinfo['player'].mention}'s attack hit {b} times for a total of {round(finaldamage)} damage to {opponentinfo['player'].mention}. ")
    elif b != '':
      await ctx.send(f"{playerinfo['player'].mention}'s attack did {round(finaldamage)} damage to {opponentinfo['player'].mention}.")
   
   else:
    await ctx.send(f"{playerinfo['player'].mention} missed.")

   if playerinfo['movedict'][move][3] != 0:
      recoildamage = playerinfo['movedict'][move][3] * ((playerinfo['health'] + playerinfo['stats'][4]/3)/140)/6
      await ctx.send(f"{playerinfo['player'].mention} took {round(recoildamage)} points of recoil damage")
   playerinfo['health'] -= (recoildamage)
   opponentinfo['health'] -= (finaldamage)

   return [opponentinfo, playerinfo]

  def check1move(msg):
    return msg.author == player1 and msg.guild == None and msg.content.lower() in player1info['moves']
  def check2move(msg):
    return msg.author == player2 and msg.guild == None and msg.content.lower() in player2info['moves']

  while player1info['health'] >= 0 and player2info['health'] >= 0:
    await player1.send("What attack would you like to perform?")
    player1move = (await bot.wait_for('message', check = check1move)).content.lower()
    await player2.send("What attack would you like to perform?")
    player2move = (await bot.wait_for('message', check = check2move)).content.lower()

    firstmove = 0 
    if ((player1info['movedict'])[player1move])[9] == 'y':
      firstmove == 1
    if ((player2info['movedict'])[player2move])[9] == 'y':
      if firstmove == 1: #checks for both priority moves
        firstmove=0
      else:
        firstmove=2
    
    if firstmove == 0:
      if (player1info['stats'])[4] > (player2info['stats'])[4]:
        firstmove = 1
      elif (player2info['stats'])[4] > (player1info['stats'])[4]:
        firstmove = 2
      else: #checks for tied stats
        firstmove = random.choice([1,2]) #lol im so dumb rofl


    def embedhealthmaker(playerinfo, type):
        icon = Image.open(f"{playerinfo['icon2']}{type}.png")
        icon = icon.resize((500,700))
        hpbar = Image.open('rect.png')
        varpercent = playerinfo['health']/playerinfo['stats'][4]
        hpbar = hpbar.resize((500,50))
        hpbarempty = hpbar.crop((0,27, 500, 50))
        hpbarfull = hpbar.crop((0,2,(500 -500*varpercent),25))


        #icon.paste(hpbar,((500 + round(-500*varpercent)), 0))
        icon.paste(hpbarempty,  (0, 0))
        icon.paste(hpbarfull, (0, 0))
        #icon.paste(hpbarempty,  (0, 0))

        icon.save(f"{playerinfo['classname']}healthembed.png")
        
        imagefile = discord.File(f'C:\\Users\\Owner\\Desktop\\Python\\discord python\\hard commands\\{playerinfo["classname"]}healthembed.png', filename = f"{playerinfo['classname']}healthembed.png")
        
        if type == 1:

          embed = discord.Embed(title = f"{playerinfo['classname']} Level {playerinfo['level']}", color = playerinfo['color'])
          embed.add_field(name = f"{playerinfo['moves'][0]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][0]])[10]}", inline = False)
          embed.add_field(name = f"{playerinfo['moves'][1]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][1]])[10]}", inline = False)
          embed.add_field(name = f"{playerinfo['moves'][2]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][2]])[10]}", inline = False)
          embed.add_field(name = f"{playerinfo['moves'][3]}", value = f"{(playerinfo['movedict'][playerinfo['moves'][3]])[10]}", inline = False)
          embed.set_thumbnail(url=f"attachment://{playerinfo['classname']}healthembed.png")

        elif type == 2: 

          embed = discord.Embed(title = f"{playerinfo['classname']} User {playerinfo['player']}", color = playerinfo['color'])
          embed.set_image(url = f"attachment://{playerinfo['classname']}healthembed.png")
          


          
        return [embed, imagefile]
  

    if firstmove == 1:
      p1 = await countdamage(player1move, player1info, player2info, player2move)
      player1info = p1[1]
      player2info = p1[0]
      if player1info['health'] <= 0 or player2info['health'] <= 0:
        break
      p2 = await countdamage(player2move, player2info, player1info, player1move) 
      player1info = p2[0]
      player2info = p2[1]
      
    elif firstmove == 2: 
      p2 = await countdamage(player2move, player2info, player1info, player1move) 
      player1info = p2[0]
      player2info = p2[1]
      if player1info['health'] <= 0 or player2info['health'] <= 0:
        break
      p1 = await countdamage(player1move, player1info, player2info, player2move)
      player1info = p1[1]
      player2info = p1[0]

    if player1info['health'] <= 0 or player2info['health'] <= 0:
        break


    embed1 = embedhealthmaker(player1info,1)
    embed2 = embedhealthmaker(player2info,1)
    await player1.send (embed = embed1[0], file = embed1[1])
    await player2.send (embed = embed2[0], file = embed2[1])
  
  if player1info['health'] <= 0:
    finalembed1 = embedhealthmaker(player1info,2)
    await ctx.send (embed = finalembed1[0], file = finalembed1[1])
  elif player2info['health'] <= 0:
    finalembed2 = embedhealthmaker(player2info,2)
    await ctx.send (embed = finalembed2[0], file = finalembed2[1])
  

bot.run("INSERT TOKEN HERE")
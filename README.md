# Rose-Lite Bot — Render Deployment

1. Put these 5 files in a GitHub repo.
2. On render.com: New -> Web Service -> connect the repo.
3. Settings:
   - Runtime: Python 3
   - Build Command:  pip install -r requirements.txt
   - Start Command:  python bot.py
   - Instance Type:  Free
4. Environment -> Add: BOT_TOKEN = your token from @BotFather
5. Deploy. Check the Logs tab — you should see "Bot is running..."

IMPORTANT: Render free web services sleep after 15 minutes of
no incoming HTTP traffic. Keep the bot awake with a free UptimeRobot
(uptimerobot.com) monitor pinging https://YOUR-APP.onrender.com/ every 5 minutes.

Note: the free tier has an ephemeral disk — settings reset on every
redeploy. Upgrade to a paid plan + persistent disk to keep settings,
or accept resets if you redeploy rarely.

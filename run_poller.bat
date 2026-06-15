@echo off
cd /d "%~dp0"
echo FUB_API_KEY=fka_0oLnKwXpmGYRziW3j8fZBEYCb13rimVcHQ > .env
python poller.py

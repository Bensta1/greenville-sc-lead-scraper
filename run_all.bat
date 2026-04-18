@echo off
cd /d "%~dp0"

echo Running tax sale scraper...
python fetch.py

echo Running probate scraper...
python probate_fetch.py

echo Merging and scoring...
python merge_and_score.py

echo Done.
pause
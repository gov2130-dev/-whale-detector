name: حوت 54 - رادار V600
on:
  schedule:
    - cron: '30 8 * * 1-5'
    - cron: '30 13 * * 1-5'
    - cron: '0 20 * * 1-5'
  workflow_dispatch:
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install yfinance pandas requests pytz
      - run: python app.py --scan
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}

name: Build Daily Feed
on:
  schedule:
    - cron: '0 5 * * *'
  workflow_dispatch:
permissions:
  contents: write
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Build
        run: python build.py
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: .
          publish_branch: gh-pages
          include_files: index.html

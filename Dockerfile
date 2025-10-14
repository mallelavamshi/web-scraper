FROM python:3.11-slim

WORKDIR /app

# Install Chrome and system dependencies for Ubuntu 24.04
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl xvfb \
    libxi6 libgconf-2-4 libnss3 libxss1 \
    libappindicator3-1 libasound2 \
    libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 \
    libnspr4 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Verify Chrome installation
RUN google-chrome --version

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scrape_zip_optimized.py scrape_zip.py

RUN mkdir -p /app/excel_files /app/output /app/logs

ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome

CMD ["python", "-u", "scrape_zip.py"]

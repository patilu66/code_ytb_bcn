# Dockerfile pour sockpuppets YouTube avec idéologies politiques
FROM python:3.11-slim-bullseye

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_BIN=/usr/local/bin/chromedriver

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    xvfb \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Installer Chrome stable
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Installer ChromeDriver compatible (version moderne avec nouvelle API)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1) \
    && echo "Chrome major version: $CHROME_VERSION" \
    && if [ "$CHROME_VERSION" -ge "115" ]; then \
        # Pour Chrome 115+, utiliser la nouvelle API ChromeDriver
        CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE" | tr -d '\n') \
        && CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip"; \
    else \
        # Pour Chrome < 115, utiliser l'ancienne API
        CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
        && CHROMEDRIVER_URL="https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"; \
    fi \
    && echo "ChromeDriver version: $CHROMEDRIVER_VERSION" \
    && echo "Download URL: $CHROMEDRIVER_URL" \
    && wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && find /tmp -name "chromedriver" -executable -type f -exec mv {} /usr/local/bin/chromedriver \; \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && chromedriver --version

# Installer les dépendances Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers de l'application
COPY sockpuppet.py eytdriver_autonomous.py ./

# Copier les fichiers de données
COPY data/ ./data/

# Créer les dossiers de sortie avec permissions larges
RUN mkdir -p /app/output /app/data \
    && chmod -R 777 /app/output /app/data

# Script de démarrage avec Xvfb
RUN echo '#!/bin/bash\n\
# Démarrer Xvfb en arrière-plan\n\
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &\n\
export DISPLAY=:99\n\
\n\
# Attendre que X soit prêt\n\
sleep 2\n\
\n\
# S'\''assurer que les permissions sont correctes\n\
chmod -R 777 /app/output 2>/dev/null || true\n\
\n\
# Exécuter la commande passée en argument\n\
exec "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "sockpuppet.py"]
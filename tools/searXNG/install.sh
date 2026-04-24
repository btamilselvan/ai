mkdir -p ./searxng/core-config/
cd ./searxng/

curl -fsSL \
    -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml \
    -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example

cp -i .env.example .env

docker compose up -d
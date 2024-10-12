# medidaspr


# Connect to db
docker compose exec db psql --username=medidaspr --dbname=medidaspr
# View tables
docker compose exec db psql --username=medidaspr --dbname=medidaspr -c '\dt'
# Do query
docker compose exec db psql --username=medidaspr --dbname=medidaspr -c '\x' -c 'SELECT * FROM measures;'


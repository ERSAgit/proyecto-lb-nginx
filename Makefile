# Atajos para los comandos más usados. Requiere "make" (sudo apt install -y make).
COMPOSE = docker compose -f docker-compose.yml

.PHONY: up dev down ps logs estado politica rampa carga comparar resiliencia distribucion limpiar

up:            ## Levanta el entorno de pruebas (sin recarga en caliente)
	$(COMPOSE) up -d --build

dev:           ## Levanta el entorno de desarrollo (con docker-compose.override.yml)
	docker compose up -d --build

down:          ## Detiene y elimina los contenedores y la red
	docker compose down

ps:            ## Estado de los contenedores
	$(COMPOSE) ps

logs:          ## Logs del balanceador en vivo
	tail -f logs/nginx/access.log

estado:        ## Métricas de stub_status
	bash scripts/estado.sh

politica:      ## Cambia el algoritmo. Ej: make politica P=least_conn
	bash scripts/cambiar_politica.sh $(P)

rampa:         ## Prueba con ramp-up progresivo
	$(COMPOSE) run --rm artillery run rampa.yml --output /results/rampa.json

carga:         ## Prueba de 1000 usuarios durante 60 s con el algoritmo actual
	$(COMPOSE) run --rm artillery run carga-1000.yml --output /results/carga.json

comparar:      ## Prueba de 1000 usuarios con los 3 algoritmos y tabla comparativa
	bash scripts/comparar_algoritmos.sh

resiliencia:   ## Elimina un backend en caliente durante la carga
	bash scripts/prueba_resiliencia.sh

distribucion:  ## Peticiones por backend según el access.log
	bash scripts/analizar_logs.sh

limpiar:       ## Borra resultados y logs
	rm -f results/*.json results/*.txt results/*.md results/*.log
	$(COMPOSE) exec -T nginx sh -c ': > /var/log/nginx/access.log' || true

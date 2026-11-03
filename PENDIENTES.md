# Pendientes del proyecto (para quien continúa)

El proyecto ya está construido y funcionando. Falta repetir las pruebas pesadas en un PC con más memoria, porque en el PC donde se desarrolló (7.3 GB de RAM) la VM se congelaba durante las pruebas de 1000 usuarios.

## Requisitos del PC

- **16 GB de RAM o más** (la VM usa 4 GB).
- Unos **15 GB libres** en disco.
- VirtualBox, Vagrant y Git instalados.
- Durante las pruebas: cargador conectado, suspensión desactivada y sin programas pesados abiertos (Chrome, Discord).

## 1. Levantar el entorno

```bash
git clone https://github.com/ERSAgit/proyecto-lb-nginx.git
cd proyecto-lb-nginx/vagrant
vagrant up          # crea la VM e instala Docker (tarda unos minutos la primera vez)
vagrant ssh
```

Dentro de la VM:

```bash
cd ~/proyecto-lb-nginx
docker compose -f docker-compose.yml up -d --build
docker compose -f docker-compose.yml ps     # NGINX y los 3 backends deben salir "healthy"
```

Comprobar en el navegador: `http://192.168.100.10:8080` (al recargar cambia de backend) y Prometheus en `http://192.168.100.10:9091`.

## 2. Correr las pruebas

La primera vez que se usa Artillery se descarga su imagen, que es grande. Esperar a que termine.

```bash
# a) Ramp-up progresivo (~2 min)
docker compose -f docker-compose.yml run --rm artillery run rampa.yml --output /results/rampa.json | tee results/rampa_artillery.txt
python3 scripts/resumen_resultados.py results/rampa.json

# b) Comparación de los 3 algoritmos con 1000 usuarios (~8 min)
bash scripts/comparar_algoritmos.sh

# c) Resiliencia: elimina backend2 en plena carga (~2 min)
bash scripts/cambiar_politica.sh round_robin
bash scripts/prueba_resiliencia.sh
```

**Cómo saber si una prueba salió limpia:** Artillery imprime un reporte `Metrics for period to: HH:MM:SS` cada 10 segundos. Si entre dos reportes hay un salto de minutos, el PC se congeló y esa prueba hay que repetirla.

**Capturas para el informe:** en otra terminal dentro de la VM, `bash scripts/estado.sh -w` muestra el stub_status en vivo. Tomar una captura durante la prueba de cada algoritmo, cuando `Active connections` esté cerca de 1000.

## 3. Mostrar la recarga en caliente (para el informe y la demo)

```bash
docker compose -f docker-compose.yml down
docker compose up -d                # sin -f: aplica docker-compose.override.yml
docker compose logs -f nginx        # dejar abierto
```

En otra terminal, editar `nginx/nginx.conf` (por ejemplo cambiar `proxy_read_timeout 5s;` por `6s;`) y guardar. En los logs debe aparecer `[hot-reload] configuración recargada`. Si se introduce un error de sintaxis, debe aparecer `la configuración tiene errores, NO se recarga`.

## 4. Subir los resultados a GitHub

La carpeta `results/` no se sube a GitHub (está en `.gitignore`). Copiar los resultados a la carpeta `resultados/`, sin los `.log` que son muy pesados:

```bash
mkdir -p resultados/pc-16gb
cp results/*.json results/*.txt results/*.md resultados/pc-16gb/
```

Luego, desde la carpeta del proyecto:

```bash
git add resultados
git commit -m "Resultados de las pruebas en PC de 16 GB"
git push
```

## Resultados que ya existen (PC de 7.3 GB)

Están en `resultados/pc-7gb/`:

| Prueba | Estado |
|---|---|
| Rampa | ✅ Válida: 12 600 peticiones, 0 errores, p99 242 ms |
| 1000 usuarios con round_robin | ✅ Válida: 55 000 peticiones, 0 errores, 33.33 % por backend |
| 1000 usuarios con ip_hash | ⚠️ Válida en lo principal: 99.99 % a backend3. Los 103 errores fueron por un congelamiento del PC al final |
| 1000 usuarios con least_conn | ❌ **No válida**: el PC se congeló 5 minutos en plena prueba |
| Resiliencia (en `corrida1/`) | ✅ Válida: 4500 peticiones, 0 errores, backend2 en 0 mientras estuvo eliminado |

Sirven como respaldo y para comparar, pero la tabla final del informe debe salir de una sola corrida limpia de los 3 algoritmos en el mismo PC.

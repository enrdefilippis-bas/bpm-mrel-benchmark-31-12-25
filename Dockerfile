# --------------------------------------------------------------------------
# Build stage — rigenera dashboard_mrel_cda_2025q4.html dai dati Q4 2025
# --------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Solo le dipendenze necessarie a build_dashboard.py (pandas, pyarrow)
RUN pip install --no-cache-dir pandas==2.2.* pyarrow==17.* duckdb==1.1.*

# Copia il codice + dati processati
COPY core/ ./core/
COPY scripts/ ./scripts/
COPY data/processed/ ./data/processed/

# Genera la dashboard (output: dashboard_mrel_cda_2025q4.html)
RUN python scripts/build_dashboard.py

# --------------------------------------------------------------------------
# Runtime stage — nginx leggerissimo serve la dashboard statica
# --------------------------------------------------------------------------
FROM nginx:1.27-alpine

# Sostituisco la default page nginx con la dashboard CdA
COPY --from=builder /build/dashboard_mrel_cda_2025q4.html /usr/share/nginx/html/index.html

# Render usa la $PORT env var (default 8080 per il piano free)
# Patch della config nginx per ascoltare su $PORT al boot
RUN rm /etc/nginx/conf.d/default.conf

COPY <<'EOF' /etc/nginx/templates/default.conf.template
server {
    listen       ${PORT};
    server_name  _;

    root /usr/share/nginx/html;
    index index.html;

    # Forza no-cache così aggiornamenti dashboard sono immediati
    location / {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
        try_files $uri $uri/ /index.html;
    }

    # Health check su / per Render
    location = /healthz {
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Render imposta PORT a runtime; default per local testing
ENV PORT=8080
EXPOSE 8080

# nginx:alpine ha già l'entrypoint che fa envsubst sui template e poi avvia nginx

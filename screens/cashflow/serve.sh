#!/bin/bash
# Avvia il server locale per la riproduzione offline della pagina cashflow
cd "$(dirname "$0")/offline" && python3 -m http.server 8080

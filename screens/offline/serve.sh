#!/bin/bash
# Avvia il server locale per la riproduzione offline di tutto il sito Sibill
cd "$(dirname "$0")/offline" && python3 server.py

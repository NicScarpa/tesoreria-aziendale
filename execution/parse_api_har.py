#!/usr/bin/env python3
"""
Analizza il file HAR delle richieste API di Sibill.
Estrae endpoint unici, categorizza per sezione, analizza strutture delle risposte.
Genera:
  - assets/api-traces/*.json (un file per sezione)
  - .tmp/api-catalog.json (catalogo completo)
  - .tmp/har-analysis.json (analisi intermedia completa)
"""

import json
import sys
import os
from collections import defaultdict
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime

PROJECT_ROOT = "/Users/nicolascarpa/Desktop/Progetti/sibill-re"
HAR_FILE = os.path.join(PROJECT_ROOT, "assets/har/api-requests.json")
API_TRACES_DIR = os.path.join(PROJECT_ROOT, "assets/api-traces")
TMP_DIR = os.path.join(PROJECT_ROOT, ".tmp")

# Mapping sezioni -> pattern URL
SECTION_MAPPING = {
    "01-auth-flow": {
        "name": "Autenticazione",
        "patterns": ["/api/auth/", "/api/v1/users/me", "/api/v1/users/token", "/api/v1/users/chat-token"],
        "url": "https://app.sibill.com/login"
    },
    "02-cashflow": {
        "name": "Cashflow / Dashboard",
        "patterns": ["/api/v1/cashflow/"],
        "url": "https://app.sibill.com/cashflow"
    },
    "03-categorie": {
        "name": "Categorie Cashflow",
        "patterns": ["/api/v1/categories"],
        "url": "https://app.sibill.com/cashflow/categories"
    },
    "04-movimenti": {
        "name": "Movimenti",
        "patterns": ["/api/v1/transactions"],
        "url": "https://app.sibill.com/transactions/movements"
    },
    "05-pagamenti": {
        "name": "Pagamenti",
        "patterns": ["/api/v1/payments"],
        "url": "https://app.sibill.com/transactions/payments"
    },
    "06-regole": {
        "name": "Regole Categorizzazione",
        "patterns": ["/api/v1/categorization-rules", "/api/v1/transaction-rules", "/api/v1/rules"],
        "url": "https://app.sibill.com/transactions/rules"
    },
    "07-riconciliazioni": {
        "name": "Riconciliazioni",
        "patterns": ["/api/v1/reconciliations"],
        "url": "https://app.sibill.com/reconciliations"
    },
    "08-conti": {
        "name": "Conti Bancari",
        "patterns": ["/api/v1/accounts", "/api/v1/user-bank-accounts", "/api/v1/institutions", "/api/v1/consents"],
        "url": "https://app.sibill.com/accounts"
    },
    "09-scadenzario": {
        "name": "Scadenzario",
        "patterns": ["/api/v1/outstanding", "/api/v1/deadlines", "/api/v1/scheduled"],
        "url": "https://app.sibill.com/outstanding"
    },
    "10-ricorrenze": {
        "name": "Ricorrenze",
        "patterns": ["/api/v1/recurrences"],
        "url": "https://app.sibill.com/outstanding/recurrences/received"
    },
    "11-fatture": {
        "name": "Fatture / Documenti",
        "patterns": ["/api/v1/documents", "/api/v1/invoices"],
        "url": "https://app.sibill.com/invoices/dashboard"
    },
    "12-controparti": {
        "name": "Clienti e Fornitori",
        "patterns": ["/api/v1/counterparts"],
        "url": "https://app.sibill.com/counterparts"
    },
    "13-f24": {
        "name": "F24",
        "patterns": ["/api/v1/f24", "/api/v1/tax-payments"],
        "url": "https://app.sibill.com/f24"
    },
    "14-settings": {
        "name": "Impostazioni",
        "patterns": ["/api/v1/companies", "/api/v1/company-users", "/api/v1/subscriptions", "/api/v1/cards", "/api/v1/settings"],
        "url": "https://app.sibill.com/settings/team"
    }
}


def load_har():
    """Carica il file HAR."""
    with open(HAR_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_api_request(req):
    """Verifica se la richiesta è verso l'API Sibill."""
    url = req.get("url", "")
    return "api.sibill.com" in url


def normalize_path(url):
    """Normalizza il path dell'URL rimuovendo UUID e query params."""
    parsed = urlparse(url)
    path = parsed.path
    # Sostituisci UUID con {id}
    import re
    path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', path)
    # Sostituisci numeri interi lunghi con {id}
    path = re.sub(r'/\d{5,}/', '/{id}/', path)
    return path


def extract_params(url):
    """Estrai i query parameters dall'URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    # Decodifica e semplifica
    result = {}
    for key, values in params.items():
        decoded_key = unquote(key)
        result[decoded_key] = values[0] if len(values) == 1 else values
    return result


def analyze_json_structure(json_str, max_depth=4, current_depth=0):
    """Analizza la struttura di un JSON senza dati sensibili."""
    if current_depth >= max_depth:
        return "..."

    if json_str is None:
        return None

    if isinstance(json_str, str):
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return "string"
    else:
        data = json_str

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Maschera valori sensibili
            if any(s in key.lower() for s in ['token', 'password', 'secret', 'key', 'email', 'phone', 'iban']):
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = analyze_json_structure(value, max_depth, current_depth + 1)
            elif isinstance(value, list):
                if len(value) > 0:
                    result[key] = [analyze_json_structure(value[0], max_depth, current_depth + 1)]
                    if len(value) > 1:
                        result[key].append(f"... ({len(value)} items total)")
                else:
                    result[key] = []
            elif isinstance(value, bool):
                result[key] = "boolean"
            elif isinstance(value, int):
                result[key] = "integer"
            elif isinstance(value, float):
                result[key] = "float"
            elif value is None:
                result[key] = "null"
            else:
                # Maschera stringhe che sembrano ID o valori sensibili
                str_val = str(value)
                if len(str_val) > 50:
                    result[key] = f"string (len={len(str_val)})"
                else:
                    result[key] = "string"
        return result
    elif isinstance(data, list):
        if len(data) > 0:
            return [analyze_json_structure(data[0], max_depth, current_depth + 1), f"... ({len(data)} items)"]
        return []
    elif isinstance(data, bool):
        return "boolean"
    elif isinstance(data, (int, float)):
        return "number"
    else:
        return "string"


def extract_jsonapi_fields(json_str):
    """Estrai campi da una risposta JSON:API."""
    try:
        if isinstance(json_str, str):
            data = json.loads(json_str)
        else:
            data = json_str
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    result = {
        "is_jsonapi": False,
        "entity_type": None,
        "fields": [],
        "relationships": [],
        "meta": None,
        "included_types": [],
        "pagination": None,
        "is_collection": False
    }

    # Check JSON:API structure
    if "data" in data:
        result["is_jsonapi"] = True
        api_data = data["data"]

        if isinstance(api_data, list):
            result["is_collection"] = True
            if len(api_data) > 0:
                item = api_data[0]
            else:
                item = None
        elif isinstance(api_data, dict):
            item = api_data
        else:
            item = None

        if item and isinstance(item, dict):
            result["entity_type"] = item.get("type")

            # Attributes
            attrs = item.get("attributes", {})
            if isinstance(attrs, dict):
                for key, value in attrs.items():
                    field_type = type(value).__name__ if value is not None else "null"
                    if isinstance(value, str) and len(value) > 100:
                        field_type = "string (long)"
                    result["fields"].append({
                        "name": key,
                        "type": field_type,
                        "sample": None  # Non salvare dati sensibili
                    })

            # Relationships
            rels = item.get("relationships", {})
            if isinstance(rels, dict):
                for rel_name, rel_data in rels.items():
                    if isinstance(rel_data, dict) and "data" in rel_data:
                        rel_content = rel_data["data"]
                        if isinstance(rel_content, list):
                            rel_type = rel_content[0].get("type") if rel_content else "unknown"
                            result["relationships"].append({
                                "name": rel_name,
                                "type": "has_many",
                                "related_type": rel_type
                            })
                        elif isinstance(rel_content, dict):
                            result["relationships"].append({
                                "name": rel_name,
                                "type": "belongs_to",
                                "related_type": rel_content.get("type", "unknown")
                            })
                        elif rel_content is None:
                            result["relationships"].append({
                                "name": rel_name,
                                "type": "belongs_to (nullable)",
                                "related_type": "unknown"
                            })

        # Meta (pagination etc.)
        if "meta" in data:
            result["meta"] = analyze_json_structure(data["meta"], max_depth=3)
            meta = data["meta"]
            if isinstance(meta, dict):
                # Check for pagination
                pagination_keys = ["page", "total", "total-pages", "total_pages", "per-page", "per_page", "current-page", "current_page"]
                pag = {}
                for key in pagination_keys:
                    if key in meta:
                        pag[key] = meta[key]
                if pag:
                    result["pagination"] = pag

        # Included types
        if "included" in data and isinstance(data["included"], list):
            included_types = set()
            for inc in data["included"]:
                if isinstance(inc, dict) and "type" in inc:
                    included_types.add(inc["type"])
            result["included_types"] = sorted(list(included_types))

    elif "errors" in data:
        result["is_jsonapi"] = True
        result["entity_type"] = "error"
        errors = data["errors"]
        if isinstance(errors, list) and len(errors) > 0:
            result["fields"] = [{"name": k, "type": "string", "sample": None} for k in errors[0].keys()]

    return result


def classify_request(req):
    """Classifica una richiesta nella sezione corretta."""
    url = req.get("url", "")
    parsed = urlparse(url)
    path = parsed.path

    for section_key, section_info in SECTION_MAPPING.items():
        for pattern in section_info["patterns"]:
            if pattern in path:
                return section_key

    return None


def determine_trigger(req, all_reqs, idx):
    """Tenta di determinare il trigger UI della richiesta."""
    method = req.get("method", "GET")
    url = req.get("url", "")
    path = urlparse(url).path

    if method == "POST" and "/api/auth/login" in path:
        return "form submit - login"
    if method == "POST" and "/api/auth/logout" in path:
        return "click logout"

    if method == "GET":
        if "/metadata" in path:
            return "page load - metadata fetch"
        if "page[number]" in url or "page%5Bnumber%5D" in url:
            return "pagination - cambio pagina"
        if "filter[" in url or "filter%5B" in url:
            return "filter change"
        if "/chart" in path:
            return "page load - chart data"
        if "/table" in path:
            return "page load - table data"
        if "/summary" in path:
            return "page load - summary data"
        if "/suggested" in path:
            return "autocomplete / suggestion"
        if "include=" in url:
            return "page load - data with relationships"
        return "page load"

    if method == "POST":
        return "form submit / create"
    if method == "PUT" or method == "PATCH":
        return "update / edit"
    if method == "DELETE":
        return "delete action"

    return "unknown"


def sanitize_response_body(body_str):
    """Analizza e sanitizza il response body."""
    if not body_str:
        return None
    try:
        return analyze_json_structure(body_str, max_depth=4)
    except Exception:
        return "non-JSON response"


def main():
    print(f"[+] Caricamento HAR da {HAR_FILE}...")
    all_requests = load_har()
    print(f"[+] Caricate {len(all_requests)} richieste totali")

    # Filtra solo API Sibill
    api_requests = [r for r in all_requests if is_api_request(r)]
    print(f"[+] {len(api_requests)} richieste verso api.sibill.com")

    # Statistiche generali
    methods = defaultdict(int)
    statuses = defaultdict(int)
    endpoints_unique = set()

    for req in api_requests:
        methods[req.get("method", "?")] += 1
        statuses[req.get("status", 0)] += 1
        norm_path = normalize_path(req["url"])
        endpoints_unique.add(f'{req.get("method", "?")} {norm_path}')

    print(f"\n[+] Statistiche:")
    print(f"    Endpoint unici: {len(endpoints_unique)}")
    print(f"    Metodi: {dict(methods)}")
    print(f"    Status: {dict(sorted(statuses.items()))}")

    # Classifica per sezione
    sections = defaultdict(list)
    unclassified = []

    for idx, req in enumerate(api_requests):
        section = classify_request(req)
        if section:
            sections[section].append((idx, req))
        else:
            unclassified.append(req)

    print(f"\n[+] Classificazione per sezione:")
    for section_key in sorted(sections.keys()):
        section_name = SECTION_MAPPING[section_key]["name"]
        print(f"    {section_key}: {section_name} → {len(sections[section_key])} richieste")
    if unclassified:
        print(f"    [non classificate] → {len(unclassified)} richieste")
        for req in unclassified[:10]:
            print(f"      {req.get('method')} {urlparse(req['url']).path}")

    # Analisi dettagliata per endpoint unico
    print(f"\n[+] Analisi dettagliata degli endpoint...")
    endpoint_details = {}  # key: "METHOD /path" -> details
    entities = {}  # key: entity type -> fields + relationships

    for req in api_requests:
        method = req.get("method", "GET")
        norm_path = normalize_path(req["url"])
        endpoint_key = f"{method} {norm_path}"
        params = extract_params(req["url"])
        status = req.get("status", 0)

        if endpoint_key not in endpoint_details:
            endpoint_details[endpoint_key] = {
                "method": method,
                "path": norm_path,
                "original_urls": [],
                "params_seen": {},
                "statuses_seen": set(),
                "request_bodies": [],
                "response_structures": [],
                "jsonapi_info": None,
                "count": 0,
                "section": classify_request(req),
                "triggers": set()
            }

        detail = endpoint_details[endpoint_key]
        detail["count"] += 1
        detail["statuses_seen"].add(status)
        detail["original_urls"].append(req["url"][:200])
        detail["triggers"].add(determine_trigger(req, api_requests, 0))

        # Params
        for k, v in params.items():
            if k not in detail["params_seen"]:
                detail["params_seen"][k] = set()
            detail["params_seen"][k].add(str(v)[:100])

        # Request body
        if req.get("postData"):
            try:
                body = json.loads(req["postData"])
                # Maschera dati sensibili
                if isinstance(body, dict):
                    sanitized = {}
                    for k, v in body.items():
                        if any(s in k.lower() for s in ['password', 'token', 'secret', 'email']):
                            sanitized[k] = "[REDACTED]"
                        else:
                            sanitized[k] = type(v).__name__
                    if sanitized not in detail["request_bodies"]:
                        detail["request_bodies"].append(sanitized)
            except:
                pass

        # Response body analysis (solo per successi)
        if 200 <= status < 300 and req.get("responseBody"):
            jsonapi_info = extract_jsonapi_fields(req["responseBody"])
            if jsonapi_info and jsonapi_info["is_jsonapi"]:
                detail["jsonapi_info"] = jsonapi_info

                # Raccolta entità
                etype = jsonapi_info.get("entity_type")
                if etype and etype != "error":
                    if etype not in entities:
                        entities[etype] = {
                            "fields": {},
                            "relationships": {},
                            "endpoints": set(),
                            "included_in": set()
                        }

                    for field in jsonapi_info.get("fields", []):
                        fname = field["name"]
                        entities[etype]["fields"][fname] = field["type"]

                    for rel in jsonapi_info.get("relationships", []):
                        rname = rel["name"]
                        entities[etype]["relationships"][rname] = {
                            "type": rel["type"],
                            "related_type": rel["related_type"]
                        }

                    entities[etype]["endpoints"].add(endpoint_key)

                # Included types
                for inc_type in jsonapi_info.get("included_types", []):
                    if etype and etype != "error":
                        entities[etype]["included_in"].add(inc_type)

            # Anche se non JSON:API, analizza struttura
            if not detail["response_structures"]:
                struct = sanitize_response_body(req["responseBody"])
                if struct:
                    detail["response_structures"].append(struct)

    # Serializza sets
    for key, detail in endpoint_details.items():
        detail["statuses_seen"] = sorted(list(detail["statuses_seen"]))
        detail["triggers"] = sorted(list(detail["triggers"]))
        detail["original_urls"] = detail["original_urls"][:5]  # Max 5 esempi
        for k, v in detail["params_seen"].items():
            detail["params_seen"][k] = sorted(list(v))[:10]  # Max 10 valori

    for etype, edata in entities.items():
        edata["endpoints"] = sorted(list(edata["endpoints"]))
        edata["included_in"] = sorted(list(edata["included_in"]))

    # ===== GENERA OUTPUT =====

    os.makedirs(API_TRACES_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)

    # 1. File per sezione in assets/api-traces/
    print(f"\n[+] Generazione file per sezione in {API_TRACES_DIR}...")

    for section_key in sorted(SECTION_MAPPING.keys()):
        section_info = SECTION_MAPPING[section_key]
        section_reqs = sections.get(section_key, [])

        apis = []
        seen_endpoints = set()

        for idx, req in section_reqs:
            method = req.get("method", "GET")
            norm_path = normalize_path(req["url"])
            endpoint_key = f"{method} {norm_path}"

            # Evita duplicati nello stesso file
            if endpoint_key in seen_endpoints:
                continue
            seen_endpoints.add(endpoint_key)

            detail = endpoint_details.get(endpoint_key, {})
            params = extract_params(req["url"])

            # Struttura response
            response_structure = None
            if detail.get("jsonapi_info"):
                jinfo = detail["jsonapi_info"]
                response_structure = {
                    "is_jsonapi": True,
                    "entity_type": jinfo.get("entity_type"),
                    "is_collection": jinfo.get("is_collection", False),
                    "fields": [f["name"] for f in jinfo.get("fields", [])],
                    "relationships": {r["name"]: r["type"] for r in jinfo.get("relationships", [])},
                    "included_types": jinfo.get("included_types", []),
                    "pagination": jinfo.get("pagination"),
                    "meta": jinfo.get("meta")
                }
            elif detail.get("response_structures"):
                response_structure = detail["response_structures"][0]

            api_entry = {
                "endpoint": norm_path,
                "method": method,
                "trigger": detail.get("triggers", ["unknown"])[0] if detail.get("triggers") else "unknown",
                "request": {
                    "headers": {"Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json"},
                    "params": params if params else None,
                    "body": detail["request_bodies"][0] if detail.get("request_bodies") else None
                },
                "response": {
                    "status": req.get("status", 0),
                    "body_structure": response_structure
                },
                "notes": f"Visto {detail.get('count', 1)} volte. Status osservati: {detail.get('statuses_seen', [])}"
            }
            apis.append(api_entry)

        section_output = {
            "section": section_info["name"],
            "url": section_info["url"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_requests_observed": len(section_reqs),
            "unique_endpoints": len(apis),
            "apis": sorted(apis, key=lambda a: (a["method"], a["endpoint"]))
        }

        output_path = os.path.join(API_TRACES_DIR, f"{section_key}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(section_output, f, indent=2, ensure_ascii=False)
        print(f"    ✓ {output_path} ({len(apis)} endpoint)")

    # 2. Catalogo API (.tmp/api-catalog.json)
    print(f"\n[+] Generazione catalogo API...")

    catalog_endpoints = []
    for endpoint_key, detail in sorted(endpoint_details.items()):
        if detail.get("section"):
            section_name = SECTION_MAPPING.get(detail["section"], {}).get("name", "Altro")
        else:
            section_name = "Non classificato"

        entity = None
        if detail.get("jsonapi_info"):
            entity = detail["jsonapi_info"].get("entity_type")

        # Descrizione auto-generata
        method = detail["method"]
        path = detail["path"]
        desc = f"{method} {path}"
        if entity:
            if method == "GET" and "{id}" not in path:
                desc = f"Lista {entity}"
            elif method == "GET" and "{id}" in path:
                desc = f"Dettaglio {entity}"
            elif method == "POST":
                desc = f"Crea {entity}"
            elif method in ("PUT", "PATCH"):
                desc = f"Aggiorna {entity}"
            elif method == "DELETE":
                desc = f"Elimina {entity}"

        # Response fields
        response_fields = []
        if detail.get("jsonapi_info") and detail["jsonapi_info"].get("fields"):
            response_fields = [f["name"] for f in detail["jsonapi_info"]["fields"]]

        # Relationships
        relationships = {}
        if detail.get("jsonapi_info") and detail["jsonapi_info"].get("relationships"):
            for rel in detail["jsonapi_info"]["relationships"]:
                relationships[rel["name"]] = rel["type"]

        catalog_endpoints.append({
            "method": method,
            "path": path,
            "section": section_name,
            "entity": entity,
            "description": desc,
            "params": sorted(list(detail.get("params_seen", {}).keys())),
            "response_fields": response_fields,
            "relationships": relationships if relationships else None,
            "statuses_seen": detail.get("statuses_seen", []),
            "count": detail.get("count", 1)
        })

    # Entità per il catalogo
    catalog_entities = {}
    for etype, edata in entities.items():
        catalog_entities[etype] = {
            "fields": edata["fields"],
            "relationships": {
                rname: rdata["type"] for rname, rdata in edata["relationships"].items()
            },
            "endpoints": edata["endpoints"],
            "included_in": edata["included_in"]
        }

    catalog = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "base_url": "https://api.sibill.com",
        "auth_type": "cookie (_sibill_key, httpOnly, secure)",
        "api_version": "v1",
        "api_format": "JSON:API (application/vnd.api+json)",
        "total_requests_analyzed": len(api_requests),
        "unique_endpoints": len(endpoint_details),
        "entities_discovered": len(entities),
        "endpoints": sorted(catalog_endpoints, key=lambda e: (e["section"], e["method"], e["path"])),
        "entities": catalog_entities
    }

    catalog_path = os.path.join(TMP_DIR, "api-catalog.json")
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"    ✓ {catalog_path}")

    # 3. Analisi intermedia completa (.tmp/har-analysis.json)
    print(f"\n[+] Generazione analisi completa...")

    analysis = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_requests": len(all_requests),
            "api_requests": len(api_requests),
            "unique_endpoints": len(endpoints_unique),
            "methods": dict(methods),
            "statuses": {str(k): v for k, v in sorted(statuses.items())},
            "entities_discovered": len(entities),
            "sections_coverage": {k: len(v) for k, v in sections.items()},
            "unclassified_count": len(unclassified)
        },
        "unique_endpoints_list": sorted(list(endpoints_unique)),
        "endpoint_details": {k: v for k, v in sorted(endpoint_details.items())},
        "entities": {k: v for k, v in sorted(entities.items())},
        "unclassified_urls": [urlparse(r["url"]).path for r in unclassified[:50]]
    }

    analysis_path = os.path.join(TMP_DIR, "har-analysis.json")
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"    ✓ {analysis_path}")

    # 4. Stampa riepilogo endpoint unici
    print(f"\n{'='*60}")
    print(f"RIEPILOGO ENDPOINT UNICI ({len(endpoints_unique)})")
    print(f"{'='*60}")
    for ep in sorted(endpoints_unique):
        print(f"  {ep}")

    # 5. Stampa riepilogo entità
    print(f"\n{'='*60}")
    print(f"ENTITÀ SCOPERTE ({len(entities)})")
    print(f"{'='*60}")
    for etype, edata in sorted(entities.items()):
        fields_list = ", ".join(sorted(edata["fields"].keys())[:15])
        rels_list = ", ".join(sorted(edata["relationships"].keys()))
        print(f"\n  [{etype}]")
        print(f"    Campi ({len(edata['fields'])}): {fields_list}")
        if rels_list:
            print(f"    Relazioni: {rels_list}")
        if edata["included_in"]:
            print(f"    Incluso con: {', '.join(edata['included_in'])}")

    print(f"\n[+] Fatto! Output generati in:")
    print(f"    - {API_TRACES_DIR}/ (14 file per sezione)")
    print(f"    - {catalog_path}")
    print(f"    - {analysis_path}")

    return analysis


if __name__ == "__main__":
    analysis = main()

# KOMPAS Clinical Reasoning Agent

Een klein, gericht prototype met de OpenAI Agents SDK. Het zet casustekst om in een gestructureerd KOMPAS-rapport met hypothesen, casusconceptualisatie, onderhoudende mechanismen en behandelindicatie.

## Belangrijk

Dit hulpmiddel ondersteunt professioneel klinisch redeneren, maar vervangt geen bevoegde behandelaar, MDO, risicotaxatie, medische beoordeling of verificatie van richtlijnen en bronnen.

## Installatie

```bash
uv sync
```

Zorg dat `OPENAI_API_KEY` beschikbaar is in de omgeving. Optioneel kan `OPENAI_MODEL` worden ingesteld.

## CLI

```bash
uv run python main.py --file data/sample_case.txt
```

Of:

```bash
cat data/sample_case.txt | uv run python main.py
```

## API-server

```bash
PORT=8000 uv run python main.py
```

Controle:

```bash
curl http://127.0.0.1:8000/health
```

Analyse:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"case_text":"Plak hier geanonimiseerde casusinformatie."}'
```

## Privacy

Gebruik in de ontwikkel- en testfase uitsluitend geanonimiseerde of fictieve casusinformatie. Leg vóór productiegebruik vast hoe toestemming, logging, bewaartermijnen, toegangsbeheer, dataminimalisatie en menselijke eindcontrole worden geregeld.

## Word-rapport genereren

De API kan de gestructureerde analyse direct omzetten naar een professioneel Word-document:

```bash
curl -X POST http://127.0.0.1:8000/analyze/docx \
  -H 'Content-Type: application/json' \
  -d '{"case_text":"Plak hier geanonimiseerde casusinformatie."}' \
  --output kompas-rapport.docx
```

Het Word-document bevat hypothesetoetsing, integratieve casusconceptualisatie, de KOMPAS-behandelmatrix, beschermende factoren, risico's en ontbrekende informatie.

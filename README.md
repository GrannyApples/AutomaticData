# AutomaticData

Examensarbete — data engineering. En pipeline som tar emot CSV-, JSON- och
Excel-filer via en Streamlit-frontend, konverterar dem till Parquet och
standardiserar dem till en gemensam struktur (Bronze → Silver → Gold).
Okända attribut och schemaförändringar flaggas i stället för att tappas.
 
> **Frågeställning:** Hur kan en automatiserad pipeline standardisera filer i
> olika format och upptäcka okända attribut och schemaförändringar utan
> dataförlust och med bibehållen spårbarhet?
## Arkitektur
 
```
Upload (Streamlit)
      │
      ▼
   BRONZE   (originalfil + metadata: källa, hash, tid, radantal)
      │  konvertering → Parquet
      ▼
   SILVER   (profilering, mappning mot standardschema, flaggning)
      │  godkända mappningar
      ▼
    GOLD    (dimensionell modell: dim_* + fakta, i DuckDB)
      │
      ▼
  Analys / dashboard (Streamlit)
```
 
Varje lager är en egen, testbar funktion. Bygg hela kedjan för **ett**
filformat (CSV) först, innan JSON och Excel läggs till.
 
---


## Tech stack
 
| Område | Val | Varför |
|---|---|---|
| Språk | Python 3.11+ | Krav från utbildningen, bred paketsupport |
| Tabelldata i minnet | Pandas | Enkelt, väldokumenterat |
| Filformat | PyArrow / Parquet | Kolumnlagring, schema inbyggt, snabbt i DuckDB |
| Analys/SQL | DuckDB | Serverlös, läser Parquet direkt, bra för en ensamutvecklare |
| Frontend | Streamlit | Snabbt att bygga upload + granskningsvyer |
| Miljö | Docker + docker-compose | Reproducerbarhet, lätt att demonstrera |
| Versionshantering | Git/GitHub, branches | Krav från utbildningen |
 
**Medvetet bortvalt i MVP** (motivera i rapporten, inte här): Spark, Snowflake,
Azure, Kafka, PostgreSQL, FastAPI. Se avgränsningar i projektplanen.
 
---
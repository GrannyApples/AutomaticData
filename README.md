# AutomaticData

Examensarbete — data engineering. En pipeline som tar emot CSV-, JSON- och
Excel-filer via en Streamlit-frontend, konverterar dem till Parquet och
standardiserar dem till en gemensam struktur (Bronze(bytes) → Silver(dataframe) → Gold).
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

## Designbeslut: hantera filer som bytes

All inläsning sker som råa bytes (`bytes`) i stället för att direkt
tolka filen till en DataFrame.

**Varför:**
- **Ett gemensamt inputformat.** CSV, JSON, Excel och zip hanteras av
  samma funktioner (hash, dedup, uppackning) utan formatspecifik kod.
- **Bronze bevarar originalet.** Filhashen (SHA-256) beräknas på de
  exakta råbytesen, vilket gör att oförändrad lagring kan bevisas.
- **Streamlit-uppladdningar är redan bytes**, så uppladdning och
  nedladdning från API delar samma kodväg.
- **Testbarhet.** Tester körs i minnet (`io.BytesIO`) utan temporära filer.

**Hur det testas:** varje funktion verifieras i EDA-notebooken med
asserts på bytes, bland annat filsignaturen (magic number) `PK\x03\x04`
som bekräftar att en extraherad fil är en giltig zip-baserad fil
(xlsx är internt ett zip-arkiv). Testdata genereras med Faker och
paketeras som xlsx i zip, på samma sätt som den verkliga källan
Online Retail II levereras, så att samma pipeline-funktioner testas mot
både verklig och genererad data.

**Avvägning:** att arbeta med bytes ger mindre läsbar felsökning än
DataFrames. Det vägs upp av att tolkningen till tabell sker först efter
Bronze, när originalet redan är säkrat.


## Resultat: Bronze-lagret (Online Retail II)

Mätt på källan Online Retail II (UCI, CC BY 4.0), en körning på utvecklingsdatorn.
Siffrorna är en första indikation, inte ett statistiskt underlag.

| Mått | Värde |
|---|---|
| Rader in / ut | 1 067 371 / 1 067 371 (ingen dataförlust) |
| Blad i xlsx | 2 (Year 2009-2010: 525 461 rader, Year 2010-2011: 541 910 rader) |
| Storlek xlsx | 45,6 MB |
| Storlek Parquet (zstd) | 6,06 MB (ca 7,5 gånger mindre) |
| Hämta + packa upp (första gången) | 4,2 s |
| xlsx → Parquet (första gången) | 37,7 s |
| xlsx → Parquet (cache-träff) | 0,0 s (hoppas över) |
| Läsa Parquet-fil från disk (cache) | 42 ms |
| Tolka Parquet till DataFrame | 58 ms |

**Slutsats:** konverteringen kostar ca 38 s en gång per källfil. Därefter tar det
ca 100 ms att få en DataFrame, mot ca 38-40 s om xlsx skulle läsas varje gång.

### Designbeslut i Bronze

- **Originalet sparas orört** i `data/bronze/` med SHA-256, storlek och tidpunkt
  (`<källa>.meta.json`).
- **Hash verifieras vid varje läsning.** Om en Bronze-fil har ändrats stoppas
  körningen i stället för att felaktig data går vidare.
- **Cachen är kopplad till källfilens hash.** Parquet byggs om om källan ändras,
  annars återanvänds den.
- **Blandade datatyper hanteras uttryckligen.** Kolumner som blandar tal och text
  (t.ex. `Invoice` med avbokningskoder som `C489449`) castas till text innan
  Parquet-skrivning, med null bevarade. Kolumner som castades i Retail II:
  `Invoice`, `StockCode`, `Description`. Identifierare är nominala och ska inte
  räknas på, så text är rätt typ.
- **Blad med olika kolumner stoppar körningen** (schema drift), i stället för att
  slås ihop tyst.
- **Konverteringen loggar** rader in/ut, blad, kolumner och castade kolumner.

### Öppna punkter från Bronze

- testa snappy istället för zstd
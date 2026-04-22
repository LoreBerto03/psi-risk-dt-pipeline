# PSI-Risk-DT Pipeline

Pipeline riproducibile per esperimenti di drift detection entropica su dataset sintetici.

Il progetto genera tre scenari sintetici (`stable`, `drift_gradual`, `shock`), li carica in Apache Jena Fuseki, calcola le metriche entropiche su sliding window e produce:

- 15 grafici finali `H(t)` per le configurazioni `C1..C5` sui 3 scenari
- un report testuale con detection time, delay, falsi positivi e peak intensity

## Requisiti

- Docker
- Docker Compose plugin (`docker compose`)

Le dipendenze Python sono già descritte in [`requirements.txt`](requirements.txt), ma per il flusso standard non serve installarle localmente: la pipeline gira dentro il container `pipeline`.

## Esecuzione rapida

Dalla root del repository:

```bash
bash run_all.sh
```

Lo script esegue in sequenza:

1. avvio di Fuseki
2. generazione del dataset sintetico con seed fisso
3. upload RDF su Fuseki
4. calcolo delle entropie su sliding window
5. generazione dei 15 grafici finali
6. esportazione del report testuale

## Configurazione

I parametri principali sono centralizzati in [`Config/config.py`](Config/config.py):

- dataset sintetico: seed, numero punti, rumore, intensita' drift/shock
- sliding window: configurazioni sperimentali esplicite `C1..C5`
- output directory

Parametri principali:

- `C1 = (W=128, stride=1)` configurazione di riferimento
- `C2 = (W=64, stride=1)` effetto window piccola
- `C3 = (W=256, stride=1)` effetto window grande
- `C4 = (W=128, stride=4)` effetto stride medio
- `C5 = (W=128, stride=8)` effetto stride ampio
- `SYNTHETIC_SEED`
- `SYNTHETIC_POINTS_PER_SCENARIO`

## Output generati

Gli output runtime finiscono in `05_Risultati/`:

- `tables/entropy_final.csv`: risultato completo della sliding window
- `tables/raw_points.csv`: segnali sintetici generati
- `figures/entropy/`: solo le 15 immagini finali richieste
- `figures/run_results_summary.txt`: tabella testuale con i risultati dei run

## Struttura del repository

```text
01_Generazione_dati/      dataset sintetico + upload su Fuseki
02_Calcolo_entropie/      implementazioni entropiche
03_Sliding_window/        sliding window e calcolo Delta H
04_Analisi_grafici/       generazione grafici
05_Risultati/             output generati automaticamente
Config/                   configurazione centralizzata e utility
docker/                   compose e immagine del container pipeline
run_all.sh                esecuzione end-to-end
```

## Note

- Gli output intermedi in `05_Risultati/` restano ignorati da Git; vengono versionati solo i deliverable finali curati per tesi/paper.
- La sliding window genera solo le configurazioni richieste dalla griglia sperimentale `C1..C5`, evitando combinazioni extra non previste.
- Il progetto mantiene una pipeline deterministica tramite seed fisso e configurazione centralizzata.
- La cartella `figures/` viene mantenuta minimale: solo le 15 immagini finali e il report `.txt`.

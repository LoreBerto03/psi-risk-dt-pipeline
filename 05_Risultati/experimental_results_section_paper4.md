## 2.1 Experimental Results

### 2.1.1 Recap dell'experimental setup
L'esperimento e stato eseguito su tre scenari sintetici implementati nel codice come `stable`, `drift_gradual` e `shock`. Per allineamento con la notazione di tesi/paper, in questa sezione li indichiamo come: Scenario A (stabile), Scenario B (drift graduale) e Scenario C (shock). Ogni scenario contiene 3000 campioni temporali, con drift attivo in `t=1000..2000` e inizio evento shock in `t=1450`.

La griglia sperimentale comprende cinque configurazioni di sliding window:
- `C1 = (W=128, stride=1)` configurazione di riferimento;
- `C2 = (W=64, stride=1)` finestra piccola;
- `C3 = (W=256, stride=1)` finestra grande;
- `C4 = (W=128, stride=4)` stride medio;
- `C5 = (W=128, stride=8)` stride ampio.

Su ogni finestra sono state calcolate Shannon Entropy, Sample Entropy e Permutation Entropy. Il segnale usato per la detection e `|Delta H|` (variazione assoluta tra finestre consecutive della stessa metrica). Per ogni coppia configurazione-metrica, la soglia di allarme e definita come:
`tau = mean(|Delta H| nello scenario stabile) + 3 * std(|Delta H| nello scenario stabile)`.

Le metriche di valutazione riportate nel summary run sono: detection time (primo superamento soglia dopo l'evento), delay (detection time meno inizio evento), falsi positivi (superamenti soglia prima dell'evento) e picco `peak |Delta H|`.

### 2.1.2 Effetto della finestra W (C2/C1/C3, stride=1)
A stride fissato (`s=1`), il confronto `C2 -> C1 -> C3` mostra un trade-off non lineare tra reattivita e stabilita.

Sul drift (Scenario B), Shannon rileva molto presto con `C1` e `C3` (`delay=12` e `14`), mentre `C2` risulta piu lenta (`delay=36`), cioe un comportamento opposto all'aspettativa "finestra piu piccola = risposta sempre piu rapida". Per Sample, `C2` e la piu rapida (`delay=27`) ma con maggiore attivita spurie pre-evento (`false_pos=32`) rispetto a `C3` (`delay=30`, `false_pos=17`). Per Permutation, `C2` e l'unica configurazione realmente reattiva sul drift (`delay=47`), mentre `C1` e `C3` sono molto ritardate (`delay=369` e `371`).

Sul shock (Scenario C), si osservano comportamenti ancora piu marcati. Shannon passa da `delay=50` in `C1` a `delay=6` in `C2`, ma in `C3` degrada drasticamente (`delay=141`, `false_pos=106`). Sample resta sistematicamente lenta in tutte le finestre (`delay=149..210`). Permutation e estremamente rapida in `C1` (`delay=1`) e ancora buona in `C2` (`delay=5`), ma torna lenta in `C3` (`delay=172`).

Guardando lo scenario stabile (A), `C2` tende a essere la meno stabile: ad esempio Sample passa da `44` falsi positivi in `C1` a `122` in `C2`, con aumento del picco `|Delta H|` da `0.481` a `1.281`. `C3` riduce invece l'intensita dei picchi (es. Shannon `0.034` vs `0.061` in `C1`) ma puo introdurre ritardi importanti sugli eventi rapidi.

In sintesi, la riduzione di `W` aumenta la sensibilita ma puo amplificare la variabilita del segnale (specialmente con Sample), mentre l'aumento di `W` stabilizza l'ampiezza di `|Delta H|` ma rischia ritardi elevati e, in alcuni casi, anche peggioramenti inattesi sui falsi positivi (es. Shannon in shock con `C3`).

### 2.1.3 Effetto dello stride (C1/C4/C5, W=128)
A finestra fissa (`W=128`), l'aumento di stride (`1 -> 4 -> 8`) rende le curve temporalmente piu regolari e meno dense (meno finestre valutate), ma peggiora in generale la granularita temporale della detection.

Sul drift, il delay aumenta per tutte le metriche: Shannon da `12` (`C1`) a `120` (`C4`) e `80` (`C5`); Sample da `75` a `80`; Permutation da `369` a `372` e `376`. Quindi la minore frequenza di aggiornamento penalizza soprattutto la reattivita su cambiamenti graduali.

Sul shock il quadro e misto: per Shannon il delay migliora (`50 -> 6 -> 6`), mentre per Sample e Permutation peggiora (`152 -> 154 -> 158` e `1 -> 10 -> 14`). Questo indica che, su eventi impulsivi, l'effetto stride dipende fortemente dalla metrica.

I falsi positivi diminuiscono nettamente in valore assoluto con stride alto (es. scenario stabile Shannon: `65` in `C1`, `9` in `C4`, `3` in `C5`). Tuttavia, questa lettura va interpretata con cautela: con stride alto il numero di finestre e molto inferiore (`2873` finestre in `C1`, `719` in `C4`, `360` in `C5`), quindi parte della riduzione dipende anche da meno opportunita di falso allarme. Normalizzando per finestre pre-evento, in alcuni casi la stabilita non migliora (es. shock-Permutation: circa `2.9%` in `C1` contro `5.5%` in `C4`).

Nel complesso, lo stride elevato e utile quando il vincolo principale e il costo computazionale e quando si accetta una minore precisione temporale; non e una scelta universalmente migliore sul piano detection.

### 2.1.4 Confronto tra Shannon, Sample e Permutation Entropy
Considerando insieme scenari B e C, Shannon e la metrica mediamente piu reattiva (`delay` medio circa `47`), ma anche la piu "rumorosa" in termini di falsi positivi complessivi (`346`). Sample mostra un comportamento intermedio (`delay` medio circa `111.5`, falsi positivi `187`) con picchi `|Delta H|` molto elevati (media circa `0.678`), segnale di forte sensibilita alle fluttuazioni locali. Permutation e mediamente la meno reattiva (`delay` medio circa `173.7`) ma mantiene picchi molto contenuti (media circa `0.011`), quindi con dinamica piu "compressa".

Per scenario, emergono tre profili distinti:
- Scenario A (stabile): Permutation tende ad avere i picchi piu bassi, ma non e sempre quella con meno falsi positivi; Shannon e spesso la piu incline ad attivazioni spurie.
- Scenario B (drift): Shannon fornisce il miglior compromesso reattivita/ritardo nelle configurazioni a stride basso, mentre Permutation fatica a catturare drift graduali (ritardi molto alti in `C1`/`C3`).
- Scenario C (shock): Permutation puo essere eccellente nel tempo di primo rilevamento (`delay=1` in `C1`), ma il vantaggio non e robusto su tutte le configurazioni; Shannon con `C2/C4/C5` ottiene detection rapida ma con forte dipendenza dalla configurazione.

### 2.1.5 Interpretazione dei trade-off e risultati negativi/ambigui
I risultati confermano che non esiste una configurazione dominante su tutte le dimensioni (detection time, delay, falsi positivi, peak `|Delta H|`). Il trade-off principale e tra:
- reattivita alta (delay basso) con maggiore rischio di instabilita/falsi allarmi;
- stabilita del segnale (`|Delta H|` piu contenuto) con maggiore latenza di detection.

Risultati negativi o ambigui da evidenziare esplicitamente:
- `C2` non e sempre piu reattiva di `C1` (es. Shannon su drift: `delay 36` vs `12`), quindi "finestra piccola" non implica vantaggio sistematico.
- `C3` mostra casi critici su eventi rapidi (es. Shannon su shock: `delay=141`, `false_pos=106`), peggiori del previsto per una configurazione teoricamente piu stabile.
- Per Sample, la forte intensita dei picchi (`peak |Delta H|` fino a `1.373`) non si traduce in detection molto rapida sullo shock (ritardi sempre elevati).
- Aumento stride riduce i falsi positivi assoluti ma puo peggiorare le percentuali normalizzate in alcuni scenari/metriche; quindi il beneficio sulla stabilita non e sempre reale, ma talvolta effetto della minore densita di campionamento.

Operativamente, i dati suggeriscono di usare configurazioni con stride basso quando la priorita e minimizzare il delay su drift; per shock, una scelta competitiva e Shannon con `C2` o Permutation con `C1`, ma con monitoraggio attento dei falsi positivi e della robustezza cross-scenario.

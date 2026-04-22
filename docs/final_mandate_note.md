## Nota Finale Di Mandato

Il lavoro di consolidamento richiesto per le settimane 7-8 e stato completato.
Il repository contiene ora una sezione `Experimental Results` in stile accademico, una nota metodologica dedicata alla Permutation Entropy e una nota di consolidamento scientifico che interpreta l'analisi di sensibilita nei tre scenari A, B e C.
Il pacchetto finale di figure e stato selezionato e organizzato in `results/figures/final/`, con caption tecniche e note interpretative.
La tabella finale pronta per la pubblicazione e stata prodotta sia in formato CSV sia in formato LaTeX in `results/tables/final/`.
Il repository e stato riorganizzato in una struttura riproducibile (`src/`, `configs/`, `results/`, `scripts/`, `docs/`) e il README e stato aggiornato per un valutatore esterno.
Il workflow end-to-end e stato verificato tramite una riesecuzione completa a partire dall'entrypoint principale `bash run_all.sh`, con rigenerazione corretta di figure e tabelle finali. (dopo git clone)

Al momento non risultano aperti punti scientifici o metodologici rilevanti all'interno del perimetro di questo mandato.
L'unico lavoro residuo e di tipo editoriale, non tecnico, e consiste nell'integrazione diretta dei testi, delle figure e delle tabelle nel layout finale della tesi o del paper.

Le seguenti componenti possono gia essere considerate paper-ready:
- il testo `Experimental Results` in `docs/experimental_results_section_paper4.md`;
- il pacchetto finale di figure in `results/figures/final/`;
- la tabella finale pronta per la pubblicazione in `results/tables/final/`;
- la nota metodologica sulla Permutation Entropy in `docs/permutation_entropy_methodological_note.md`.

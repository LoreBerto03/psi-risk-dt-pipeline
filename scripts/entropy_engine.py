import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import os
from scipy.stats import entropy

# 1. Caricamento configurazione centralizzata
with open('config/global_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

SEED = config['reproducibility']['global_seed']
WINDOW_SIZE = config['entropy_axis']['window_size_dt']
THRESHOLD_H = config['entropy_axis']['threshold_h']
BASELINE_SAMPLES = config['entropy_axis']['baseline_samples']

np.random.seed(SEED)

def calculate_shannon_entropy(data):
    """Calcola l'Entropia di Shannon su una finestra di dati."""
    _, counts = np.unique(data, return_counts=True)
    return entropy(counts, base=2)

def evaluate_thresholds(h_values, baseline_mean, attack_start_idx):
    """
    Analizza i falsi positivi e il detection rate al variare della soglia.
    Genera la tabella comparativa per l'Asse 1.
    """
    # Range di soglie da testare (Ablation Analysis)
    test_thresholds = [0.25, 0.50, 0.80, 1.15, 1.50, 2.00]
    results = []
    
    for th in test_thresholds:
        # Un'anomalia viene segnalata se H(t) scende sotto (baseline_mean - th)
        predicted_anomalies = np.array(h_values) < (baseline_mean - th)
        
        # Suddivisione tra zona Baseline (dove ci aspettiamo 0 anomalie) e zona Attacco
        baseline_predictions = predicted_anomalies[:attack_start_idx]
        attack_predictions = predicted_anomalies[attack_start_idx:]
        
        # Metriche
        fp = np.sum(baseline_predictions)  # Falsi Positivi (allarme su traffico normale)
        tn = len(baseline_predictions) - fp
        
        tp = np.sum(attack_predictions)    # Veri Positivi (allarme su attacco reale)
        fn = len(attack_predictions) - tp
        
        fpr = (fp / (fp + tn)) * 100 if (fp + tn) > 0 else 0
        tpr = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0
        
        results.append({
            'Soglia_H': th,
            'Falsi_Positivi_FP': fp,
            'FP_Rate_%': round(fpr, 2),
            'Veri_Positivi_TP': tp,
            'Detection_Rate_%': round(tpr, 2)
        })
        
    # Salvataggio in DataFrame e CSV
    df = pd.DataFrame(results)
    os.makedirs('results/tables', exist_ok=True)
    csv_path = 'results/tables/threshold_analysis.csv'
    df.to_csv(csv_path, index=False)
    print(f"Tabella comparativa generata con successo: {csv_path}")
    print("\nAnteprima Tabella (Analisi Soglie):")
    print(df.to_string(index=False))
    
    return df

def main():
    print("Avvio elaborazione Entropia (Sliding Window)...")
    
    # 2. Simulazione del flusso (Baseline vs Attacco OOD)
    baseline_len = 500
    baseline_data = np.random.choice(['GET', 'POST', 'PUT'], size=baseline_len, p=[0.7, 0.2, 0.1])
    attack_data = np.random.choice(['GET', 'POST', 'PUT'], size=200, p=[0.33, 0.33, 0.34])
    full_stream = np.concatenate([baseline_data, attack_data])
    
    # 3. Implementazione Sliding Window
    h_values = []
    for i in range(len(full_stream) - WINDOW_SIZE):
        window = full_stream[i : i + WINDOW_SIZE]
        h_values.append(calculate_shannon_entropy(window))
    
    # 4. Calcolo ∆H rispetto alla baseline
    h_series = pd.Series(h_values)
    baseline_mean = h_series[:BASELINE_SAMPLES].mean()
    
    # --- NOVITA': Generazione Tabella Falsi Positivi ---
    # L'attacco inizia quando la finestra esce completamente dalla zona baseline
    attack_start_idx = baseline_len - WINDOW_SIZE 
    evaluate_thresholds(h_values, baseline_mean, attack_start_idx)
    # ---------------------------------------------------
    
    # 5. Produzione Grafico H(t)
    plt.figure(figsize=(10, 5))
    plt.plot(h_values, label='H(t) Entropia misurata', color='blue')
    plt.axhline(y=baseline_mean, color='green', linestyle='-', label='Baseline calibrata')
    plt.axhline(y=baseline_mean - THRESHOLD_H, color='red', linestyle='--', label=f'Soglia Operativa (\u03B8H={THRESHOLD_H})')
    
    # Evidenziamo la zona di attacco
    plt.axvspan(attack_start_idx, len(h_values), color='red', alpha=0.1, label='Finestra Attacco OOD')
    
    plt.title("Analisi Entropica su Flusso Simulato (Sliding Window)")
    plt.xlabel("Tempo (indice finestra)")
    plt.ylabel("Entropia di Shannon (bits)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs('results/figures', exist_ok=True)
    plt.savefig('results/figures/entropy_drift.png')
    print("Grafico H(t) generato in results/figures/entropy_drift.png")

if __name__ == "__main__":
    main()
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

m = 5.4              
cp = 900.0           
sigma = 5.67e-8      
eps = 0.80           
A = 1.0              
Gs = 1418.0          
alpha = 0.14         

T_nom_C = -22.0
T_nom_K = T_nom_C + 273.15
Q_in = sigma * eps * A * (T_nom_K**4)

def cooling_model(T, t):
    return (Q_in - sigma * eps * A * (T**4)) / (m * cp)


t_exp_minutes_list = [20.0, 15.0, 10.0, 6.0, 3.0] 

t_sim = np.linspace(0, 7200, 1000) 
plt.figure(figsize=(12, 7))

colors = ['#d73027', '#fc8d59', '#fee090', '#91bfdb', '#4575b4']

for i, t_exp_min in enumerate(t_exp_minutes_list):
    
    t_exp_sec = t_exp_min * 60.0
    
    T_start_C = T_nom_C + (t_exp_sec * Gs * alpha * A) / (m * cp)
    
    T_start_K = T_start_C + 273.15
    T_res_K = odeint(cooling_model, T_start_K, t_sim)
    T_res_C = T_res_K.flatten() - 273.15
    
    label_str = f"Exposition {t_exp_min} min -> Chauffe à {T_start_C:.1f} °C"
    plt.plot(t_sim / 60.0, T_res_C, color=colors[i], linewidth=2.5, label=label_str)

plt.axhline(y=T_nom_C, color='black', linestyle='--', linewidth=1.5, 
            label=f"Équilibre nominal ({T_nom_C} °C)")
plt.axhline(y=-10.0, color='green', linestyle=':', linewidth=2, 
            label="Seuil 'Prêt pour opération' GNC (-10 °C)")

plt.title("Abaque de Récupération selon le Temps d'Exposition", fontsize=16, fontweight='bold')
plt.xlabel("Temps de refroidissement (minutes)", fontsize=13)
plt.ylabel("Température du Radiateur (°C)", fontsize=13)
plt.grid(True, which='both', linestyle='--', alpha=0.6)
plt.legend(fontsize=11, loc='upper right')
plt.xlim(0, 120)
plt.ylim(-25, 35)

plt.tight_layout()
plt.show()
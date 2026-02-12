import matplotlib.pyplot as plt
import numpy as np

# Constants
sigma = 5.67e-8
Area_rad = 0.60
eps_rad = 0.80
Mass = 14.0 # kg
Cp = 900 # J/kgK

# Temperatures (Kelvin)
T_nominal = 25.0 + 273.15 # 298.15 K
T_recovery_target = 25.1 + 273.15 # Target for "Recovery" (0.1 deg margin)

# Loads
Q_diss = 117.5
Q_env_nominal = 70.9 + 25.8 # Sun Leak + Earth Leak
Q_in_nominal = Q_diss + Q_env_nominal # 214.2 W

# Maneuver Load
# Radiator faces Sun (119.1 W absorbed)
# + Internal (117.5 W)
# + Remaining Earth Leaks (approx 25.8 W)
Q_in_maneuver = 119.1 + 117.5 + 25.8 # 262.4 W

def get_recovery_time(maneuver_duration_minutes):
    dt = 1.0 # seconds
    
    # 1. Heating Phase
    current_T = T_nominal
    maneuver_duration_s = maneuver_duration_minutes * 60
    
    for t in np.arange(0, maneuver_duration_s, dt):
        Q_out = sigma * eps_rad * Area_rad * (current_T**4)
        Q_net = Q_in_maneuver - Q_out
        dTemp = (Q_net * dt) / (Mass * Cp)
        current_T += dTemp
        
    T_peak = current_T
    
    # 2. Cooling Phase
    recovery_time_s = 0
    while current_T > T_recovery_target:
        Q_out = sigma * eps_rad * Area_rad * (current_T**4)
        Q_net = Q_in_nominal - Q_out # Negative value
        dTemp = (Q_net * dt) / (Mass * Cp)
        current_T += dTemp
        recovery_time_s += dt
        
        if recovery_time_s > 50000: # Safety break
            break
            
    return recovery_time_s / 60.0 # Return minutes

# Run Simulations
durations = np.arange(1, 46, 1) # 1 to 45 minutes
recovery_times = [get_recovery_time(d) for d in durations]

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(durations, recovery_times, marker='o', linestyle='-', color='#007acc')
plt.title('Temps de Récupération Thermique vs Durée de Manœuvre\n(Retour à T_nominale + 0.1°C)', fontsize=14)
plt.xlabel('Durée de la Manœuvre (minutes)', fontsize=12)
plt.ylabel('Temps de Récupération (minutes)', fontsize=12)
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.axvline(x=20, color='r', linestyle='--', label='Manœuvre Standard (20 min)')
plt.legend()
plt.tight_layout()

# Save plot
plt.savefig('recovery_time_graph.png')
plt.show()

# Print some key values for the text response
print(f"Recovery for 10 min: {get_recovery_time(10):.1f} min")
print(f"Recovery for 20 min: {get_recovery_time(20):.1f} min")
print(f"Recovery for 30 min: {get_recovery_time(30):.1f} min")
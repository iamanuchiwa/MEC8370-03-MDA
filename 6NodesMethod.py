import numpy as np

# =============================================================================
# PARAMETRES & CONSTANTES
# =============================================================================
SIGMA = 5.67e-8  # Constante Stefan-Boltzmann

# Géométrie (Cube 1U+ / 1m3)
L_SAT = 1.044  # m
A_FACE = L_SAT**2  # 1.09 m2
A_TOTAL_EXT = 6 * A_FACE  # 6.54 m2
MASS_THERMAL = 10.0  # kg (Masse thermique participant au transitoire)
CP_ALU = 900.0  # J/kg.K

# Dissipation Interne
Q_DISS_HOT = 117.5  # W
Q_DISS_COLD = 20.0  # W (Safe Mode)

# Environnement (LEO Dusk-Dawn 600km)
# Worst Case Hot
GS_HOT = 1418.0  # W/m2
IR_EARTH_HOT = 258.0  # W/m2
ALBEDO_HOT = 0.35

# Propriétés Optiques (EOL = Hot Case, BOL = Cold Case/Transient start)
# Radiateur OSR
ALPHA_OSR_EOL = 0.12
ALPHA_OSR_BOL = 0.08
EPS_OSR = 0.80

# MLI (Haute Performance)
EPS_EFF_MLI = 0.03
ALPHA_MLI = 0.50  # Face externe Kapton vieillissante
EPS_MLI_EXT = 0.80

# Cellules Solaires (+Y)
ALPHA_SC = 0.92
EPS_SC = 0.85

# Températures Cibles
T_TARGET_HOT = 25.0 + 273.15  # 25°C
T_TARGET_COLD = 0.0 + 273.15  # 0°C

# =============================================================================
# PARTIE 1 : ANALYSE STATIQUE 6 NOEUDS (HOT CASE)
# =============================================================================
print("--- RESULTATS ANALYSE 6 NOEUDS (HOT CASE) ---")

# Flux incidents estimés par face (Dusk-Dawn)
# +Y = Soleil, -Z = Radiateur, Autres = Ombre/Terre rase
flux_inputs = {
    '+Y (Sun)':    {'Solar': GS_HOT, 'IR': 0.0},        # Face Soleil
    '+Z (Nadir)':  {'Solar': 0.0,    'IR': IR_EARTH_HOT}, # Face Terre
    '-Y (Anti-Sun)': {'Solar': 0.0,  'IR': 40.0},       # Faible IR
    '+X (Vel)':    {'Solar': 0.0,    'IR': 60.0},       # IR rasant
    '-X (Anti-Vel)': {'Solar': 0.0,  'IR': 60.0},       # IR rasant
    '-Z (Zenith)': {'Solar': 0.0,    'IR': 0.0}         # Espace profond (Radiateur)
}

net_env_heat_balance = 0.0  # Bilan total des gains/pertes environnementaux

for face, fluxes in flux_inputs.items():
    if face == '-Z (Zenith)':
        continue # On traite le radiateur séparément

    # Choix des propriétés
    if '+Y' in face:
        alpha, eps = ALPHA_SC, EPS_SC # Panneaux solaires
        type_face = "Solar Array"
    else:
        alpha, eps = ALPHA_MLI, EPS_MLI_EXT # MLI
        type_face = "MLI"

    # 1. Flux absorbé par la peau externe
    q_abs = alpha * fluxes['Solar'] + eps * fluxes['IR']

    # 2. Température d'équilibre de la peau (Skin Temp)
    # Bilan: q_abs + q_leak_from_internal = q_emit
    # q_leak = sigma * eps_eff * (T_int^4 - T_skin^4)
    # Equation: q_abs + sigma*eps_eff*T_int^4 = sigma*(eps_ext + eps_eff)*T_skin^4
    
    lhs = q_abs + SIGMA * EPS_EFF_MLI * (T_TARGET_HOT**4)
    rhs_coeff = SIGMA * (eps + EPS_EFF_MLI)
    T_skin = (lhs / rhs_coeff)**0.25
    
    # 3. Fuite thermique vers l'intérieur (si +) ou perte vers l'extérieur (si -)
    # Q_leak = A_FACE * sigma * eps_eff * (T_skin^4 - T_int^4)
    # Note: Dans le rapport on calcule souvent T_int^4 - T_skin^4 (Perte).
    # Ici: positif = gain de chaleur pour le satellite
    q_leak_total = A_FACE * SIGMA * EPS_EFF_MLI * (T_skin**4 - T_TARGET_HOT**4)
    
    net_env_heat_balance += q_leak_total
    
    print(f"Face {face}: T_skin = {T_skin-273.15:.1f} °C, Net Heat Flow = {q_leak_total:.2f} W")

print(f"--> Bilan Environnemental Net (Hors Radiateur) : {net_env_heat_balance:.2f} W")

# Dimensionnement Radiateur
# Le radiateur doit rejeter : Dissipation + (ou -) Bilan Environnemental
Q_TO_REJECT = Q_DISS_HOT + net_env_heat_balance
# Capacité de rejet par m2 (Face Zenith = 0 flux incident)
q_rejection_capacity = SIGMA * EPS_OSR * T_TARGET_HOT**4

A_RAD_REQ = Q_TO_REJECT / q_rejection_capacity

print(f"--> Puissance Totale à Rejeter : {Q_TO_REJECT:.2f} W")
print(f"--> Surface Radiateur Requise : {A_RAD_REQ:.4f} m2")
print("------------------------------------------------\n")


# =============================================================================
# PARTIE 2 : ANALYSE COLD CASE (HEATERS)
# =============================================================================
print("--- RESULTATS COLD CASE (SAFE MODE) ---")

# Hypothèse : T_sat = 0°C, Pas de soleil (Safe Mode Dark)
# Pertes par le Radiateur (Surface fixée par Hot Case)
Q_LOSS_RAD = A_RAD_REQ * SIGMA * EPS_OSR * T_TARGET_COLD**4

# Pertes par le MLI (Surface restante)
A_MLI_REMAINING = A_TOTAL_EXT - A_RAD_REQ
Q_LOSS_MLI = A_MLI_REMAINING * SIGMA * EPS_EFF_MLI * T_TARGET_COLD**4

TOTAL_LOSS = Q_LOSS_RAD + Q_LOSS_MLI
HEATERS_REQ = TOTAL_LOSS - Q_DISS_COLD

print(f"Pertes Radiateur ({A_RAD_REQ:.2f} m2) : {Q_LOSS_RAD:.2f} W")
print(f"Pertes MLI ({A_MLI_REMAINING:.2f} m2) : {Q_LOSS_MLI:.2f} W")
print(f"Pertes Totales : {TOTAL_LOSS:.2f} W")
print(f"Besoin Heaters (avec 20W dissipation) : {HEATERS_REQ:.2f} W")
print("------------------------------------------------\n")


# =============================================================================
# PARTIE 3 : ANALYSE TRANSITOIRE (10 MIN MANOEUVRE)
# =============================================================================
print("--- RESULTATS ANALYSE TRANSITOIRE (10 MIN) ---")

# Paramètres
DURATION = 10 * 60  # secondes
DT = 1.0  # pas de temps
T_current = 25.0 + 273.15 # Init à 25°C

# Boucle temporelle
times = []
temps = []

for t in np.arange(0, DURATION, DT):
    # 1. Chaleur Entrante (Dissipation + Soleil sur Radiateur)
    # On utilise Alpha EOL (0.12) pour le pire cas chaud
    Q_in_solar = GS_HOT * A_RAD_REQ * ALPHA_OSR_EOL
    Q_in_total = Q_DISS_HOT + Q_in_solar
    
    # 2. Chaleur Sortante (Rejet radiatif)
    Q_out = A_RAD_REQ * SIGMA * EPS_OSR * T_current**4
    
    # 3. Bilan Net
    Q_net = Q_in_total - Q_out
    
    # 4. Hausse de Température (Inertie)
    # Q = m * Cp * dT/dt  => dT = (Q_net * dt) / (m * Cp)
    dT = (Q_net * DT) / (MASS_THERMAL * CP_ALU)
    
    T_current += dT
    
    times.append(t)
    temps.append(T_current - 273.15)

print(f"Température Initiale : {temps[0]:.2f} °C")
print(f"Température Finale (10 min) : {temps[-1]:.2f} °C")
print(f"Delta T : +{temps[-1] - temps[0]:.2f} °C")

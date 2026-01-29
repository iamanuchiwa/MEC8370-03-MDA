import numpy as np

# Constants
sigma = 5.67e-8
T_sat_hot = 25 + 273.15
T_sat_cold = 0 + 273.15

# Geometry
L = 1.044
A_face = L**2 # 1.09

# Fluxes
Gs_hot = 1418
IR_hot = 258
Alb_hot = 0.35

Gs_cold = 1322
IR_cold = 216

# Materials
eps_eff_MLI = 0.03
alpha_MLI_EOL = 0.50
eps_MLI_ext = 0.80

alpha_OSR_EOL = 0.12
eps_OSR = 0.80

alpha_SC = 0.92
eps_SC = 0.85

# Matching Keys
faces = ['+Z (Nadir)', '-Z (Zenith)', '+Y (Sun)', '-Y (Anti-Sun)', '+X (Vel)', '-X (Anti-Vel)']

flux_hot = {
    '+Z (Nadir)': {'Sun': 0, 'Earth': IR_hot * 0.85, 'Albedo': Gs_hot * Alb_hot * 0.15},
    '-Z (Zenith)': {'Sun': 0, 'Earth': 0, 'Albedo': 0},
    '+Y (Sun)':   {'Sun': Gs_hot, 'Earth': IR_hot * 0.15, 'Albedo': Gs_hot * Alb_hot * 0.05},
    '-Y (Anti-Sun)': {'Sun': 0, 'Earth': IR_hot * 0.15, 'Albedo': 0},
    '+X (Vel)':   {'Sun': 0, 'Earth': IR_hot * 0.15, 'Albedo': Gs_hot * Alb_hot * 0.05},
    '-X (Anti-Vel)': {'Sun': 0, 'Earth': IR_hot * 0.15, 'Albedo': Gs_hot * Alb_hot * 0.05}
}

# 1. Calculate Skin Temps and Leaks per Face (HOT)
results_hot = {}
total_leak_5faces = 0

print("--- 6-NODE FACE BALANCE (HOT CASE) ---")
for face in faces:
    f = flux_hot[face]
    Q_solar = f['Sun'] + f['Albedo']
    Q_ir = f['Earth']
    Q_inc = Q_solar + Q_ir
    
    # Determine type
    if 'Zenith' in face:
        # Radiator Face (Special handling later)
        # Calculate Potential Leak if it was MLI (for the non-rad part)
        alpha, eps = alpha_MLI_EOL, eps_MLI_ext
        type_f = 'Radiator/MLI'
    elif 'Sun' in face and 'Anti' not in face: # +Y
        # Solar Panel
        alpha, eps = alpha_SC, eps_SC
        type_f = 'Solar Array'
    else:
        # MLI
        alpha, eps = alpha_MLI_EOL, eps_MLI_ext
        type_f = 'MLI'
        
    # Absorbed on Skin
    Q_abs_skin = alpha * Q_solar + eps * Q_ir
    
    # Solve T_skin equilibrium
    # Q_abs + Q_leak_from_sat = Q_emit
    # Q_abs + sigma*eps_eff*(T_sat^4 - T_skin^4) = sigma*eps*T_skin^4
    # Note: Using eps_eff for coupling
    
    lhs = sigma * (eps + eps_eff_MLI)
    rhs = Q_abs_skin + sigma * eps_eff_MLI * T_sat_hot**4
    T_skin = (rhs / lhs)**0.25
    
    # Leak INTO Sat
    Q_leak_density = sigma * eps_eff_MLI * (T_skin**4 - T_sat_hot**4)
    Q_leak_total = Q_leak_density * A_face
    
    results_hot[face] = {
        'Q_inc': Q_inc,
        'Q_abs_skin': Q_abs_skin,
        'T_skin_C': T_skin - 273.15,
        'Q_leak_W': Q_leak_total,
        'q_leak_m2': Q_leak_density
    }
    
    if 'Zenith' not in face:
        total_leak_5faces += Q_leak_total
        print(f"{face} ({type_f}): Inc={Q_inc:.1f} W/m2, T_skin={T_skin-273.15:.1f}C, Leak={Q_leak_total:.2f} W")

# 2. Sizing Radiator on Zenith Face
# Equation: A_rad * q_net_rad + (A_face - A_rad) * q_leak_zenith = Q_diss + Q_leak_5faces
# q_net_rad = Capacity - Absorbed_on_Rad
# Absorbed_on_Rad (Zenith) = alpha_OSR * Solar + eps_OSR * IR
# Zenith fluxes are 0 usually, but let's be rigorous
f_z = flux_hot['-Z (Zenith)']
q_abs_rad = alpha_OSR_EOL * (f_z['Sun'] + f_z['Albedo']) + eps_OSR * f_z['Earth']
q_emit_rad = sigma * eps_OSR * T_sat_hot**4
q_net_rad = q_emit_rad - q_abs_rad

q_leak_zenith_MLI = results_hot['-Z (Zenith)']['q_leak_m2'] # Leak density if MLI
# Note: q_leak_zenith_MLI is likely negative (Heat loss) or near zero since Zenith sees 0 flux
# T_skin zenith MLI will be low.
# Let's check:
# Zenith Q_inc = 0. T_skin equilibrium with T_sat=25C.
# T_skin will be < 25C. Heat flows OUT. Q_leak is negative.
# This helps the radiator!

Q_diss = 117.5
# A_rad * q_net + A_face * q_leak - A_rad * q_leak = Q_total
# A_rad * (q_net - q_leak) = Q_diss + Q_leak_5 + A_face * q_leak
# Note: q_leak is negative (loss). So A_face*q_leak is a relief.
# q_net is positive (rejection).

numerator = Q_diss + total_leak_5faces - (A_face * q_leak_zenith_MLI)
denominator = q_net_rad - q_leak_zenith_MLI
A_rad_req = numerator / denominator

print(f"\n--- RADIATOR SIZING ---")
print(f"Internal Dissipation: {Q_diss} W")
print(f"Sum Leaks (5 Faces): {total_leak_5faces:.2f} W")
print(f"Zenith MLI Leak Density: {q_leak_zenith_MLI:.2f} W/m2")
print(f"Radiator Net Capacity: {q_net_rad:.2f} W/m2")
print(f"Radiator Area Required: {A_rad_req:.4f} m2")

# 3. Cold Case Check
# Assume A_rad fixed.
# Calculate Heaters.
print(f"\n--- COLD CASE CHECK (A_rad={A_rad_req:.2f} m2) ---")
# Fluxes = 0 (Dark).
# T_sat = 0C.
# Leak density for MLI with 0 flux:
# T_skin = T_sat * (eps_eff / (eps_ext + eps_eff))^0.25
ratio = eps_eff_MLI / (eps_MLI_ext + eps_eff_MLI)
T_skin_cold = T_sat_cold * (ratio**0.25)
q_leak_cold = sigma * eps_eff_MLI * (T_skin_cold**4 - T_sat_cold**4) # Negative (Loss)

# Total MLI Loss (from all MLI areas)
# Area_MLI = A_total - A_rad
A_total = 6 * A_face
A_MLI_total = A_total - A_rad_req
Q_loss_MLI = A_MLI_total * abs(q_leak_cold)

# Radiator Loss
# Q_rad = A_rad * sigma * eps * T_sat^4 (Into 0K)
Q_loss_Rad = A_rad_req * sigma * eps_OSR * T_sat_cold**4

Q_safe = 20.0
Q_heaters = Q_loss_Rad + Q_loss_MLI - Q_safe

print(f"Radiator Loss: {Q_loss_Rad:.2f} W")
print(f"MLI Loss: {Q_loss_MLI:.2f} W")
print(f"Heater Power: {Q_heaters:.2f} W")
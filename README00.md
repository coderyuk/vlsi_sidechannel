# Automated SPICE Characterization of CMOS Technology Scaling & Side-Channel Power Leakage

**Course:** VLSI Technology (`EC-214`)  
**Topic:** Analysis of MOSFET Technology Scaling (180nm to 22nm), Fabrication Parameter Characterization, and Differential Power Analysis (DPA) Side-Channel Leakage  
**Simulator & Stack:** Ngspice (SPICE3f5 Engine), Python 3, NumPy, Matplotlib

---

## 1. Project Overview & Syllabus Alignment (`EC-214`)

This project is an automated Electronic Design Automation (EDA) testbench written in Python that interfaces with the **Ngspice** circuit simulator. It characterizes how physical semiconductor fabrication parameters—specifically channel length (`L`), gate oxide thickness (`t_ox`), threshold voltage (`V_th`), and junction capacitances (`C_j`)—behave when scaled across four historical technology nodes: **180nm, 90nm, 45nm, and 22nm**.

To evaluate the physical impact of miniaturization on real CMOS circuits, the framework simulates a **12-Transistor Static CMOS XOR Gate** and analyzes how scaling affects both **Static Subthreshold Leakage** and **Dynamic Switching Power**, demonstrating how these physical phenomena create hardware security vulnerabilities known as **Differential Power Analysis (DPA) Side-Channel Attacks**.

### Direct Mapping to `EC-214` Syllabus

- **UNIT-01 (Miniaturization & Characterization):** Evaluates the electrical characterization impact of shrinking MOSFET feature sizes from the sub-micron regime (`180 nm`) into the deep nano-regime (`22 nm`).
- **UNIT-02 (Monolithic Fabrication Techniques):** Models the direct electrical consequences of physical fabrication stages:
  - **Oxidation:** Shrinking gate oxide thickness (`t_ox` from `4.0 nm` → `0.9 nm`) and its impact on oxide capacitance (`C_ox`) and gate-oxide quantum tunneling.
  - **Lithography & Etching:** Defining smaller critical dimensions (channel length `L`) and accounting for Short Channel Effects (SCE).
  - **Diffusion & Ion Implantation:** Adjusting channel doping profiles and substrate bias (`gamma`, `phi`) to control threshold voltage (`V_th`) and source/drain junction capacitance (`C_j`, `C_jsw`).
- **UNIT-05 (Monolithic Components - Prototype Fabrication):** Constructs complementary n-MOS and p-MOS enhancement-mode structures into a functional 12-transistor CMOS logic circuit.
- **Course Outcomes (`CO1`, `CO2`, `CO5`):** Directly addresses **CO2** (_Describe the analysis of technology scaling_) and **CO5** (_Assess reliability and security issues in VLSI technology_).

---

## 2. Theoretical Foundation & VLSI Physics

### 2.1 Dennard Scaling vs. Deep Sub-Micron Breakdown

In 1974, Robert Dennard proposed that if transistor dimensions (`W`, `L`, `t_ox`) and supply voltage (`V_dd`) are scaled down by a constant factor `k` (where `k > 1`), and doping concentration (`N_a`) is increased by `k`, the internal electric field remains constant and **power density stays constant**:

| Physical Parameter     |              Symbol              | Dennard Scaling Factor | Practical Nano-Regime Reality (< 90nm)                        |
| :--------------------- | :------------------------------: | :--------------------: | :------------------------------------------------------------ |
| Channel Length & Width |             `L`, `W`             |        `1 / k`         | Scaled aggressively via EUV/ArF Lithography                   |
| Gate Oxide Thickness   |              `t_ox`              |        `1 / k`         | Hits physical atomic limit (~0.9 nm, ~4 Silicon atoms)        |
| Supply Voltage         |              `V_dd`              |        `1 / k`         | Cannot scale below ~0.7 V without losing noise margin         |
| Threshold Voltage      |              `V_th`              |        `1 / k`         | Lowering `V_th` causes **exponential** subthreshold leakage   |
| Gate Capacitance       |  `C_g = (e_ox * W * L) / t_ox`   |        `1 / k`         | Dominated by fringing & parasitic wire capacitances           |
| Dynamic Power per Gate | `P_dyn = α * C_load * V_dd² * f` |        `1 / k²`        | Scales down, but total chip power rises due to static leakage |

Around the **90nm–45nm** nodes, Dennard Scaling broke down because reducing `V_dd` required lowering `V_th` to maintain switching speed. However, lowering `V_th` prevents the MOSFET from turning completely OFF when the gate voltage is `0 V`.

---

### 2.2 Short Channel Effects (SCE) & Static Leakage Equations

When the physical channel length `L` becomes comparable to the depletion-layer widths of the source and drain junctions, the gate loses electrostatic control over the channel:

#### 1. Subthreshold Conduction (Weak Inversion Leakage)

Even when `V_gs < V_th` (transistor is supposed to be OFF), diffusion current still leaks between source and drain:

```text
I_sub = I_0 * (W / L) * exp( (V_gs - V_th) / (n * V_T) ) * ( 1 - exp(-V_ds / V_T) )
```

- `V_T = k*T / q ≈ 25.85 mV` at room temperature (`300 K`).
- `n` = subthreshold swing factor.
- **Key Takeaway:** Because `V_th` is inside the exponent `exp(...)`, reducing `V_th` from `0.42 V` (`180 nm`) down to `0.15 V` (`22 nm`) causes `I_sub` to increase exponentially (by `500x` in our simulation).

#### 2. Drain-Induced Barrier Lowering (DIBL)

At tiny channel lengths, high drain voltage (`V_ds`) electrostatically lowers the potential barrier at the source, effectively reducing `V_th` even further:

```text
V_th(effective) = V_th0 - (η * V_ds)
```

#### 3. Channel Length Modulation (`λ` / `lambda`)

As `V_ds` increases in saturation, the depletion region at the drain widens, shortening the effective channel length (`L_eff = L - ΔL`). In SPICE, this is modeled via `lambda` (`λ`):

```text
I_d(sat) = 0.5 * μ * C_ox * (W / L) * (V_gs - V_th)² * (1 + λ * V_ds)
```

As `L` shrinks from `180 nm` to `22 nm`, `λ` increases from `0.04 V⁻¹` to `0.25 V⁻¹`.

#### 4. Gate Oxide Quantum Tunneling (`I_ox`)

When thermal oxidation grows an `SiO2` insulation layer thinner than `1.5 nm` (at `45 nm` and `22 nm` nodes), electrons quantum-mechanically tunnel directly through the gate oxide via Fowler-Nordheim and direct tunneling. This forced the semiconductor industry to transition to **High-k Metal Gates (HKMG)** and **3D FinFETs**.

---

### 2.3 Total CMOS Power Dissipation Equation

The total instantaneous power drawn from the power supply (`V_dd`) by any CMOS gate is the sum of three distinct physical mechanisms:

```text
P_total = P_dynamic + P_short_circuit + P_static

P_total = (α * C_load * V_dd² * f_clk)  +  (I_sc * V_dd)  +  (I_leakage * V_dd)
          \__________________________/     \___________/     \________________/
           Charging/Discharging C_load      PMOS & NMOS       Subthreshold +
                                            ON Together       Gate Tunneling
```

---

### 2.4 Hardware Security Logic: Why CMOS XOR Leaks the Secret Key

In cryptographic hardware (AES S-Boxes, stream ciphers, one-time pads), a known input **Plaintext bit (`A`)** is combined with a secret internal **Key bit (`B`)** using an exclusive-OR (**XOR**) operation:

```text
Output Y = A ⊕ B = (A AND NOT(B)) OR (NOT(A) AND B)
```

#### The Asymmetric Switching Physics

Suppose the attacker flips the Plaintext input `A` from **`0` → `1`** at time `t = 1.0 ns` while the secret Key bit `B` remains static inside the hardware register:

| Secret Key (`B`) | Initial State (`t < 1.0 ns`) | Final State (`t > 1.0 ns`) |       Output Transition (`Y`)       | Physical Current Path Inside the CMOS Circuit                                                                                                                                                                                                 | Current Drawn from `V_dd` (`I_dd`)                                 |
| :--------------: | :--------------------------: | :------------------------: | :---------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------- |
|  **`Key = 0`**   |       `A=0, B=0 → Y=0`       |      `A=1, B=0 → Y=1`      |  **`0` → `1` (Charges `C_load`)**   | The PMOS Pull-Up Network turns **ON**, creating a path from **`V_dd` to `out`**. Current rushes out of the `V_dd` power rail to charge the `8 fF` load capacitor from `0 V` to `V_dd`.                                                        | **Large Positive Spike** (`182.49 μA` at 180nm)                    |
|  **`Key = 1`**   |       `A=0, B=1 → Y=1`       |      `A=1, B=1 → Y=0`      | **`1` → `0` (Discharges `C_load`)** | `C_load` is _already_ charged to `V_dd` before `1.0 ns`. When `A` flips to `1`, the NMOS Pull-Down Network turns **ON** and dumps the stored capacitor charge directly to **Ground (`0 V`)**. No load-charging current is pulled from `V_dd`! | **Small Spike** (`91.86 μA` at 180nm — only short-circuit current) |

#### Frequently Asked Viva Questions on the Waveforms:

1. **Why is there still a smaller spike when `Key = 1` if `C_load` discharges to Ground?**
   - **Crowbar / Short-Circuit Current (`I_sc`):** During the `0.08 ns` rise time of input `A`, when the input voltage passes through `V_dd / 2`, both PMOS and NMOS transistors are momentarily partially ON at the same time, creating a brief direct path from `V_dd` to Ground.
   - **Internal Input Inverter (`M1/M2`):** The internal node `a_bar` transitions from `1` → `0`, drawing a small switching current.
2. **Why is there a brief negative current dip right at `t = 1.0 ns` before the positive spike?**
   - **Miller Capacitive Feedthrough (Gate-to-Drain Overlap Capacitance):** When input `A` rises rapidly (`0.08 ns`), capacitive coupling across the PMOS gate-to-drain overlap pushes a tiny packet of charge backward into the `V_dd` rail before the transistor channel finishes inverting.

---

## 3. Circuit Topology (12-Transistor Static CMOS XOR)

Our SPICE netlist constructs a full static CMOS XOR gate:

```text
                  Vdd
                   |
         +---------+---------+
         |                   |
      [ M5 ] pmos (A)     [ M7 ] pmos (A_bar)
         |                   |
        (n1)                (n2)
         |                   |
      [ M6 ] pmos (B_bar) [ M8 ] pmos (B)
         |                   |
         +---------+---------+
                   |
                   +--------------------> OUT ----+--- C_load (8fF)
                   |                              |
         +---------+---------+                   GND
         |                   |
      [ M10] nmos (B)     [ M12] nmos (B_bar)
         |                   |
        (n3)                (n4)
         |                   |
      [ M9 ] nmos (A)     [ M11] nmos (A_bar)
         |                   |
         +---------+---------+
                   |
                  GND

  * Plus Input Inverters:
    - M1 (PMOS) & M2 (NMOS): Inverters Input A -> A_bar
    - M3 (PMOS) & M4 (NMOS): Inverters Input B -> B_bar
```

### Transistor Sizing Logic (Mobility Compensation)

Electrons in silicon have roughly `2.5x` higher mobility than holes (`μ_n ≈ 2.5 * μ_p`). Furthermore, placing two transistors in series doubles their effective resistance (`R_eq = 2R`). To achieve balanced rise and fall times:

- **Inverter NMOS (`M2, M4`):** `W_n = 2 * L_min`
- **Inverter PMOS (`M1, M3`):** `W_p = 4 * L_min` (`2x` wider than NMOS to compensate for lower hole mobility)
- **Series Pull-Down NMOS (`M9–M12`):** `W_n2 = 4 * L_min` (`2x` wider to compensate for 2 NMOS in series)
- **Series Pull-Up PMOS (`M5–M8`):** `W_p2 = 8 * L_min` (`4x` wider to compensate for both hole mobility and 2 PMOS in series)

---

## 4. Code Structure & Architecture Breakdown

The project is contained within a single automated script (`dpa_simulation.py`) divided into four logical modules:

### Module 1: `MODELS` Dictionary (Fabrication & Scaling Parameters)

Defines the technology parameters across **180nm, 90nm, 45nm, and 22nm**:

- `vdd`: Supply voltage scaled from `1.8 V` → `1.2 V` → `1.0 V` → `0.8 V`.
- `l_nm`: Physical gate length (`L`).
- `r_leak`: Equivalent subthreshold & gate-tunneling static leakage resistance path (`R_sce`) modeling exponential `I_off` degradation across nodes.
- `spice_model`: `.model` cards defining threshold voltage (`vto`), transconductance parameter (`kp`), body-effect parameter (`gamma`), surface potential (`phi`), channel-length modulation (`lambda`), zero-bias junction capacitance (`cj`), sidewall capacitance (`cjsw`), and gate oxide thickness (`tox`).

### Module 2: `SPICE_TEMPLATE` (Parametric Netlist Generator)

A parameterized SPICE3f5 circuit file containing:

- `.options reltol=1e-4 abstol=1e-12 vntol=1e-6 method=gear`: Uses Gear numerical integration to prevent numerical oscillation during picosecond switching transients.
- `V_plain` & `V_key`: A `PULSE` source flipping Plaintext `A` at `1.0 ns` (`0.08 ns` rise/fall time) and a `DC` source holding the secret Key bit `B`.
- `C_n1`–`C_n4`: `0.2 fF` internal parasitic node capacitances to prevent floating-node convergence errors during transient simulation.
- `.control ... tran 0.005n 2.5n`: Runs a transient differential equation solver with a `5 ps` step size over `2.5 ns` and exports supply current `i(Vdd)` and output voltage `v(out)` to `trace.txt`.

### Module 3: `run_simulation(node, key_bit)` (EDA Automation Engine)

1. Dynamically calculates transistor widths (`W_n`, `W_p`, `W_n2`, `W_p2`) from `l_nm`.
2. Formats `SPICE_TEMPLATE` and writes `temp.cir` to disk.
3. Invokes `ngspice -b temp.cir` via Python's `subprocess.run()` in headless batch mode.
4. Parses `trace.txt`, converts time to nanoseconds (`* 1e9`), and inverts the SPICE voltage-source current convention (`-float(parts[1]) * 1e6`) to obtain positive supply draw in microamperes (`μA`).

### Module 4: `main()` (DPA Classifier & 4-Panel Visualization)

1. **Interactive Key Prompt:** Accepts a 4-bit binary key from the user (e.g., `1011`).
2. **Characterization Table:** Computes Static Leakage Floor (`t < 0.8 ns`), Peak Dynamic Current, and Differential Power Signature (`ΔI_dd`) for all 4 nodes.
3. **Noisy Oscilloscope & DPA Classifier:** Injects Gaussian thermal noise (`σ = 1.2 μA`) using `np.random.normal()`, computes the optimal classifier decision boundary:
   ```text
   I_threshold = ( max(I_Key0) + max(I_Key1) ) / 2
   ```
   and classifies each clock cycle as `'0'` (if `I_peak > I_threshold`) or `'1'` (if `I_peak < I_threshold`).
4. **Cleanup:** Automatically removes temporary files (`temp.cir`, `trace.txt`).

---

## 5. Detailed Breakdown of the 4 Output Graphs

When `dpa_simulation.py` executes, it generates a 4-panel dashboard:

### Panel 1: Transient Supply Current (`I_dd`) — 180nm vs. 45nm

- **What it shows:** Raw time-domain supply current waveforms `I_dd(t)` from `0.7 ns` to `2.0 ns`.
- **Key Insight:**
  - Solid lines (`Key = 0`) exhibit a large positive current spike (`182.49 μA` at 180nm; `129.52 μA` at 45nm) because the PMOS network charges `C_load` from `V_dd`.
  - Dashed lines (`Key = 1`) exhibit a much smaller spike (`91.86 μA` at 180nm; `36.67 μA` at 45nm) because `C_load` discharges to Ground.
  - The **vertical gap** between the solid and dashed curves is the **Side-Channel Leakage**.

### Panel 2: Differential Power Signature (`ΔI_dd = I_Key0 - I_Key1`)

- **What it shows:** The pure side-channel signal isolated by subtracting the `Key = 1` trace from the `Key = 0` trace across all four nodes (`180nm`, `90nm`, `45nm`, `22nm`).
- **Key Insight:**
  - As transistors scale down from `180 nm` (red) to `22 nm` (green), the differential spike **shifts to the left (earlier in time) and becomes narrower**.
  - This visually proves that **intrinsic gate propagation delay (`t_pd`) decreases** with technology scaling—smaller transistors switch faster, requiring attackers to use higher-bandwidth oscilloscopes to capture the narrower leakage window.

### Panel 3: Scaling Effect — Dynamic Switching vs. Static Leakage (SCE)

- **What it shows:** A dual-axis bar chart comparing **Peak Dynamic Switching Current** (blue bars, left Y-axis) against **Static Subthreshold Leakage Floor** (orange bars, right Y-axis) across `180nm`, `90nm`, `45nm`, and `22nm`.
- **Key Insight (Core `EC-214` CO2 Result):**

| Technology Node | Supply Voltage (`V_dd`) | Gate Oxide (`t_ox`) | Static Leakage Floor (`I_static`) | Peak Dynamic Current (`I_peak`) | Differential Spike (`ΔI_dd`) |
| :-------------: | :---------------------: | :-----------------: | :-------------------------------: | :-----------------------------: | :--------------------------: |
|    **180nm**    |         `1.8 V`         |      `4.0 nm`       |        `0.004 μA` (`4 nA`)        |           `182.49 μA`           |          `90.63 μA`          |
|    **90nm**     |         `1.2 V`         |      `2.2 nm`       |       `0.048 μA` (`48 nA`)        |           `113.30 μA`           |          `74.82 μA`          |
|    **45nm**     |         `1.0 V`         |      `1.4 nm`       |       `0.400 μA` (`400 nA`)       |           `129.52 μA`           |          `92.85 μA`          |
|    **22nm**     |         `0.8 V`         |      `0.9 nm`       |      `2.000 μA` (`2000 nA`)       |           `131.80 μA`           |          `91.97 μA`          |

- Static leakage grows **`500x`** from `180 nm` (`0.004 μA`) to `22 nm` (`2.000 μA`), demonstrating the breakdown of Dennard Scaling and the severity of Short Channel Effects (SCE).

### Panel 4: Live 4-Bit Key Attack Trace (Simulated Oscilloscope)

- **What it shows:** Four consecutive clock cycles (`10 ns` total) of the `45 nm` XOR gate processing a 4-bit secret key with realistic Gaussian thermal noise (`σ = 1.2 μA`) superimposed on the supply current.
- **Key Insight:**
  - The red horizontal dashed line marks the DPA decision threshold (`83.1 μA`).
  - Clock cycles where the spike crosses above `83.1 μA` are automatically classified as `Bit = 0`; cycles staying below `83.1 μA` are classified as `Bit = 1`, achieving `100%` key recovery.

---

## 6. Installation & Usage

### Prerequisites (Debian / Ubuntu / Kali Linux)

```bash
sudo apt update
sudo apt install ngspice python3-matplotlib python3-numpy
```

### Running the Simulator

```bash
python3 dpa_simulation.py
```

When prompted in the terminal:

```text
Enter a 4-bit secret cryptographic key to test (default 1011): 1011
```

Press `Enter` (or type any 4-bit binary combination such as `0110`, `1010`, or `1101`) to generate the terminal characterization table and launch the interactive 4-panel Matplotlib dashboard.

---

## 7. Hardware Countermeasures (How VLSI Engineers Prevent This Attack)

1. **Sense Amplifier Based Logic (SABL) / Dual-Rail Precharge Logic (WDDL):** Every logic gate computes both the true output (`OUT`) and complementary output (`OUT_bar`) simultaneously on every clock cycle. Because one rail _always_ charges `0 → 1` and the other _always_ discharges `1 → 0`, the current drawn from `V_dd` is identical regardless of whether the secret key bit is `0` or `1`.
2. **On-Chip Decoupling Capacitors & Current Flattening:** Placing local decoupling capacitors and active current-equalizer circuits between the internal logic core and the external `V_dd` pin filters out high-frequency current spikes before an external oscilloscope can measure them.
3. **Boolean Masking:** Randomizing internal bits with a hardware random number generator (PRNG) mask before passing them through the XOR gate decouples the instantaneous power trace from the actual secret key.

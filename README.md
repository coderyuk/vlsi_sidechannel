# Automated SPICE Characterization of CMOS Technology Scaling & Side-Channel Power Leakage

**Course:** VLSI Technology (`EC-214`)  
**Topic:** Analysis of MOSFET Technology Scaling (180nm to 22nm), Fabrication Parameter Characterization, and Differential Power Analysis (DPA) Side-Channel Leakage  
**Simulator & Stack:** Ngspice (SPICE3f5 Engine), Python 3, NumPy, Matplotlib

---

## 1. Project Overview & Syllabus Alignment (`EC-214`)

This project is an automated Electronic Design Automation (EDA) testbench written in Python that interfaces with the **Ngspice** circuit simulator. It characterizes how physical semiconductor fabrication parameters—specifically channel length ($L$), gate oxide thickness ($t_{ox}$), threshold voltage ($V_{th}$), and junction capacitances ($C_j$)—behave when scaled across four historical technology nodes: **180nm, 90nm, 45nm, and 22nm**.

To evaluate the physical impact of miniaturization on real CMOS circuits, the framework simulates a **12-Transistor Static CMOS XOR Gate** and analyzes how scaling affects both **Static Subthreshold Leakage** and **Dynamic Switching Power**, demonstrating how these physical phenomena create hardware security vulnerabilities known as **Differential Power Analysis (DPA) Side-Channel Attacks**.

### Direct Mapping to `EC-214` Syllabus

- **UNIT-01 (Miniaturization & Characterization):** Evaluates the electrical characterization impact of shrinking MOSFET feature sizes from the sub-micron regime ($180\text{ nm}$) into the deep nano-regime ($22\text{ nm}$).
- **UNIT-02 (Monolithic Fabrication Techniques):** Models the direct electrical consequences of physical fabrication stages:
  - **Oxidation:** Shrinking gate oxide thickness ($t_{ox}$ from $4.0\text{ nm} \rightarrow 0.9\text{ nm}$) and its impact on oxide capacitance ($C_{ox}$) and gate-oxide quantum tunneling.
  - **Lithography & Etching:** Defining smaller critical dimensions (channel length $L$) and accounting for Short Channel Effects (SCE).
  - **Diffusion & Ion Implantation:** Adjusting channel doping profiles and substrate bias ($\gamma$, $\phi$) to control threshold voltage ($V_{th}$) and source/drain junction capacitance ($C_j$, $C_{jsw}$).
- **UNIT-05 (Monolithic Components - Prototype Fabrication):** Constructs complementary n-MOS and p-MOS enhancement-mode structures into a functional 12-transistor CMOS logic circuit.
- **Course Outcomes (`CO1`, `CO2`, `CO5`):** Directly addresses **CO2** (_Describe the analysis of technology scaling_) and **CO5** (_Assess reliability and security issues in VLSI technology_).

---

## 2. Theoretical Foundation & VLSI Physics

### 2.1 Dennard Scaling vs. Deep Sub-Micron Breakdown

In 1974, Robert Dennard proposed that if transistor dimensions ($W, L, t_{ox}$) and supply voltage ($V_{DD}$) are scaled down by a constant factor $\kappa$ (where $\kappa > 1$), and doping concentration ($N_a$) is increased by $\kappa$, the electric field remains constant and **power density remains constant**:

| Physical Parameter     |                   Symbol                    | Dennard Scaling Factor | Practical Nano-Regime Reality (< 90nm)                               |
| :--------------------- | :-----------------------------------------: | :--------------------: | :------------------------------------------------------------------- |
| Channel Length & Width |                   $L, W$                    |       $1/\kappa$       | Scaled aggressively via EUV/ArF Lithography                          |
| Gate Oxide Thickness   |                  $t_{ox}$                   |       $1/\kappa$       | Hits physical atomic limit ($\sim 0.9\text{ nm}$, $\sim 4$ Si atoms) |
| Supply Voltage         |                  $V_{DD}$                   |       $1/\kappa$       | Cannot scale below $\sim 0.7\text{ V}$ without losing noise margin   |
| Threshold Voltage      |                  $V_{th}$                   |       $1/\kappa$       | Lowering $V_{th}$ causes **exponential** subthreshold leakage        |
| Gate Capacitance       | $C_g = \frac{\varepsilon_{ox} W L}{t_{ox}}$ |       $1/\kappa$       | Dominated by fringing & parasitic wire capacitances                  |
| Dynamic Power per Gate |      $P_{dyn} = \alpha C_L V_{DD}^2 f$      |      $1/\kappa^2$      | Scales down, but total chip power rises due to static leakage        |

Around the **90nm–45nm** nodes, Dennard Scaling broke down because reducing $V_{DD}$ required lowering $V_{th}$ to maintain switching speed ($I_{on} \propto (V_{DD} - V_{th})^\alpha$). However, lowering $V_{th}$ prevents the MOSFET from turning completely OFF when $V_{GS} = 0\text{ V}$.

---

### 2.2 Short Channel Effects (SCE) & Static Leakage Equations

When the physical channel length $L$ becomes comparable to the depletion-layer widths of the source and drain junctions, the gate loses electrostatic control over the channel:

1. **Subthreshold Conduction (Weak Inversion Leakage):**
   Even when $V_{GS} < V_{th}$, diffusion current flows between source and drain:
   $$I_{sub} = I_0 \left(\frac{W}{L}\right) e^{\frac{V_{GS} - V_{th}}{n V_T}} \left(1 - e^{-\frac{V_{DS}}{V_T}}\right)$$
   Where $V_T = \frac{kT}{q} \approx 25.85\text{ mV}$ at room temperature ($300\text{ K}$) and $n$ is the subthreshold swing factor. Because $V_{th}$ is inside the exponent, reducing $V_{th}$ from $0.42\text{ V}$ ($180\text{ nm}$) to $0.15\text{ V}$ ($22\text{ nm}$) causes $I_{sub}$ to increase by orders of magnitude.

2. **Drain-Induced Barrier Lowering (DIBL):**
   At tiny channel lengths, high drain voltage ($V_{DS}$) electrostatically lowers the potential barrier at the source, effectively reducing $V_{th}$ further:
   $$V_{th(\text{effective})} = V_{th0} - \eta V_{DS}$$

3. **Channel Length Modulation ($\lambda$):**
   As $V_{DS}$ increases in saturation, the depletion region at the drain widens, shortening the effective channel length ($L_{\text{eff}} = L - \Delta L$). In SPICE, this is modeled via $\lambda$:
   $$I_{D(\text{sat})} = \frac{1}{2} \mu C_{ox} \left(\frac{W}{L}\right) (V_{GS} - V_{th})^2 (1 + \lambda V_{DS})$$
   As $L$ shrinks from $180\text{ nm}$ to $22\text{ nm}$, $\lambda$ increases from $0.04\text{ V}^{-1}$ to $0.25\text{ V}^{-1}$.

4. **Gate Oxide Quantum Tunneling ($I_{ox}$):**
   When thermal oxidation grows an $\text{SiO}_2$ layer thinner than $1.5\text{ nm}$ (at $45\text{ nm}$ and $22\text{ nm}$ nodes), electrons quantum-mechanically tunnel directly through the gate oxide via Fowler-Nordheim and direct tunneling, requiring the industry transition to **High-$\kappa$ Metal Gates (HKMG)** and **3D FinFETs**.

---

### 2.3 Total CMOS Power Dissipation Equation

The total instantaneous power drawn from the power supply ($V_{DD}$) by any CMOS gate is the sum of three distinct physical mechanisms:

$$P_{\text{total}} = P_{\text{dynamic}} + P_{\text{short-circuit}} + P_{\text{static}}$$

$$P_{\text{total}} = \underbrace{\alpha \cdot C_{\text{load}} \cdot V_{DD}^2 \cdot f_{\text{clk}}}_{\text{Charging/Discharging } C_{\text{load}}} + \underbrace{I_{\text{sc}} \cdot V_{DD}}_{\text{PMOS \& NMOS ON Simultaneously}} + \underbrace{I_{\text{leakage}} \cdot V_{DD}}_{\text{Subthreshold + Gate Tunneling}}$$

---

### 2.4 Hardware Security Logic: Why CMOS XOR Leaks the Secret Key

In cryptographic hardware (AES S-Boxes, stream ciphers, one-time pads), a known input **Plaintext bit ($A$)** is combined with a secret internal **Key bit ($B$)** using an exclusive-OR (**XOR**) operation:

$$Y = A \oplus B = (A \cdot \overline{B}) + (\overline{A} \cdot B)$$

#### The Asymmetric Switching Physics

Suppose the attacker flips the Plaintext input $A$ from **`0` $\rightarrow$ `1`** at time $t = 1.0\text{ ns}$ while the secret Key bit $B$ remains static inside the hardware register:

| Secret Key ($B$) | Initial State ($t < 1.0\text{ ns}$) | Final State ($t > 1.0\text{ ns}$) |                 Output Transition ($Y$)                  | Physical Current Path Inside the CMOS Circuit                                                                                                                                                                                                                           | Current Drawn from $V_{DD}$ ($I_{DD}$)                                           |
| :--------------: | :---------------------------------: | :-------------------------------: | :------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------- |
|  **`Key = 0`**   |       $A=0, B=0 \implies Y=0$       |      $A=1, B=0 \implies Y=1$      |  **`0` $\rightarrow$ `1` (Charges $C_{\text{load}}$)**   | The PMOS Pull-Up Network turns **ON**, creating a low-resistance path from **$V_{DD}$ to `out`**. Current rushes out of the $V_{DD}$ power rail to charge the $8\text{ fF}$ load capacitor from $0\text{ V}$ to $V_{DD}$.                                               | **Large Positive Spike** ($I_{\text{charge}} + I_{\text{sc}}$)                   |
|  **`Key = 1`**   |       $A=0, B=1 \implies Y=1$       |      $A=1, B=1 \implies Y=0$      | **`1` $\rightarrow$ `0` (Discharges $C_{\text{load}}$)** | $C_{\text{load}}$ is _already_ charged to $V_{DD}$ before $1.0\text{ ns}$. When $A$ flips to `1`, the NMOS Pull-Down Network turns **ON** and dumps the stored capacitor charge directly to **Ground ($0\text{ V}$)**. No load-charging current is drawn from $V_{DD}$! | **Small Spike** (Only internal inverter + short-circuit current $I_{\text{sc}}$) |

> **Why is there still a smaller spike when `Key = 1`?**
>
> 1. **Crowbar / Short-Circuit Current ($I_{\text{sc}}$):** During the $0.08\text{ ns}$ rise time of input $A$, when the input voltage passes through $V_{DD}/2$, both PMOS and NMOS transistors are momentarily partially conducting, creating a brief direct path from $V_{DD}$ to Ground.
> 2. **Internal Input Inverter (`M1/M2`):** The internal node `a_bar` transitions from `1` $\rightarrow$ `0`, drawing a small switching current.

> **Why is there a brief negative dip right at $t = 1.0\text{ ns}$?**
> This is **Miller Capacitive Feedthrough (Gate-to-Drain Overlap Capacitance)**. When input $A$ rises rapidly ($0.08\text{ ns}$), capacitive coupling across the PMOS gate-source/gate-drain overlap pushes a tiny packet of charge backward into the $V_{DD}$ rail before the channel finishes inverting.

---

## 3. Circuit Topology (12-Transistor Static CMOS XOR)

Our SPICE netlist constructs a full static CMOS XOR gate without pass-transistor threshold voltage degradation:

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
                   +--------------------> OUT 6---┳--- C_load (8fF)
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

Electrons in silicon have roughly $2\times$ to $3\times$ higher mobility than holes ($\mu_n \approx 2.5 \mu_p$). Furthermore, transistors in series double the effective resistance ($R_{\text{eq}} = 2R$). To achieve symmetrical rise and fall times:

- **Inverter NMOS (`M2, M4`):** $W_n = 2 \cdot L_{\min}$
- **Inverter PMOS (`M1, M3`):** $W_p = 4 \cdot L_{\min}$ ($2\times$ wider than NMOS to compensate for lower hole mobility)
- **Series Pull-Down NMOS (`M9–M12`):** $W_{n2} = 4 \cdot L_{\min}$ ($2\times$ wider to compensate for 2 NMOS in series)
- **Series Pull-Up PMOS (`M5–M8`):** $W_{p2} = 8 \cdot L_{\min}$ ($4\times$ wider to compensate for both hole mobility and 2 PMOS in series)

---

## 4. Code Structure & Architecture Breakdown

The project is contained within a single automated script (`dpa_simulation.py`) divided into four logical modules:

### Module 1: `MODELS` Dictionary (Fabrication & Scaling Parameters)

Defines the technology parameters across **180nm, 90nm, 45nm, and 22nm**:

- `vdd`: Supply voltage scaled from $1.8\text{ V} \rightarrow 1.2\text{ V} \rightarrow 1.0\text{ V} \rightarrow 0.8\text{ V}$.
- `l_nm`: Physical gate length ($L$).
- `r_leak`: Equivalent subthreshold & gate-tunneling static leakage resistance path ($R_{\text{sce}}$) modeling exponential $I_{\text{off}}$ degradation across nodes.
- `spice_model`: `.model` cards defining threshold voltage (`vto`), transconductance parameter (`kp`), body-effect parameter (`gamma`), surface potential (`phi`), channel-length modulation (`lambda`), zero-bias junction capacitance (`cj`), sidewall capacitance (`cjsw`), and gate oxide thickness (`tox`).

### Module 2: `SPICE_TEMPLATE` (Parametric Netlist Generator)

A parameterized SPICE3f5 circuit file containing:

- `.options reltol=1e-4 abstol=1e-12 vntol=1e-6 method=gear`: Uses Gear numerical integration to prevent numerical oscillation during picosecond switching transients.
- `V_plain` & `V_key`: A `PULSE` source flipping Plaintext $A$ at $1.0\text{ ns}$ (`0.08ns` rise/fall time) and a `DC` source holding the secret Key bit $B$.
- `C_n1`–`C_n4`: $0.2\text{ fF}$ internal parasitic node capacitances to prevent floating-node Jacobian singularity errors during transient simulation.
- `.control ... tran 0.005n 2.5n`: Runs a transient differential equation solver with a $5\text{ ps}$ step size over $2.5\text{ ns}$ and exports supply current `i(Vdd)` and output voltage `v(out)` to `trace.txt`.

### Module 3: `run_simulation(node, key_bit)` (EDA Automation Engine)

1. Dynamically calculates transistor widths ($W_n, W_p, W_{n2}, W_{p2}$) from `l_nm`.
2. Formats `SPICE_TEMPLATE` and writes `temp.cir` to disk.
3. Invokes `ngspice -b temp.cir` via Python's `subprocess.run()` in headless batch mode.
4. Parses `trace.txt`, converts time to nanoseconds ($\times 10^9$), and inverts the SPICE voltage-source current convention (`-float(parts[1]) * 1e6`) to obtain positive supply draw in microamperes ($\mu\text{A}$).

### Module 4: `main()` (DPA Classifier & 4-Panel Visualization)

1. **Interactive Key Prompt:** Accepts a 4-bit binary key from the user (e.g., `1011`).
2. **Characterization Table:** Computes Static Leakage Floor ($t < 0.8\text{ ns}$), Peak Dynamic Current, and Differential Power Signature ($\Delta I_{DD}$) for all 4 nodes.
3. **Noisy Oscilloscope & DPA Classifier:** Injects Gaussian thermal noise ($\sigma = 1.2\ \mu\text{A}$) using `np.random.normal()`, computes the optimal classifier decision boundary:
   $$I_{\text{threshold}} = \frac{\max(I_{\text{Key}=0}) + \max(I_{\text{Key}=1})}{2}$$
   and classifies each clock cycle as `'0'` (if $I_{\text{peak}} > I_{\text{threshold}}$) or `'1'` (if $I_{\text{peak}} < I_{\text{threshold}}$).
4. **Cleanup:** Automatically removes temporary files (`temp.cir`, `trace.txt`).

---

## 5. Detailed Breakdown of the 4 Output Graphs

When `dpa_simulation.py` executes, it generates a 4-panel dashboard:

### Panel 1: Transient Supply Current ($I_{DD}$) — 180nm vs. 45nm

- **What it shows:** Raw time-domain supply current waveforms $I_{DD}(t)$ from $0.7\text{ ns}$ to $2.0\text{ ns}$.
- **Key Insight:**
  - Solid lines (`Key = 0`) exhibit a large positive current spike ($182.49\ \mu\text{A}$ at 180nm; $129.52\ \mu\text{A}$ at 45nm) because the PMOS network charges $C_{\text{load}}$ from $V_{DD}$.
  - Dashed lines (`Key = 1`) exhibit a much smaller spike ($91.86\ \mu\text{A}$ at 180nm; $36.67\ \mu\text{A}$ at 45nm) because $C_{\text{load}}$ discharges to Ground.
  - The **vertical gap** between the solid and dashed curves is the **Side-Channel Leakage**.

### Panel 2: Differential Power Signature ($\Delta I_{DD} = I_{\text{Key}=0} - I_{\text{Key}=1}$)

- **What it shows:** The pure side-channel signal isolated by subtracting the `Key = 1` trace from the `Key = 0` trace across all four nodes (`180nm`, `90nm`, `45nm`, `22nm`).
- **Key Insight:**
  - As transistors scale down from $180\text{ nm}$ (red) to $22\text{ nm}$ (green), the differential spike **shifts to the left (earlier in time) and becomes narrower**.
  - This visually proves that **intrinsic gate propagation delay ($t_{pd} \propto \frac{C V_{DD}}{I_{on}}$) decreases** with technology scaling—smaller transistors switch faster, requiring attackers to use higher-bandwidth oscilloscopes (higher sampling rates in GSa/s) to capture the narrower leakage window.

### Panel 3: Scaling Effect — Dynamic Switching vs. Static Leakage (SCE)

- **What it shows:** A dual-axis bar chart comparing **Peak Dynamic Switching Current** (blue bars, left Y-axis) against **Static Subthreshold Leakage Floor** (orange bars, right Y-axis) across `180nm`, `90nm`, `45nm`, and `22nm`.
- **Key Insight (Core `EC-214` CO2 Result):**

| Technology Node | Supply Voltage ($V_{DD}$) | Gate Oxide ($t_{ox}$) | Static Leakage Floor ($I_{\text{static}}$) | Peak Dynamic Current ($I_{\text{peak}}$) | Differential Spike ($\Delta I_{DD}$) |
| :-------------: | :-----------------------: | :-------------------: | :----------------------------------------: | :--------------------------------------: | :----------------------------------: |
|    **180nm**    |      $1.8\text{ V}$       |    $4.0\text{ nm}$    |    $0.004\ \mu\text{A}$ ($4\text{ nA}$)    |          $182.49\ \mu\text{A}$           |         $90.63\ \mu\text{A}$         |
|    **90nm**     |      $1.2\text{ V}$       |    $2.2\text{ nm}$    |   $0.048\ \mu\text{A}$ ($48\text{ nA}$)    |          $113.30\ \mu\text{A}$           |         $74.82\ \mu\text{A}$         |
|    **45nm**     |      $1.0\text{ V}$       |    $1.4\text{ nm}$    |   $0.400\ \mu\text{A}$ ($400\text{ nA}$)   |          $129.52\ \mu\text{A}$           |         $92.85\ \mu\text{A}$         |
|    **22nm**     |      $0.8\text{ V}$       |    $0.9\text{ nm}$    |  $2.000\ \mu\text{A}$ ($2000\text{ nA}$)   |          $131.80\ \mu\text{A}$           |         $91.97\ \mu\text{A}$         |

- Static leakage grows **$500\times$** from $180\text{ nm}$ ($0.004\ \mu\text{A}$) to $22\text{ nm}$ ($2.000\ \mu\text{A}$), demonstrating the breakdown of Dennard Scaling and the severity of Short Channel Effects (SCE).

### Panel 4: Live 4-Bit Key Attack Trace (Simulated Oscilloscope)

- **What it shows:** Four consecutive clock cycles ($10\text{ ns}$ total) of the $45\text{ nm}$ XOR gate processing a 4-bit secret key with realistic Gaussian thermal noise ($\sigma = 1.2\ \mu\text{A}$) superimposed on the supply current.
- **Key Insight:**
  - The red horizontal dashed line marks the DPA decision threshold ($83.1\ \mu\text{A}$).
  - Clock cycles where the spike crosses above $83.1\ \mu\text{A}$ are automatically classified as `Bit = 0`; cycles staying below $83.1\ \mu\text{A}$ are classified as `Bit = 1`, achieving $100\%$ key recovery.

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

1. **Sense Amplifier Based Logic (SABL) / Dual-Rail Precharge Logic (WDDL):** Every logic gate computes both the true output (`OUT`) and complementary output (`OUT_bar`) simultaneously on every clock cycle. Because one rail _always_ charges `0 → 1` and the other _always_ discharges `1 → 0`, the current drawn from $V_{DD}$ is identical regardless of whether the secret key bit is `0` or `1`.
2. **On-Chip Decoupling Capacitors & Current Flattening:** Placing local decoupling capacitors and active current-equalizer circuits between the internal logic core and the external $V_{DD}$ pin filters out high-frequency current spikes before an external oscilloscope can measure them.
3. **Boolean Masking:** Randomizing internal bits with a hardware random number generator (PRNG) mask before passing them through the XOR gate decouples the instantaneous power trace from the actual secret key.

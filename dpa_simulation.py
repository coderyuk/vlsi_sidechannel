import os
import subprocess

import matplotlib.pyplot as plt
import numpy as np

# =====================================================================
# 1. PREDICTIVE TECHNOLOGY MODELS (SCALING FROM 180nm DOWN TO 22nm)
# Includes oxide thickness (tox), channel length modulation (lambda),
# junction capacitances (cj), and subthreshold leakage models.
# =====================================================================
MODELS = {
    "180nm": {
        "vdd": 1.8,
        "l_nm": 180,
        "r_leak": "500Meg",  # Very low static leakage at 180nm
        "spice_model": (
            ".model pmos pmos level=1 vto=-0.42 kp=45u gamma=0.5 phi=0.6 lambda=0.04 cj=1e-4 cjsw=2e-10 tox=4.0e-9\n"
            ".model nmos nmos level=1 vto=0.42 kp=150u gamma=0.5 phi=0.6 lambda=0.04 cj=1e-4 cjsw=2e-10 tox=4.0e-9"
        ),
    },
    "90nm": {
        "vdd": 1.2,
        "l_nm": 90,
        "r_leak": "25Meg",  # Moderate subthreshold leakage
        "spice_model": (
            ".model pmos pmos level=1 vto=-0.30 kp=75u gamma=0.45 phi=0.6 lambda=0.08 cj=1.5e-4 cjsw=1.5e-10 tox=2.2e-9\n"
            ".model nmos nmos level=1 vto=0.30 kp=220u gamma=0.45 phi=0.6 lambda=0.08 cj=1.5e-4 cjsw=1.5e-10 tox=2.2e-9"
        ),
    },
    "45nm": {
        "vdd": 1.0,
        "l_nm": 45,
        "r_leak": "2.5Meg",  # High SCE & gate-oxide tunneling leakage
        "spice_model": (
            ".model pmos pmos level=1 vto=-0.22 kp=110u gamma=0.4 phi=0.6 lambda=0.15 cj=2e-4 cjsw=1e-10 tox=1.4e-9\n"
            ".model nmos nmos level=1 vto=0.22 kp=320u gamma=0.4 phi=0.6 lambda=0.15 cj=2e-4 cjsw=1e-10 tox=1.4e-9"
        ),
    },
    "22nm": {
        "vdd": 0.8,
        "l_nm": 22,
        "r_leak": "400k",  # Severe planar leakage (Why FinFETs were invented)
        "spice_model": (
            ".model pmos pmos level=1 vto=-0.15 kp=150u gamma=0.35 phi=0.6 lambda=0.25 cj=2.5e-4 cjsw=0.8e-10 tox=0.9e-9\n"
            ".model nmos nmos level=1 vto=0.15 kp=420u gamma=0.35 phi=0.6 lambda=0.25 cj=2.5e-4 cjsw=0.8e-10 tox=0.9e-9"
        ),
    },
}

# =====================================================================
# 2. 12-TRANSISTOR CMOS XOR GATE SPICE NETLIST TEMPLATE
# =====================================================================
SPICE_TEMPLATE = """CMOS XOR Gate - VLSI Scaling & DPA Side-Channel Analysis
{model_data}

* Solver convergence options + Gmin modeling subthreshold floor
.options reltol=1e-4 abstol=1e-12 vntol=1e-6 method=gear

* Power Supply
Vdd vdd 0 DC {vdd}

* Subthreshold & Gate-Tunneling Static Leakage Path Model (SCE)
R_sce vdd 0 {r_leak}

* Inputs: Plaintext flips 0 -> 1 at 1.0ns; Key is held static
V_plain a 0 PULSE(0 {vdd} 1.0n 0.08n 0.08n 5n 10n)
V_key b 0 DC {key_voltage}

* Input Inverters (A -> A_bar, B -> B_bar)
M1 a_bar a vdd vdd pmos W={w_p} L={l_min}
M2 a_bar a 0   0   nmos W={w_n} L={l_min}
M3 b_bar b vdd vdd pmos W={w_p} L={l_min}
M4 b_bar b 0   0   nmos W={w_n} L={l_min}

* CMOS XOR Pull-Up Network (PMOS)
M5 n1  a     vdd vdd pmos W={w_p2} L={l_min}
M6 out b_bar n1  vdd pmos W={w_p2} L={l_min}
M7 n2  a_bar vdd vdd pmos W={w_p2} L={l_min}
M8 out b     n2  vdd pmos W={w_p2} L={l_min}

* CMOS XOR Pull-Down Network (NMOS)
M9  n3  a     0   0 nmos W={w_n2} L={l_min}
M10 out b     n3  0 nmos W={w_n2} L={l_min}
M11 n4  a_bar 0   0 nmos W={w_n2} L={l_min}
M12 out b_bar n4  0 nmos W={w_n2} L={l_min}

* Internal Parasitic Node Capacitances (Prevents floating-node convergence crash)
C_n1 n1 0 0.2f
C_n2 n2 0 0.2f
C_n3 n3 0 0.2f
C_n4 n4 0 0.2f

* Output Load Capacitance (Next Logic Stage Fan-out)
C_load out 0 8f

.control
set wr_singlescale
tran 0.005n 2.5n
wrdata trace.txt i(Vdd) v(out)
quit
.endc
.end
"""


def run_simulation(node, key_bit):
    params = MODELS[node]
    vdd = params["vdd"]
    l_nm = params["l_nm"]
    key_voltage = vdd if key_bit == 1 else 0.0

    # Format dimensions cleanly in nanometers for SPICE
    l_min = f"{l_nm}n"
    w_n = f"{l_nm * 2}n"
    w_p = f"{l_nm * 4}n"
    w_n2 = f"{l_nm * 4}n"
    w_p2 = f"{l_nm * 8}n"

    netlist = SPICE_TEMPLATE.format(
        model_data=params["spice_model"],
        vdd=vdd,
        r_leak=params["r_leak"],
        key_voltage=key_voltage,
        l_min=l_min,
        w_n=w_n,
        w_p=w_p,
        w_n2=w_n2,
        w_p2=w_p2,
    )

    with open("temp.cir", "w") as f:
        f.write(netlist.strip() + "\n")

    if os.path.exists("trace.txt"):
        os.remove("trace.txt")

    result = subprocess.run(  # noqa: PLW1510
        ["ngspice", "-b", "temp.cir"],
        capture_output=True,
        text=True,
    )

    if not os.path.exists("trace.txt"):
        raise RuntimeError(f"Ngspice failed:\n{result.stderr}")

    t_ns, i_ua, v_out = [], [], []
    with open("trace.txt", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    t_ns.append(float(parts[0]) * 1e9)
                    # -i(Vdd) converts SPICE voltage source current to positive draw
                    i_ua.append(-float(parts[1]) * 1e6)
                    v_out.append(float(parts[2]))
                except ValueError:
                    continue

    return np.array(t_ns), np.array(i_ua), np.array(v_out)


def main():
    print("=" * 72)
    print("  VLSI MOS SCALING & DPA SIDE-CHANNEL HARDWARE ATTACK SIMULATOR")
    print("=" * 72)
    secret_key = input(
        "Enter a 4-bit secret cryptographic key to test (default 1011): "
    ).strip()
    if len(secret_key) != 4 or any(c not in "01" for c in secret_key):
        print("[!] Invalid input. Using default 4-bit key: 1011")
        secret_key = "1011"

    print(
        "\n[*] Running Ngspice transistor-level simulations across 4 technology nodes..."
    )

    results = {}
    print("\n" + "-" * 78)
    print(
        f"{'Tech Node':<10} | {'Vdd (V)':<8} | {'Static Leak (uA)':<17} | {'Peak Current (uA)':<18} | {'DPA Delta (uA)':<15}"
    )
    print("-" * 78)

    for node in MODELS:
        t0, i0, v0 = run_simulation(node, 0)
        t1, i1, v1 = run_simulation(node, 1)
        results[node] = (t0, i0, v0, t1, i1, v1)

        # Calculate engineering metrics
        static_leak = np.mean(i0[t0 < 0.8])
        peak_k0 = np.max(i0)
        peak_k1 = np.max(i1)
        dpa_delta = peak_k0 - peak_k1

        print(
            f"{node:<10} | {MODELS[node]['vdd']:<8.1f} | {static_leak:<17.3f} | {peak_k0:<18.2f} | {dpa_delta:<15.2f}"
        )
    print("-" * 78)

    # =================================================================
    # SIMULATE AUTOMATED DPA KEY EXTRACTION ON 45nm NODE WITH NOISE
    # =================================================================
    print(
        f"\n[*] Simulating Oscilloscope Capture & DPA Attack on 45nm Node (Secret Key: {secret_key})..."
    )
    t0_45, i0_45, _, t1_45, i1_45, _ = results["45nm"]

    # Threshold halfway between Key=0 peak (charges C_load) and Key=1 peak (discharges C_load)
    threshold = (np.max(i0_45) + np.max(i1_45)) / 2.0

    cracked_key = ""
    bit_traces_time = []
    bit_traces_curr = []

    np.random.seed(42)
    for idx, bit_char in enumerate(secret_key):
        bit_val = int(bit_char)
        base_trace = i0_45 if bit_val == 0 else i1_45
        # Inject realistic Gaussian thermal + measurement noise (sigma = 1.2 uA)
        noisy_trace = base_trace + np.random.normal(0, 1.2, size=len(base_trace))

        # Measure peak current in switching window (0.95ns to 1.50ns)
        window_mask = (t0_45 >= 0.95) & (t0_45 <= 1.50)
        measured_peak = np.max(noisy_trace[window_mask])

        # DPA Decision Logic: High Vdd current spike means Output charged 0->1 (so Key=0)
        guessed_bit = "0" if measured_peak > threshold else "1"
        cracked_key += guessed_bit

        print(
            f"    Clock Cycle {idx + 1}: Measured Peak = {measured_peak:6.2f} uA  (Threshold = {threshold:.2f} uA)  --> Cracked Bit: {guessed_bit}"
        )

        bit_traces_time.append(t0_45 + idx * 2.5)
        bit_traces_curr.append(noisy_trace)

    print(f"\n[+] SECRET KEY INJECTED : {secret_key}")
    print(
        f"[+] DPA RECOVERED KEY   : {cracked_key}  ({'100% MATCH - ATTACK SUCCESSFUL!' if cracked_key == secret_key else 'PARTIAL'})"
    )

    # =================================================================
    # BUILD 4-PANEL VLSI DASHBOARD
    # =================================================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        "VLSI MOS Scaling & Differential Power Analysis (DPA) Attack Dashboard",
        fontsize=15,
        fontweight="bold",
    )

    # Panel 1: 180nm vs 45nm Transient Waveforms
    ax = axes[0, 0]
    t0_180, i0_180, _, t1_180, i1_180, _ = results["180nm"]
    ax.plot(t0_180, i0_180, color="#d62728", lw=1.8, label="180nm Key=0 (Out 0→1)")
    ax.plot(
        t1_180, i1_180, color="#d62728", lw=1.5, ls="--", label="180nm Key=1 (Out 1→0)"
    )
    ax.plot(t0_45, i0_45, color="#1f77b4", lw=1.8, label="45nm Key=0 (Out 0→1)")
    ax.plot(
        t1_45, i1_45, color="#1f77b4", lw=1.5, ls="--", label="45nm Key=1 (Out 1→0)"
    )
    ax.set_title("1. Transient Supply Current ($I_{DD}$) — 180nm vs 45nm")
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel(r"Supply Current $I_{DD}$ ($\mu$A)")
    ax.set_xlim(0.7, 2.0)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.4)

    # Panel 2: Differential Trace (Delta I = I_key0 - I_key1) Across All Nodes
    ax = axes[0, 1]
    colors = {
        "180nm": "#d62728",
        "90nm": "#ff7f0e",
        "45nm": "#1f77b4",
        "22nm": "#2ca02c",
    }
    for node in MODELS:
        t0, i0, _, t1, i1, _ = results[node]
        min_len = min(len(i0), len(i1))
        diff_trace = i0[:min_len] - i1[:min_len]
        ax.plot(
            t0[:min_len],
            diff_trace,
            color=colors[node],
            lw=1.8,
            label=f"{node} (Vdd={MODELS[node]['vdd']}V)",
        )
    ax.set_title(
        r"2. Differential Power Signature ($\Delta I_{DD} = I_{Key=0} - I_{Key=1}$)"
    )
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel(r"Differential Current $\Delta I_{DD}$ ($\mu$A)")
    ax.set_xlim(0.8, 1.8)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.4)

    # Panel 3: Scaling Trade-off (Dynamic Peak vs Static Leakage Floor)
    ax = axes[1, 0]
    nodes_list = list(MODELS.keys())
    dyn_peaks = [np.max(results[n][1]) for n in nodes_list]
    stat_leaks = [np.mean(results[n][1][results[n][0] < 0.8]) for n in nodes_list]

    x_idx = np.arange(len(nodes_list))
    ax_twin = ax.twinx()
    b1 = ax.bar(
        x_idx - 0.18,
        dyn_peaks,
        width=0.35,
        color="#1f77b4",
        label=r"Peak Switching Current ($\mu$A)",
    )
    b2 = ax_twin.bar(
        x_idx + 0.18,
        stat_leaks,
        width=0.35,
        color="#ff7f0e",
        label=r"Static Leakage Floor ($\mu$A)",
    )

    ax.set_title("3. Scaling Effect: Dynamic Switching vs. Static Leakage (SCE)")
    ax.set_xticks(x_idx)
    ax.set_xticklabels(nodes_list)
    ax.set_xlabel("MOSFET Technology Node")
    ax.set_ylabel(r"Peak Dynamic Current ($\mu$A)", color="#1f77b4")
    ax_twin.set_ylabel(r"Static Subthreshold Leakage ($\mu$A)", color="#ff7f0e")
    ax.grid(True, axis="y", alpha=0.3)

    # Combine legends for dual-axis bar chart
    handles = [b1, b2]
    labels = [h.get_label() for h in handles]
    ax.legend(handles, labels, loc="upper center", fontsize=8)

    # Panel 4: Live 4-Bit Key Extraction Oscilloscope Trace
    ax = axes[1, 1]
    full_t = np.concatenate(bit_traces_time)
    full_i = np.concatenate(bit_traces_curr)
    ax.plot(full_t, full_i, color="#2ca02c", lw=1.0, label="Noisy 45nm Power Trace")
    ax.axhline(
        threshold,
        color="red",
        ls="--",
        lw=1.2,
        label=rf"DPA Classifier Threshold ({threshold:.1f} $\mu$A)",
    )

    for idx, bit_char in enumerate(cracked_key):
        center_t = idx * 2.5 + 1.15
        ax.annotate(
            f"Bit {idx + 1}\nCracked: '{bit_char}'",
            xy=(center_t, threshold + 5),
            ha="center",
            fontsize=8,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.2", "fc": "yellow", "alpha": 0.7},
        )
        if idx > 0:
            ax.axvline(idx * 2.5, color="gray", ls=":", alpha=0.6)

    ax.set_title(
        f"4. Live 4-Bit Key Attack Trace (Injected: {secret_key} → Cracked: {cracked_key})"
    )
    ax.set_xlabel("Time Across 4 Clock Cycles (ns)")
    ax.set_ylabel(r"Measured $I_{DD}$ with Noise ($\mu$A)")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.4)

    plt.tight_layout()
    plt.show()

    # Cleanup temporary files
    for temp_file in ["temp.cir", "trace.txt"]:
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    main()

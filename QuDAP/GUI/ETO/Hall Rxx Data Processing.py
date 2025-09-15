#!/usr/bin/env python3
# coding: utf-8
"""
Rxx/Rxy Batch Processor (single-CSV with tidy-wide on the right, signed Rxy included)

Features:
- Robust field-based even/odd pairing via interpolation (+B with -B).
- Processes one or many CSV files via a simple Tk GUI.
- Writes ONE CSV per input: [processed wide ABS columns] | (blank)(blank) | [tidy-wide incl. signed Rxy].
- Saves exactly two plots per input:
    RXX vs Field_<TempUsed>
    RXY vs Field_<TempUsed>
- Puts all outputs into a subfolder named by the measurement temperature (e.g., "75K").
- Uses non-interactive Matplotlib backend ('Agg') to avoid GUI-in-thread warnings.

Expected input columns:
- "Field (Oe)"
- Either/both channel sets:
  * "Channel 1 Voltage (V)", "Channel 1 Resistance (Ohm)"
  * "Channel 2 Voltage (V)", "Channel 2 Resistance (Ohm)"
- Optional: "Temperature (K)"
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
import pandas as pd

# IMPORTANT: set non-interactive backend BEFORE importing pyplot (fixes thread GUI warnings)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ===================== Utilities / Units =====================

def convert_with_units(value, unit, kind="current"):
    value = float(value)
    if kind == "current":
        factors = {"A": 1.0, "mA": 1e-3, "µA": 1e-6, "nA": 1e-9}
    else:
        factors = {"m": 1.0, "cm": 1e-2, "mm": 1e-3, "µm": 1e-6, "nm": 1e-9}
    return value * factors[unit]

# ===================== Core engine =====================

def split_by_turnaround(B: np.ndarray) -> int:
    """Index where field reaches its most negative value (turnaround)."""
    idx = int(np.argmin(B))
    return max(1, min(idx, len(B) - 2))

def process_pair_field_based(field_col: pd.Series, sig_col: pd.Series, which: str) -> pd.DataFrame:
    """
    Field-based sym/antisym with interpolation (robust to unequal half lengths & non-uniform steps).
    which: 'odd' -> 0.5*(S(+B) - S(-B)); 'even' -> 0.5*(S(+B) + S(-B))
    Returns two columns [Field, ProcessedSignal] in original acquisition order.
    """
    B = pd.to_numeric(field_col, errors='coerce').to_numpy()
    S = pd.to_numeric(sig_col,   errors='coerce').to_numpy()
    m = np.isfinite(B) & np.isfinite(S)
    B, S = B[m], S[m]

    if len(B) < 4:
        raise ValueError("Not enough points to split forward/reverse.")

    # Split at turnaround
    turn = split_by_turnaround(B)
    B_fwd, B_rev = B[:turn], B[turn:]
    S_fwd, S_rev = S[:turn], S[turn:]

    # Sort halves by field for stable interpolation
    fidx = np.argsort(B_fwd); Bf, Sf = B_fwd[fidx], S_fwd[fidx]
    ridx = np.argsort(B_rev); Br, Sr = B_rev[ridx], S_rev[ridx]

    # Interpolate reverse onto -Bf (pair +B with -B)
    Sr_on_negBf = np.interp(-Bf, Br, Sr)

    # Compute processed half on forward grid
    if which == 'odd':
        Shalf_fwd = 0.5 * (Sf - Sr_on_negBf)
    elif which == 'even':
        Shalf_fwd = 0.5 * (Sf + Sr_on_negBf)
    else:
        raise ValueError("`which` must be 'odd' or 'even'.")

    # Map half back to ORIGINAL forward acquisition order
    S_fwd_proc = np.empty_like(Shalf_fwd)
    S_fwd_proc[fidx] = Shalf_fwd

    # Evaluate symmetry on reverse grid and map back to ORIGINAL reverse order
    Shalf_on_negBr = np.interp(-Br, Bf, Shalf_fwd)
    S_rev_sorted = -Shalf_on_negBr if which == 'odd' else Shalf_on_negBr
    S_rev_proc = np.empty_like(S_rev_sorted)
    S_rev_proc[ridx] = S_rev_sorted

    # Full-length in original acquisition order
    B_full = np.concatenate([B_fwd, B_rev])
    S_full = np.concatenate([S_fwd_proc, S_rev_proc])

    return pd.DataFrame({field_col.name: B_full, sig_col.name: S_full})

# ===================== File processing =====================

V1, V2 = "Channel 1 Voltage (V)", "Channel 2 Voltage (V)"
R1, R2 = "Channel 1 Resistance (Ohm)", "Channel 2 Resistance (Ohm)"
FIELD = "Field (Oe)"
TEMP = "Temperature (K)"

def choose_voltage_channel(df: pd.DataFrame, mode: str) -> tuple[str, str, list[str]]:
    """Pick voltage/resistance columns (Auto/Ch1/Ch2). Return (Vcol, Rcol, drop_cols)."""
    candidates = []
    if V1 in df.columns and R1 in df.columns:
        candidates.append((V1, R1))
    if V2 in df.columns and R2 in df.columns:
        candidates.append((V2, R2))
    if not candidates:
        raise ValueError("No complete voltage/resistance channel pair found.")

    if mode == "Ch1" and (V1, R1) in candidates:
        return V1, R1, [V2, R2]
    if mode == "Ch2" and (V2, R2) in candidates:
        return V2, R2, [V1, R1]

    # Auto: choose V column with larger robust variance
    best = None
    best_var = -np.inf
    for Vcol, Rcol in candidates:
        v = pd.to_numeric(df[Vcol], errors='coerce').to_numpy()
        m = np.isfinite(v) & (np.abs(v) > 0)
        var = np.var(v[m]) if np.any(m) else -np.inf
        if var > best_var:
            best_var, best = var, (Vcol, Rcol)
    Vcol, Rcol = best
    drop = [c for c in (V1, R1, V2, R2) if c not in (Vcol, Rcol) and c in df.columns]
    return Vcol, Rcol, drop

def _format_temp_label(temp_val: float | None) -> str:
    """Always return an integer-based folder label, e.g. '75K' or 'UnknownTemp'."""
    if temp_val is None or not np.isfinite(temp_val):
        return "UnknownTemp"
    return f"{int(round(temp_val))}K"

def process_file(in_csv: str, base_outfolder: str, I_si: float, chan_mode: str) -> str:
    df = pd.read_csv(in_csv)
    if FIELD not in df.columns:
        raise ValueError(f"{os.path.basename(in_csv)}: missing '{FIELD}' column.")

    Vcol, Rcol, drop = choose_voltage_channel(df, chan_mode)
    df = df.drop(columns=[c for c in drop if c in df.columns], errors='ignore')

    # even/odd from voltage, then divide by current -> Ohms
    rxy_processed = process_pair_field_based(df[FIELD], df[Vcol], which='odd')
    rxx_processed = process_pair_field_based(df[FIELD], df[Vcol], which='even')

    B_proc = rxx_processed[FIELD].to_numpy()
    turn = split_by_turnaround(B_proc)
    B_fwd, B_rev = B_proc[:turn], B_proc[turn:]

    S_even_all = rxx_processed[df[Vcol].name].to_numpy()
    S_odd_all  = rxy_processed[df[Vcol].name].to_numpy()
    Rxx_all = S_even_all / I_si
    Rxy_all = S_odd_all  / I_si

    # --- signed and absolute forms ---
    Rxx_f = np.abs(Rxx_all[:turn]); Rxx_r = np.abs(Rxx_all[turn:])
    Rxy_signed_f = Rxy_all[:turn]
    Rxy_signed_r = Rxy_all[turn:]
    Rxy_f = np.abs(Rxy_signed_f)
    Rxy_r = np.abs(Rxy_signed_r)

    # Determine temperature label from first finite value (for folder and plot titles)
    temp_used = None
    if TEMP in df.columns:
        T_vals = pd.to_numeric(df[TEMP], errors='coerce').to_numpy()
        finite = T_vals[np.isfinite(T_vals)]
        if finite.size > 0:
            temp_used = float(finite[0])
    temp_label = _format_temp_label(temp_used)

    # Output folder by temperature
    outfolder = os.path.join(base_outfolder, temp_label)
    os.makedirs(outfolder, exist_ok=True)

    # Optional temperature vector aligned to forward branch (kept exactly as before)
    T_fwd = None
    if TEMP in df.columns:
        T_fwd = pd.to_numeric(df[TEMP], errors='coerce').to_numpy()[:len(B_fwd)]

    # --- pad arrays for the processed wide section (left block) ---
    def pad_to(arr, n):
        return np.pad(arr, (0, max(0, n - len(arr))), mode='constant', constant_values=np.nan)

    max_len = max(len(B_fwd), len(B_rev))
    B_fwd_p = pad_to(B_fwd, max_len)
    B_rev_p = pad_to(B_rev, max_len)
    Rxx_f_p = pad_to(Rxx_f, max_len)
    Rxx_r_p = pad_to(Rxx_r, max_len)
    Rxy_f_p = pad_to(Rxy_f, max_len)
    Rxy_r_p = pad_to(Rxy_r, max_len)
    data_wide = {
        'Field_forward (Oe)': B_fwd_p,
        'Field_reverse (Oe)': B_rev_p,
        '|Rxx|_forward (Ohm)': Rxx_f_p,
        '|Rxx|_reverse (Ohm)': Rxx_r_p,
        '|Rxy|_forward (Ohm)': Rxy_f_p,
        '|Rxy|_reverse (Ohm)': Rxy_r_p,
    }
    if T_fwd is not None:
        data_wide['Temperature (K)'] = pad_to(T_fwd, max_len)
    wide_df = pd.DataFrame(data_wide)

    # --- tidy-wide (right block): includes signed Rxy column ---
    tidy_wide_fwd = pd.DataFrame({
        'Field (Oe)': B_fwd,
        '|Rxx| (Ohm)': Rxx_f,
        '|Rxy| (Ohm)': Rxy_f,
        'Rxy (Ohm)': Rxy_signed_f,   # signed Hall
        'branch': 'forward'
    })
    tidy_wide_rev = pd.DataFrame({
        'Field (Oe)': B_rev,
        '|Rxx| (Ohm)': Rxx_r,
        '|Rxy| (Ohm)': Rxy_r,
        'Rxy (Ohm)': Rxy_signed_r,   # signed Hall
        'branch': 'reverse'
    })
    tidy_wide = pd.concat([tidy_wide_fwd, tidy_wide_rev], ignore_index=True)

    # --- horizontally merge: [wide] | (blank)(blank) | [tidy-wide] ---
    total_rows = max(len(wide_df), len(tidy_wide))

    def pad_series(s: pd.Series, n: int) -> pd.Series:
        arr = s.to_numpy()
        arr = np.pad(arr, (0, max(0, n - len(arr))), mode='constant', constant_values=np.nan)
        return pd.Series(arr)

    merged = {}
    # left: processed wide (unchanged)
    for col in wide_df.columns:
        merged[col] = pad_series(wide_df[col], total_rows)
    # two blank spacer columns
    merged['']  = pd.Series([np.nan]*total_rows)
    merged[' '] = pd.Series([np.nan]*total_rows)
    # right: tidy-wide
    for col in tidy_wide.columns:
        merged[col] = pad_series(tidy_wide[col], total_rows)

    merged_df = pd.DataFrame(merged)

    # save single CSV
    name = os.path.splitext(os.path.basename(in_csv))[0]
    save_csv = os.path.join(outfolder, name + "_processed.csv")
    merged_df.to_csv(save_csv, index=False)

    # ---------------- Plots (two only), ABS values, titles/filenames include temperature ----------------
    # RXX
    plt.figure()
    if len(B_fwd):
        plt.plot(B_fwd, Rxx_f, label='|Rxx| forward')
    if len(B_rev):
        plt.plot(B_rev, Rxx_r, label='|Rxx| reverse')
    plt.xlabel('Field (Oe)'); plt.ylabel('Ohm'); plt.title(f'RXX vs Field_{temp_label}')
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(outfolder, f"RXX_vs_Field_{temp_label}.png"), dpi=300)
    plt.close()

    # RXY
    plt.figure()
    if len(B_fwd):
        plt.plot(B_fwd, Rxy_f, label='|Rxy| forward')
    if len(B_rev):
        plt.plot(B_rev, Rxy_r, label='|Rxy| reverse')
    plt.xlabel('Field (Oe)'); plt.ylabel('Ohm'); plt.title(f'RXY vs Field_{temp_label}')
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(outfolder, f"RXY_vs_Field_{temp_label}.png"), dpi=300)
    plt.close()

    return save_csv

# ===================== GUI =====================

def browse_inputs(entry):
    paths = filedialog.askopenfilenames(filetypes=[("CSV","*.csv")])
    if paths:
        entry.delete(0, tk.END)
        entry.insert(0, " | ".join(paths))
        entry.paths = list(paths)

def browse_output(entry):
    d = filedialog.askdirectory()
    if d:
        entry.delete(0, tk.END)
        entry.insert(0, d)

def run_processing(inp_entry, out_entry, c_ent, c_u, chan_var, prog, stat):
    paths = getattr(inp_entry, 'paths', None)
    if not paths:
        stat.config(text="Select one or more input CSV files")
        return
    base_outfolder = out_entry.get().strip()
    if not base_outfolder:
        stat.config(text="Select an output folder")
        return
    if not os.path.isdir(base_outfolder):
        stat.config(text="Output folder not found")
        return

    try:
        I_si = convert_with_units(c_ent.get(), c_u.get(), kind="current")
    except Exception:
        stat.config(text="Invalid current value")
        return

    prog['maximum'] = len(paths)
    prog['value'] = 0
    stat.config(text="Processing…")

    def work():
        successes = 0
        errors = []
        for p in paths:
            try:
                process_file(p, base_outfolder, I_si, chan_var.get())
                successes += 1
            except Exception as e:
                errors.append(f"{os.path.basename(p)}: {e}")
            finally:
                prog['value'] = successes + len(errors)
                prog.update_idletasks()
        if errors:
            stat.config(text=f"Done with {successes} ok, {len(errors)} failed. See details.")
            messagebox.showerror("Some files failed", "\n".join(errors))
        else:
            stat.config(text=f"Done. Processed {successes} file(s).")

    threading.Thread(target=work, daemon=True).start()

def reset_gui(inp_entry, out_entry, prog, stat):
    inp_entry.delete(0, tk.END)
    if hasattr(inp_entry, 'paths'):
        delattr(inp_entry, 'paths')
    out_entry.delete(0, tk.END)
    prog['value'] = 0
    stat.config(text="")

def main():
    root = tk.Tk()
    root.title("Rxx/Rxy Batch Processor (single CSV, tidy-wide on right, signed Rxy)")
    root.geometry("840x420")

    # Inputs
    tk.Label(root, text="Input CSV(s):").grid(row=0, column=0, sticky="e", padx=6, pady=6)
    inp = tk.Entry(root, width=80)
    inp.grid(row=0, column=1, padx=4)
    tk.Button(root, text="Browse", command=lambda: browse_inputs(inp)).grid(row=0, column=2, padx=4)

    tk.Label(root, text="Output Folder:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
    outp = tk.Entry(root, width=80)
    outp.grid(row=1, column=1, padx=4)
    tk.Button(root, text="Browse", command=lambda: browse_output(outp)).grid(row=1, column=2, padx=4)

    # Params
    tk.Label(root, text="Current:").grid(row=2, column=0, sticky="e", padx=6)
    c_ent = tk.Entry(root, width=12); c_ent.insert(0, "20"); c_ent.grid(row=2, column=1, sticky="w")
    c_u = ttk.Combobox(root, values=["A","mA","µA","nA"], width=6); c_u.set("µA"); c_u.grid(row=2, column=2, sticky="w")

    tk.Label(root, text="Channel:").grid(row=3, column=0, sticky="e", padx=6)
    chan_var = tk.StringVar(value="Auto")
    ttk.Combobox(root, values=["Auto","Ch1","Ch2"], textvariable=chan_var, width=8).grid(row=3, column=1, sticky="w")

    # Controls
    prog = ttk.Progressbar(root, length=620, mode="determinate")
    prog.grid(row=5, column=0, columnspan=3, pady=14, padx=6)

    stat = tk.Label(root, text="", anchor="w")
    stat.grid(row=6, column=0, columnspan=3, sticky="w", padx=6)

    tk.Button(
        root,
        text="Start Processing",
        command=lambda: run_processing(inp, outp, c_ent, c_u, chan_var, prog, stat)
    ).grid(row=4, column=0, columnspan=2, pady=8, padx=6, sticky="w")

    tk.Button(root, text="Reset", command=lambda: reset_gui(inp, outp, prog, stat)).grid(row=4, column=2, sticky="e", padx=6)

    root.mainloop()

if __name__ == "__main__":
    main()

import argparse, requests, math, random, csv
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
import logging

from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error, ReadoutError

from poc03_end_to_end.qiskit_impl.grover_oracle import oracle_mark_target, diffusion_operator

API = "http://127.0.0.1:8008"

for name in ["qiskit_ibm_runtime", "qiskit_ibm_runtime.qiskit_runtime_service"]:
    logging.getLogger(name).setLevel(logging.ERROR)

# ---------------- Víctima (API) ----------------
def get_challenge(nbits: int) -> Tuple[str, int]:
    r = requests.get(f"{API}/challenge", params={"nbits": nbits}, timeout=10)
    r.raise_for_status()
    j = r.json()
    return j["msg"], j["nbits"]

def challenge_debug(msg: str, nbits: int) -> str:
    r = requests.post(f"{API}/challenge_debug", json={"msg": msg, "nbits": nbits}, timeout=10)
    r.raise_for_status()
    return r.json()["target"]

def verify(msg: str, proof_bits: str, nbits: int) -> bool:
    r = requests.post(
        f"{API}/verify",
        json={"msg": msg, "proof_bits": proof_bits, "nbits": nbits},
        timeout=10,
    )
    return r.ok and r.json().get("ok", False)

# ---------------- Util / Ruido sintético (opcional) ----------------
def make_noise_model_sintetico():
    noise = NoiseModel()
    t1, t2, gate_t = 100e-6, 80e-6, 2e-7
    relax_1q = thermal_relaxation_error(t1, t2, gate_t)
    relax_2q = thermal_relaxation_error(t1, t2, 2 * gate_t).tensor(
        thermal_relaxation_error(t1, t2, 2 * gate_t)
    )
    readout = ReadoutError([[0.985, 0.015], [0.025, 0.975]])
    for g in ["x", "h", "rz"]:
        noise.add_all_qubit_quantum_error(relax_1q, [g])
    noise.add_all_qubit_quantum_error(relax_2q, ["cx"])
    noise.add_all_qubit_readout_error(readout, list(range(32)))
    return noise

def optimal_iters(n: int) -> int:
    return max(1, int((math.pi / 4) * math.sqrt(2 ** n)))

# ---------------- Deploy + Attack + Métricas ----------------
@dataclass
class DeployInfo:
    msg: str
    nbits: int
    k_grid: List[int]

def deploy_oracle(nbits: int, alpha_range: List[float]) -> DeployInfo:
    """
    Pide challenge y calcula la grilla de k a probar (sin revelar target).
    """
    msg, nbits_srv = get_challenge(nbits)
    k_opt = optimal_iters(nbits_srv)
    ks = sorted(set(max(1, int(max(0.2, min(1.0, a)) * k_opt)) for a in alpha_range))
    return DeployInfo(msg=msg, nbits=nbits_srv, k_grid=ks)

@dataclass
class AttackMetrics:
    success: bool
    msg: str
    nbits: int
    trial_success: Optional[int]
    k_used: Optional[int]
    best_hits: Optional[int]

# ---------------- TODO #1: construir Grover ----------------
def build_grover(n: int, target_bits: str, iters: int) -> QuantumCircuit:
    """
    TODO: Construye el circuito de Grover para 'n' qubits.
      - Estado inicial |+>^n
      - Repite 'iters' veces: Oracle(target_bits) + Diffusion
      - Mide todos los qubits al final

    Pistas:
      - oracle = oracle_mark_target(n, target_bits)
      - diff   = diffusion_operator(n)
      - qc.append(oracle, range(n)) / qc.append(diff, range(n))
    """
    qc = QuantumCircuit(n, n)

    # --- COMPLETAR DESDE AQUÍ ---
    # qc.h(range(n))
    # for _ in range(max(1, iters)):
    #     qc.append(oracle_mark_target(n, target_bits), range(n))
    #     qc.append(diffusion_operator(n), range(n))
    # qc.measure(range(n), range(n))
    # return qc
    # --- HASTA AQUÍ ---

    raise NotImplementedError("Completa build_grover(n, target_bits, iters)")

# ---------------- TODO #2–#3: ejecutar y elegir candidato ----------------
def execute_attack(
    dep: DeployInfo,
    *,
    backend: str,
    shots: int,
    trials: int,
    topk_size: int,
    demo: bool = False,
) -> AttackMetrics:
    """
    Ejecuta el ataque probando varios k y rounds.
    En modo reto NO uses challenge_debug (demo=False) para no revelar target.
    """

    # En reto: NO conocer el target (usa placeholder). En dev: demo=True para probar.
    target = challenge_debug(dep.msg, dep.nbits) if demo else "0" * dep.nbits

    for trial in range(1, trials + 1):
        seed_sim = 12345 + trial
        seed_trans = 54321 + trial

        for k in dep.k_grid:
            # --- requiere TODO #1 ---
            qc = build_grover(dep.nbits, target, iters=k)

            # ---------- TODO #2: ejecutar en backend local ----------
            # Pistas:
            #  - backend = Aer.get_backend("aer_simulator")
            #  - backend.set_options(method="matrix_product_state")
            #  - tqc = transpile(qc, backend=backend, optimization_level=2, seed_transpiler=seed_trans)
            #  - result = backend.run(tqc, shots=shots).result()
            #  - counts = result.get_counts()
            counts: Dict[str, int] = {}
            # COMPLETAR: asignar 'counts' con el diccionario bitstring->frecuencia
            raise NotImplementedError("Ejecuta el circuito en Aer y devuelve 'counts'")

            # ---------- TODO #3: elegir candidato del Top-K ----------
            # Pistas:
            # topk = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:topk_size]
            # best, hits = topk[0]  # bitstring y frecuencia
            best, hits = "", 0
            raise NotImplementedError("Ordena por frecuencia y elige el mejor candidato")

            # Validación end-to-end (no imprimir el candidato)
            if verify(dep.msg, best, dep.nbits):
                return AttackMetrics(
                    success=True,
                    msg=dep.msg,
                    nbits=dep.nbits,
                    trial_success=trial,
                    k_used=k,
                    best_hits=hits,
                )

    return AttackMetrics(
        success=False, msg=dep.msg, nbits=dep.nbits, trial_success=None, k_used=None, best_hits=None
    )

def report_metrics(m: AttackMetrics):
    if m.success:
        print(
            f"[✓] Ataque end-to-end logrado (nbits={m.nbits})  "
            f"trial={m.trial_success}  k={m.k_used}  hits≈{m.best_hits}"
        )
    else:
        print(
            f"[×] Intentos agotados (nbits={m.nbits}). "
            f"Ajusta shots/topk/trials o reduce nbits."
        )

# ---------------- CLI ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nbits", type=int, default=6)
    ap.add_argument("--backend", choices=["local"], default="local")  # en skeleton solo LOCAL
    ap.add_argument("--shots", type=int, default=4096)
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--topk", type=int, default=8)
    ap.add_argument("--alpha-range", default="0.35,0.45,0.55")
    ap.add_argument("--demo", action="store_true", help="Solo DEV: compila el oráculo con target real (server LAB_DEBUG=1).")
    args = ap.parse_args()

    alphas = [float(x) for x in args.alpha_range.split(",")]
    dep = deploy_oracle(args.nbits, alphas)

    metrics = execute_attack(
        dep,
        backend=args.backend,
        shots=args.shots,
        trials=args.trials,
        topk_size=args.topk,
        demo=args.demo,
    )
    report_metrics(metrics)

if __name__ == "__main__":
    main()










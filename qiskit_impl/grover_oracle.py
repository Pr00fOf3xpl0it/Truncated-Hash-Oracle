from qiskit import QuantumCircuit
from qiskit.circuit.library import MCXGate

def oracle_mark_target(n: int, target_bits: str) -> QuantumCircuit:
    qc = QuantumCircuit(n, name="Oracle")
    zero_pos = [i for i, b in enumerate(target_bits[::-1]) if b == '0']
    for q in zero_pos: qc.x(q)
    last = n - 1
    qc.h(last)
    mcx = MCXGate(n - 1)
    controls = list(range(n - 1))
    qc.append(mcx, controls + [last])
    qc.h(last)
    for q in zero_pos: qc.x(q)
    return qc

def diffusion_operator(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name="Diffusion")
    qc.h(range(n)); qc.x(range(n))
    last = n - 1
    qc.h(last)
    mcx = MCXGate(n - 1)
    controls = list(range(n - 1))
    qc.append(mcx, controls + [last])
    qc.h(last)
    qc.x(range(n)); qc.h(range(n))
    return qc

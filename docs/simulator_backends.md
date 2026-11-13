# Optional CPU and CUDA simulator backends

This experimental change keeps `Connector` as the public entry point. Real
board drivers and the default simulator path are unchanged. No hardware is
needed for these tests.

```python
connector = Connector(
    silent=True, logger=logger, cb_type='simulator',
    board_type='rp5_fpga_python', task_format='SI',
    config=config, crossbar_serial='my_array',
    simulator_backend='cpu',  # legacy (default), cpu, or cuda
)
connector.open_port()
try:
    result = connector.impact(task)
    results = connector.impact_many(tasks)  # ordered list, maximum 4096 commands
finally:
    connector.close_port()
```

`cpu` snapshots resolved board INI values, removing repeated ConfigParser
interpolation, and uses bounded per-connection caches of the native DAC/ADC
converters. These caches contain unit conversions, never device currents or
MVM responses. It does not change device equations, stochastic updates, pulse
length, ADC/DAC conversions, per-write persistence, or command order. Recreate
the Connector after changing its configuration. Simulator INI is likewise
snapshotted on simulator construction. `legacy` preserves dynamic lookup.

`cuda` additionally evaluates subthreshold mode10 device currents with optional
CUDA-enabled PyTorch and FP64 tensors. PyTorch is imported only when CUDA is
selected; missing CUDA raises an explicit error. It is not an ideal linear
matrix multiply: device nonlinearity, state clipping, resistance limits and
last-resistance updates remain represented. CPU summation follows BL order.
Programming and any threshold-crossing batch use the existing scalar model,
preserving NumPy RNG consumption. No GPU SET/RESET implementation is claimed.

`impact_many` accelerates all-mode10 CUDA batches; mixed commands, other
backends and real boards dispatch through ordinary ordered `impact` calls.
It never moves programming across reads. Below-threshold clipping is idempotent
and consumes no random numbers, so batched currents can be computed together
and state updates committed in command order. Commands must not depend on
earlier results within the same batch. Caller current/ADC checks still apply;
batching does not authorize omission of hardware guards.

## Verification

From the repository root, with the normal NumPy dependency installed:

```sh
python -m unittest tests.test_simulator_backends -v
python -m tests.benchmark_simulator_backends --count 2000
# Optional CUDA-enabled PyTorch installation required for the GPU measurement:
python -m tests.benchmark_simulator_backends --count 2000 --cuda
```

Tested on Windows, GTX1660SUPER, Python3.11, PyTorch2.4.1+cu124. CPU also
tested on Python3.12. Tests replay reads, SET/RESET pulses, scalar and batched
MVM, zeros, sparse voltages and a threshold-crossing fallback. ADC/response
tuples match exactly; device state tolerance is2e-13 relative; RNG state is
identical. CUDA libm results are not promised bit-identical for every possible
custom parameter set or near an ADC rounding boundary. This backend remains
opt-in pending broader numerical validation.

One warm benchmark (concurrent background CPU work; seconds, not a guarantee):

| Workload | Legacy | CPU | CUDA |
|---|---:|---:|---:|
|8000 calls: three resistance guards then sparse MVM|1.616|0.142|3.536|
|2000 MVM, batches of256, without guard reads|1.516|0.162|0.230|

All output tuples matched. CUDA batching removes much of the per-call kernel
launch overhead, but CPU remains faster on these small arrays. Do not enable
CUDA merely because it is available. These microbenchmarks do not establish
end-to-end training acceleration or a5000-neuron/8-hour runtime target. Full
training can remain dominated by command logging, scalar plasticity, guards
and persistence. Cross-array resident GPU storage is not implemented here.

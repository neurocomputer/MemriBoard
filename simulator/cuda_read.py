"""Optional CUDA evaluation of subthreshold device currents, not ideal G@V.

Programming, threshold-crossing reads and RNG stay in the scalar reference.
FP64 device equations are evaluated on CUDA. Last resistance and clipping are
written back before the next command. Summation remains in reference BL order.
Small arrays can be slower on CUDA; selection is explicit, never automatic.
"""
from __future__ import annotations

from simulator.memristor import MemristorModel


class CudaRead:
    def __init__(self) -> None:
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA requested but unavailable; install a CUDA-enabled PyTorch')
        self.torch = torch
        self.calls = 0
        self.fallback_calls = 0

    def mvm(self, crossbar: list[list[MemristorModel]], *, vol: list[float],
            wl: int, gain: float, sum_gain: float, adc_bit: int,
            vol_ref_adc: float) -> int:
        return self.mvm_batch(crossbar,[(wl,vol)],gain=gain,sum_gain=sum_gain,
                              adc_bit=adc_bit,vol_ref_adc=vol_ref_adc)[0]

    def mvm_batch(self, crossbar: list[list[MemristorModel]],
                  commands: list[tuple[int,list[float]]], *, gain: float,
                  sum_gain: float, adc_bit: int, vol_ref_adc: float) -> list[int]:
        """Batch subthreshold operations; preserve BL reduction and last-read state.

        Subthreshold state clipping is idempotent, with no RNG draws. Therefore
        currents can be computed concurrently, then committed in command order.
        Any threshold-crossing voltage falls back for the entire ordered batch.
        """
        from simulator.src import send_mode_mvm_to_crossbar
        groups = [[(row[wl],v) for row,v in zip(crossbar,vol) if v != 0]
                  for wl,vol in commands]
        active = [pair for group in groups for pair in group]
        if any(not c.voltage_react_set < v < c.voltage_react_reset for c,v in active):
            self.fallback_calls += len(commands)
            return [send_mode_mvm_to_crossbar(crossbar,vol=vol,wl=wl,gain=gain,
                sum_gain=sum_gain,adc_bit=adc_bit,vol_ref_adc=vol_ref_adc) for wl,vol in commands]
        if not active:
            return [0]*len(commands)
        torch = self.torch
        # All per-device parameters come from the actual model objects.
        rows = [[v,c.state_variable,c.DR,c.T,c.B,c.ELECTRON_CHARGE,
                 c.BOLZMAN,c.fi_electron,c.area_filament,
                 c.resistance_max,c.resistance_min,float(c.noise_flag)] for c,v in active]
        data = torch.tensor(rows,dtype=torch.float64,device='cuda')
        v,w,dr,temp,b,e,k,barrier,area,rmax,rmin,noise = data.unbind(1)
        w = torch.where(noise != 0,w.clamp(0.,1.),w)
        linear = dr*1e8*torch.exp(1-300/temp)*v
        nonlinear = b*v*torch.exp(-(e/(k*temp))*(barrier-.5*.07*torch.sqrt(torch.abs(v))))
        current = (w*linear+(1-w)*nonlinear)*area
        if bool(torch.any((current == 0)&((rmax != 0)|(rmin != 0)))):
            raise ZeroDivisionError('Zero device current with enabled resistance limits')
        current = torch.where((rmax != 0)&(v/current > rmax),v/rmax,current)
        current = torch.where((rmin != 0)&(v/current < rmin),v/rmin,current)
        values = torch.stack((w,current),dim=1).cpu().tolist()
        output: list[int] = []
        cursor = 0
        for group in groups:
            total = 0.
            for cell,voltage in group:
                state,amperes = values[cursor]
                cursor += 1
                cell.state_variable = state
                cell.last_resistance = voltage/amperes if amperes != 0 else float('inf')
                total += amperes
            output.append(int(2**adc_bit*(total*sum_gain)/vol_ref_adc))
        self.calls += len(commands)
        return output

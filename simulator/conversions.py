"""Bounded, per-connection caches for immutable SIM conversion parameters."""
from __future__ import annotations

from collections.abc import Mapping
from manager.service import v2d, d2v, a2r


class SimulatorConversions:
    """Cache converter outputs, never device state or measured MVM values."""

    def __init__(self, board: Mapping[str,str]) -> None:
        self.bits = int(board['dac_bit'])
        self.reference = float(board['vol_ref_dac'])
        self.encoded: dict[float,int] = {}
        self.decoded: dict[int,float] = {}
        self.resistances: dict[int,int] = {}
        self.read_parameters = (float(board['gain']),float(board['res_load']),
            float(board['vol_read']),int(board['adc_bit']),float(board['vol_ref_adc']),
            float(board['res_switches']))

    def encode(self, voltage: float) -> int:
        voltage = abs(float(voltage))
        if voltage not in self.encoded:
            result = v2d(self.bits,self.reference,voltage)
            if len(self.encoded)>=4096:
                self.encoded.clear()
            self.encoded[voltage] = result
        return self.encoded[voltage]

    def decode(self, code: int) -> float:
        if code not in self.decoded:
            result = d2v(self.bits,self.reference,code)
            if len(self.decoded)>=4096:
                self.decoded.clear()
            self.decoded[code] = result
        return self.decoded[code]

    def resistance(self, adc: int) -> int:
        adc = int(adc)
        if adc not in self.resistances:
            result = a2r(*self.read_parameters,adc)
            if len(self.resistances)>=16384:
                self.resistances.clear()
            self.resistances[adc] = result
        return self.resistances[adc]

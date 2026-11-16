"""Finite public Connector benchmark; no physical I/O. Run from repo root."""
import argparse
import copy
from configparser import ConfigParser
import json
import logging
from pathlib import Path
import random
import shutil
import tempfile
import time

import numpy as np
from manager.board import Connector
from simulator.src import create_crossbar_array


def run(backend: str, initial: Path, root: Path, count: int) -> tuple[float,list[tuple[float,int,int]]]:
    config = ConfigParser()
    config.read('simulator/simulator_settings.ini')
    serial = str(root/backend)
    shutil.copyfile(initial,serial+'.cb')
    connector = Connector(silent=True,logger=logging.getLogger(),cb_type='simulator',
        board_type='rp5_fpga_python',task_format='SI',config=config,
        crossbar_serial=serial,simulator_backend=backend)
    connector.open_port()
    results = []
    started = time.perf_counter()
    try:
        for i in range(count):
            # Representative guards then one sparse MVM, repeated across WLs.
            for bl in (5,10,15):
                results.append(connector.impact(dict(mode_flag=7,wl=i%8,bl=bl,vol=0.,sign=0,pulse_width=0.,id=i)))
            results.append(connector.impact(dict(mode_flag=10,wl=i%8,vol=[.05 if b in (5,10,15) else 0. for b in range(32)],id=0)))
    finally:
        connector.close_port()
    return time.perf_counter()-started,results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--cuda',action='store_true')
    parser.add_argument('--count',type=int,default=5000)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        random.seed(101)
        np.random.seed(101)
        create_crossbar_array(str(root/'initial'),32,8)
        output = {}
        reference = None
        for backend in ['legacy','cpu']+(['cuda'] if args.cuda else []):
            duration,result = run(backend,root/'initial.cb',root,args.count)
            if reference is None:
                reference = result
            output[backend] = dict(seconds=duration,calls=len(result),exact_output_parity=result==reference)
        # A separate workload: no guards/writes, chunked MVM on one array.
        # This is not the end-to-end training speedup.
        batch_results = {}
        batch_reference = None
        tasks = [dict(mode_flag=10,wl=i%8,vol=[.05 if (b+i)%3 else 0. for b in range(32)],id=i) for i in range(args.count)]
        for backend in ['legacy','cpu']+(['cuda'] if args.cuda else []):
            config = ConfigParser()
            config.read('simulator/simulator_settings.ini')
            serial = str(root/('batch_'+backend))
            shutil.copyfile(root/'initial.cb',serial+'.cb')
            connector = Connector(silent=True,logger=logging.getLogger(),cb_type='simulator',
                board_type='rp5_fpga_python',config=config,crossbar_serial=serial,
                task_format='SI',simulator_backend=backend)
            connector.open_port()
            started = time.perf_counter()
            results = []
            try:
                for start in range(0,len(tasks),256):
                    results.extend(connector.impact_many(tasks[start:start+256]))
            finally:
                connector.close_port()
            duration = time.perf_counter()-started
            if batch_reference is None:
                batch_reference = results
            batch_results[backend] = dict(seconds=duration,calls=len(results),exact_output_parity=results==batch_reference)
        output['mvm_batches_256'] = batch_results
        print(json.dumps(output,indent=2))


if __name__ == '__main__':
    main()

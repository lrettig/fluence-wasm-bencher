"""
Copyright 2018 Fluence Labs Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from project.settings import interpreter_launches_count,\
    compiler_launches_count
#   test_export_function_name

from os import listdir
from os.path import join
from time import time
import subprocess
from subprocess import Popen
from collections import defaultdict
import logging
import durationpy
import re


class Record:
    """Contains measures of one test launch.

    Attributes
    ----------
    time : time_type
        The execution time of one test.
    cpu_load : int
        The cpu load (in percents) of one test (currently not supported).

    """
    def __init__(self, time=0.0, compile_time=0.0, exec_time=0.0, cpu_load=0):
        self.time = time
        self.compile_time = compile_time
        self.exec_time = exec_time
        self.cpu_load = cpu_load  # TODO


class WasmVMBencher:
    """Launches each VM on given directory on each provided test."""

    def __init__(self, vm_dir="/"):
        self.vm_dir = vm_dir
        #self.enabled_vm = listdir(vm_dir)
        #self.enabled_vm = ['wavm', 'wasmer', 'wasmi', 'life', 'wagon']
        self.enabled_vm = []

    def run_tests(self, test_descriptors, vm_descriptors):
        """Launches provided tests and returns their execution time.

        Parameters
        ----------
        test_descriptors
            Descriptors of test that should be used for benchmark Wasm VM.
        vm_descriptors
            Descriptors of Wasm VM that should be tested on provided tests.

        Returns
        -------
        {vm : {test_name : [Records]}}
            Collected test results.

       """
        # {vm : {test_name : [Records]}}
        results = defaultdict(lambda: defaultdict(list))
        logger = logging.getLogger("wasm_bencher_logger")

        test_export_function_name = 'main'
        self.enabled_vm = list(vm_descriptors.keys())


        for test_name, test_path in test_descriptors.items():
            logger.info("<wasm_bencher>: launch {} test".format(test_name))
            for vm in self.enabled_vm:
                if vm not in vm_descriptors:
                    continue

                vm_binary_full_path = join(vm_descriptors[vm].vm_binary_path)
                cmd = vm_binary_full_path + " " \
                      + vm_descriptors[vm].vm_launch_cmd.format(wasm_file_path=test_path,
                                                                function_name=test_export_function_name)

                launch_count = compiler_launches_count if vm_descriptors[vm].is_compiler_type \
                    else interpreter_launches_count
                for _ in range(launch_count):
                    logger.info("<wasm_bencher>: {}".format(cmd))
                    if vm == "lifePolymerase":
                        result_record = self.do_life_poly_test(cmd)
                    elif vm == "wavm":
                        result_record = self.do_wavm_test(cmd)
                    elif vm == "wasmer":
                        result_record = self.do_wasmer_test(cmd)
                    elif vm == "v8-liftoff" or vm == "v8-turbofan" or vm == "v8-interpreter":
                        result_record = self.do_v8_test(cmd)
                    elif vm == "wagon":
                        result_record = self.do_wagon_test(cmd)
                    elif vm == "wabt":
                        result_record = self.do_wabt_test(cmd)
                    else:
                        result_record = self.__do_one_test(cmd)
                    results[vm][test_name].append(result_record)
                    logger.info("<wasm_bencher>: {} result collected: time={} compiletime={} exectime={}".format(vm, result_record.time, result_record.compile_time, result_record.exec_time))

        return results

    def __do_one_test(self, vm_cmd):
        """Launches provided shell command string via subprocess.Popen and measure its execution time.

        Parameters
        ----------
        vm_cmd : str
            An exactly command that should be executed.

        Returns
        -------
        time_type
            An elapsed time of provided cmd execution.

        """
        start_time = time()
        Popen(vm_cmd, shell=True).wait(None)
        end_time = time()
        return Record(end_time - start_time)

    def do_wasmer_test(self, vm_cmd):
        """02/15/2019 11:23:55 PM <wasm_bencher>: /engines/wasmer/target/release/wasmer run /wasmfiles/ecpairing.wasm
           compile time: 88.381ms
           total run time (compile + execute): 172.762637ms
           02/15/2019 11:23:55 PM <wasm_bencher>: wasmer result collected: time=0.18068552017211914 compiletime=0.0
        """ 
        # the other wasmer patch prints "run time: 172.762637ms"
        #runtime_match = re.search("run time: ([\w\.]+)", runtime_line)
        time_parse_info = {
          'compile_line_num' : 0,
          'exec_line_num' : 1,
          'compile_regex': "compile time: ([\w\.]+)",
          'exec_regex': "total run time \(compile \+ execute\): ([\w\.]+)"
        }
        result = self.doCompilerTest(vm_cmd, time_parse_info, stderr_redir=False)
        execution_time = result.exec_time - result.compile_time
        return Record(time=result.time, compile_time=result.compile_time, exec_time=execution_time)

    def do_wavm_test(self, vm_cmd):
        """02/16/2019 12:03:32 AM <wasm_bencher>: /engines/wavm-build/bin/wavm-run /wasmfiles/ecpairing.wasm -f main
           Instantiation/compile time: 1654661us
           Invoke/run time: 48594us
        """
        time_parse_info = {
          'compile_line_num' : 0,
          'exec_line_num' : 1,
          'compile_regex': "Instantiation/compile time: ([\w\.]+)",
          'exec_regex': "Invoke/run time: ([\w\.]+)"
        }
        return self.doCompilerTest(vm_cmd, time_parse_info)

    def do_life_poly_test(self, vm_cmd):
        """02/15/2019 03:34:52 PM <wasm_bencher>: /engines/life/life -polymerase -entry main /wasmfiles/ecpairing.wasm
           [Polymerase] Compilation started.
           [Polymerase] Compilation finished successfully in 9.683856378s.
           return value = 0, duration = 46.712798ms
        """
        time_parse_info = {
          'compile_line_num' : 1,
          'exec_line_num' : 2,
          'compile_regex': "Compilation finished successfully in ([\w\.]+s).",
          'exec_regex': "duration = ([\w\.]+)"
        }
        return self.doCompilerTest(vm_cmd, time_parse_info)

    def do_v8_test(self, vm_cmd):
        """02/17/2019 07:14:04 PM <wasm_bencher>: /engines/node/node --wasm-interpret-all /engines/node/node-timer.js /wasmfiles/ecpairing.wasm
        args: [ '/wasmfiles/ecpairing.wasm' ]
        ---- reading wasm file..
        ---- wasm file read.
        instantiate: 67.677ms
        ---- calling main...
        run-main: 13406.809ms
        ---- wasm returns: undefined
        """
        time_parse_info = {
          'compile_line_num' : 3,
          'exec_line_num' : 5,
          'compile_regex': "instantiate: ([\w\.]+)",
          'exec_regex': "run-main: ([\w\.]+)"
        }
        return self.doCompilerTest(vm_cmd, time_parse_info)

    def do_wabt_test(self, vm_cmd):
        """02/16/2019 09:56:43 PM <wasm_bencher>: /engines/wabt/bin/wasm-interp /wasmfiles/ecpairing.wasm --run-all-exports
        ec_pairing() => error: argument type mismatch
        main() =>
        parse time: 45430us
        exec time: 62390657us
        """
        time_parse_info = {
          'compile_line_num' : -2,
          'exec_line_num' : -1,
          'compile_regex': "parse time: ([\w]+)",
          'exec_regex': "exec time: ([\w]+)"
        }
        return self.doCompilerTest(vm_cmd, time_parse_info)

    def do_wagon_test(self, vm_cmd):
        """02/16/2019 09:56:29 PM <wasm_bencher>: /engines/wagon/cmd/wasm-run/wasm-run /wasmfiles/ecpairing.wasm
        parse time: 10.763108ms
        ec_pairing() => wasm-run: running exported functions with input parameters is not supported
        main() =>
        memory() => wasm-run: running exported functions with input parameters is not supported
        exec time: 13.551017849s
        """
        time_parse_info = {
          'compile_line_num' : 0,
          'exec_line_num' : -1,
          'compile_regex': "parse time: ([\w\.]+)",
          'exec_regex': "exec time: ([\w\.]+)"
        }
        return self.doCompilerTest(vm_cmd, time_parse_info)

    def doCompilerTest(self, vm_cmd, time_parse_info, stderr_redir=True):
        start_time = time()
        if stderr_redir:
            vm_process = Popen(vm_cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        else:
            vm_process = Popen(vm_cmd, stdout=subprocess.PIPE, shell=True)
        vm_process.wait(None)
        end_time = time()
        total_time = end_time - start_time
        stdoutlines = [str(line, 'utf8') for line in vm_process.stdout]
        print(("").join(stdoutlines), end="")
        compile_line = stdoutlines[time_parse_info['compile_line_num']]
        compile_match = re.search(time_parse_info['compile_regex'], compile_line)
        compile_time = durationpy.from_str(compile_match[1])
        exec_line = stdoutlines[time_parse_info['exec_line_num']]
        exec_match = re.search(time_parse_info['exec_regex'], exec_line)
        exec_time = durationpy.from_str(exec_match[1])
        return Record(time=total_time, compile_time=compile_time.total_seconds(), exec_time=exec_time.total_seconds())






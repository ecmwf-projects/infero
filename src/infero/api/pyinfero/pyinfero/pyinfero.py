#
# (C) Copyright 1996- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import copy
import cffi
import platform
import numpy as np


ffi = cffi.FFI()


class InferoException(RuntimeError):
    pass


class PatchedLib:
    """
    Patch a CFFI library with error handling

    Finds the header file associated with the C API and parses it, loads the shared library,
    and patches the accessors with automatic python-C error handling.
    """
    __type_names = {}

    def __init__(self):

        ffi.cdef(self.__read_header())        

        libName = {
            'Linux': 'libinferoapi.so'
        }

        self.__lib = ffi.dlopen(libName[platform.system()])

        # All of the executable members of the CFFI-loaded library are functions in the Infero
        # C API. These should be wrapped with the correct error handling. Otherwise forward
        # these on directly.

        for f in dir(self.__lib):
            try:
                attr = getattr(self.__lib, f)
                setattr(self, f, self.__check_error(attr, f) if callable(attr) else attr)
            except Exception as e:
                print(e)
                print("Error retrieving attribute", f, "from library")

    def __read_header(self):
        with open(os.path.join(os.path.dirname(__file__), 'pyinfero-headers.h'), 'r') as f:
            return f.read()

    def __check_error(self, fn, name):
        """
        If calls into the Infero library return errors, ensure that they get detected and reported
        by throwing an appropriate python exception.
        """

        def wrapped_fn(*args, **kwargs):
            retval = fn(*args, **kwargs)
            # if retval != self.__lib.FDB_SUCCESS:
            if retval != 0:
                error_str = "Error in function {}: {}".format(name, self.__lib.infero_error_string(retval))
                raise InferoException(error_str)
            return retval

        return wrapped_fn


# Bootstrap the library

lib = PatchedLib()



class Infero:
    """
    Minimal class that wraps the infero C API
    """

    def __init__(self, model_path, model_type):

        # path to infero model
        self.model_path = model_path

        # model type (see available infero backends)
        self.model_type = model_type

        # inference configuration string
        self.config_str = f"path: {self.model_path}\ntype: {self.model_type}"

        # C API handle
        self.infero_hdl = None

    def initialise(self):
        """
        Initialise the library
        :return:
        """

        # main args not directly used by the API
        args = [""]
        cargs = [ffi.new("char[]", ar.encode('ascii')) for ar in args]
        argv = ffi.new(f'char*[]', cargs)

        # init infero lib
        lib.infero_initialise(len(cargs), argv)
        config_cstr = ffi.new("char[]", self.config_str.encode('ascii'))

        # get infero handle
        self.infero_hdl = ffi.new('infero_handle_t**')

        # self.infero_hdl = ffi.new('int*')
        lib.infero_create_handle_from_yaml_str(config_cstr, self.infero_hdl)

        # open the handle
        lib.infero_open_handle(self.infero_hdl[0])

    def infer(self, input_data, output_shape):
        """
        Run Inference
        :param input_data:
        :param output_shape:
        :return:
        """

        # input set to Fortran order
        input_data = np.array(input_data, order='C', dtype=np.float32)
        cdata1p = ffi.cast("float *", input_data.ctypes.data)
        cshape1 = ffi.new(f"int[]", input_data.shape)

        # output also expected in Fortran order
        cdata2 = np.zeros(output_shape, order='C', dtype=np.float32)
        cdata2p = ffi.cast("float *", cdata2.ctypes.data)
        cshape2 = ffi.new(f"int[]", output_shape)

        lib.infero_inference_float_ctensor(self.infero_hdl[0],
                                           len(input_data.shape), cdata1p, cshape1,
                                           len(output_shape), cdata2p, cshape2)

        return_output = copy.deepcopy(cdata2)
        return_output = np.array(return_output)

        return return_output

    def finalise(self):
        """
        Finalise the Infero API
        :return:
        """

        # close the handle
        lib.infero_close_handle(self.infero_hdl[0])

        # delete the handle
        lib.infero_delete_handle(self.infero_hdl[0])

        # finalise
        lib.infero_finalise()

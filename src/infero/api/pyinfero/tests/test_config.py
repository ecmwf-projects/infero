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
import numpy as np
import pyinfero
from pyinfero.pyinfero import InferoException

import pytest

def test_invalid_config():

    with pytest.raises(InferoException):
        infero = pyinfero.Infero("path_to_model", "unsupported-backend")
        infero.initialise()
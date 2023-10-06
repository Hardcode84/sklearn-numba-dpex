from numpy import int64

from numba_mlir.kernel import kernel_func as func
from numba_mlir.kernel import *

local_array = local.array
private_array = private.array

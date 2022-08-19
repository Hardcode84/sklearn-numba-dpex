import warnings


# TODO: when dpctl.SyclDevice also exposes relevant attributes,
# remove the dependency to opencl and only use dpctl.
# A unittest in test_device_params check the availability of the relevant
# attributes and will fault when pyopencl is not needed anymore.
try:
    import pyopencl
except ImportError:
    pyopencl = None


class _DEFAULT_VALUES:
    global_mem_cache_size = 1048576  # 1 MiB
    preferred_work_group_size_multiple = 64


class _DeviceParams:
    """This class aggregates information about a SyclDevice with informations
    from pyopencl.

    If pyopencl is not available, it will try to guess missing informations,
    either using safe default values that might be inaccurate, or more
    complex routines that might be slower to fetch the information."""

    def __init__(self, sycl_device):

        self.has_aspect_fp64 = sycl_device.has_aspect_fp64
        self.max_work_group_size = sycl_device.max_work_group_size
        self._sycl_device = sycl_device
        self.name = self._sycl_device.name
        self._cl_device = next(
            (
                device
                for platform in _get_cl_platforms()
                for device in platform.get_devices()
                if device.name == self.name
            ),
            None,
        )

    @property
    def preferred_work_group_size_multiple(self):
        try:
            return self._sycl_device.preferred_work_group_size_multiple
        except AttributeError:
            return _get_cl_param(
                cl_device=self._cl_device,
                value="preferred_work_group_size_multiple",
                default=_DEFAULT_VALUES.preferred_work_group_size_multiple,
                device_name=self.name,
            )

    @property
    def global_mem_cache_size(self):
        try:
            return self._sycl_device.global_mem_cache_size
        except AttributeError:
            return _get_cl_param(
                cl_device=self._cl_device,
                value="global_mem_cache_size",
                default=_DEFAULT_VALUES.global_mem_cache_size,
                device_name=self.name,
            )


def _get_cl_platforms():
    return pyopencl.get_platforms() if pyopencl else []


def _get_cl_param(cl_device, value, default, device_name):
    if cl_device is None:
        _warns_missing_cl_param(value, default, device_name)
        return default
    return getattr(cl_device, value)


def _warns_missing_cl_param(value, default, device_name):
    text = [
        f"Trying to fetch the parameter {value} for the executing device {device_name} "
        f"from opencl interface "
    ]
    if pyopencl is None:
        text.append("with pyopencl, but pyopencl is missing.")
    else:
        text.append(
            "but opencl can't find the device. Ensure the opencl drivers are available on the "
            "system for this device."
        )
    text.append(
        f"\nUsing default value {value} = {default} as a fallback, which might be inadapted."
    )
    warnings.warn("".join(text), RuntimeWarning)

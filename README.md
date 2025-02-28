# sklearn-numba-dpex

Experimental plugin for scikit-learn to be able to run (some) estimators on Intel GPUs
via [numba-dpex](https://github.com/IntelPython/numba-dpex). Support for other GPU
constructors is also on the roadmap and depends on progress of interoperability features
of the `numba-dpex` stack.

This package requires working with the following branch of scikit-learn:

- `feature/engine-api` branch on https://github.com/scikit-learn/scikit-learn

A step-by-step guide is provided in this README for installing `numba-dpex`, along with
the `feature/engine-api` branch of `scikit-learn` and this plugin from source.

🚧 TODO: at the moment it is unusually complicated to install this plugin and its
dependencies. Once `feature/engine-api` is merge and released in scikit-learn and we aim
to make it possible to install `sklearn-numba-dpex` and all its dependencies with a one
liner `conda install` command or `pip install` or both.

## List of Included Engines

- `sklearn.cluster.KMeans` for the standard LLoyd's algorithm on dense data arrays,
  including `kmeans++` support.

## Getting started:

### Step 1: Installing a `numba_dpex` environment

Getting started requires a working environment for using `numba_dpex`. Currently a
[conda install](#using-a-conda-installation) or a [docker image](#using-the-docker-image)
are available.

#### Using a conda installation

Conda does not currently support installation of the low-level runtime libraries for
GPUs, so the first part of the installation guide consists in installing those libraries
on the host system.

The second part consists in running conda commands that create the environment with
all the required packages and configuration. Note that the installation logic is a bit
complicated since it mixes packages from several conda channels `conda-forge`,
`dppy/label/dev`, and `intel`, some of which being experimental. Neither the builds nor
the channels are maintained by the `sklearn_numba_dpex` team and their level of
stability is unknown.

🚧 TODO: update the instructions to install everything from non-dev conda packages on
always up-to-date channels whenever it's available.

##### Install low-level runtime libraries for your GPU (1/2)

At this time, only Intel GPUs are supported.

###### Intel GPU runtime libraries

For Intel GPUs, two backends are available. You might want to install both of those,
and test if one gives better performances.

🚧 TODO: write a guide on how to select the device and the backend in a python script.

- **Intel OpenCL for GPU**: the intel OpenCL runtime can be installed following
  [this link](https://github.com/intel/compute-runtime#installation-options).

  ⚠⚠⚠ **WARNING** ⚠⚠⚠: for Ubuntu (confirmed for `focal` and `jammy`) the `apt`-based
  installation is broken, see https://github.com/IntelPython/dpctl/issues/1010.
  Prefer the upstream `.deb` packages provided at:
  https://github.com/intel/compute-runtime/releases.

  <details>

  <summary markdown="span">Click to expand a guide for the recommended installation
  steps for Ubuntu</summary>

  ⚠ Like whenever installing packages outside of official repositories, existing
  workarounds might make your system unstable and are not recommended outside of a
  containerized environment and/or for expert users.

  To not alter the `apt`-based version tree too much and risk other compatibility
  issues, the recommended workaround consists in identifying the version that is
  officially supported by your OS (use [packages.ubuntu.com](https://packages.ubuntu.com/search?keywords=intel-opencl-icd&searchon=names))
  then find the corresponding build from the [Intel release page on github](https://github.com/intel/compute-runtime/releases)
  and follow the instruction from the release page, e.g for `jammy`:

  ```bash
  mkdir neo
  cd neo
  wget https://github.com/intel/compute-runtime/releases/download/22.14.22890/intel-gmmlib_22.0.2_amd64.deb
  wget https://github.com/intel/intel-graphics-compiler/releases/download/igc-1.0.10840/intel-igc-core_1.0.10840_amd64.deb
  wget https://github.com/intel/intel-graphics-compiler/releases/download/igc-1.0.10840/intel-igc-opencl_1.0.10840_amd64.deb
  wget https://github.com/intel/compute-runtime/releases/download/22.14.22890/intel-opencl-icd_22.14.22890_amd64.deb
  dpkg -i *.deb  # requires root permissions
  apt-get install -y ocl-icd-libopencl1  # requires root permissions
  cd ../ && rm -Rf neo
  ```

</details>

- **oneAPI level zero loader**: alternatively, or in addition, the oneAPI level zero
  backend can be used. This backend is more experimental, and is sometimes preferred
  over OpenCL. Source and `deb` archives are available
  [here](https://github.com/oneapi-src/level-zero/releases).

###### Give permissions to submit GPU workloads

Non-root users might lack permission to access the GPU device to submit workloads. Add
the current user to the `video` group and/or `render` group:

```bash
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER
```

##### Setup a conda environment for numba-dpex (2/2)

You can setup a [`conda`](https://docs.conda.io/en/latest/) environment, and install
dependencies (`numba-dpex` and `intel::dpcpp_linux-64`) distributed on the
`conda-forge`, `intel` and experimental `dppy/label/dev` channels with:

```bash
export CONDA_DPEX_ENV_NAME=my-dpex-env
```

(where you can replace the name of the environment `my-dpex-env` with a name of your
liking) followed by

```bash
conda create --yes --name $CONDA_DPEX_ENV_NAME \
             --channel dppy/label/dev \
             --channel conda-forge \
             --channel intel \
             numba-dpex=0.21.1=py310h776878d_35
```

Note that different versions of `sklearn_numba_dpex` can require to pin different
versions, builds or channels in this last command.

`scikit-learn` must be installed from source using an experimental version available on
[`feature/engine-api`](https://github.com/scikit-learn/scikit-learn/tree/feature/engine-api), a
development branch. Be careful to build with compatible `python` and `numpy` versions.

<details>

<summary markdown="span">Click to expand a guide for building scikit-learn </summary>

We use a separate conda environment dedicated to building `scikit-learn`. The following
sequence of commands will create the appropriate conda environment, build the
scikit-learn binary, then remove the environment:

```bash
conda activate $CONDA_DPEX_ENV_NAME
export DPEX_PYTHON_VERSION=$(python -c "import platform; print(platform.python_version())")
export DPEX_NUMPY_VERSION=$(python -c "import numpy; print(numpy.__version__)")
conda create --yes --name sklearn-dev \
                   --channel conda-forge \
                   "python==$DPEX_PYTHON_VERSION" \
                   "numpy==$DPEX_NUMPY_VERSION" \
                   scipy cython joblib threadpoolctl pytest compilers
conda activate sklearn-dev
git clone https://github.com/scikit-learn/scikit-learn -b "feature/engine-api" --depth 1
cd scikit-learn
git checkout 2ccfc8c4bdf66db005d7681757b4145842944fb9
python setup.py bdist_wheel
conda activate $CONDA_DPEX_ENV_NAME
cd dist/
pip install *.whl
unset DPEX_PYTHON_VERSION
unset DPEX_NUMPY_VERSION
conda env remove --name sklearn-dev --yes
cd ../../
conda deactivate
rm -Rf scikit-learn
```

</details>

Finally, activate the environment with the command:
```bash
conda activate my-dpex-env
```

#### Using the docker image

Alternatively, a docker image is available and provides an up-to-date, one-command
install environment. You can either build it from the [Dockerfile](./docker/Dockerfile):

```bash
cd docker
DOCKER_BUILDKIT=1 docker build . -t numba_dpex_dev
```

or pull the docker image from
[this publicly available repository](https://hub.docker.com/repository/docker/jjerphan/numba_dpex_dev):

```bash
docker pull jjerphan/numba_dpex_dev:latest
```

Run the container in interactive mode with your favorite docker flags, for example:

```bash
docker run --name my_container_name -it -v /my/host/volume/:/mounted/volume --device=/dev/dri jjerphan/numba_dpex_dev:latest
```

or alternatively, replace `jjerphan/numba_dpex_dev:latest` by `numba_dpex_dev` or
any tag you used when building the image locally from the provided `Dockerfile`.

⚠ The flag `--device=/dev/dri` is **mandatory** to enable the gpu within the container,
also the user starting the `docker run` command must have access to the gpu, see
[Give permissions to submit GPU workloads](#give-permissions-to-submit-gpu-workloads).

Unless using the flag `--rm` when starting a container, you can restart it after it was
exited, with the command:

```bash
sudo docker start -a -i my_container_name
```

Once you have loaded into the container, follow those instructions to install the
`feature/engine-api` branch of scikit-learn:

```bash
git clone https://github.com/scikit-learn/scikit-learn -b "feature/engine-api" --depth 1
cd scikit-learn
git checkout 2ccfc8c4bdf66db005d7681757b4145842944fb9
pip install -e .
cd ..
```

### Step 2: Check the installation of the environment was successfull

Once the environment you just installed with one of those two methods is activated,
you can inspect the available hardware:

```bash
python -c "import dpctl; print(dpctl.get_devices())"
```

this should print a list of available devices, including `cpu` and `gpu` devices, once
for each available backends (`opencl`, `level_zero`,...).

### Step 3: install this plugin

FIXME: currently, non-editable mode installation does not work.

When loaded into your `numba_dpex` + `scikit-learn` environment from previous steps,
run:

```bash
git clone https://github.com/soda-inria/sklearn-numba-dpex
cd sklearn-numba-dpex
pip install -e .
```

## Intended usage

See the `sklearn_numba_dpex/kmeans/tests` folder for example usage.

🚧 TODO: write some examples here instead.

### Running the tests

To run the tests run the following from the root of the `sklearn_numba_dpex` repository:

```bash
pytest sklearn_numba_dpex
```

To run the `scikit-learn` tests with the `sklearn_numba_dpex` engine you can run the
following:

```bash
SKLEARN_NUMBA_DPEX_TESTING_MODE=1 pytest --sklearn-engine-provider sklearn_numba_dpex --pyargs sklearn.cluster.tests.test_k_means
```

(change the `--pyargs` option accordingly to select other test suites).

The `--sklearn-engine-provider sklearn_numba_dpex` option offered by the sklearn pytest
plugin will automatically activate the `sklearn_numba_dpex` engine for all tests.

Tests covering unsupported features (that trigger
`sklearn.exceptions.FeatureNotCoveredByPluginError`) will be automatically marked as
_xfailed_.

### Running the benchmarks

Repeat the pip installation step exposed in [step 3](#step-3-install-this-plugin) with
the following edit:

```bash
pip install -e .[benchmark]
```

(i.e adding the _benchmark_ extra-require), followed by:

```bash
cd benckmark
python ./kmeans.py
```

to run a benchmark for different k-means implementations and print a short summary of
the performance.

The command

```bash
python ./kmeans --help
```

will output more information about the available parameters.

### Notes about the preferred floating point precision (float32)

In many machine learning applications, operations using single-precision (float32)
floating point data require twice as less memory that double-precision (float64), are
regarded as faster, accurate enough and more suitable for GPU compute. Besides, most
GPUs used in machine learning projects are significantly faster with float32 than with
double-precision (float64) floating point data.

To leverage the full potential of GPU execution, it's strongly advised to use a float32
data type.

By default, unless specified otherwise numpy array are created with type float64, so be
especially careful to the type whenever the loader does not explicitly document the
type nor expose a type option.

Transforming NumPy arrays from float64 to float32 is also possible using
[`numpy.ndarray.astype`](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.astype.html),
although it is less recommended to prevent avoidable data copies. `numpy.ndarray.astype`
can be used as follows:

```python
X = my_data_loader()
X_float32 = X.astype(float32)
my_gpu_compute(X_float32)
```

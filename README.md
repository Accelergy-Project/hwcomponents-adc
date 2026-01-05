# HWComponents-ADC
HWComponents-ADC models the area and energy of Analog-Digital Converters (ADCs) for use
in analog & mixed-signal accelerator designs.

These models are for use with the HWComponents package, found at
https://accelergy-project.github.io/hwcomponents/.

Models are based on statistical analysis of published ADC performance data in Boris
Murmann's ADC Performance Survey [1]. The energy model is based on the observation that
the maximum efficiency of an ADC is bounded by the sampling rate and the resolution [1],
and the area model is based on regression analysis. Estimations are optimistic; they
answer the question "what is the best possible ADC design for the given parameters?".

## Installation

Install from PyPI:

```bash
pip install hwcomponents-adc

# Check that the installation is successful
hwc --list | grep ADC
```

## Usage
### Inerface

This model introduces the ADC model. ADC models can be instantiated with the
following parameters:
- `n_bits`: the resolution of the ADC
- `tech_node`: the technology node in meters
- `n_adcs`: the number of ADCs working together, in the case of alternating
  ADCs
- `throughput`: the aggregate throughput of the ADCs, in samples per second

ADCs support the following actions:
- `read` or `convert`: Convert a single value from analog to digital. Note: if
  there are multiple ADCs, this is a single conversion from a single ADC.

### Exploring Tradeoffs
There are several tradeoffs available around ADC design:
- Lower-resolution ADCs are smaller and more energy-efficient.
- Using more ADCs in parallel allows for a lower frequency, but increases the
  area.
- Using fewer ADCs in parallel allows for a higher frequency. Up to a point,
  this will not increase the area or energy/area of the ADCs. However, at some
  this will result in an exponential increase in energy/area.
- Lower-resolution ADCs can run at higher frequencies before the exponential
  increase in energy/area occurs.

When the HWComponents-ADC runs, it will output a list of alternative design options.
Each will report a number of ADCs and frequency needed to achieve the desired
throughput, as well as the area and energy of the ADCs. You can then use this
information to make tradeoffs between ADC resolution, frequency, and number of
ADCs.

HWComponents-ADC is the work of Tanner Andrulis & Ruicong Chen.

## Updating the ADC Model
The generated ADC model is based on the data in Boris Murmann's survey [1],
included in the submodule. This survey is updated periodically. The model can
be update to reflect the most recent data by running the following:

```bash
pip3 install scikit-learn
pip3 install pandas
pip3 install numpy
git submodule update --init --recursive --remote
python3 update_model.py
```

This is only necessary if more recent data is published. If the data here is
out of date, please open an issue or pull request.

## References
[1] B. Murmann, "ADC Performance Survey 1997-2023," [Online]. Available:
https://github.com/bmurmann/ADC-survey

## License
This work is licensed under the MIT license. See license.txt for details.

## Citing HWComponents-ADC
If you use this model in your work, please cite the following:

```bibtex
@misc{andrulis2024modelinganalogdigitalconverterenergyarea,
      title={Modeling Analog-Digital-Converter Energy and Area for Compute-In-Memory Accelerator Design},
      author={Tanner Andrulis and Ruicong Chen and Hae-Seung Lee and Joel S. Emer and Vivienne Sze},
      year={2024},
      eprint={2404.06553},
      archivePrefix={arXiv},
      primaryClass={cs.AR},
      url={https://arxiv.org/abs/2404.06553},
}
```

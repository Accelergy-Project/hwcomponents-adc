import logging
import sys
import os
import re
from typing import Dict, List
import yaml
from hwcomponents_adc.headers import *
from .optimizer import ADCRequest
from hwcomponents import ComponentModel, action

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

MODEL_FILE = os.path.join(SCRIPT_DIR, "adc_data/model.yaml")

CLASS_NAMES = [
    "adc",
    "pim_adc",
    "sar_adc",
    "array_adc",
    "pim_array_adc",
    "cim_array_adc",
    "cim_adc",
]
ACTION_NAMES = ["convert", "drive", "read", "sample", "leak", "activate"]

# ==============================================================================
# Input Parsing
# ==============================================================================


def adc_attr_to_request(attributes: Dict, logger: logging.Logger) -> ADCRequest:
    """Creates an ADC Request from a list of attributes"""

    def checkerr(attr, numeric):
        assert attr in attributes, f"No attribute found: {attr}"
        if numeric and isinstance(attributes[attr], str):
            v = re.findall(r"(\d*\.?\d+|\d+\.?\d*)", attributes[attr])
            assert v, f"No numeric found for attribute: {attr}"
            return float(v[0])
        return attributes[attr]

    try:
        n_adcs = int(checkerr("n_adcs", numeric=True))
    except AssertionError:
        n_adcs = 1

    def try_check(keys, numeric):
        for k in keys[:-1]:
            try:
                return checkerr(k, numeric)
            except AssertionError:
                pass
        return checkerr(keys[-1], numeric)

    resolution_names = []
    for x0 in ["adc", ""]:
        for x1 in ["resolution", "bits", "n_bits"]:
            for x2 in ["adc", ""]:
                x = "_".join([x for x in [x0, x1, x2] if x != ""])
                resolution_names.append(x)
    resolution_names.append("resolution")

    r = ADCRequest(
        bits=try_check(resolution_names, numeric=True),
        tech=float(checkerr("tech_node", numeric=True)) * 1e9,  # m -> nm
        throughput=float(checkerr("throughput", numeric=True)),
        n_adcs=n_adcs,
        logger=logger,
    )
    return r


def dict_to_str(attributes: Dict) -> str:
    """Converts a dictionary into a multi-line string representation"""
    s = "\n"
    for k, v in attributes.items():
        s += f"\t{k}: {v}\n"
    return s


class ADC(ComponentModel):
    """
    Analog digital converter (ADC) model based on https://arxiv.org/abs/2404.06553.

    Args:
        n_bits: The number of bits of the ADC. For those who are not familiar with ADCs,
           ignore the following: this is assumed to be the effective number of bits
           (ENOB), not the bit precision of the output.
        tech_node: The technology node of the ADC in meters.
        throughput: The throughput of the ADC in samples per second.
        n_adcs: The number of ADCs. If there is >1 ADC, then throughput is the total
           throughput of all ADCs.

    Attributes:
        n_bits: The number of bits of the ADC.
        tech_node: The technology node of the ADC in meters.
        throughput: The throughput of the ADC in samples per second.
        n_adcs: The number of ADCs.
    """

    component_name = [
        "adc",
        "pim_adc",
        "sar_adc",
        "array_adc",
        "pim_array_adc",
        "cim_array_adc",
        "cim_adc",
    ]
    priority = 0.35

    def __init__(self, n_bits: int, tech_node: float, throughput: float, n_adcs=1):
        self.n_bits = n_bits
        self.tech_node = tech_node
        self.throughput = throughput
        self.n_adcs = n_adcs

        self._model = self.make_model()

        assert self.n_bits >= 4, f"Bits must be >= 4"

        area = self._get_area()
        # Assume leakage is 20% of the total energy
        leak_power = self.get_energy() * self.throughput * 0.2
        super().__init__(leak_power=leak_power, area=area)

    def make_model(self):
        if not os.path.exists(MODEL_FILE):
            self.logger.info(f'python3 {os.path.join(SCRIPT_DIR, "run.py")} -g')
            os.system(f'python3 {os.path.join(SCRIPT_DIR, "run.py")} -g')
        if not os.path.exists(MODEL_FILE):
            self.logger.error(f"ERROR: Could not find model file: {MODEL_FILE}")
            self.logger.error(
                f'Try running: "python3 {os.path.join(SCRIPT_DIR, "run.py")} '
                f'-g" to generate a model.'
            )
        with open(MODEL_FILE, "r") as f:
            self._model = yaml.safe_load(f)
        return self._model

    def _get_area(self) -> float:
        """
        Returns the area of the ADC in um^2
        """
        request = adc_attr_to_request(
            {
                "n_bits": self.n_bits,
                "tech_node": self.tech_node,
                "throughput": self.throughput,
                "n_adcs": self.n_adcs,
            },
            self.logger,
        )
        return request.area(self._model) * 1e-12  # um^2 -> m^2

    def get_energy(self):
        """
        Returns the energy for one ADC conversion in Joules.

        Returns:
            The energy for one ADC conversion in Joules.
        """
        request = adc_attr_to_request(
            {
                "n_bits": self.n_bits,
                "tech_node": self.tech_node,
                "throughput": self.throughput,
                "n_adcs": self.n_adcs,
            },
            self.logger,
        )
        return request.energy_per_op(self._model) * 1e-12  # pJ -> J

    @action
    def convert(self) -> tuple[float, float]:
        """
        Returns the energy and latency for one ADC conversion.

        Returns:
            (energy, latency): Tuple in (Joules, seconds).
        """
        # Assume leakage is 20% of the total energy
        return self.get_energy() * 0.8, 1 / self.throughput

    @action
    def drive(self) -> tuple[float, float]:
        """
        Returns the energy and latency for one ADC conversion.

        Returns:
            (energy, latency): Tuple in (Joules, seconds).
        """
        return self.convert()

    @action
    def read(self) -> tuple[float, float]:
        """
        Returns the energy and latency for one ADC conversion.

        Returns:
            (energy, latency): Tuple in (Joules, seconds).
        """
        return self.convert()

    @action
    def sample(self) -> tuple[float, float]:
        """
        Returns the energy and latency for one ADC conversion.

        Returns:
            (energy, latency): Tuple in (Joules, seconds).
        """
        return self.convert()

    @action
    def activate(self) -> tuple[float, float]:
        """
        Returns the energy and latency for one ADC conversion.

        Returns:
            (energy, latency): Tuple in (Joules, seconds).
        """
        return self.convert()

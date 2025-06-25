import logging
import sys
import os
import re
from typing import Dict, List
import yaml
from hwcomponents_adc.headers import *
from .optimizer import ADCRequest
from hwcomponents import EnergyAreaEstimator, actionDynamicEnergy

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
        tech=float(checkerr("tech_node", numeric=True)),
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


class ADC(EnergyAreaEstimator):
    component_name = [
        "adc",
        "pim_adc",
        "sar_adc",
        "array_adc",
        "pim_array_adc",
        "cim_array_adc",
        "cim_adc",
    ]
    percent_accuracy_0_to_100 = 75

    def __init__(self, n_bits: int, tech_node: str, throughput: float, n_adcs=1):
        self.n_bits = n_bits
        self.tech_node = tech_node
        self.throughput = throughput
        self.n_adcs = n_adcs

        self.model = self.make_model()

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
            self.model = yaml.safe_load(f)
        return self.model

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
        return request.area(self.model) * 1e-12  # um^2 -> m^2

    def get_energy(self):
        request = adc_attr_to_request(
            {
                "n_bits": self.n_bits,
                "tech_node": self.tech_node,
                "throughput": self.throughput,
                "n_adcs": self.n_adcs,
            },
            self.logger,
        )
        return request.energy_per_op(self.model) * 1e-12  # pJ -> J

    @actionDynamicEnergy
    def convert(self):
        # Assume leakage is 20% of the total energy
        return self.get_energy() * 0.8

    @actionDynamicEnergy
    def drive(self):
        return self.convert()

    @actionDynamicEnergy
    def read(self):
        return self.convert()

    @actionDynamicEnergy
    def sample(self):
        return self.convert()

    @actionDynamicEnergy
    def activate(self):
        return self.convert()
